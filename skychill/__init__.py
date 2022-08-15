from .chillzone import skychill


async def setup(bot):
    await bot.add_cog(skychill(bot))
