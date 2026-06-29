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
    if me := plugin.app.get_me():
        ct = ct.removeprefix(f"<@{me.id}>").strip()
    ct = ct.removeprefix("io/").strip()

    if ct.startswith("run"):
        action = models.Action.RUN
    elif ct.startswith("asm"):
        action = models.Action.ASM
    else:
        return None

    instance = await Instance.from_original(event.message, event.author_id)
    if not instance:
        return

    instance.action = action
    await instance.execute()
