import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import pagify




class Mewtradeutil(commands.Cog):
    """Trade Utility for mewbot"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def trade(self, ctx, msg_id: int):
        """Trade Utility for Mewbot"""
        m = await ctx.channel.fetch_message(msg_id)
        lines = m.embeds[0].description.split('\n')
        result = []  #  <---here?
        for line in lines:
            start = line.find('**__No.__** - ')
            sub = line[start + 14:]
            end = sub.find('|')
            final = sub[:end - 1]
            result.append(int(final))
        result = " ".join([str(x) for x in result])
        embed = discord.Embed(title = "ID's requested", description=result, color=0xEE8700)
        await ctx.send(embed=embed)
        await ctx.send(result)



def setup(bot):
    bot.add_cog(Mewtradeutil(Bot))
