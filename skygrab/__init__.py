from .snatch import Snatch

def setup(bot):
    s = Snatch(bot)
    bot.add_cog(s)
    bot.loop.create_task(s.go_sniffing())
