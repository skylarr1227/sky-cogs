from .skygrab import SkyGrab

def setup(bot):
    s = SkyGrab(bot)
    bot.add_cog(s)
    bot.loop.create_task(s.go_sniffing())
