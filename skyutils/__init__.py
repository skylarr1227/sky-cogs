from .skyutils import Skyutils


def setup(bot):
    cog = Skyutils(bot)
    bot.add_cog(cog)
