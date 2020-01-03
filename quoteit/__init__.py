from .quoteit import quoteit, PersonalQuotes


def setup(bot):
    cog = quoteit(bot)
    bot.add_cog(cog)
