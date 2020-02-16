from .skymoji import Skymoji


def setup(bot):
    bot.add_cog(Skymoji(bot))
