from __future__ import annotations

import contextlib
import enum
import typing as t
from dataclasses import dataclass, field

import crescent
import hikari

from bot import models
from bot.app import Plugin
from bot.lang_defaults import DEFAULTS
from bot.utils import parse

plugin = Plugin()
instances: dict[hikari.Snowflake, Instance] = {}


K = t.TypeVar("K")
V = t.TypeVar("V")


class ComponentID(enum.StrEnum):
    DELETE = "delete"
    REFRESH_CODE = "refresh_code"
    CODE_BLOCK = "code_block"
    LANGUAGE = "language"
    TOGGLE_MODE = "toggle_mode"
    INSTRUCTION_SET = "instruction_set"
    COMPILER_TYPE = "compiler_type"
    VERSION = "version"
    STDIN = "stdin"


class ModalID(enum.StrEnum):
    LANGUAGE = "language"
    STDIN = "stdin"


def next_in_default_chain(path: list[str | None]) -> str | None:
    tree = DEFAULTS
    for k in path:
        if isinstance(tree, str):
            return None
        tree = tree.get(k)  # type: ignore
        if not tree:
            return None

    if isinstance(tree, str):
        return tree
    elif isinstance(tree, dict):
        return next(iter(tree.keys()))
    return None


def get_or_first(
    dct: dict[str | None, V], key: str | None, path: list[str | None]
) -> tuple[str | None, V] | None:
    with contextlib.suppress(KeyError):
        return (key, dct[key])

    if k := next_in_default_chain(path):
        with contextlib.suppress(KeyError):
            return (k, dct[k])

    with contextlib.suppress(StopIteration):
        return next(iter(dct.items()))

    return None


@plugin.include
@crescent.event
async def on_modal_interaction(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ModalInteraction):
        return

    if not (message := event.interaction.message):
        return

    if not (inst := instances.get(message.id)):
        return

    id = event.interaction.custom_id

    match id:
        case ModalID.LANGUAGE:
            lang: str | None = event.interaction.components[0].components[0].value
            if not lang:
                if inst.code:
                    lang = inst.code.language
                else:
                    lang = None
                inst.update_language(lang, False)
            else:
                inst.update_language(lang, True)
        case ModalID.STDIN:
            inst.stdin = event.interaction.components[0].components[0].value

    await event.app.rest.create_interaction_response(
        event.interaction,
        event.interaction.token,
        hikari.ResponseType.MESSAGE_UPDATE,
        components=inst.components(),
        content="Working...",
        attachment=None,
    )
    await inst.execute()


@plugin.include
@crescent.event
async def on_component_interaction(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ComponentInteraction):
        return

    if not (inst := instances.get(event.interaction.message.id)):
        return

    if event.interaction.user.id != inst.requester:
        await event.app.rest.create_interaction_response(
            event.interaction,
            event.interaction.token,
            hikari.ResponseType.MESSAGE_CREATE,
            flags=hikari.MessageFlag.EPHEMERAL,
            content="Only the person who created this instance can edit it.",
        )
        return

    id = event.interaction.custom_id

    match id:
        case ComponentID.DELETE:
            await inst.delete()
            return
        case ComponentID.REFRESH_CODE:
            message = await plugin.app.rest.fetch_message(inst.channel, inst.message)
            await inst.update(message)
        case ComponentID.CODE_BLOCK:
            if v := event.interaction.values:
                for x, block in enumerate(inst.codes):
                    if str(x) == v[0]:
                        inst.update_code(block)
                        break
            else:
                if inst.codes:
                    inst.update_code(inst.codes[0])
        case ComponentID.LANGUAGE:
            await event.app.rest.create_modal_response(
                event.interaction,
                event.interaction.token,
                title="Select Language",
                custom_id=ModalID.LANGUAGE,
                component=event.app.rest.build_modal_action_row().add_text_input(
                    ModalID.LANGUAGE,
                    "Language",
                    placeholder="Leave empty to use the default.",
                    required=False,
                ),
            )
            return
        case ComponentID.TOGGLE_MODE:
            if inst.action is models.Action.RUN:
                inst.update_action(models.Action.ASM)
            else:
                inst.update_action(models.Action.RUN)
        case ComponentID.INSTRUCTION_SET:
            if v := event.interaction.values:
                inst.instruction_set = v[0]
            else:
                inst.instruction_set = None
            inst.compiler_type = None
            inst.version = None
        case ComponentID.COMPILER_TYPE:
            if v := event.interaction.values:
                inst.compiler_type = v[0]
            else:
                inst.compiler_type = None
            inst.version = None
        case ComponentID.VERSION:
            if v := event.interaction.values:
                inst.version = v[0]
            else:
                inst.version = None
        case ComponentID.STDIN:
            await event.app.rest.create_modal_response(
                event.interaction,
                event.interaction.token,
                title="Set STDIN",
                custom_id=ModalID.STDIN,
                component=event.app.rest.build_modal_action_row().add_text_input(
                    ModalID.STDIN,
                    "Set STDIN",
                    value=inst.stdin or hikari.UNDEFINED,
                    required=False,
                    style=hikari.TextInputStyle.PARAGRAPH,
                ),
            )
            return

    await event.app.rest.create_interaction_response(
        event.interaction,
        event.interaction.token,
        hikari.ResponseType.MESSAGE_UPDATE,
        content="Working...",
        attachment=None,
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


class Selector(t.NamedTuple):
    id: ComponentID
    """The custom ID for the component used to select this."""
    selected: str | None
    """The currently selected runtime."""
    options: list[str | None]
    """A list of all runtimes the user can select."""


@dataclass
class Instance:
    channel: hikari.Snowflake
    message: hikari.Snowflake
    requester: hikari.Snowflake
    codes: list[models.Code]

    code: t.Optional[models.Code] = None
    stdin: str | None = None
    language: Setting[t.Optional[str]] = Setting.make(None)
    action: models.Action = models.Action.RUN
    instruction_set: str | None = None
    compiler_type: str | None = None
    version: str | None = None

    response: t.Optional[hikari.Snowflake] = None

    def update_code(self, code: models.Code | None) -> None:
        self.code = code
        if (
            code
            and code.language
            and plugin.model.manager.unalias(code.language.lower()) != self.language.v
            and not self.language.overwritten
        ):
            self.update_language(code.language, False)

    def update_language(self, language: str | None, user: bool) -> None:
        if language:
            language = plugin.model.manager.unalias(language.lower())
        if user:
            self.language.user_update(language)
        else:
            self.language.update(language)

        self.reset_selectors()

    def update_action(self, action: models.Action) -> None:
        self.action = action

    def reset_selectors(self) -> None:
        self.instruction_set = None
        self.compiler_type = None
        self.version = None

    def selectors(self) -> list[Selector]:
        if self.language.v is None:
            return []

        selectors: list[Selector] = []

        runtimes = plugin.model.manager.runtimes
        match self.action:
            case models.Action.RUN:
                tree = runtimes.run
            case models.Action.ASM:
                tree = runtimes.asm

        path: list[str | None] = []
        if instructions := tree.get(self.language.v):
            path.append(self.language.v)
            if instruction_set_select := get_or_first(
                instructions, self.instruction_set, path
            ):
                instruction_set, compilers = instruction_set_select
                if len(instructions) > 1:
                    selectors.append(
                        Selector(
                            id=ComponentID.INSTRUCTION_SET,
                            selected=instruction_set,
                            options=list(instructions),
                        )
                    )
                path.append(instruction_set)

                if compiler_type_select := get_or_first(
                    compilers, self.compiler_type, path
                ):
                    compiler, versions = compiler_type_select
                    if len(compilers) > 1:
                        selectors.append(
                            Selector(
                                id=ComponentID.COMPILER_TYPE,
                                selected=compiler,
                                options=list(compilers),
                            )
                        )
                    path.append(compiler)

                    if version_select := get_or_first(versions, self.version, path):
                        version, _ = version_select
                        selectors.append(
                            Selector(
                                id=ComponentID.VERSION,
                                selected=version,
                                options=list(versions),
                            )
                        )

        return selectors

    @property
    def runtime(self) -> models.Runtime | None:
        lang = self.language.v

        match self.action:
            case models.Action.RUN:
                tree = plugin.model.manager.runtimes.run
            case models.Action.ASM:
                tree = plugin.model.manager.runtimes.asm

        path: list[str | None] = [lang]
        if not (tree2 := tree.get(lang)):
            return None

        if not (tree3 := get_or_first(tree2, self.instruction_set, path)):
            return None
        self.instruction_set = tree3[0]
        path.append(tree3[0])
        if not (tree4 := get_or_first(tree3[1], self.compiler_type, path)):
            return None
        self.compiler_type = tree4[0]
        path.append(tree4[0])
        tree5 = get_or_first(tree4[1], self.version, path)
        if tree5:
            self.version = tree5[0]
            return tree5[1]
        else:
            return None

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

    async def delete(self) -> None:
        if not self.response:
            return
        try:
            await plugin.app.rest.delete_message(self.channel, self.response)
        except hikari.NotFoundError:
            pass
        else:
            del instances[self.response]

    async def update(self, message: hikari.Message) -> None:
        if not (codes := await parse.get_codes(message)):
            await self.delete()
            return

        self.codes = codes
        self.update_code(codes[0])

    def components(self) -> list[hikari.api.MessageActionRowBuilder]:
        rows = []

        # basic buttons
        rows.append(
            plugin.app.rest.build_message_action_row()
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY, ComponentID.DELETE, label="Delete"
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                ComponentID.REFRESH_CODE,
                label="Refresh Code",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                ComponentID.TOGGLE_MODE,
                label="Mode: Execute"
                if self.action is models.Action.RUN
                else "Mode: ASM",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                ComponentID.LANGUAGE,
                label=f"Language: {self.language.v or 'Unknown'}",
            )
            .add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                ComponentID.STDIN,
                label="Set STDIN",
            )
        )

        # code block selection
        if len(self.codes) > 1:
            select = plugin.app.rest.build_message_action_row().add_text_menu(
                ComponentID.CODE_BLOCK,
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
            select = (
                plugin.app.rest.build_message_action_row()
                .add_text_menu(id)
                .set_is_disabled(len(options) == 1)
            )
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
        code_file: hikari.Bytes | None = None
        stdin_file: hikari.Bytes | None = None
        out: list[str] = [f"<@{self.requester}>"]

        code_output_in_file = False
        stdin_in_file = False

        code_output: str = ""
        if self.runtime:
            ret = await self.runtime.provider.execute(self)
            code_output = ret.format()

            if not code_output.strip():
                out.append("Your code ran with no output.")
                code_output = ""
        else:
            out.append("No runtime selected.")

        stdin = self.stdin or ""
        formatted_stdin = "\n".join(
            f"\x1b[1;33mIN:\x1b[0m {line}" for line in stdin.splitlines()
        )

        if len(code_output) + len(formatted_stdin) > 1_950:
            if len(code_output) < 1_950:
                stdin_in_file = True
            elif len(formatted_stdin) < 1_950:
                code_output_in_file = True
            else:
                code_output_in_file = True
                stdin_in_file = True

        if code_output:
            if code_output_in_file:
                code_file = hikari.Bytes(code_output, "code.ansi")
            else:
                out.append(f"```ansi\n{code_output}```")

        if stdin:
            if stdin_in_file:
                stdin_file = hikari.Bytes(stdin, "stdin.txt")
            else:
                out.append(f"```ansi\n{formatted_stdin}```")

        # send message
        out_str = "\n".join(out)
        rows = self.components()
        attachments = list(filter(None, [code_file, stdin_file]))
        if self.response:
            await plugin.app.rest.edit_message(
                self.channel,
                self.response,
                out_str,
                components=rows,
                attachments=attachments,
            )
        else:
            resp = await plugin.app.rest.create_message(
                self.channel,
                out_str,
                reply=self.message,
                components=rows,
                attachments=attachments,
                user_mentions=[self.requester],
            )
            self.response = resp.id
            instances[resp.id] = self
