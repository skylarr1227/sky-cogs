from discord.ext import commands
import discord
import random
import re
from redbot.core import Config, commands, checks


colors = {
  'DEFAULT': 0x000000,
  'WHITE': 0xFFFFFF,
  'AQUA': 0x1ABC9C,
  'GREEN': 0x2ECC71,
  'BLUE': 0x3498DB,
  'PURPLE': 0x9B59B6,
  'LUMINOUS_VIVID_PINK': 0xE91E63,
  'GOLD': 0xF1C40F,
  'ORANGE': 0xE67E22,
  'RED': 0xE74C3C,
  'GREY': 0x95A5A6,
  'NAVY': 0x34495E,
  'DARK_AQUA': 0x11806A,
  'DARK_GREEN': 0x1F8B4C,
  'DARK_BLUE': 0x206694,
  'DARK_PURPLE': 0x71368A,
  'DARK_VIVID_PINK': 0xAD1457,
  'DARK_GOLD': 0xC27C0E,
  'DARK_ORANGE': 0xA84300,
  'DARK_RED': 0x992D22,
  'DARK_GREY': 0x979C9F,
  'DARKER_GREY': 0x7F8C8D,
  'LIGHT_GREY': 0xBCC0C0,
  'DARK_NAVY': 0x2C3E50,
  'BLURPLE': 0x7289DA,
  'GREYPLE': 0x99AAB5,
  'DARK_BUT_NOT_BLACK': 0x2C2F33,
  'NOT_QUITE_BLACK': 0x23272A
}

bot = commands.Bot
BaseCog = getattr(commands, "Cog", object)
listener = getattr(commands.Cog, "listener", None) 
if listener is None:

    def listener(name=None):
        return lambda x: x

class Skyembed(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    #@commands.command(name='joinsrv', description='send invite for discord server')
   # async def joinsrv(self, ctx):
    #    invitelinknew = await self.bot.create_invite(destination = ctx.message.channel, xkcd = True, max_uses = 100)
     #   embed = discord.Embed(title="Here's the invite link", color=0xf41af4)
    #    embed.add_field(name="Discord Invite Link", value=invitelinknew)
    #    embed.set_footer(text="Discord server invite link.")
    #    await ctx.send(embed=embed)

    @commands.command(name='advhelp', description='Help menu for the Adventure module')
    async def adv_help(self, ctx): 
        embed = discord.Embed(title="The Adventure module", colour=discord.Colour(0x343cde), description="A general outline of our Adventure module and how to get started")

        embed.set_image(url="https://pokepla.net/adv.png")
        embed.set_thumbnail(url="https://pokepla.net/epic2.gif")
        embed.set_author(name="+advhelp ")
        embed.set_footer(text="Thank you Bust, and Volpe for many new bosses, and Foreboding/Kungfuartist for all the code help past present and future, you guys are the  best for helping me learn!!!", icon_url="https://pokepla.net/epic2.gif")

        embed.add_field(name="To start an adventure in your current channel use ", value="```+adventure```")
        embed.add_field(name="Your stats and equiped items can be viewed with", value="```+stats```")
        embed.add_field(name="You can view your backback inventory and trade items with", value="```+backpack\n+backpack trade <buyer> [asking=1000] <item>```")
        embed.add_field(name="Chests can be Combined and Looted by using", value="```+loot <type of chest> <optional #>\n+combine <type of chest ```", inline=True)
        embed.add_field(name="There are 5 basic classes to chooose from at level 10.", value="```+heroclass\n   -Bard\n   -Wizard\n   -Ramger\n   -Beserker\n   -Cleric```", inline=True)

        await ctx.send(embed=embed)
      
      
    @commands.command(name='phelp', description='Help menu for users profile')
    async def profile_help(self, ctx): 
        embed = discord.Embed(title="Skybot's leveling system", colour=discord.Colour(0x19b74d), description="How to configure your +profile options")
        embed.set_image(url="https://pokepla.net/phelp.png")
        embed.set_thumbnail(url="https://pokepla.net/skybot.png")
        embed.set_author(name="Skybot's Profile/Rank System overview", icon_url="https://pokepla.net/epic2.gif")
        embed.set_footer(text="See +rhelp, and +bhelp for detailed help on other profile sections", icon_url="https://pokepla.net/epic2.gif")

        embed.add_field(name="Show backgrounds available to pick from for your +profile", value="```+backgrounds profile```")
        embed.add_field(name="To set your background image for your +profile", value="``` +setbg <name of bg>```")
        embed.add_field(name="To change the overlay color of your +profile [not recommended]", value="```+lvlset profile color [ex. 0xf59b42]```")
        embed.add_field(name="To change the about me section of your +profile", value="```+setpinfo <message content>```", inline=True)
        embed.add_field(name="To change the Title displayed above the About me section of your +profile", value="```+setptitle <desired display title>```", inline=True)

        await ctx.send(embed=embed)
    
    @commands.command(name='lvlhelp', description='Help menu for leveler module')
    async def level_help(self, ctx): 
        embed = discord.Embed(title="Skybot's leveling system", colour=discord.Colour(0xfbfcfb), description="```diff\n+ You level up by sending messages where the bot can see them\n- Hope this menu helps with using our system! Have fun!```")

        embed.set_image(url="https://pokepla.net/lvlhelp.png")
        embed.set_thumbnail(url="https://pokepla.net/skybot.png")
        embed.set_author(name="Skybot's Profile/Rank System overview", icon_url="https://pokepla.net/epic2.gif")
        embed.set_footer(text="See +phelp, +rhelp, and +bhelp for detailed help on each one", icon_url="https://pokepla.net/epic2.gif")

        embed.add_field(name="Command for basic user configuration", value="```+lvlset```")
        embed.add_field(name="Profile configuration options - show profile with +profile", value="```+lvlset profile```")
        embed.add_field(name="Profile badge display configuration options", value="```+lvlset badge```")
        embed.add_field(name="Level-up Display configuration options", value="```+lvlset levelup```", inline=True)
        embed.add_field(name="Rank display configuration options - Show rank display with +rank", value="```+lvlset rank```", inline=True)

        await ctx.send(embed=embed)
    
    
    @commands.command(name='showdown', description='Links and info about Skys Pokemon showdown server')
    async def showdown_help(self, ctx):
        embed = discord.Embed(title="The link above is for Sky's Pokemon Showdown Server", colour=discord.Colour(0x12bdca), description="")

        embed.set_thumbnail(url="https://pokepla.net/epic.gif")
        embed.set_author(name="Click here for Showdown", url="http://pokepla.net", icon_url="https://go.goodguitarist.com/hosted/images/78/538b29231e4c1ab2c02cb6b8dc24b1/blue-arrows-flashing.gif")
      #  embed.set_footer(text="Suggestions on how to make this better? DM Skylarr#6666!!", icon_url="https://pokepla.net/epic2.gif")
        await ctx.send(embed=embed)
        
        
         
    @commands.command(name='rhelp', description='Help menu for users +Rank Display')
    async def rank_help(self, ctx):
        embed = discord.Embed(title="Skybot's Leveling System", colour=discord.Colour(0x12bdca), description="For help with other display options within the leveler system see: `\n+lvlhelp`")

        embed.set_image(url="https://pokepla.net/rhelp.png")
        embed.set_thumbnail(url="https://pokepla.net/epic.gif")
        embed.set_author(name="+rank Display Help", url="https://pokepla.net/epic.gif", icon_url="https://pokepla.net/epic2.gif")
        embed.set_footer(text="Suggestions on how to make this better? DM Skylarr#6666!!", icon_url="https://pokepla.net/epic2.gif")

        embed.add_field(name="Rank Background Viewer", value="```+backgrounds rank```")
        embed.add_field(name="Set Rank Display Background", value="```+setrbg [bg name]```")
        embed.add_field(name="Set Rank Color Overlay [not recommended]", value="```+setrcolor [0x52345]```")

        await ctx.send(embed=embed)
        
        

    @commands.command(
        name='sembed',
        description='The embed command',
    )
    async def embed_command(self, ctx):

        # Defined check function  
        def check(ms):        
            return ms.channel == ctx.message.channel and ms.author == ctx.message.author

         #title
        await ctx.send(content='What would you like the title to be?')

        # Wait for a response and get the title
        msg = await self.bot.wait_for('message', check=check)
        title = msg.content # Set the title

        # content
        await ctx.send(content='What would you like the Description to be?')
        msg = await self.bot.wait_for('message', check=check)
        desc = msg.content

        # make and send it
        msg = await ctx.send(content='Now generating the embed...')

        color_list = [c for c in colors.values()]
        # Convert
        # random

        embed = discord.Embed(
            title=title,
            description=desc,
            color=random.choice(color_list)
        )
        # thumbnail to be the bot's pfp
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        # user
        embed.set_author(
            name=ctx.message.author.name,
            icon_url=ctx.message.author.avatar_url
        )

        await msg.edit(
            embed=embed,
            content=None
        )
        
        
        

        return
        
        
       

def setup(bot):
    bot.add_cog(Skyembed(Bot))
