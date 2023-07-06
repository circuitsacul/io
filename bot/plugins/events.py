import crescent
import hikari

from bot import models
from bot.app import Plugin
from bot.plugins.instance import Instance

plugin = Plugin()


@plugin.include
@crescent.event
async def on_message(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human:
        return None
    if not (ct := event.message.content):
        return None
    if not ct.startswith("io/"):
        return None
    try:
        cmd = ct[3:].splitlines()[0].split(" ", 1)[0]
    except KeyError:
        return None
    match cmd:
        case "run":
            action = models.Action.RUN
        case "asm":
            action = models.Action.ASM
        case _:
            return None

    instance = await Instance.from_original(event.message, event.author_id)
    if not instance:
        return

    instance.action = action
    await instance.execute()
