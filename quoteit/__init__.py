from .quoteit import QuoteIT, PersonalQuotes


def setup(bot):
    cog = Quoteit(bot)
    bot.add_cog(cog)
