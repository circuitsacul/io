from __future__ import annotations

import abc
import typing as t

if t.TYPE_CHECKING:
    from coderunner import models
    from coderunner.app import Model
    from coderunner.plugins.instance import Instance


class Provider(abc.ABC):
    def __init__(self, model: Model) -> None:
        self.model = model

    @abc.abstractmethod
    async def execute(self, instance: Instance) -> models.Result:
        ...

    @abc.abstractmethod
    async def update_data(self) -> None:
        ...

    @abc.abstractproperty
    def languages(self) -> dict[str, list[models.Runtime]]:
        ...

    def __str__(self) -> str:
        return self.__class__.__name__.lower()
