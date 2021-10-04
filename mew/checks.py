import discord
from redbot.core import commands
from enum import IntEnum
from functools import wraps
# This file holds checks that can be used to limit access to certain functions.

# Staff checks will allow any user of at least that rank to use the command.
# The hierarchy is Admin > Investigator > Mod > Helper.
# This Enum outlines the hierarchy. Higher values indicate more access.
# These numbers can be safely modified WITHOUT touching the rest of the file in order to add or remove ranks without changing current access.
class Rank(IntEnum):
    USER = 0
    SUPPORT = 1
    GYM = 2
    HELPER = 3
    MOD = 4
    GYMAUTH = 5
    INVESTIGATOR = 6
    ADMIN = 7
    DEVELOPER = 8

# In order to prevent developers from being locked out, this variable holds the user ids of developers.
# Any ID in this tuple will always be able to use commands, regardless of rank or DB status.
# Be careful adding IDs to this tuple, as they get access to a large number of commands.
OWNER_IDS = (
    455277032625012737, # Dylee
    478605505145864193, # Cheese (help during my surgery on the 8th)
    790722073248661525, # Sky (main)
    409149408681263104, # Doom
    145519400223506432, # Flame
    473541068378341376, # Neuro
    334155028170407949, # Fore
)

def check_admin():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        return rank >= Rank.ADMIN
    return commands.check(predicate)

def check_investigator():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        # ONLY allow EXACTLY invest (or higher) to use
        return rank >= Rank.INVESTIGATOR
    return commands.check(predicate)

def check_gymauth():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        # ONLY allow EXACTLY gym auth (or higher) to use
        return rank >= Rank.GYMAUTH
    return commands.check(predicate)

def check_mod():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        return rank >= Rank.MOD
    return commands.check(predicate)

def check_helper():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        return rank >= Rank.HELPER
    return commands.check(predicate)

def check_support():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        async with ctx.cog.db.acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", ctx.author.id)
        if rank is None:
            return False
        rank = Rank[rank.upper()]
        return rank >= Rank.SUPPORT
    return commands.check(predicate)
