from .skylevel import SkyLevel


async def setup(bot):
    bot.add_cog(SkyLevel(bot))
