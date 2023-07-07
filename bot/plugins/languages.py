import crescent
import hikari

from bot.app import Plugin
from bot.constants import EMBED_COLOR

plugin = Plugin()


@plugin.include
@crescent.command
async def languages(ctx: crescent.Context) -> None:
    lang_names = list(
        f"`{runtime}`" for runtime in plugin.model.manager.runtimes.run if runtime
    )
    embed = hikari.Embed(
        title="Supported Languages", description=",".join(lang_names), color=EMBED_COLOR
    )
    await ctx.respond(embed=embed)
