from .skychill import skychill


def setup(bot):
    bot.add_cog(skychill(bot))
