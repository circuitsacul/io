from __future__ import annotations

import abc
import typing as t

import aiohttp

from bot import models

if t.TYPE_CHECKING:
    from bot.app import Model
    from bot.plugins.instance import Instance


class Provider(abc.ABC):
    def __init__(self, model: Model) -> None:
        self.model = model
        self.runtimes = models.RuntimeTree()
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        assert self._session, "aiohttp session not initialized"
        return self._session

    async def shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @abc.abstractmethod
    async def startup(self) -> None:
        ...

    @abc.abstractmethod
    async def execute(self, instance: Instance) -> models.Result:
        ...

    @abc.abstractmethod
    async def update_data(self) -> None:
        ...

    def __str__(self) -> str:
        return self.__class__.__name__.lower()
