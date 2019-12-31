#import config
import aiohttp
from discord import Message, Forbidden, Member, User, TextChannel, Role, utils
from discord.ext.commands import Context, Bot
import string
import random
import re

_CHANNEL_MENTION_MATCH = re.compile('<#([0-9]+)>$')
_ROLE_MENTION_MATCH = re.compile('<@&([0-9]+)>$')


def remove_html(string):
    return string.replace('&amp;', '&').replace("&lt;", '<').replace("&gt;", '>').replace('&quot;', '"').replace(
        '&#039;', "'")

def resolve_channel(string: str, ctx: Context) -> TextChannel or None:
    """Resolve a channel based on mention, ID, or name.
    Args:
          string (str): The ``str`` used to get the channel from.
          ctx (Context): The ``Context`` to get the guild from.
    Returns:
          TextChannel or None: The ``TextChannel`` found or None if none found.
    """
    match = _CHANNEL_MENTION_MATCH.match(string)
    if match:
        channel = utils.get(ctx.guild.text_channels, id=int(match.group(1)))
    else:
        try:
            channel = utils.get(ctx.guild.text_channels, id=int(string))
        except ValueError:
            channel = utils.get(ctx.guild.text_channels, name=string)
    return channel


def resolve_role(string: str, ctx: Context) -> Role or None:
    """Resolve a role based on mention, ID, or name.
    Args:
          string (str): The ``str`` used to get the role from.
          ctx (Context): The ``Context`` to get the guild from.
    Returns:
          Role or None: The ``Role`` found or None if none found.
    """
    match = _ROLE_MENTION_MATCH.match(string)
    if match:
        role = utils.get(ctx.guild.roles, id=int(match.group(1)))
    else:
        try:
            role = utils.get(ctx.guild.roles, id=int(string))
        except ValueError:
            role = utils.get(ctx.guild.roles, name=string)
    return role


def generate_id(size: int = 6, chars: str = string.ascii_uppercase + string.digits) -> str:
    """Generate an ID with the given length and possible characters.
    Mostly used for an error ID.
    Args:
        size (int): The length of the generated ID. (Default: 6)
        chars (str): A ``str`` with all possible characters that the random generator can choose from. (Default: string.ascii_uppercase + string.digits)
    Returns:
        str: The ``str`` of the generated ID.
    """
    return ''.join(random.choice(chars) for _ in range(size))


def resolve_emoji(emoji: str, msg: Message or Context or TextChannel) -> str:
    """Resolve an emoji that will be sent based on the permissions of the SelfUser.
    Args:
        emoji (str): The emoji type to get.
        msg (Message or Context or TextChannel): The message or context to get the user/channel from.
    Returns:
        str: The ``str`` of the emoji, an empty string if not found or if ``msg`` is not a Message or Context.
    """
    if isinstance(msg, Message):
        me = msg.guild.me
        channel = msg.channel
    elif isinstance(msg, Context):
        me = msg.me
        channel = msg.channel
    elif isinstance(msg, TextChannel):
        me = msg.guild.me
        channel = msg
    else:
        return ''
    emojis = {
        'ERROR': ['❌', '<:crossed:402968721515347968>'],
        'SUCCESS': ['✅', '<:check:394001925860884480>'],
        'WARN': ['⚠', '<:warning:394314103604117504>'],
        'INFO': ['❗', '<:exclamation:394001925198315530>'],
        'TSUNDERE': ['😳', '<:catBaka:389802304808943641>'],
        'ONLINE': ['💚', '<:online:398856032392183819>'],
        'IDLE': ['💛', '<:idle:398856031360253962>'],
        'DND': ['❤', '<:dnd:398856030068670477>']
    }
    num = ~~channel.permissions_for(me).external_emojis
    try:
        return emojis[emoji][num]
    except KeyError:
        return ''


def escape_markdown(string: str, codeblock: bool = False) -> str:
    """Escape the markdown of a given string.
    Args:
        string (str): The ``str`` that will have markdown escaped.
        codeblock (bool): The ``bool`` that tells if the escaped content will be in a code block.
    Returns:
        str: The ``str`` that has markdown escaped.
    """
    string = string.replace('```', '`\u200D``')
    if not codeblock:
        string = string.replace('*', '\\*').replace('~', '\\~').replace('_', '\\_').replace('`', '\\`')
    return string




def parse_flags(string):
    if not isinstance(string, str):
        return dict()
    match = re.findall('--(?P<key>\S+) (?P<value>"[^"]*"|[^\r\n\t\f\v -]*)', string)
    return dict(match)
