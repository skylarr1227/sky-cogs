from .botblock import DiscordListsGet

def setup(bot):
    cog = DiscordListsGet(bot)
    bot.add_cog(cog)
