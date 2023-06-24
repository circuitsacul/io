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
        self.runtimes = models.RuntimeTree()
        self.aliases: dict[str, str] = {}
        self.model = model

    async def startup(self) -> None:
        await asyncio.gather(
            *(asyncio.create_task(p.startup()) for p in self.providers)
        )

    async def shutdown(self) -> None:
        await asyncio.gather(
            *(asyncio.create_task(p.shutdown()) for p in self.providers)
        )

    async def update_data(self) -> None:
        await asyncio.gather(
            *(asyncio.create_task(p.update_data()) for p in self.providers)
        )

        runtimes = models.RuntimeTree()
        for provider in self.providers:
            runtimes.extend(provider.runtimes)
        runtimes.sort()
        self.runtimes = runtimes

    def unalias(self, language: str) -> str | None:
        if language in self.runtimes.run or language in self.runtimes.asm:
            return language

        return self.aliases.get(language)
