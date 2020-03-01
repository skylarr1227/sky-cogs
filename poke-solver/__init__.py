
from .pokename import PokeName


def setup(bot):
    cog = PokeName(bot)
    bot.add_cog(cog)
