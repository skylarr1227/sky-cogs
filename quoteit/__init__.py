from .quoteit import *


def setup(bot):
    cog = quoteit(bot)
    bot.add_cog(cog)
