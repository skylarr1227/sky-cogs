import discord
from redbot.core import commands
from redbot.core import Config


def __init__(self, bot):
  self.config = Config.get_conf(self, identifier=790722073248661525)
  self.config.register_user(
    switch_code = None,
  )

@commands.command()
async def setswitch(self, ctx, code: str):
  await self.config.user(ctx.author).switch_code.set(code)
  embed = discord.Embed(title= "Successfull", description=f"Your Nintendo Switch invite code has been registered.\nCode:`{code}`, color=0xEE8700)
	await ctx.send(embed=embed)

@commands.command()
async def getswitch(self, ctx, member: discord.Member):
  code = await self.config.user(member).switch_code()
  if code is None:
    await ctx.send("This user does not have their switch invite code registered.")
    return
  embed = discord.Embed(title= f"Users Invite Code:", description=f"`{code}`, color=0xEE8700)
	await ctx.send(embed=embed)
