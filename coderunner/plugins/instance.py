from __future__ import annotations

import typing as t
from dataclasses import dataclass

import crescent
import hikari

from coderunner import models
from coderunner.app import Plugin
from coderunner.utils import parse

plugin = Plugin()
instances: dict[hikari.Snowflake, Instance] = {}


@plugin.include
@crescent.event
async def on_modal(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ModalInteraction):
        return

    if not (message := event.interaction.message):
        return
    if not (inst := instances.get(message.id)):
        return

    inst.language.user_update(event.interaction.components[0].components[0].value)
    await event.app.rest.create_interaction_response(
        event.interaction,
        event.interaction.token,
        hikari.ResponseType.MESSAGE_UPDATE,
        components=inst.components(),
    )
    await inst.execute()


@plugin.include
@crescent.event
async def on_button(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ComponentInteraction):
        return

    if not (inst := instances.get(event.interaction.message.id)):
        return
    id = event.interaction.custom_id

    if id == "toggle_advanced":
        inst.advanced = not inst.advanced
    elif id == "toggle_mode":
        if inst.action.v is models.Action.RUN:
            inst.action.user_update(models.Action.ASM)
        else:
            inst.action.user_update(models.Action.RUN)
        if rt := inst.valid_runtimes:
            inst.runtime.overwritten = False
            inst.runtime.v = rt[0]
    elif id == "language":
        await event.app.rest.create_modal_response(
            event.interaction,
            event.interaction.token,
            title="Select Language",
            custom_id="language",
            component=event.app.rest.build_modal_action_row()
            .add_text_input("language", "Language")
            .add_to_container(),
        )
        return

    await event.app.rest.create_interaction_response(
        event.interaction,
        event.interaction.token,
        hikari.ResponseType.MESSAGE_UPDATE,
        components=inst.components(),
    )
    await inst.execute()


T = t.TypeVar("T")


@dataclass
class Setting(t.Generic[T]):
    v: T
    overwritten: bool = False

    def user_update(self, v: T) -> None:
        if v == self.v:
            self.overwritten = False
        else:
            self.v = v
            self.overwritten = True


@dataclass
class Instance:
    channel: hikari.Snowflake
    message: hikari.Snowflake
    requester: hikari.Snowflake
    codes: list[models.Code]

    advanced: bool = False
    code: Setting[t.Optional[models.Code]] = Setting(None)
    language: Setting[t.Optional[str]] = Setting(None)
    runtime: Setting[t.Optional[models.Runtime]] = Setting(None)
    action: Setting[models.Action] = Setting(models.Action.RUN)

    response: t.Optional[hikari.Snowflake] = None

    @property
    def valid_runtimes(self) -> list[models.Runtime] | None:
        for name, runtimes in plugin.model.manager.runtimes.items():
            if name == self.language.v:
                return [rt for rt in runtimes if rt.action is self.action.v]
        return None

    @staticmethod
    async def from_original(
        message: hikari.Message, requester: hikari.Snowflake
    ) -> Instance | None:
        codes = await parse.get_codes(message)
        if not codes:
            return None

        instance = Instance(message.channel_id, message.id, requester, codes)
        code = codes[0]
        instance.code = Setting(code)
        if code.language and (
            runtimes := plugin.model.manager.get_runtimes(code.language)
        ):
            rt = runtimes[0]
            instance.language = Setting(rt.name)
            instance.runtime = Setting(rt)

        return instance

    async def update(self, message: hikari.Message) -> None:
        new = await Instance.from_original(message, self.requester)
        if not new:
            return

        self.codes = new.codes
        if not self.code.overwritten:
            self.code = new.code
        if not self.language.overwritten:
            self.language = new.language
        if not self.action.overwritten:
            self.action = new.action

    def components(self) -> list[hikari.api.MessageActionRowBuilder]:
        rows = []

        # basic buttons
        rows.append(
            plugin.app.rest.build_message_action_row()
            .add_button(hikari.ButtonStyle.SECONDARY, "toggle_advanced")
            .set_emoji("⚙️")
            .add_to_container()
            .add_button(hikari.ButtonStyle.SECONDARY, "toggle_mode")
            .set_label("Assembly" if self.action.v is models.Action.RUN else "Run Code")
            .add_to_container()
            .add_button(hikari.ButtonStyle.SECONDARY, "language")
            .set_label(f"Language: {self.language.v or 'Unknown'}")
            .add_to_container()
        )

        # code block selection
        if len(self.codes) > 1 and (self.advanced or self.code.overwritten):
            select = (
                plugin.app.rest.build_message_action_row()
                .add_select_menu(3, "code_block")
                .set_placeholder("Select the code block to run")
            )
            for x, block in enumerate(self.codes):
                if block.filename:
                    label = f"Attachment {block.filename}"
                else:
                    label = f'Code Block: "{block.code[0:32]}..."'
                option = select.add_option(label, str(x))
                if block == self.code.v:
                    option = option.set_is_default(True)
                select = option.add_to_menu()
            rows.append(select.add_to_container())

        # version selection
        if (
            not (runtimes := self.valid_runtimes)
            or self.advanced
            or self.runtime.overwritten
        ):
            select = plugin.app.rest.build_message_action_row().add_select_menu(
                3, "version"
            )
            for runtime in runtimes or ():
                option = select.add_option(
                    f"{runtime.version} ({runtime.provider})", runtime.id
                )
                if self.runtime.v and runtime.id == self.runtime.v.id:
                    option = option.set_is_default(True)
                select = option.add_to_menu()
            if not runtimes:
                mode = "execution" if self.action.v is models.Action.RUN else "assembly"
                select = (
                    select.add_option(
                        f"No runtimes for {self.language.v} in {mode} mode.", "na"
                    )
                    .set_is_default(True)
                    .add_to_menu()
                    .set_is_disabled(True)
                )
            rows.append(select.add_to_container())

        return rows

    async def execute(self) -> None:
        if not self.response:
            await plugin.app.rest.trigger_typing(self.channel)

        # try to execute code
        if self.runtime.v:
            ret = await self.runtime.v.provider.execute(self)
            out = ret.output
        else:
            out = None

        # send message
        rows = self.components()
        if self.response:
            await plugin.app.rest.edit_message(
                self.channel, self.response, out, components=rows
            )
        else:
            resp = await plugin.app.rest.create_message(
                self.channel,
                out,
                reply=self.message,
                mentions_reply=True,
                components=rows,
            )
            self.response = resp.id
            instances[resp.id] = self
