from .skymath import Calc


def setup(bot):
    cog = Calc(bot)
    bot.add_cog(cog)