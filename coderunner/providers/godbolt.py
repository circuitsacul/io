from __future__ import annotations

import typing as t

import aiohttp

from coderunner import models
from coderunner.providers.provider import Provider

if t.TYPE_CHECKING:
    from coderunner.plugins.instance import Instance


class GodBolt(Provider):
    URL = "https://godbolt.org/api/"

    async def startup(self) -> None:
        self._session = aiohttp.ClientSession(headers={"Accept": "application/json"})

    async def update_data(self) -> None:
        runtimes = models.RuntimeTree()

        async with self.session.get(self.URL + "languages/") as resp:
            resp.raise_for_status()
            for data in await resp.json():
                runtime = models.Runtime(
                    id=data["id"],
                    name=data["name"],
                    description=data["name"],
                    provider=self,
                )
                runtimes.run[data["id"]]["godbolt"] = runtime

        async with self.session.get(self.URL + "compilers/") as resp:
            resp.raise_for_status()
            for data in await resp.json():
                runtime = models.Runtime(
                    id=data["id"],
                    name=data["name"],
                    description="{}/{}/{}/{}".format(
                        data["lang"],
                        data["instructionSet"] or "none",
                        data["compilerType"] or "none",
                        data["semver"] or "none",
                    ),
                    provider=self,
                )
                # fmt: off
                (
                    runtimes.asm
                    [data["lang"]]
                    [data["instructionSet"] or "none"]
                    [data["compilerType"] or "none"]
                    [data["semver"] or "none"]
                ) = runtime
                # fmt: on

        self.runtimes = runtimes

    async def execute(self, instance: Instance) -> models.Result:
        return models.Result(str(instance) + "\n\n" + str(self))
