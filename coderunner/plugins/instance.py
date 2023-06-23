from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

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
    if rt := inst.valid_runtimes:
        inst.runtime.v = rt[0]
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

    if id == "reset":
        message = await plugin.app.rest.fetch_message(inst.channel, inst.message)
        new_inst = await Instance.from_original(message, inst.requester)
        if new_inst is None:
            await plugin.app.rest.delete_message(
                inst.channel, event.interaction.message.id
            )
            return
        inst = new_inst
        instances[event.interaction.message.id] = inst
    elif id == "toggle_advanced":
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
            component=event.app.rest.build_modal_action_row().add_text_input(
                "language", "Language"
            ),
        )
        return
    elif id == "version":
        assert inst.valid_runtimes is not None
        for runtime in inst.valid_runtimes:
            if runtime.id == event.interaction.values[0]:
                inst.runtime.user_update(runtime)
    elif id == "code_block":
        for x, block in enumerate(inst.codes):
            if str(x) == event.interaction.values[0]:
                inst.code.user_update(block)
                if block.language:
                    inst.language.v = block.language
                    inst.language.overwritten = False

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

    @classmethod
    def make(cls, v: T) -> Setting[T]:
        return field(default_factory=lambda: cls(v))


@dataclass
class Instance:
    channel: hikari.Snowflake
    message: hikari.Snowflake
    requester: hikari.Snowflake
    codes: list[models.Code]

    advanced: bool = False
    code: Setting[t.Optional[models.Code]] = Setting.make(None)
    language: Setting[t.Optional[str]] = Setting.make(None)
    runtime: Setting[t.Optional[models.Runtime]] = Setting.make(None)
    action: Setting[models.Action] = Setting.make(models.Action.RUN)

    response: t.Optional[hikari.Snowflake] = None

    @property
    def valid_runtimes(self) -> list[models.Runtime] | None:
        if not self.language.v:
            return None
        runtimes = plugin.model.manager.get_runtimes(self.language.v)
        if not runtimes:
            return None
        return [rt for rt in runtimes if rt.action is self.action.v]

    @staticmethod
    async def from_original(
        message: hikari.Message,
        requester: hikari.Snowflake,
        code: models.Code | None = None,
    ) -> Instance | None:
        codes = await parse.get_codes(message)
        if not codes:
            return None

        instance = Instance(message.channel_id, message.id, requester, codes)
        if not code:
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
        new = await Instance.from_original(
            message, self.requester, code=self.code.v if self.code.overwritten else None
        )
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

        language: str | None
        if self.language.v:
            language = plugin.model.manager.aliases.get(
                self.language.v, self.language.v
            )
        else:
            language = self.language.v

        # basic buttons
        rows.append(
            plugin.app.rest.build_message_action_row()
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                "toggle_advanced",
                label="Simple" if self.advanced else "Advanced",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY, "reset", label="Reset"
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                "toggle_mode",
                label="Assembly" if self.action.v is models.Action.RUN else "Run Code",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                "language",
                label=f"Language: {language or 'Unkown'}",
            )
        )

        # code block selection
        if len(self.codes) > 1:
            select = plugin.app.rest.build_message_action_row().add_text_menu(
                "code_block",
                placeholder="Select the code block to run",
            )
            for x, block in enumerate(self.codes):
                if block.filename:
                    label = f"Attachment {block.filename}"
                else:
                    label = f'Code Block: "{block.code[0:32]}..."'
                select.add_option(label, str(x), is_default=block == self.code.v)
            rows.append(select.parent)

        # version selection
        if (
            not (runtimes := self.valid_runtimes)
            or self.advanced
            or self.runtime.overwritten
            or self.runtime.v is None
        ):
            select = plugin.app.rest.build_message_action_row().add_text_menu(
                "version", is_disabled=not runtimes
            )
            for runtime in runtimes or ():
                select.add_option(
                    f"{runtime.version} ({runtime.provider})",
                    runtime.id,
                    is_default=(
                        self.runtime.v is not None and runtime.id == self.runtime.v.id
                    ),
                )
            if not runtimes:
                mode = "execution" if self.action.v is models.Action.RUN else "assembly"
                select.add_option(
                    f"No runtimes for {language} in {mode} mode.",
                    "na",
                    is_default=True,
                )
            rows.append(select.parent)

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
