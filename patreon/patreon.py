import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import asyncpg
import os
import ujson

CHANNEL_ID = 738543523657416837
DATABASE_URL = os.environ["DATABASE_URL"]


class Patreon(commands.Cog):
	"""Updates the patreon db."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			last_id = 743581579556945968
		)
		self.db = None
		self.task = asyncio.create_task(self._startup())

	async def init(self, con):
		"""Required for the DB."""
		await con.set_type_codec(
			typename='json',
			encoder=ujson.dumps,
			decoder=ujson.loads,
			schema='pg_catalog'
		)
	
	async def _startup(self):
		"""Opens the DB connection and check for missed updates after a cog restart."""
		try:
			self.db = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=200, command_timeout=5, init=self.init)
		except ConnectionError:
			return
		channel = self.bot.get_channel(CHANNEL_ID)
		last_id = await self.config.last_id()
		message = None
		async for message in channel.history(after=last_id, limit=None):
			if not message.channel.id == CHANNEL_ID:
				continue
			if not message.webhook_id:
				continue
			await self._update_from_message(message)
		if message:
			await self.config.last_id.set(message.id)
	
	async def _update_from_message(self, message: discord.Message):
		"""Converts a message to its values."""
		data = [x.split(':')[1].strip() for x in message.content.split('\n')]
		assert len(data) == 7
		async with self.db.acquire() as pconn:
			await pconn.execute(
				'INSERT INTO patreons (email, name, tier, pledge_current, pledge_total, id, status) VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT email DO UPDATE SET name = $2, tier = $3, pledge_current = $4, pledge_total = $5, id = $6, status = $7',
				*data
			)
	
	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.channel.id == CHANNEL_ID:
			return
		if not message.webhook_id:
			return
		await self._update_from_message(message)
		await self.config.last_id.set(message.id)
		
