import crescent
import hikari

from bot.app import Plugin
from bot.constants import EMBED_COLOR

plugin = Plugin()

HELP_EMBEDS = [
    hikari.Embed(
        description=(
            "Hi! My name is io, and my job is to run code."
            "\n I can run any code inside of code blocks:"
            "\n```"
            "\n`\u200b`\u200b`\u200b<language-name>"
            "\n<your code here>"
            "\n`\u200b`\u200b`\u200b"
            "\n```"
        ),
        color=EMBED_COLOR,
    ),
    hikari.Embed(
        description=(
            "\n- Running code - Start your message with `io/run`."
            "\n- View Assembly - Start your message with `io/asm`."
            "\nYou can use message commands by right-clicking on a message, "
            "selecting the `Apps` subcategory, then clicking on the `Create Instance` "
            "command."
        ),
        color=EMBED_COLOR,
    ),
]


@plugin.include
@crescent.command
async def help(ctx: crescent.Context) -> None:
    await ctx.respond(embeds=HELP_EMBEDS)


@plugin.include
@crescent.event
async def on_message(message: hikari.MessageCreateEvent) -> None:
    me = plugin.app.get_me()

    if not me:
        return

    if message.author_id == me.id:
        return

    if not message.content:
        return

    if not (
        message.content == me.mention
        or (
            message.content.startswith(me.mention)
            and message.content.removeprefix(me.mention).strip() == "help"
        )
    ):
        return

    await message.message.respond(embeds=HELP_EMBEDS, reply=True)
