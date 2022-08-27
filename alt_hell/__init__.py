from .alt_hell import alt_hell


async def setup(bot):
    await bot.add_cog(alt_hell(bot))
