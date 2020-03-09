import re
from datetime import timedelta
from discord.ext.commands import BadArgument, Converter, EmojiConverter

class duration(Converter):
	components = ('weeks', 'days', 'hours', 'minutes', 'seconds')
	pattern = re.compile(''.join(r'(?:(?P<{0}>\d+)(\s*{1}s?|{2}),?\s*)?'.format(comp, comp[:-1], comp[0]) for comp in components) + '$')
	
	async def convert(self, ctx, arg):
		match = self.pattern.match(arg)
		if match is None:
			raise BadArgument('{} is not a valid duration'.format(arg))
		return timedelta(**{name: int(match.group(name) or 0) for name in self.components})

class emoji(EmojiConverter):
	async def convert(self, ctx, emoji):
		try:
			return await super().convert(ctx, emoji)
		except BadArgument:
			if len(emoji) == 1:
				return emoji
			else:
				raise
