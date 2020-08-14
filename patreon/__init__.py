from .patreon import Patreon

def setup(bot):
	bot.add_cog(Patreon(bot))
