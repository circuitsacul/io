from __future__ import annotations

import functools
import re
import typing as t
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto

import dahlia

from bot.providers.provider import Provider
from bot.utils.display import format_text


class Action(Enum):
    RUN = auto()
    ASM = auto()


@dataclass
class Runtime:
    id: str
    name: str
    description: str
    provider: Provider


@dataclass
class Code:
    code: str
    filename: t.Optional[str] = None
    language: t.Optional[str] = None


@dataclass
class Result:
    output: str

    def format(self) -> str:
        out = format_text(self.output)
        try:
            out = dahlia.quantize_ansi(out, to=3)
        except Exception:
            pass
        return out


TREE_T = t.Dict[
    str | None,  # language
    t.Dict[
        str | None,  # Instruction Set
        t.Dict[
            str | None,  # Compiler Type
            t.Dict[
                str | None,  # Version
                Runtime,
            ],
        ],
    ],
]


def make_tree() -> TREE_T:
    return defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))


@dataclass
class RuntimeTree:
    asm: TREE_T = field(default_factory=make_tree)
    run: TREE_T = field(default_factory=make_tree)

    def extend(self, other: RuntimeTree) -> None:
        for this_tree, other_tree in [(self.asm, other.asm), (self.run, other.run)]:
            for lang, tree in other_tree.items():
                for compiler, tree2 in tree.items():
                    for instruction, tree3 in tree2.items():
                        for version, runtime in tree3.items():
                            this_tree[lang][compiler][instruction][version] = runtime

    def sort(self) -> None:
        self.asm = sort(self.asm)
        self.run = sort(self.run)


K = t.TypeVar("K")
T = t.TypeVar("T")
SEMVER_RE = re.compile(r"(\d+)(\.(\d+))+")


@dataclass
@functools.total_ordering
class Key:
    semver: t.Optional[list[int]]
    string: str

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, Key)
        if self.semver and other.semver:
            return self.semver < other.semver

        if self.string == "piston":
            return True
        elif other.string == "piston":
            return False

        return self.string > other.string

    def __eq__(self, other: object) -> bool:
        return False


def sort(item: dict[K, T]) -> dict[K, T]:
    def key(item: tuple[K, object]) -> Key:
        key = item[0]
        if isinstance(key, str):
            if m := SEMVER_RE.search(key):
                version = [int(i) for i in m.group().split(".")]
                return Key(version, key)
        return Key([], str(key))

    item = {k: v for k, v in sorted(item.items(), key=key, reverse=True)}
    for k, v in item.items():
        if isinstance(v, dict):
            item[k] = t.cast(T, sort(v))

    return item
