from __future__ import annotations

import typing as t
from dataclasses import dataclass
from enum import Enum, auto

from coderunner.providers.provider import Provider


class Action(Enum):
    RUN = auto()
    ASM = auto()


@dataclass
class Support:
    run: bool
    asm: bool

    def supports(self, action: Action) -> bool:
        if action is Action.RUN:
            return self.run
        return self.asm


@dataclass
class Runtime:
    id: str
    name: str
    aliases: list[str]
    version: str
    action: Action
    provider: Provider


@dataclass
class Code:
    code: str
    filename: t.Optional[str] = None
    language: t.Optional[str] = None


@dataclass
class Result:
    output: str
