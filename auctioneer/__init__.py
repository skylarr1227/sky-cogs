from .auctioneer import Auctioneer

def setup(bot):
	bot.add_cog(Auctioneer(bot))