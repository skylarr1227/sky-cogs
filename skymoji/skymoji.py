from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import sleep

import aiohttp
import discord, math, string, unicodedata
from redbot.core import checks
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.mod import get_audit_reason
from redbot.core.utils.predicates import MessagePredicate
from . import convert

_ = Translator("Skymoji", __file__)

blurple = discord.Color.blurple()
datetime_format = '%Y-%m-%d %I:%M %p UTC'
abc_emoji = [unicodedata.lookup('REGIONAL INDICATOR SYMBOL LETTER %s' % letter) for letter in string.ascii_uppercase]

@cog_i18n(_)
class Skymoji(commands.Cog):
    __version__ = "2.0.1"

    # noinspection PyMissingConstructor
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())


    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_emojis=True)
    @checks.bot_has_permissions(manage_emojis=True)
    async def e(self, ctx):
        """Manage emoji"""
        pass

    @e.command(name="add")
    async def emoji_add(self, ctx, name: str, url: str, *roles: discord.Role):
        """Create custom emoji

        Use double quotes if role name has spaces

        Examples:
            `[p]e add Example https://example.com/image.png`
            `[p]e add RoleBased https://example.com/image.png EmojiRole "Test image"`
        """
        try:
            async with self.session.get(url) as r:
                data = await r.read()
        except Exception as e:
            await ctx.send(
                chat.error(_("Unable to get emoji from provided url: {}").format(e))
            )
            return
        try:
            await ctx.guild.create_custom_emoji(
                name=name,
                image=data,
                roles=roles,
                reason=get_audit_reason(
                    ctx.author,
                    _("Restricted to roles: {}").format(
                        ", ".join([f"{role.name}" for role in roles])
                    )
                    if roles
                    else None,
                ),
            )
        except discord.InvalidArgument:
            await ctx.send(
                chat.error(_("This image type is unsupported, or link is incorrect"))
            )
        except discord.HTTPException as e:
            await ctx.send(
                chat.error(_("An error occured on adding an emoji: {}").format(e))
            )
        else:
            await ctx.tick()

    @e.command(name="rename")
    async def emoji_rename(
        self, ctx, emoji: discord.Emoji, name: str, *roles: discord.Role
    ):
        """Rename emoji and restrict to certain roles
        Only this roles will be able to use this emoji

        Use double quotes if role name has spaces

        Examples:
            `[p]e rename emoji NewEmojiName`
            `[p]e rename emoji NewEmojiName Administrator "Allowed role"`
        """
        if emoji.guild != ctx.guild:
            await ctx.send_help()
            return
        try:
            await emoji.edit(
                name=name,
                roles=roles,
                reason=get_audit_reason(
                    ctx.author,
                    _("Restricted to roles: ").format(
                        ", ".join([f"{role.name}" for role in roles])
                    )
                    if roles
                    else None,
                ),
            )
        except discord.Forbidden:
            await ctx.send(chat.error(_("I can't edit this emoji")))
        await ctx.tick()

    @e.command(name="remove")
    async def emoji_remove(self, ctx, *, emoji: discord.Emoji):
        """Remove emoji from server"""
        if emoji.guild != ctx.guild:
            await ctx.send_help()
            return
        await emoji.delete(reason=get_audit_reason(ctx.author))
        await ctx.tick()
    
   # @e.command(name="info")
   # async def emoji_information(self, ctx, emoji: convert.emoji):
  #      """Retrieve information about an emoji.
   #     This works for built-in as well as custom emojis.
    #    """
       # e = discord.Embed(type='rich', color=blurple)
     #   if isinstance(emoji, discord.Emoji):
    #        url = emoji.url.replace('discordapp.com/api', 'cdn.discordapp.com')
    #        e.set_thumbnail(url=url)
  #          e.add_field(name='Name', value=emoji.name)
    #        e.add_field(name='ID', value=emoji.id)
  #          e.add_field(name='Created at', value=emoji.created_at.strftime(datetime_format))
  #          e.add_field(name='URL', value=url)
  #      else:
    #        e.add_field(name='Name', value=unicodedata.name(emoji))
   #         e.add_field(name='ID', value='Built-in')
    #        await ctx.send(embed=e) 
