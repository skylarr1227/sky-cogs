import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS, close_menu
from redbot.core.utils.chat_formatting import pagify
import re


SWITCH_REGEX = re.compile(r"(?i)^sw(?:-[0-9]{4}){3}$")

class switch(commands.Cog):
    """Switch Friend code utility"""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=790722073248661525)
        self.config.register_user(
            switch_code = None,
        )

    @commands.command()
    async def setswitch(self, ctx, code: str):
        """Save your Nintendo Swich friend code for quick retrival."""
        if not SWITCH_REGEX.match(code):
            await ctx.send("Your code does not look like a valid switch code. Your code must be in the format `SW-0000-0000-0000`.")
            return
        code = code.upper()
        await self.config.user(ctx.author).switch_code.set(code)
        embed = discord.Embed(title= "Successful", description=f"Your Nintendo Switch invite code has been registered.\nCode:`{code}`", color=0xEE8700)
        await ctx.send(embed=embed)

    @commands.command()
    async def getswitch(self, ctx, member: discord.Member):
        """Show targeted user's Nintendo Switch friend ID/Invite code if they have one registered."""
        code = await self.config.user(member).switch_code()
        if code is None:
            await ctx.send("This user does not have their switch invite code registered.")
            return
        embed = discord.Embed(title= f"{member}'s Invite Code:", description=f"`{code}`", color=0xEE8700)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def switchboard(self, ctx):
        data = await self.config.all_users()
        result = ""
        for uid, code in data.items():
            code = code["switch_code"]
            user = self.bot.get_user(uid)
            if user is None or not code:
                continue
            result += f"`{code}` | `{user.name}`\n"
        embedlist = []
        for page in pagify(result):
            embedlist.append(discord.Embed(title="Switch code | Name", description=page))
        c = DEFAULT_CONTROLS if len(embedlist) > 1 else {"\N{CROSS MARK}": close_menu}
        await menu(ctx, embedlist, c)
