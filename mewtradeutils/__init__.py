from .mewtradeutil import Mewtradeutil

async def setup(bot):
	await bot.add_cog(Mewtradeutil(bot))
