import crescent
import hikari

from coderunner import models
from coderunner.app import Plugin
from coderunner.plugins.instance import Instance

plugin = Plugin()


@plugin.include
@crescent.event
async def on_message(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human:
        return None
    if not (ct := event.message.content):
        return None
    if cmd := ct.lstrip("io/"):
        try:
            cmd = cmd.split(" ", 1)[0]
        except KeyError:
            return None
        match cmd:
            case "run":
                action = models.Action.RUN
            case "asm":
                action = models.Action.ASM
            case unknown:
                await event.message.respond(f"Unknown command {unknown}.", reply=True)
                return None

    instance = await Instance.from_original(event.message, event.author_id)
    if not instance:
        return

    instance.action = action
    await instance.execute()
