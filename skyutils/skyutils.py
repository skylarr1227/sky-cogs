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
import time

from typing import Union, Optional
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from redbot.core.config import Config
from redbot.core import commands, checks
#from discord.ext import commands
from .tools import remove_html, resolve_emoji

bot = commands.Bot
BaseCog = getattr(commands, "Cog", object)
Embed1 = discord.Embed(title="HD poke Image test", description="How large is this image on your screen?", color=0xff0000)
Embed2 = discord.Embed(title="Quick Reference cont. Loot", description="__**+loot**__\nUse to open your lootboxes\nJust specify the type\nExample:\n```+loot normal```\nor\n```+loot epic 10```\nfor multiple at once\n\n__**+combine**__\nCombiine your loot boxes by specifying type you wish to convert", color=0x5599ff),
Embed3 = discord.Embed(title="Quick Reference cont. Hero-classes", description="```+heroclass\n   -Bard\n   -Wizard\n   -Ramger\n   -Beserker\n   -Cleric```", color=0x191638)
Embed = discord.Embed

class Skyutils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.command()
    @commands.guild_only()
    @checks.is_owner()
    async def skyrole(
        self, ctx: commands.Context, rolename: discord.Role, *, user: discord.Member = None
    ):
        """
        Add a role to a user.
        Use double quotes if the role contains spaces.
        If user is left blank it defaults to the author of the command.
        """
        if user is None:
            user = ctx.author
        await user.add_roles(rolename)


    @commands.command()
    async def fuckchoices(self, ctx):
        multiple_choice = BotMultipleChoice(ctx, ['one', 'two', 'three', 'four', 'five', 'six'], "How many babys would you eat")
        await multiple_choice.run()

        await multiple_choice.quit(multiple_choice.choice)



    @commands.command()
    async def onixian(self, ctx):
        confirmation = BotConfirmation(ctx, 0x012345)
        await confirmation.confirm("Would you like to know more about Onixian? Well, react accordingly.")

        if confirmation.confirmed:
            await confirmation.update("Onixian, a Pokemon bot from a developer many already know: Foreboding.", color=0x55ff55)
            member = ctx.author
            embed = discord.Embed(color=discord.Color.blue(),
                            description="[Click here to join the official Onixian server](https://discord.gg/67Bx3sV)\nNew features and updates added daily!\
                                          \nCommunity suggestions are heard, discussed, and implemented fast!\
                                          \nFamiliar look and commands your used to, with an epic new spin!\
                                          \nSKY is somehow involved, that's good right??? (Right...??)\
                                          \nOh and also don't forget to [vote if you want it to grow!](https://top.gg/bot/654427498565599243)\
                                          \n\n``its also in`` [sky's server](https://discord.gg/eBwrbNh) ``if you got beef with Mr. Bodeing just sayin!``")
            embed.set_author(name="Have fun!")
            embed.set_image(url="https://images.discordapp.net/avatars/654427498565599243/07fe64e8cd90e789001f1c3da4bde6c0.png")
            await ctx.send(embed=embed)
            #channel = self.bot.get_channel("599660712985624576")
            #await ctx.send_message(channel, "butts")
        else:
            await confirmation.update("Well, good job.. now Sky owns your soul. She will be by to collect within 24 hours. Please be ready.", hide_author=True, color=0xff5555)


    @commands.command()        
    async def changelog(self, ctx):
        """Change Logs for Adventure"""
        embeds = [
        Embed(title="Rebirth Update", description="**New features**\
              \n\n**Rebirths**\
              \n• Users now have the ability to rebirth at max level.\
              \n• Can be used to reset a character back to level 1\
              \n• Upon re-birthing your character gains increase base points to all stats\
              \n• The number of points for re-birthing varies based on the number of total rebirths your character has\
              \n• Between 1 - 9 rebirths you get 2 base stats per rebirth\
              \n• Between 10 - 19 rebirths you get 1 extra base stats per rebirth\
              \n• Between 20 - 29 rebirths you get 5 extra base stats per rebirth\
              \n• After 30 rebirths you get 3 extra base stats per rebirth\
              \n• Characters are guaranteed some item chests after their rebirth\
              \n• 1 common chest per 5 rebirths they have\
              \n• 1 rare chest per 10 rebirths they have\
              \n• 1 epic chest per 20 rebirths they have\
              \n• 1 legendary test per 50 rebirths they have\
              \n\n**Mechanics affected by rebirths**\
              \n*As your rebirths increases the following will change*\
              \n\n• The amount of XP you gain for activities will also increase\
              \n• The amount of currency you gain for activities will also increase\
              \n• You will get better items from loot chests\
              \n• The amount you sell items for will be higher\
              \n• Characters with more rebirths will be more likely to encounter stronger monsters that will rebirth more XP\
              \n• Character with more rebirths will be able to convert lesser loot chest into higher quality loot chests\
              \n• Characters with more rebirths will have their skill cooldowns significantly reduced\
              \n• Characters can only trade items to other users with the same or higher number of rebirths.", color=0x115599),
        Embed(title="Rebirth Update Cont.", description="How to rebirth\
              When your character reach max level they can run [p]rebirth\
              \n• This will cost all their current currency\
              \n• This will remove all their items with the following exceptions\
              \n• ```md\nSet items will stay with you forever\
              \n• Tinkerer items will stay with you as long as you are a tinkerer\
              \n• Legendary items will stay with you for 3 rebirths after you get them```\
              \n• Say you get a legendary item with you on level 30 Rebirth 3, this item will stay with you until your 6th rebirth\
              \n• Any loot chests or other items you has prior to rebirthing will be removed\
              \n• You will keep your class upon rebirthing\
              \n\nMax Level\
              \nNew dynamic Max levels based on number of rebirths your character has.\
              \n• For character with 0 rebirths the max level is 5\
              \n• For character with 1 rebirth the Max level is 20\
              \n• For character with 2 to 9 rebirths the max level increases by 5 per rebirth\
              \n• For character with 10 to 19 rebirths the max level increases by 10 per rebirth (70, 80, 90...)\
              \n• For character with 20 to 38 rebirths the max level increases by 5 per rebirth (170, 175, 180..)\
              \n• Characters will stop gaining XP once their character reach max level\
              \n\nItem Level\
              \n• • Items now have dynamically generated Item levels based on their stats.\
              \nSet Items\
              \n• Sets provide significant bonuses when all pieces are equipped.\
              \n• The 12 new sets can be broken down in a total of 86 Set items.\
              \n• Set Bonuses are as follow\
              \n• Extra Attack points\
              \n• Extra Dexterity points\
              \n• Extra Intelligence points\
              \n• Extra Charisma points\
              \n• Extra Luck points\
              \n• A XP multiplier for all activities that reward users with XP\
              \n• A Currency multiplier for all activities that reward the user with currency\
              \n• Stats multipliers, some sets bonuses will straight up multiply all your stats by the multiplier the set provides.", color=0x5599ff),
        Embed(title="test page 3", description="Why are you still here?", color=0x191638)
    ]
        Embed.set_image(url="http://cloud.skylarr.me/index.php/apps/sharingpath/skylarr/Rpg Resources/Spell HUD Icons/35.png")
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
        

#  @commands.command()
#  async def nick(self, ctx, *, nick: str):
#      """Set your nickname.
#     Usage: nick [new nickname]"""
# 3  #     if ctx.author.guild_permissions.change_nickname:
#          await ctx.author.edit(nick=nick, reason='User requested using command')
#            await ctx.send(':thumbsup: Done.')
#        else:
#           await ctx.send(':x: You don\'t have permission to change your nickname.')      
            
            

            
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

    
 
    @commands.command()
    async def latency(ctx):
        time_1 = time.perf_counter()
        await ctx.trigger_typing()
        time_2 = time.perf_counter()
        ping = round((time_2-time_1)*1000)
        await ctx.send(f"ping = {ping}")
    
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
        await ctx.send(f"and... <@{str(user.id)}> got it first!!! Reki wasted my hard work! WEEEE")
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
