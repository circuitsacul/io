from __future__ import annotations

import asyncio
import typing as t

from coderunner import models
from coderunner.providers.godbolt import GodBolt
from coderunner.providers.piston import Piston
from coderunner.providers.provider import Provider

if t.TYPE_CHECKING:
    from coderunner.app import Model


class Manager:
    def __init__(self, model: Model) -> None:
        self.providers: list[Provider] = [GodBolt(model), Piston(model)]
        self.runtimes: dict[str, list[models.Runtime]] = {}
        self.aliases: dict[str, str] = {}
        self.model = model

    async def update_data(self) -> None:
        await asyncio.gather(
            *(asyncio.create_task(p.update_data()) for p in self.providers)
        )

        languages: dict[str, list[models.Runtime]] = {}
        for provider in self.providers:
            for name, langs in provider.languages.items():
                languages.setdefault(name, []).extend(langs)
                for alias in (alias for lang in langs for alias in lang.aliases):
                    self.aliases[alias] = name
        self.runtimes = languages

    def get_runtimes(self, language: str) -> list[models.Runtime] | None:
        if langs := self.runtimes.get(language):
            return langs

        if name := self.aliases.get(language):
            return self.get_runtimes(name)

        return None
