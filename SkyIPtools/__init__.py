from .sky-iptools import SkyIP



def setup(bot):
    cog = SkyIP(bot)
    bot.add_cog(cog)
