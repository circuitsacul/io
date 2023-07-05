from __future__ import annotations

import asyncio
import typing as t

from bot import models
from bot.aliases import ALIASES
from bot.providers.godbolt import GodBolt
from bot.providers.piston import Piston
from bot.providers.provider import Provider

if t.TYPE_CHECKING:
    from bot.app import Model


class Manager:
    def __init__(self, model: Model) -> None:
        self.providers: list[Provider] = [GodBolt(model), Piston(model)]
        self.runtimes = models.RuntimeTree()
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

        return ALIASES.get(language)
