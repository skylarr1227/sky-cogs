from .mewtradeutils import Mewtradeutil

def setup(bot):
	bot.add_cog(Mewtradeutil(bot))
