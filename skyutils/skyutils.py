import asyncio
import random
import re
import string
import urllib.parse
import discord
import requests
#import config
import datetime
import json
import os
import urllib
import pytz
import io
import aiohttp
import async_timeout

from typing import Union, Optional
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from redbot.core.config import Config
from redbot.core import commands, checks
#from discord.ext import commands
from .tools import remove_html, resolve_emoji

bot = commands.Bot
BaseCog = getattr(commands, "Cog", object)
Embed = discord.Embed


class Skyutils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
   

    @commands.command()
    async def fuckchoices(self, ctx):
        multiple_choice = BotMultipleChoice(ctx, ['one', 'two', 'three', 'four', 'five', 'six'], "How many babys would you eat")
        await multiple_choice.run()

        await multiple_choice.quit(multiple_choice.choice)



    @commands.command()
    async def testconfirm(self, ctx):
        confirmation = BotConfirmation(ctx, 0x012345)
        await confirmation.confirm("Do you have any event ideas that you would like to contribute?")

        if confirmation.confirmed:
            await confirmation.update("Yes", color=0x55ff55)
        else:
            await confirmation.update("No", hide_author=True, color=0xff5555)


    @commands.command()        
    async def helpadv(self, ctx):
        """Quick reference for Adventure...bitches """
        embeds = [
            Embed(title="Quick Reference for Skybot", description="__**+adventure**__\nStart an adventure in your current channel\n__**+stats**__\nTo view your character sheet as well as\nyour currently equipped items.\n", color=0x115599),
            Embed(title="Quick Reference cont. Loot", description="__**+loot**__\nUse to open your lootboxes\nJust specify the type\nExample:\n```+loot normal```\nor\n```+loot epic 10```\nfor multiple at once\n\n__**+combine**__\nCombiine your loot boxes by specifying type you wish to convert", color=0x5599ff),
            Embed(title="Quick Reference cont. Hero-classes", description="```+heroclass\n   -Bard\n   -Wizard\n   -Ramger\n   -Beserker\n   -Cleric```", color=0x191638)
        ]

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()
  

        
  
    @commands.command()
    async def pfp(self, ctx, *, member: discord.Member = None):
        """Displays a user's avatar."""
        if member is None:
            member = ctx.author
        embed = discord.Embed(color=discord.Color.blue(),
                              description=f"[Link to Avatar]({member.avatar_url_as(static_format='png')})")
        embed.set_author(name=f"{member.name}\'s Avatar")
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)
        

    @commands.command()
    async def nick(self, ctx, *, nick: str):
        """Set your nickname.
        Usage: nick [new nickname]"""
        if ctx.author.guild_permissions.change_nickname:
            await ctx.author.edit(nick=nick, reason='User requested using command')
            await ctx.send(':thumbsup: Done.')
        else:
            await ctx.send(':x: You don\'t have permission to change your nickname.')      
            
            
   
            
    @commands.Cog.listener()
    async def on_message(self,message):
        mathshit=['+','-','*','/','^']
        msg=message.content
        msgshit=msg.split(' ')
        for a in msgshit:
            if a in mathshit:
                if a=='+':
                    await message.channel.send(str(int(msgshit[0])+int(msgshit[2])))
                elif a=='-':
                    await message.channel.send(str(int(msgshit[0])-int(msgshit[2])))
                elif a=='*':
                    await message.channel.send(str(int(msgshit[0])*int(msgshit[2])))
                elif a=='/':
                    await message.channel.send(str(int(msgshit[0])/int(msgshit[2])))
                elif a =='^':
                    await message.channel.send(str(int(msgshit[0])**int(msgshit[2])))
                else:
                    print('whatever')

    
    @checks.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def eventmsg(self, ctx, color:Optional[discord.Color]=None, *, text):
        """
        Send an embed for a special event

        Use the optional parameter color to change the color of the embed.
        The embed will contain the text text.
        All normal discord formatting will work inside the embed. 
        """
        emoji = discord.utils.get(self.bot.emojis, id=610290433725169703)
        if color is None:
            color = await ctx.embed_color()
        embed = discord.Embed(description=text, color=color)
        embed.set_footer(text="Be the first to Click the Firework reaction!!!", icon_url="https://cdn.discordapp.com/emojis/604916559709995008.gif")
        embed.set_author(name="Happy New Years!!!!", icon_url="https://cdn.discordapp.com/emojis/610290337734197252.gif")
        msg=await ctx.send(embed=embed)
        def check(reaction, user):
            if user.bot:
                return False
            if not (reaction.message.id == msg.id and reaction.emoji.id == emoji.id):
               return False
            return True
        await msg.add_reaction(emoji)
        reaction, user = await self.bot.wait_for('reaction_add', check=check)
       # await ctx.channel.send (str(user))      
        await ctx.send(f"and... <@{str(user.id)}> got it first!!! Here comes 2020 bitches.")
      #  await ctx.delete(msg)
            
           
    #@commands.command(pass_context=True)
    #async def memberlog(ctx):
    #    """Returns a CSV file of all users on the server."""
    #    await self.bot.request_offline_members(ctx.message.server)
    #    before = time.time()
    #    nicknames = [m.display_name for m in ctx.message.server.members]
    #    with open('temp.csv', mode='w', encoding='utf-8', newline='') as f:
    #        writer = csv.writer(f, dialect='excel')
    #        for v in nicknames:
    #            writer.writerow([v])
    #            after = time.time()
    #            await bot.send_file(ctx.message.author, 'temp.csv', filename='stats.csv',
    #                                content="Sent to your dms. Generated in {:.4}ms.".format((after - before)*1000))
    
    
    
                   
def setup(bot):
    bot.add_cog(Skyutils(bot))
