from redbot.core.bot import Red
from .skytime import SkyTime


def setup(bot: Red):
    bot.add_cog(TimezoneConversion(bot))
