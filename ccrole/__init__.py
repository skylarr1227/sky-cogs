from .ccrole import CCRole


async def setup(bot):
    await bot.add_cog(CCRole(bot))
