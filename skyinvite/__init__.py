from .invite import EmbedInvite

def setup(bot):

    cog = EmbedInvite(bot)

    bot.add_cog(cog)

