import crescent
import hikari

from coderunner.app import Plugin
from coderunner.plugins.instance import Instance

plugin = Plugin()


@plugin.include
@crescent.event
async def on_message(event: hikari.MessageCreateEvent) -> None:
    instance = await Instance.from_original(event.message, event.author_id)
    if not instance:
        return

    await instance.execute()
