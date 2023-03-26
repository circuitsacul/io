from __future__ import annotations

import typing as t

from coderunner import models
from coderunner.providers.provider import Provider

if t.TYPE_CHECKING:
    from coderunner.plugins.instance import Instance


class GodBolt(Provider):
    @property
    def languages(self) -> dict[str, list[models.Runtime]]:
        return {
            "python": [
                models.Runtime(
                    "godbolt_python_run",
                    "python",
                    ["py"],
                    "3.0.0",
                    models.Action.RUN,
                    self,
                ),
                # models.Runtime(
                #     "godbolt_python_asm",
                #     "python",
                #     ["py"],
                #     "3.0.0",
                #     models.Action.ASM,
                #     self,
                # ),
            ]
        }

    async def update_data(self) -> None:
        pass

    async def execute(self, instance: Instance) -> models.Result:
        return models.Result(str(instance))
