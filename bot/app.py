import os

import crescent
import dotenv
import hikari

from bot.manager import Manager

Plugin = crescent.Plugin[hikari.GatewayBot, "Model"]
INTENTS = hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT


class Model:
    def __init__(self) -> None:
        self.manager = Manager(self)

    async def startup(self) -> None:
        await self.manager.startup()

    async def shutdown(self) -> None:
        await self.manager.shutdown()


def main() -> None:
    dotenv.load_dotenv()

    token = os.getenv("TOKEN")
    if not token:
        print("No token.")
        return

    app = hikari.GatewayBot(token, intents=INTENTS)
    client = crescent.Client(app, model := Model())

    @app.listen(hikari.StartingEvent)
    async def _(_: hikari.StartingEvent) -> None:
        await model.startup()

    @app.listen(hikari.StoppingEvent)
    async def _(_: hikari.StoppingEvent) -> None:
        await model.shutdown()

    client.plugins.load_folder("bot.plugins")
    app.run()
