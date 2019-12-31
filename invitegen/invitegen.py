from discord.ext import commands
import discord
import random
import re
import asyncio
import time
import sys
from redbot.core import commands, checks, Config, bank
from redbot.core.utils.chat_formatting import box, humanize_list, pagify
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.predicates import MessagePredicate


bot = commands.Bot
BaseCog = getattr(commands, "Cog", object)
listener = getattr(commands.Cog, "listener", None) 
if listener is None:
  
    def listener(name=None):
        return lambda x: x
    
class invitegen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    

    @commands.command(name='skyping', description='a better way to pong')
    async def skyping(self, ctx):
        """Pings the bot."""
        joke = random.choice(["not actually pinging server...", "hey bb", "what am I doing with my life",
                              "Some Dragon is a dank music bot tbh", "I'd like to thank the academy for this award",
                              "The NSA is watching 👀", "`<Insert clever joke here>`", "¯\_(ツ)_/¯", "(づ｡◕‿‿◕｡)づ",
                              "I want to believe...", "Hypesquad is a joke", "EJH2#0330 is my daddy", "Robino pls",
                              "Seth got arrested again...", "Maxie y u do dis", "aaaaaaaaaaaAAAAAAAAAA", "owo",
                              "uwu", "meme team best team", "made with dicksword dot pee why", "I'm running out of "
                                                                                               "ideas here",
                              "am I *dank* enough for u?", "this is why we can't have nice things. come on",
                              "You'll understand when you're older...", "\"why\", you might ask? I do not know...",
                              "I'm a little tea pot, short and stout", "I'm not crying, my eyeballs "
                                                                       "are sweating!",
                              "When will the pain end?", "Partnership when?", "Hey Robino, rewrite when?"])
        before = time.monotonic()
        ping_msg = await ctx.send("Pinging Server...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await ping_msg.edit(content=joke + f" // ***{ping:.0f}ms***")




    @commands.command(name='joinsrv', description='send invite for discord server')
    async def create_invite(self, ctx, channel: int = None):
        """Create instant invite"""
        link = await ctx.channel.create_invite(message.channel_id, max_age = 300)
        await ctx.send(link)
    
    
    @commands.guild_only()    
    @checks.mod_or_permissions(administrator=True)    
    @commands.command(name='makeinvite', description='create invite for specified server')
    async def invite(self, ctx, guild=None):
        """
        Creates an invite to a specified server
        """
        guild_names = list("{} - ID: {}".format(g.name, g.id) for g in self.bot.guilds)
        if guild is None:
            guild = await reaction_menu.start_reaction_menu(self.bot, guild_names, ctx.author, ctx.channel, count=1,
                                                            timeout=60, per_page=10, header=header,
                                                            return_from=self.bot.guilds, allow_none=True)
            guild = guild[0]
        else:
            guild = discord.utils.find(lambda s: s.name == guild or str(s.id) == guild, self.bot.guilds)
            if guild is None:
                await ctx.send("`Unable to locate guild`")
                return

        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    invite = await channel.create_invite()
                    await ctx.send("`Created an invite to guild, I will DM it to you`")
                    dm_channel = ctx.author.dm_channel
                    if dm_channel is None:
                        dm_channel = await ctx.author.create_dm()
                    await dm_channel.send(invite.url)
                    break
                except discord.HTTPException:
                    await ctx.send("`Failed to create invite for guild!`") 



def setup(bot):
    bot.add_cog(invitegen(Bot))
