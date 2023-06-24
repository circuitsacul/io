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


K = t.TypeVar("K")
V = t.TypeVar("V")


def sole_or_get(dct: dict[K, V], key: K) -> V | None:
    if len(dct) == 1:
        return next(iter(dct.values()))
    return dct.get(key)


@plugin.include
@crescent.event
async def on_modal(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ModalInteraction):
        return

    if not (message := event.interaction.message):
        return
    if not (inst := instances.get(message.id)):
        return

    lang: str | None = event.interaction.components[0].components[0].value
    if lang == "default":
        if inst.code:
            lang = inst.code.language
        else:
            lang = None
        inst.update_language(lang, False)
    else:
        inst.update_language(lang, True)

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
        new_inst.response = inst.response
        inst = new_inst
        instances[event.interaction.message.id] = inst
    elif id == "code_block":
        if v := event.interaction.values:
            for x, block in enumerate(inst.codes):
                if str(x) == v[0]:
                    inst.update_code(block)
                    break
        else:
            if inst.codes:
                inst.update_code(inst.codes[0])
    elif id == "language":
        await event.app.rest.create_modal_response(
            event.interaction,
            event.interaction.token,
            title="Select Language",
            custom_id="language",
            component=event.app.rest.build_modal_action_row().add_text_input(
                "language", "Language", placeholder='Use "default" to use the default.'
            ),
        )
        return
    elif id == "toggle_mode":
        if inst.action is models.Action.RUN:
            inst.update_action(models.Action.ASM)
        else:
            inst.update_action(models.Action.RUN)
    elif id == "instruction_set":
        if v := event.interaction.values:
            inst.instruction_set = v[0]
        else:
            inst.instruction_set = None
        inst.compiler_type = None
        inst.version = None
    elif id == "compiler_type":
        if v := event.interaction.values:
            inst.compiler_type = v[0]
        else:
            inst.compiler_type = None
        inst.version = None
    elif id == "version":
        if v := event.interaction.values:
            inst.version = v[0]
        else:
            inst.version = None

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

    def update(self, v: T) -> None:
        self.v = v
        self.overwritten = False

    def user_update(self, v: T) -> None:
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

    code: t.Optional[models.Code] = None
    language: Setting[t.Optional[str]] = Setting.make(None)
    action: models.Action = models.Action.RUN
    instruction_set: str | None = None
    compiler_type: str | None = None
    version: str | None = None

    response: t.Optional[hikari.Snowflake] = None

    def update_code(self, code: models.Code | None) -> None:
        self.code = code
        if code and code.language and not self.language.overwritten:
            self.update_language(code.language, False)

    def update_language(self, language: str | None, user: bool) -> None:
        if user:
            self.language.user_update(language)
        else:
            self.language.update(language)

        self.reset_selectors()

    def update_action(self, action: models.Action) -> None:
        self.action = action

        self.reset_selectors()

    def reset_selectors(self) -> None:
        self.instruction_set = None
        self.compiler_type = None
        self.version = None

    def selectors(self) -> list[tuple[str, str | None, list[str | None]]]:
        if self.language.v is None:
            return []

        selectors: list[tuple[str, str | None, list[str | None]]] = []

        runtimes = plugin.model.manager.runtimes
        if self.action is models.Action.RUN:
            if run_tree := runtimes.run.get(self.language.v):
                selectors.append(("version", self.version, list(run_tree)))
        else:
            if instructions := sole_or_get(runtimes.asm, self.language.v):
                selectors.append(
                    ("instruction_set", self.instruction_set, list(instructions))
                )

                if compilers := sole_or_get(instructions, self.instruction_set):
                    selectors.append(
                        ("compiler_type", self.compiler_type, list(compilers))
                    )

                    if versions := sole_or_get(compilers, self.compiler_type):
                        selectors.append(("version", self.version, list(versions)))

        return selectors

    @property
    def runtime(self) -> models.Runtime | None:
        lang = self.language.v

        def get_run_runtime() -> models.Runtime | None:
            tree = plugin.model.manager.runtimes.run
            if lang in tree:
                return sole_or_get(tree[lang], self.version)

            return None

        def get_asm_runtime() -> models.Runtime | None:
            tree = plugin.model.manager.runtimes.asm
            if not (tree2 := tree.get(lang)):
                return None

            if not (tree3 := sole_or_get(tree2, self.instruction_set)):
                return None
            if not (tree4 := sole_or_get(tree3, self.compiler_type)):
                return None

            return sole_or_get(tree4, self.version)

        if self.action is models.Action.RUN:
            return get_run_runtime()
        else:
            return get_asm_runtime()

    @staticmethod
    async def from_original(
        message: hikari.Message,
        requester: hikari.Snowflake,
    ) -> Instance | None:
        codes = await parse.get_codes(message)
        if not codes:
            return None

        instance = Instance(message.channel_id, message.id, requester, codes)
        instance.update_code(codes[0])

        return instance

    async def update(self, message: hikari.Message) -> None:
        if not (codes := await parse.get_codes(message)):
            return

        self.codes = codes
        self.update_code(codes[0])

    def components(self) -> list[hikari.api.MessageActionRowBuilder]:
        rows = []

        # basic buttons
        rows.append(
            plugin.app.rest.build_message_action_row()
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY, "reset", label="Reset"
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                "toggle_mode",
                label="Mode: Execute"
                if self.action is models.Action.RUN
                else "Mode: ASM",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                "language",
                label=f"Language: {self.language.v or 'Unkown'}",
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
                select.add_option(label, str(x), is_default=block == self.code)
            rows.append(select.parent)

        # version
        for id, selected, options in self.selectors():
            if len(options) == 1:
                continue

            select = plugin.app.rest.build_message_action_row().add_text_menu(id)
            for option in options[0:25]:
                select.add_option(
                    str(option), str(option), is_default=option == selected
                )
            rows.append(select.parent)

        return rows

    async def execute(self) -> None:
        if not self.response:
            await plugin.app.rest.trigger_typing(self.channel)

        # try to execute code
        if self.runtime:
            ret = await self.runtime.provider.execute(self)
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
