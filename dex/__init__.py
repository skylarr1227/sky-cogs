from .skydex import Skydex


def setup(bot):
    cog = Skydex(bot)
    bot.add_cog(cog)
