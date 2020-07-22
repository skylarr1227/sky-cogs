import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import asyncpg
import datetime
import logging
import os
import ujson

ACTIVE_CAT_ID = 731973669898682379
INACTIVE_CAT_ID = 732740398535147590
DATABASE_URL = os.environ["DATABASE_URL"]


class Auctioneer(commands.Cog):
	"""Create auctions for Mewbot pokemon."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			auctions = {},
			current_num = 0,
		)
		self.db = None
		self.log = logging.getLogger('red.flamebountycogs.auctioneer')
		self.safe_num = None
		self.tasks = []
		task = asyncio.create_task(self._startup())
		task.add_done_callback(self._error_callback)
		self.tasks.append(task)
		"""
		{
			"1": {
				"author": 145519400223506432,
				"pokemon_info": "...",
				"bid_type": "mewcoins",
				"bid_min": 1000,
				"bids": [[631840748924436490, 100], [620229667294674955, 200]],
				"interval": 1,
				"channel": 731974207218647121,
				"message": 731974207717638214,
				"status": "active",
				"end": 1594603316.7081,
				"poke": 2342
			},
			"2": {...}
		}
		"""
	
	def _error_callback(self, fut):
		"""Logs errors in finished tasks."""
		try:
			fut.result()
		except asyncio.CancelledError:
			pass
		except Exception as e:
			msg = 'Error in Auctioneer.\n'
			self.log.exception(msg)
	
	async def init(self, con):
		"""Required for the DB."""
		await con.set_type_codec(
			typename='json',
			encoder=ujson.dumps,
			decoder=ujson.loads,
			schema='pg_catalog'
		)
	
	async def _startup(self):
		"""Opens the DB connection and creates auction waiting tasks after a cog restart."""
		self.db = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=200, command_timeout=5, init=self.init)
		auctions = await self.config.auctions()
		for num, auction in auctions.items():
			if auction['status'] == 'active':
				task = asyncio.create_task(self._await_auction(num))
				task.add_done_callback(self._error_callback)
				self.tasks.append(task)
	
	@commands.group(aliases=['auction', 'auc', 'a'])
	async def auctioneer(self, ctx):
		"""Create auctions for Mewbot pokemon."""
		pass
	
	@auctioneer.command()
	async def bid(self, ctx, auction_id: int, amount: int):
		"""Bid on a running auction."""
		auction_id = str(auction_id)
		try:
			auction = await self.config.auctions.get_raw(auction_id)
		except KeyError:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] == ctx.author.id:
			await ctx.send('You cannot bid on your own auction!')
			return
		if not await self._check_balance(ctx.author.id, amount, auction['bid_type']):
			await ctx.send(f'You do not have enough {auction["bid_type"]}!')
			return
		if amount < auction['bid_min']:
			await ctx.send('That bid is lower than the minimum bid!')
			return
		bids = auction['bids']
		if bids and bids[-1][0] == ctx.author.id:
			await ctx.send('You already have the highest bid!')
			return
		if bids and bids[-1][1] >= amount:
			await ctx.send('Your bid is lower than the current highest bid!')
			return
		if bids and amount - bids[-1][1] < auction['interval']:
			await ctx.send('Your bid is lower than the minimum interval!')
			return
		if bids:
			await self._add_credits(bids[-1][0], bids[-1][1], auction['bid_type'])
			user = self.bot.get_user(bids[-1][0])
			if user:
				try:
					await user.send(f'You have been outbid by {ctx.author} in auction #{auction_id}!')
				except discord.errors.HTTPException:
					pass
		bids.append([ctx.author.id, amount])
		await self.config.auctions.set_raw(auction_id, 'bids', value=bids)
		await self._remove_credits(ctx.author.id, amount, auction['bid_type'])
		await self._update_auction(auction_id)
		await ctx.send('Your bid has been submitted.')
	
	@auctioneer.command()
	async def create(self, ctx, poke: int):
		"""Create a new auction for a mewbot pokemon."""
		if poke == 1:
			await ctx.send('You can not use your first Pokemon in the auction!')
			return 
		poke = await self._find_pokemon(ctx.author.id, poke)
		if poke is None:
			await ctx.send('You do not have that Pokemon or that Pokemon is currently selected.')
			return
		category = self.bot.get_channel(ACTIVE_CAT_ID)
		if not category:
			await ctx.send('I could not find the category I am supposed to send auctions to.')
			return
		
		try:
			#Q1
			await ctx.send('Do you want to auction your pokemon for `mewcoins` or `redeem`?')
			resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
			resp = resp.content.lower()
			if resp in ('mewcoins', 'redeem'):
				bid_type = resp
			else:
				await ctx.send('Type specified was not valid.')
				return
			#Q2
			await ctx.send('What should be the minimum bid?')
			resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
			try:
				bid_min = int(resp.content)
			except ValueError:
				await ctx.send('Value specified was not a number.')
				return
			if bid_min < 1:
				await ctx.send('Value specified should not be below 1.')
				return
			#Q3
			await ctx.send('How many hours should the auction last for?')
			resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
			try:
				hours = int(resp.content)
			except ValueError:
				await ctx.send('Value specified was not a number.')
				return
			if hours < 1:
				await ctx.send('Value specified should not be below 1.')
				return
			if hours > 168:
				await ctx.send('Value specified should not be above 168.')
				return
			#Q4
			await ctx.send('What should be the minimum interval between bids?')
			resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
			try:
				interval = int(resp.content)
			except ValueError:
				await ctx.send('Value specified was not a number.')
				return
			if interval < 1:
				await ctx.send('Value specified should not be below 1.')
				return
		except asyncio.TimeoutError:
			await ctx.send('You took too long to respond.')
			return
		
		if not self.safe_num:
			self.safe_num = await self.config.current_num()
		self.safe_num += 1
		await self.config.current_num.set(self.safe_num)
		num = str(self.safe_num)
		end = (datetime.datetime.utcnow() + datetime.timedelta(hours=hours)).timestamp()
		poke_data = await self._get_pokemon_data(poke)
		pokemon_info = (
			f'Level {poke_data["pokelevel"]} {poke_data["shiny"]} {poke_data["pokname"]} "{poke_data["poknick"]}" {poke_data["gender"]}\n'
			f'**Nature**: {poke_data["nature"]}\n'
			f'**HP**: {poke_data["hpiv"]} **IVs** | {poke_data["hpev"]} **EVs**\n'
			f'**Attack**: {poke_data["atkiv"]} **IVs** | {poke_data["atkev"]} **EVs**\n'
			f'**Defense**: {poke_data["defiv"]} **IVs** | {poke_data["defev"]} **EVs**\n'
			f'**Sp. Atk**: {poke_data["spatkiv"]} **IVs** | {poke_data["spatkev"]} **EVs**\n'
			f'**Sp. Def**: {poke_data["spdefiv"]} **IVs** | {poke_data["spdefev"]} **EVs**\n'
			f'**Speed**: {poke_data["speediv"]} **IVs** | {poke_data["speedev"]} **EVs**\n'
			f'**Happiness**: {poke_data["happiness"]}\n'
			f'IV %: {poke_data["iv_percent"]}'
		)
		channel_name = f'{num} {poke_data["shiny"]}{poke_data["pokname"]} {round(poke_data["iv_percent"])}'
		return (pokemon_info, channel_name)
		embed = await self._build_embed(num, ctx.author.id, pokemon_info, bid_type, bid_min, [], interval, 'active', end)
		
		try:
			channel = await category.create_text_channel(channel_name, reason='Auctioneer')
		except discord.errors.HTTPException:
			await ctx.send('I do not have permission to create text channels.')
			return
		message = await channel.send(embed=embed)
		auction = {
			'author': ctx.author.id,
			'pokemon_info': pokemon_info,
			'bid_type': bid_type,
			'bid_min': bid_min,
			'bids': [],
			'interval': interval,
			'channel': channel.id,
			'message': message.id,
			'status': 'active',
			'end': end,
			'poke': poke,
			'poke_data': poke_data
		}
		await self.config.auctions.set_raw(num, value=auction)
		await self._remove_pokemon(ctx.author.id, poke)
		task = asyncio.create_task(self._await_auction(num))
		task.add_done_callback(self._error_callback)
		self.tasks.append(task)
		await ctx.send(f'Auction #{num} created.')

	@auctioneer.command()
	async def cancel(self, ctx, auction_id: int):
		"""
		Cancel an existing auction you created.
		
		Auctions can only be canceled if there are no bids.
		"""
		auction_id = str(auction_id)
		try:
			auction = await self.config.auctions.get_raw(auction_id)
		except KeyError:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] != ctx.author.id:
			await ctx.send('You cannot cancel auctions you do not own!')
			return
		bids = auction['bids']
		if bids:
			await ctx.send('There are bids on that auction! Use `,a endearly` to end an auction early.')
			return
		await self._add_pokemon(ctx.author.id, auction['poke'])
		await self.config.auctions.set_raw(auction_id, 'status', value='canceled')
		await self.config.auctions.set_raw(auction_id, 'end', value=datetime.datetime.utcnow().timestamp())
		await self._update_auction(auction_id)
		cat = self.bot.get_channel(INACTIVE_CAT_ID)
		channel = self.bot.get_channel(auction['channel'])
		if cat and channel:
			await channel.edit(category=cat)
		if channel:
			await channel.send(f'Auction #{auction_id} by {ctx.author.mention} was canceled.')
		await ctx.send('Your auction has been canceled.')

	@auctioneer.group()
	async def edit(self, ctx):
		"""Edit the properties of an existing auction."""
		pass
	
	@edit.command()
	async def interval(self, ctx, auction_id: int, interval: int):
		"""Set the minimum interval for an auction."""
		auction_id = str(auction_id)
		try:
			auction = await self.config.auctions.get_raw(auction_id)
		except KeyError:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] != ctx.author.id:
			await ctx.send('You cannot edit auctions you do not own!')
			return
		if interval < 1:
			await ctx.send('Value specified should not be below 1.')
		await self.config.auctions.set_raw(auction_id, 'interval', value=interval)
		await self._update_auction(auction_id)
		await ctx.send('Interval set.')
	
	@edit.command()
	async def minbid(self, ctx, auction_id: int, minbid: int):
		"""
		Set the minimum bid for an auction.
		
		Auctions with bids cannot have their minimum bid changed.
		"""
		auction_id = str(auction_id)
		try:
			auction = await self.config.auctions.get_raw(auction_id)
		except KeyError:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] != ctx.author.id:
			await ctx.send('You cannot edit auctions you do not own!')
			return
		bids = auction['bids']
		if bids:
			await ctx.send('There are already bids on that auction!')
			return
		if minbid < 1:
			await ctx.send('Value specified should not be below 1.')
			return
		await self.config.auctions.set_raw(auction_id, 'bid_min', value=minbid)
		await self._update_auction(auction_id)
		await ctx.send('Minimum bid set.')

	@auctioneer.command()
	async def endearly(self, ctx, auction_id: int):
		"""
		End an auction early, accepting the current highest bid.
		
		Auctions can only be ended early once they have a bid.
		"""
		auction_id = str(auction_id)
		try:
			auction = await self.config.auctions.get_raw(auction_id)
		except KeyError:
			await ctx.send('An auction with that id does not exist!')
			return
		if auction['status'] != 'active':
			await ctx.send('That auction is no longer active!')
			return
		if auction['author'] != ctx.author.id:
			await ctx.send('You cannot end auctions you do not own!')
			return
		bids = auction['bids']
		if not bids:
			await ctx.send('There are no bids on that auction! Use `,a cancel` to cancel an auction.')
			return
		await self.config.auctions.set_raw(auction_id, 'end', value=datetime.datetime.utcnow().timestamp())
		await self._end_auction(auction_id)
		await ctx.send('Your auction has been ended.')

	@auctioneer.command(name='list')
	async def list_auctions(self, ctx):
		"""List all active auctions."""
		data = []
		auctions = await self.config.auctions()
		for auction_id in auctions:
			if auctions[auction_id]['status'] != 'active':
				continue
			poke_data = auctions[auction_id]['poke_data']
			if auctions[auction_id]['bids']:
				bidder = auctions[auction_id]['bids'][0]
				bidder = self.bot.get_user() or bidder
				bid = auctions[auction_id]['bids'][1]
			else:
				bidder = f'Min bid: {auctions[auction_id]["bid_min"]}'
				bid = 'No one yet...'
			data.append([auction_id, poke_data[''], poke_data[''], bid, bidder])
		msg = tabulate(data, headers=['#', 'Name', 'IV %', 'Highest Bid', 'Bidder'])
		paged = pagify(msg)
		box_paged = (f'```\n{x}```' for x in paged)
		await ctx.send_interactive(box_paged)

	async def _build_embed(self, num, author, pokemon_info, bid_type, bid_min, bids, interval, status, end):
		"""Creates an embed that represents a given auction."""
		colors = {'active': discord.Color.green(), 'ended': discord.Color.red(), 'canceled': discord.Color.dark_red()}
		embed = discord.Embed(
			title=f'Auction #{num}',
			description=pokemon_info,
			color=colors[status],
			timestamp=datetime.datetime.fromtimestamp(end)
		)
		author = self.bot.get_user(author) or author
		embed.add_field(name='**Author**', value=f'{author}')
		if bid_type == 'mewcoins':
			emoji = self.bot.get_emoji(731709469414785047) or 'Mewcoins'
		else:
			emoji = 'Redeem'
		if bids:
			bid_member = self.bot.get_user(bids[-1][0]) or bids[-1][0]
			bid_value = bids[-1][1]
			embed.add_field(name='**Top bid**', value=f'{bid_value} {emoji} by {bid_member}')
			if status == 'active':
				embed.add_field(name='**Minimum interval**', value=f'{interval} {emoji}')
		else:
			embed.add_field(name='**Top bid**', value=f'No bids yet\nMinimum bid is {bid_min} {emoji}')
		embed.set_footer(text='Auction ends' if status == 'active' else 'Auction ended')
		return embed
	
	async def _update_auction(self, num):
		"""Updates the auction message for a given auction."""
		auction = await self.config.auctions.get_raw(num)
		embed = await self._build_embed(num, auction['author'], auction['pokemon_info'], auction['bid_type'], auction['bid_min'], auction['bids'], auction['interval'], auction['status'], auction['end'])
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
		await self.config.auctions.set_raw(num, 'status', value='ended')
		await self._update_auction(num)
		auction = await self.config.auctions.get_raw(num)
		cat = self.bot.get_channel(INACTIVE_CAT_ID)
		channel = self.bot.get_channel(auction['channel'])
		if cat and channel:
			await channel.edit(category=cat)
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
		await self._add_credits(auction['author'], amount, auction['bid_type'])
		await self._add_pokemon(bids[-1][0], auction['poke'])
		winner = self.bot.get_user(bids[-1][0])
		if winner:
			winner = winner.mention
		else:
			winner = bids[-1][0]
		if auction['bid_type'] == 'mewcoins':
			emoji = self.bot.get_emoji(731709469414785047) or 'Mewcoins'
		else:
			emoji = 'Redeem'
		if channel:
			await channel.send(f'Auction #{num} by {author} has ended.\nThe winner is {winner} with a bid of {amount} {emoji}.')
	
	def cog_unload(self):
		"""Closes auction tasks on cog unload."""
		for task in self.tasks:
			try:
				task.cancel()
			except Exception:
				pass
		task = asyncio.create_task(self._shutdown())
		task.add_done_callback(self._error_callback)
		
	async def _shutdown(self):
		"""Close the DB connection when unloading the cog."""
		if self.db:
			await self.db.close()
	
	#DB INTERACTING FUNCS
	async def _find_pokemon(self, userid: int, user_poke: int):
		"""
		Gets the pokeid of a specific pokemon "userid" owns.
		
		Returns the actual pokeid of the pokemon, or None if it could not be found.
		"""
		async with self.db.acquire() as pconn:
			poke = await pconn.fetchval('SELECT pokes[$1] FROM users WHERE u_id = $2', user_poke, userid)
			name = await pconn.fetchval('SELECT pokname FROM pokes WHERE id = $1', poke)
			if name in (None, 'Egg'):
				return None
			selected = await pconn.fetchval('SELECT selected FROM users WHERE u_id = $1', userid)
			if selected and selected == poke:
				return None
			return poke
	
	async def _add_pokemon(self, userid: int, poke: int):
		"""Add a pokemon with id "poke" from user "userid"."""
		async with self.db.acquire() as pconn:
			await pconn.execute('UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2', poke, userid)

	async def _remove_pokemon(self, userid: int, poke: int):
		"""Remove a pokemon with id "poke" from user "userid"."""
		async with self.db.acquire() as pconn:
			await pconn.execute('UPDATE users SET pokes = array_remove(pokes, $1) WHERE u_id = $2', poke, userid)
	
	async def _get_pokemon_data(self, poke: int):
		"""
		Gets the pokemon info of a specific pokemon.
		
		Returns a dict containing the information about that pokemon.
		"""
		async with self.db.acquire() as pconn:
			call = (
				'SELECT pokelevel, pokname, poknick, gender, '
				'nature, hpiv, hpev, atkiv, atkev, defiv, defev, '
				'spatkiv, spatkev, spdefiv, spdefev, speediv, speedev, '
				'happiness, shiny FROM pokes WHERE id = $1'
			)
			pokemon = await pconn.fetchrow(call, poke)
			pokemon = dict(pokemon)
			pokemon['shiny'] = '\N{SPARKLES} ' if pokemon['shiny'] else ''
			total_iv = pokemon['hpiv'] + pokemon['atkiv'] + pokemon['defiv'] + pokemon['spatkiv'] + pokemon['spdefiv'] + pokemon['speediv']
			pokemon['iv_percent'] = round((total_iv / 186) * 100, 2)
			if pokemon['gender'] == '-m':
				pokemon['gender'] = self.bot.get_emoji(732731801797132370) or '\N{MALE SIGN}'
			else:
				pokemon['gender'] = self.bot.get_emoji(732731778674065448) or '\N{FEMALE SIGN}'
			return pokemon
	
	async def _check_balance(self, userid: int, amount: int, bid_type: str):
		"""Returns a bool indicating whether or not "userid" has at least "amount" credits of "bid_type" type."""
		async with self.db.acquire() as pconn:
			#Yes, I know I'm testing for equality then hardcoding intead of just using the string. However, since this is technically
			#string user input, I'd rather be slightly inefficient than risk a db breach.
			if bid_type == 'mewcoins':
				money = await pconn.fetchval('SELECT mewcoins FROM users WHERE u_id = $1', userid)
			elif bid_type == 'redeem':
				money = await pconn.fetchval('SELECT redeems FROM users WHERE u_id = $1', userid)
			else:
				raise ValueError(f'Invalid bid_type "{bid_type}".')
			return money >= amount
		
	async def _add_credits(self, userid: int, amount: int, bid_type: str):
		"""Adds "amount" credits to the balance of "userid" of "bid_type" type."""
		async with self.db.acquire() as pconn:
			if bid_type == 'mewcoins':
				await pconn.execute('UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2', amount, userid)
			elif bid_type == 'redeem':
				await pconn.execute('UPDATE users SET redeems = redeems + $1 WHERE u_id = $2', amount, userid)
			else:
				raise ValueError(f'Invalid bid_type "{bid_type}".')
			
		
	async def _remove_credits(self, userid: int, amount: int, bid_type: str):
		"""Removes "amount" credits from the balance of "userid" of "bid_type" type."""
		async with self.db.acquire() as pconn:
			if bid_type == 'mewcoins':
				await pconn.execute('UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2', amount, userid)
			elif bid_type == 'redeem':
				await pconn.execute('UPDATE users SET redeems = redeems - $1 WHERE u_id = $2', amount, userid)
			else:
				raise ValueError(f'Invalid bid_type "{bid_type}".')
