from .skybash import skyBash

async def setup(bot):
    await bot.add_cog(skyBash(bot))
