from .skyerror import Skyerror


def setup(bot):
    cog = Skyerror(bot)
    bot.add_cog(cog)
