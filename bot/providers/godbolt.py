from __future__ import annotations

import typing as t

import aiohttp

from bot import models
from bot.config import CONFIG
from bot.providers.provider import Provider
from bot.utils.fixes import transform_code

if t.TYPE_CHECKING:
    from bot.plugins.instance import Instance


class GodBolt(Provider):
    URL = CONFIG.GODBOLT_URL

    async def startup(self) -> None:
        self._session = aiohttp.ClientSession(headers={"Accept": "application/json"})

    async def update_data(self) -> None:
        runtimes = models.RuntimeTree()

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
                for tree in [runtimes.asm, runtimes.run]:
                    # godbolt supports execution and compilation
                    # fmt: off
                    (
                        tree 
                        [data["lang"]]
                        [data["instructionSet"] or "none"]
                        [data["compilerType"] or "none"]
                        [data["semver"] or "none"]
                    ) = runtime
                    # fmt: on

        self.runtimes = runtimes

    async def _run(self, instance: Instance) -> models.Result:
        if not (rt := instance.runtime):
            return models.Result("No runtime selected.")
        if not (code := instance.code):
            return models.Result("No code to run.")
        if not (lang := instance.language.v):
            return models.Result("No language.")

        url = self.URL + f"compiler/{rt.id}/compile"
        post_data = {
            "source": transform_code(lang, code.code),
            "lang": lang.lower(),
            "options": {
                "compilerOptions": {"executorRequest": True},
                "filters": {"execute": True},
            },
        }

        async with self.session.post(url, json=post_data) as resp:
            resp.raise_for_status()
            data = await resp.json()

        if data["code"] == -1:
            out = "\n".join(dct["text"] for dct in data["buildResult"]["stderr"])
        else:
            out = (
                "\n".join(dct["text"] for dct in data["stdout"])
                + "\n"
                + "\n".join(dct["text"] for dct in data["stderr"])
            )

        return models.Result(out)

    async def _asm(self, instance: Instance) -> models.Result:
        assert instance.runtime
        assert instance.language.v
        assert instance.code

        rt = instance.runtime
        lang = instance.language.v
        code = instance.code

        url = self.URL + f"compiler/{rt.id}/compile"
        post_data = {
            "source": transform_code(lang, code.code),
            "lang": lang.lower(),
            "options": {
                "compilerOptions": {
                    "executorRequest": False,
                },
                "filters": {
                    "binary": False,
                    "binaryObject": False,
                    "commentOnly": True,
                    "demangle": True,
                    "directives": True,
                    "execute": False,
                    "intel": True,
                    "labels": True,
                    "libraryCode": False,
                    "trim": False,
                },
            },
        }

        async with self.session.post(url, json=post_data) as resp:
            resp.raise_for_status()
            data = await resp.json()

        out = (
            "\n".join(dct["text"] for dct in data["asm"])
            + "\n"
            + "\n".join(dct["text"] for dct in data["stderr"])
        )
        return models.Result(out)

    async def execute(self, instance: Instance) -> models.Result:
        match instance.action:
            case models.Action.RUN:
                return await self._run(instance)
            case models.Action.ASM:
                return await self._asm(instance)
