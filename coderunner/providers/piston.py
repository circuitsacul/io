from __future__ import annotations

import typing as t

import aiohttp

from coderunner import models
from coderunner.providers.provider import Provider
from coderunner.utils.fixes import transform_code

if t.TYPE_CHECKING:
    from coderunner.plugins.instance import Instance


class Piston(Provider):
    URL = "https://emkc.org/api/v2/piston/"

    async def startup(self) -> None:
        self._session = aiohttp.ClientSession(
            headers={"content-type": "application/json"}
        )

    async def update_data(self) -> None:
        runtimes = models.RuntimeTree()

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

                runtimes.run[data["language"]]["piston"]["piston"][version] = runtime

        self.runtimes = runtimes

    async def execute(self, instance: Instance) -> models.Result:
        assert instance.runtime
        assert instance.language.v
        assert instance.code

        lang, version = instance.runtime.id.split("@")
        post_data = {
            "language": lang,
            "version": version,
            "files": [
                {"content": transform_code(lang, instance.code.code)}
            ],
        }
        async with self.session.post(self.URL + "execute", json=post_data) as resp:
            resp.raise_for_status()
            data = await resp.json()

        out = data["run"]["stdout"] + "\n" + data["run"]["stderr"]
        return models.Result(out)
