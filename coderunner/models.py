from __future__ import annotations

import functools
import re
import typing as t
from collections import defaultdict
from dataclasses import dataclass, field
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


ASM_TREE_T = t.Dict[
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
RUN_TREE_T = t.Dict[str, t.Dict[str | None, Runtime]]


def make_asm_tree() -> ASM_TREE_T:
    return defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))


def make_run_tree() -> RUN_TREE_T:
    return defaultdict(dict)


@dataclass
class RuntimeTree:
    asm: ASM_TREE_T = field(default_factory=make_asm_tree)
    run: RUN_TREE_T = field(default_factory=make_run_tree)

    def extend(self, other: RuntimeTree) -> None:
        for lang, tree in other.asm.items():
            for compiler, tree2 in tree.items():
                for instruction, tree3 in tree2.items():
                    for version, runtime in tree3.items():
                        self.asm[lang][compiler][instruction][version] = runtime

        for lang, tree4 in other.run.items():
            for version, runtime in tree4.items():
                self.run[lang][version] = runtime

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
