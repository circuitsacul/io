from __future__ import annotations

import typing as t

import aiohttp

from bot import models
from bot.config import CONFIG
from bot.providers.provider import Provider
from bot.utils.fixes import transform_code

if t.TYPE_CHECKING:
    from bot.app import Model
    from bot.plugins.instance import Instance


class Piston(Provider):
    URL = CONFIG.PISTON_URL

    def __init__(self, model: Model) -> None:
        self.aliases: dict[str, str] = {}
        super().__init__(model)

    async def startup(self) -> None:
        self._session = aiohttp.ClientSession(
            headers={"content-type": "application/json"}
        )

    async def update_data(self) -> None:
        runtimes = models.RuntimeTree()
        aliases: dict[str, str] = {}

        async with self.session.get(self.URL + "runtimes/") as resp:
            resp.raise_for_status()
            for data in await resp.json():
                if "runtime" in data:
                    version = "{}@{}".format(data["runtime"], data["version"])
                else:
                    version = data["version"]
                runtime = models.Runtime(
                    id="{}@{}".format(data["language"], data["version"]),
                    name=data["language"],
                    description="{} {}".format(data["language"], version),
                    provider=self,
                )

                for alias in data["aliases"]:
                    aliases[alias] = runtime.name

                runtimes.run[data["language"]]["piston"]["piston"][version] = runtime

        self.aliases = aliases
        self.runtimes = runtimes

    async def execute(self, instance: Instance) -> models.Result:
        assert instance.runtime
        assert instance.language.v
        assert instance.code

        lang, version = instance.runtime.id.split("@")
        post_data = {
            "language": lang,
            "version": version,
            "files": [{"content": transform_code(lang, instance.code.code)}],
        }
        async with self.session.post(self.URL + "execute", json=post_data) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return models.Result(
            "\n".join(
                [
                    data.get("compile", {}).get("output", ""),
                    data.get("run", {}).get("output", ""),
                ]
            )
        )
