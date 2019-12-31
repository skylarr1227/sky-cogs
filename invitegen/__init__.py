from .invitegen import invitegen


def setup(bot):
    cog = invitegen(bot)
    bot.add_cog(cog)
