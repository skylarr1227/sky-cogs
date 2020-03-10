from .skyimginfo import SkyImgInfo


def setup(bot):
    cog = SkyImgInfo(bot)
    bot.add_cog(cog)