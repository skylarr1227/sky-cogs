import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import pagify




class Mewtradeutil(commands.Cog):
	"""Trade Utility for mewbot"""
	def __init__(self, bot):
		self.bot = bot
		
@commands.command(name='tradeutil')
async def trade(ctx, msg_id: int):
	"""Trade Utility for Mewbot"""
	m = await ctx.channel.fetch_message(msg_id)
	lines = m.embeds[0].description.split('\n')
	result = []
	for line in lines:
		start = line.find('**__No.__** - ')
		sub = line[start + 14:]
		end = sub.find('|')
		final = sub[:end - 1]
		result.append(int(final)
	await ctx.send()



def setup(bot):
    bot.add_cog(Mewtradeutil(Bot))
