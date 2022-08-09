from .auctioneer import Auctioneer

async def setup(bot):
	await bot.add_cog(Auctioneer(bot))