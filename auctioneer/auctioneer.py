import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import pagify
import asyncio
import asyncpg
import datetime
import logging
import os
import ujson
from tabulate import tabulate

ACTIVE_CAT_ID = 731973669898682379
INACTIVE_CAT_ID = 732740398535147590
LOG_CHANNEL = 740017242401407026
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
		self.allow_interaction = True
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
				"buyout": 10000,
				"channel": 731974207218647121,
				"message": 731974207717638214,
				"status": "active",
				"end": 1594603316.7081,
				"poke": 2342,
				"poke_data": {
					"pokelevel": 1,
					"pokname": "Clefable",
					"poknick": "",
					"gender": "\N{MALE SIGN}",
					"nature": "Lax",
					"hpiv": 0,
					"hpev": 0,
					"atkiv": 0,
					"atkev": 0,
					"defiv": 0,
					"defev": 0,
					"spatkiv": 0,
					"spatkev": 0,
					"spdefiv": 0,
					"spdefev": 0,
					"speediv": 0,
					"speedev": 0,
					"happiness": 2,
					"shiny": "",
					"iv_percent": 4.42
				}
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
		try:
			self.db = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=200, command_timeout=5, init=self.init)
		except ConnectionError:
			self.allow_interaction = False
			return
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
		if not self.allow_interaction or not await self._test_db():
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
		if amount < auction['bid_min']:
			await ctx.send('That bid is lower than the minimum bid!')
			return
		bids = auction['bids']
		if bids and bids[-1][1] >= amount:
			await ctx.send('Your bid is lower than the current highest bid!')
			return
		#user wants to raise their own bid
		if bids and bids[-1][0] == ctx.author.id:
			delta = amount - bids[-1][1]
			if not await self._check_balance(ctx.author.id, delta, auction['bid_type']):
				await ctx.send(f'You do not have enough {auction["bid_type"]}!')
				return
			await self._remove_credits(ctx.author.id, delta, auction['bid_type'])
		#user bidding normally
		else:
			if bids and amount - bids[-1][1] < auction['interval']:
				await ctx.send('Your bid is lower than the minimum interval!')
				return
			if not await self._check_balance(ctx.author.id, amount, auction['bid_type']):
				await ctx.send(f'You do not have enough {auction["bid_type"]}!')
				return
			if bids:
				await self._add_credits(bids[-1][0], bids[-1][1], auction['bid_type'])
				user = self.bot.get_user(bids[-1][0])
				if user:
					try:
						await user.send(f'You have been outbid by {ctx.author} in auction #{auction_id}!')
					except discord.errors.HTTPException:
						pass
			await self._remove_credits(ctx.author.id, amount, auction['bid_type'])
		bids.append([ctx.author.id, amount])
		await self.config.auctions.set_raw(auction_id, 'bids', value=bids)
		if auction['buyout'] and amount >= auction['buyout']:
			await self.config.auctions.set_raw(auction_id, 'end', value=datetime.datetime.utcnow().timestamp())
			await self._end_auction(auction_id)
		else:
			await self._update_auction(auction_id)
		await ctx.send('Your bid has been submitted.')
		await self._log_interaction(f'Bid\nAuction: {auction_id}\nUser: {ctx.author}\nAmount: {amount}')
	
	@auctioneer.command()
	async def create(self, ctx, poke: int):
		"""Create a new auction for a mewbot pokemon."""
		if not self.allow_interaction or not await self._test_db():
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
		if poke == 1:
			await ctx.send('You can not use your first Pokemon in the auction!')
			return 
		poke = await self._find_pokemon(ctx.author.id, poke)
		if poke is None:
			await ctx.send('You do not have that Pokemon, that Pokemon is currently selected, or that pokemon is enlisted in the market.')
			return
		category = self.bot.get_channel(ACTIVE_CAT_ID)
		if not category:
			await ctx.send('I could not find the category I am supposed to send auctions to.')
			return
		if len(category.channels) >= 50:
			await ctx.send('There are currently too many auctions to create a new one. Try again later.')
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
			#Q5
			await ctx.send('What should be the buyout amount? If you do not want a buyout, say `none`.')
			resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
			if resp.content.lower() == 'none':
				buyout = None
			else:
				try:
					buyout = int(resp.content)
				except ValueError:
					await ctx.send('Value specified was not a number or `none`.')
					return
				if buyout < 1:
					await ctx.send('Value specified should not be below 1.')
					return
				if buyout <= bid_min:
					await ctx.send('Value specified should be greater than the minimum bid.')
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
		auction = {
			'author': ctx.author.id,
			'pokemon_info': pokemon_info,
			'bid_type': bid_type,
			'bid_min': bid_min,
			'bids': [],
			'interval': interval,
			'buyout': buyout,
			'channel': 0, #set AFTER sending message
			'message': 0, #^
			'status': 'active',
			'end': end,
			'poke': poke,
			'poke_data': poke_data
		}
		embed = await self._build_embed(num, auction)
		
		try:
			channel = await category.create_text_channel(channel_name, reason='Auctioneer')
		except discord.errors.HTTPException:
			await ctx.send('I do not have permission to create text channels.')
			return
		message = await channel.send(embed=embed)
		auction['channel'] = channel.id
		auction['message'] = message.id
		
		await self.config.auctions.set_raw(num, value=auction)
		await self._remove_pokemon(ctx.author.id, poke)
		task = asyncio.create_task(self._await_auction(num))
		task.add_done_callback(self._error_callback)
		self.tasks.append(task)
		await ctx.send(f'Auction #{num} created.')
		await self._log_interaction(f'Auction Created\nAuction: {num}\nUser: {ctx.author}')

	@auctioneer.command()
	async def cancel(self, ctx, auction_id: int):
		"""
		Cancel an existing auction you created.
		
		Auctions can only be canceled if there are no bids.
		"""
		if not self.allow_interaction or not await self._test_db():
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
		await self._log_interaction(f'Auction Canceled\nAuction: {auction_id}\nUser: {ctx.author}')

	@auctioneer.group()
	async def edit(self, ctx):
		"""Edit the properties of an existing auction."""
		pass
	
	@edit.command()
	async def buyout(self, ctx, auction_id: int, buyout: int):
		"""Set the buyout for an auction."""
		if not self.allow_interaction:
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
		if buyout < 1:
			await ctx.send('Value specified should not be below 1.')
			return
		if buyout <= auction['bid_min']:
			await ctx.send('Value specified should be greater than the minimum bid.')
			return
		if auction['bids'] and buyout <= auction['bids'][-1][1]:
			await ctx.send('Value specified should be greater than the current highest bid.')
			return
		await self.config.auctions.set_raw(auction_id, 'buyout', value=buyout)
		await self._update_auction(auction_id)
		await ctx.send('Buyout set.')
		await self._log_interaction(f'Auction Edited\nAuction: {auction_id}\nUser: {ctx.author}\nBuyout: {buyout}')
	
	@edit.command()
	async def interval(self, ctx, auction_id: int, interval: int):
		"""Set the minimum interval for an auction."""
		if not self.allow_interaction:
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
			return
		await self.config.auctions.set_raw(auction_id, 'interval', value=interval)
		await self._update_auction(auction_id)
		await ctx.send('Interval set.')
		await self._log_interaction(f'Auction Edited\nAuction: {auction_id}\nUser: {ctx.author}\nInterval: {interval}')
	
	@edit.command()
	async def minbid(self, ctx, auction_id: int, minbid: int):
		"""
		Set the minimum bid for an auction.
		
		Auctions with bids cannot have their minimum bid changed.
		"""
		if not self.allow_interaction:
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
		if auction['bids']:
			await ctx.send('There are already bids on that auction!')
			return
		if minbid < 1:
			await ctx.send('Value specified should not be below 1.')
			return
		await self.config.auctions.set_raw(auction_id, 'bid_min', value=minbid)
		await self._update_auction(auction_id)
		await ctx.send('Minimum bid set.')
		await self._log_interaction(f'Auction Edited\nAuction: {auction_id}\nUser: {ctx.author}\nMinimum Bid: {minbid}')

	@auctioneer.command()
	async def endearly(self, ctx, auction_id: int):
		"""
		End an auction early, accepting the current highest bid.
		
		Auctions can only be ended early once they have a bid.
		"""
		if not self.allow_interaction or not await self._test_db():
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
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
		if not self.allow_interaction:
			await ctx.send('This cog is currently disabled because I cannot access the database.')
			return
		data = []
		auctions = await self.config.auctions()
		for auction_id in auctions:
			if auctions[auction_id]['status'] != 'active':
				continue
			poke_data = auctions[auction_id]['poke_data']
			
			if auctions[auction_id]['bid_type'] == 'mewcoins':
				bid_type = 'c'
			elif auctions[auction_id]['bid_type'] == 'redeem':
				bid_type = 'r'
			
			if auctions[auction_id]['bids']:
				bidder = auctions[auction_id]['bids'][-1][0]
				bidder = self.bot.get_user(bidder) or bidder
			else:
				bidder = '-'
			
			t = datetime.datetime.fromtimestamp(auctions[auction_id]['end'])
			d = t - datetime.datetime.utcnow()
			if d.days:
				time = str(d.days) + 'd'
			elif d.seconds // 3600:
				time = str(d.seconds // 3600) + 'h'
			elif d.seconds // 60:
				time = str(d.seconds // 60) + 'm'
			elif d.seconds:
				time = str(d.seconds) + 's'
			
			data.append([auction_id, poke_data['shiny'].strip(), poke_data['pokname'], str(poke_data['iv_percent']) + '%', bid_type, bidder, time])
		msg = tabulate(data, headers=['#', '\N{SPARKLES}', 'Name', 'IV %', '$', 'Bidder', 'Time'])
		paged = pagify(msg)
		box_paged = (f'```\n{x}```' for x in paged)
		await ctx.send_interactive(box_paged)

	async def _build_embed(self, num, auction):
		"""Creates an embed that represents a given auction."""
		colors = {'active': discord.Color.green(), 'ended': discord.Color.red(), 'canceled': discord.Color.dark_red()}
		embed = discord.Embed(
			title=f'Auction #{num}',
			description=auction['pokemon_info'],
			color=colors[auction['status']],
			timestamp=datetime.datetime.fromtimestamp(auction['end'])
		)
		author = self.bot.get_user(auction['author']) or auction['author']
		embed.add_field(name='**Author**', value=f'{author}')
		if auction['bid_type'] == 'mewcoins':
			emoji = self.bot.get_emoji(731709469414785047) or 'Mewcoins'
		else:
			emoji = 'Redeem'
		if auction['bids']:
			bid_member = self.bot.get_user(auction['bids'][-1][0]) or auction['bids'][-1][0]
			bid_value = auction['bids'][-1][1]
			embed.add_field(name='**Top bid**', value=f'{bid_value} {emoji} by {bid_member}')
			if auction['status'] == 'active':
				embed.add_field(name='**Minimum interval**', value=f'{auction["interval"]} {emoji}')
		else:
			embed.add_field(name='**Top bid**', value=f'No bids yet\nMinimum bid is {auction["bid_min"]} {emoji}')
		if auction['buyout']:
			embed.add_field(name='**Buyout**', value=f'{auction["buyout"]} {emoji}')
		embed.set_footer(text='Auction ends' if auction['status'] == 'active' else 'Auction ended')
		return embed
	
	async def _update_auction(self, num):
		"""Updates the auction message for a given auction."""
		auction = await self.config.auctions.get_raw(num)
		embed = await self._build_embed(num, auction)
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
		if not self.allow_interaction or not await self._test_db():
			return
		auction = await self.config.auctions.get_raw(num)
		if not auction['status'] == 'active':
			return
		await self.config.auctions.set_raw(num, 'status', value='ended')
		cat = self.bot.get_channel(INACTIVE_CAT_ID)
		channel = self.bot.get_channel(auction['channel'])
		if cat and channel:
			if len(cat.channels) >= 50:
				try:
					await cat.channels[0].delete()
				except discord.errors.HTTPException:
					pass
			try:
				await channel.edit(category=cat)
			except discord.errors.HTTPException:
				pass
		await self._update_auction(num)
		bids = auction['bids']
		author = self.bot.get_user(auction['author'])
		if not author:
			author = auction['author']
		if not bids:
			await self._add_pokemon(auction['author'], auction['poke'])
			if channel:
				await channel.send(f'Auction #{num} by {author.mention} has ended.\nThere were no bids.')
			await self._log_interaction(f'Auction Ended\nAuction: {num}\nUser: {author}\nWinner: None')
			return
		amount = bids[-1][1]
		await self._add_credits(auction['author'], amount, auction['bid_type'])
		await self._add_pokemon(bids[-1][0], auction['poke'])
		winner = self.bot.get_user(bids[-1][0])
		if not winner:
			winner = bids[-1][0]
		if auction['bid_type'] == 'mewcoins':
			emoji = self.bot.get_emoji(731709469414785047) or 'Mewcoins'
		else:
			emoji = 'Redeem'
		if channel:
			await channel.send(f'Auction #{num} by {author.mention} has ended.\nThe winner is {winner.mention} with a bid of {amount} {emoji}.')
		await self._log_interaction(f'Auction Ended\nAuction: {num}\nUser: {author}\nWinner: {winner}\nAmount: {amount}')
	
	async def _log_interaction(self, message):
		"""Logs a message to the designated logging channel."""
		channel = self.bot.get_channel(LOG_CHANNEL)
		if channel:
			try:
				await channel.send(f'```\n{message}```')
			except Exception:
				pass
	
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
	async def _test_db(self):
		"""Tests if the DB is available, shuts down the cog if it is not."""
		try:
			async with self.db.acquire() as pconn:
				pass
		except ConnectionError:
			for task in self.tasks:
				try:
					task.cancel()
				except Exception:
					pass
			self.allow_interaction = False
			return False
		return True
	
	async def _find_pokemon(self, userid: int, user_poke: int):
		"""
		Gets the pokeid of a specific pokemon "userid" owns.
		
		Returns the actual pokeid of the pokemon, or None if it could not be found.
		"""
		async with self.db.acquire() as pconn:
			poke = await pconn.fetchval('SELECT pokes[$1] FROM users WHERE u_id = $2', user_poke, userid)
			data = await pconn.fetchrow('SELECT pokname, market_enlist FROM pokes WHERE id = $1', poke)
			if data['pokname'] in (None, 'Egg'):
				return None
			if data['market_enlist']:
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
			#Yes, I know I'm testing for equality then hardcoding instead of just using the string. However, since this is technically
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
