from .skyembed import Skyembed


def setup(bot):
    cog = Skyembed(bot)
    bot.add_cog(cog)
