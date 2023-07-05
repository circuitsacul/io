import crescent
import hikari

from bot.app import Plugin

from .instance import Instance

plugin = Plugin()

@plugin.include
@crescent.message_command(name="Create Instance")
async def create_instance(ctx: crescent.Context, msg: hikari.Message) -> None:
    inst = await Instance.from_original(msg, ctx.user.id)
    if not inst:
        await ctx.respond("No code blocks to run could be found.", ephemeral=True)
        return

    await ctx.respond("Instance created.", ephemeral=True)
    await inst.execute()
