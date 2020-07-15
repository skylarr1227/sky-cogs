import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import datetime

CAT_ID = 731973669898682379


class Auctioneer(commands.Cog):
	"""Create auctions for Mewbot pokemon."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			auctions = {},
			current_num = 0,
		)
		self.safe_num = None
		self.tasks = []
		task = asyncio.create_task(self._startup())
		self.tasks.append(task)
		"""
		{
			"1": {
				"author": 145519400223506432,
				"pokemon_info": "...",
				"bids": [[631840748924436490, 100], [620229667294674955, 200]],
				"channel": 731974207218647121,
				"message": 731974207717638214,
				"status": "active",
				"end": 1594603316.7081,
				"poke": 2342
			},
			"2": {...}
		}
		"""
		# https://discordapp.com/channels/723511253334622229/724384098616868874/731664173712539830
		# https://discordapp.com/channels/723511253334622229/724384098616868874/731664203835899955
	
	async def _startup(self):
		"""Creates auction waiting tasks after a cog restart."""
		auctions = await self.config.auctions()
		for num, auction in auctions.items():
			if auction['status'] == 'active':
				await asyncio.create_task(self._await_auction(num))
	
	@commands.group(aliases=['auction', 'auc', 'a'])
	async def auctioneer(self, ctx):
		"""Create auctions for Mewbot pokemon."""
		pass
	
	@auctioneer.command()
	async def bid(self, ctx, auction_id: int, amount: int):
		"""Bid on a running auction."""
		auction_id = str(auction_id)
		auction = await self.config.auctions.get_raw(auction_id)
		if not auction:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] == ctx.author.id:
			await ctx.send('You cannot bid on your own auction!')
			return
		if not await self._check_balance(ctx.author.id, amount):
			await ctx.send('You do not have enough credits!')
			return
		bids = auction['bids']
		if bids and bids[-1][0] == ctx.author.id:
			await ctx.send('You already have the highest bid!')
			return
		if bids and bids[-1][1] >= amount:
			await ctx.send('Your bid is lower than the current highest bid!')
			return
		if bids:
			await self._add_credits(bids[-1][0], bids[-1][1])
		bids.append([ctx.author.id, amount])
		await self.config.auctions.set_raw(auction_id, 'bids', value=bids)
		await self._remove_credits(ctx.author.id, amount)
		await self._update_auction(auction_id)
		await ctx.send('Your bid has been submitted.')
	
	@auctioneer.command()
	async def create(self, ctx, poke: int):
		"""Create a new auction for a mewbot pokemon."""
		if poke == 1:
			await ctx.send('You can not use your first Pokemon in the auction!')
			return 
		poke = self._find_pokemon(poke, ctx.author.id)
		if poke is None:
			await ctx.send('You do not have that Pokemon!')
			return
		category = self.bot.get_channel(CAT_ID)
		if not category:
			await ctx.send('I could not find the category I am supposed to send auctions to.')
			return
		
		pokemon_info, channel_name = await self._get_pokemon_info(poke)
		
		if not self.safe_num:
			self.safe_num = await self.config.current_num()
		self.safe_num += 1
		await self.config.current_num.set(self.safe_num)
		num = str(self.safe_num)
		end = (datetime.datetime.utcnow() + datetime.timedelta(seconds=30)).timestamp() #TODO: revert this to days=1
		embed = await self._build_embed(num, ctx.author.id, pokemon_info, [], 'active', end)
		
		try:
			channel = await category.create_text_channel(channel_name, reason='Auctioneer')
		except discord.errors.HTTPException:
			await ctx.send('I do not have permission to create text channels.')
			return
		message = await channel.send(embed=embed)
		auction = {
			'author': ctx.author.id,
			'pokemon_info': pokemon_info,
			'bids': [],
			'channel': channel.id,
			'message': message.id,
			'status': 'active',
			'end': end,
			'poke': poke
		}
		await self.config.auctions.set_raw(num, value=auction)
		await self._remove_pokemon(ctx.author.id, poke)
		task = asyncio.create_task(self._await_auction(num))
		self.tasks.append(task)

	async def _build_embed(self, num, author, pokemon_info, bids, status, end):
		"""Creates an embed that represents a given auction."""
		colors = {'active': discord.Color.green(), 'ended': discord.Color.red()}
		embed = discord.Embed(
			title=f'Auction #{num}',
			description=pokemon_info,
			color=colors[status],
			timestamp = datetime.datetime.fromtimestamp(end)
		)
		author = self.bot.get_user(author) or author
		embed.add_field(name='**Author**', value=f'{author}')
		if bids:
			bid_member = self.bot.get_user(bids[-1][0]) or bids[-1][0]
			bid_value = bids[-1][1]
			emoji = self.bot.get_emoji(731709469414785047) or 'Mewcoins'
			embed.add_field(name='**Top bid**', value=f'{bid_value} {emoji} by {bid_member}')
		else:
			embed.add_field(name='**Top bid**', value='No bids yet')
		embed.set_footer(text='Auction ends' if status == 'active' else 'Auction ended')
		return embed
	
	async def _update_auction(self, num):
		"""Updates the auction message for a given auction."""
		auction = await self.config.auctions.get_raw(num)
		embed = await self._build_embed(num, auction['author'], auction['pokemon_info'], auction['bids'], auction['status'], auction['end'])
		channel = self.bot.get_channel(auction['channel'])
		if not channel:
			return
		try:
			message = await channel.fetch_message(auction['message'])
		except discord.errors.HTTPException:
			return
		await message.edit(embed=embed)
	
	async def _await_auction(self, num):
		"""Waits for the amount of time a given auction has remaining."""
		end = await self.config.auctions.get_raw(num, 'end')
		time = end - datetime.datetime.utcnow().timestamp()
		await asyncio.sleep(time)
		await self._end_auction(num)
	
	async def _end_auction(self, num):
		"""Ends a given auction."""
		status = auction = await self.config.auctions.get_raw(num, 'status')
		if not status == 'active':
			return
		auction = await self.config.auctions.set_raw(num, 'status', value='ended')
		await self._update_auction(num)
		auction = await self.config.auctions.get_raw(num)
		channel = self.bot.get_channel(auction['channel'])
		bids = auction['bids']
		author = self.bot.get_user(auction['author'])
		if author:
			author = author.mention
		else:
			author = auction['author']
		if not bids:
			await self._add_pokemon(auction['author'], auction['poke'])
			if channel:
				await channel.send(f'Auction #{num} by {author} has ended.\nThere were no bids.')
			return
		amount = bids[-1][1]
		await self._add_credits(auction['author'], amount)
		await self._add_pokemon(bids[-1][0], auction['poke'])
		winner = self.bot.get_user(bids[-1][0])
		if winner:
			winner = winner.mention
		else:
			winner = bids[-1][0]
		await channel.send(f'Auction #{num} by {author} has ended.\nThe winner is {winner} with a bid of {amount}.')
	
	def cog_unload(self):
		"""Closes auction tasks on cog unload."""
		for task in self.tasks:
			try:
				task.cancel()
			except Exception:
				pass
	
	#DB INTERACTING FUNCS - TO BE EDITED
	async def _find_pokemon(self, userid: int, user_poke: int):
		"""
		Gets the pokeid of a specific pokemon "userid" owns.
		
		Returns the actual pokeid of the pokemon, or None if it could not be found.
		"""
		async with self.bot.db[0].acquire() as pconn:
			poke = await pconn.fetchval("SELECT pokes[$1] FROM users WHERE u_id = $2", user_poke, userid)
			name = await pconn.fetchval("SELECT pokname FROM pokes WHERE id = $1", poke)
			if name in (None, 'Egg'):
				return None
			return poke
	
	async def _add_pokemon(self, userid: int, poke: int):
		"""Add a pokemon with id "poke" from user "userid"."""
		async with self.bot.db[0].acquire() as pconn:
			await pconn.execute('UPDATE users SET pokes = array_remove(pokes, $1)', poke)
	
	async def _remove_pokemon(self, userid: int, poke: int):
		"""Remove a pokemon with id "poke" from user "userid"."""
		async with self.bot.db[0].acquire() as pconn:
			await pconn.execute('UPDATE users SET pokes = array_remove(pokes, $1)', poke)
	
	async def _get_pokemon_info(self, poke: int):
		"""
		Gets the pokemon info of a specific pokemon.
		
		Returns (pokemon_info, channel_name).
		"""
		async with self.bot.db[0].acquire() as pconn:
			call = (
				'SELECT pokelevel, pokname, poknick, gender, '
				'nature, hpiv, hpev, atkiv, atkev, defiv, defev, '
				'spatkiv, spatkev, spdefiv, spdefev, speediv, speedev, '
				'happiness, shiny FROM pokes WHERE id = $1'
			)
			star = '\N{SPARKLES} ' if pokemon['shiny'] else ''
			pokemon = await pconn.fetchrow(call, poke)
			#TODO: define iv
			iv = 0
			pokemon_info = (
				f'Level {pokemon["pokelevel"]} {pokemon["pokname"]} "{pokemon["poknick"]}" {pokemon["gender"]}\n'
				f'**Nature**: {pokemon["nature"]}\n'
				f'**HP**: {pokemon["hpiv"]} **IVs** | {pokemon["hpev"]} **EVs**\n'
				f'**Attack**: {pokemon["atkiv"]} **IVs** | {pokemon["atkev"]} **EVs**\n'
				f'**Defense**: {pokemon["defiv"]} **IVs** | {pokemon["defev"]} **EVs**\n'
				f'**Sp. Atk**: {pokemon["spatkiv"]} **IVs** | {pokemon["spatkev"]} **EVs**\n'
				f'**Sp. Def**: {pokemon["spdefiv"]} **IVs** | {pokemon["spdefev"]} **EVs**\n'
				f'**Speed**: {pokemon["speediv"]} **IVs** | {pokemon["speedev"]} **EVs**\n'
				f'**Happiness**: {pokemon["happiness"]}\n'
				f'IV %: {iv}'
			)
			channel_name = f'{star}{pokemon["pokemon"]} {iv}'
			return (pokemon_info, channel_name)
	
	async def _check_balance(self, userid: int, amount: int):
		"""Returns a bool indicating whether or not "userid" has at least "amount" credits."""
		async with self.bot.db[0].acquire() as pconn:
			credits = await pconn.fetchval('SELECT mewcoins FROM users WHERE u_id = $1', userid)
			return credits >= amount
		
	async def _add_credits(self, userid: int, amount: int):
		"""Adds "amount" credits to the balance of "userid"."""
		async with self.bot.db[0].acquire() as pconn:
			await pconn.execute('mewcoins = mewcoins + $1 WHERE u_id = $2', amount, userid)
		
	async def _remove_credits(self, userid: int, amount: int):
		"""Removes "amount" credits from the balance of "userid"."""
		async with self.bot.db[0].acquire() as pconn:
			await pconn.execute('mewcoins = mewcoins - $1 WHERE u_id = $2', amount, userid)
