import os

import crescent
import dotenv
import hikari

from coderunner.manager import Manager

Plugin = crescent.Plugin[hikari.GatewayBot, "Model"]
INTENTS = hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT


class Model:
    def __init__(self) -> None:
        self.manager = Manager(self)


def main() -> None:
    dotenv.load_dotenv()

    token = os.getenv("TOKEN")
    if not token:
        print("No token.")
        return

    app = hikari.GatewayBot(token, intents=INTENTS)
    client = crescent.Client(app, Model())

    client.plugins.load_folder("coderunner.plugins")
    app.run()
