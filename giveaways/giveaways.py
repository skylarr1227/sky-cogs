import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import asyncpg
import datetime
import os
import random
import ujson

DATABASE_URL = os.environ["DATABASE_URL"]


class GiveawayView(discord.ui.View):
    """Simple view to add the button to enter a giveaway."""
    def __init__(self):
        super().__init__(timeout=0)
    
    @discord.ui.button(label="Enter giveaway", style=discord.ButtonStyle.primary)
    async def callback(self, button, interaction):
        pass


class Giveaways(commands.Cog):
    """Giveaway mewbot pokemon or credits."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=145519400223506432)
        self.config.register_global(
            giveaways = {},
            blacklisted = [],
        )
        self.db = None
        self.tasks = []
        self.allow_interaction = True
        self.lock = asyncio.Lock()
        task = asyncio.create_task(self._startup())
        self.tasks.append(task)

    async def cog_check(self, ctx):
        """Prevent blacklisted users from using the cog."""
        blacklisted = await self.config.blacklisted()
        if ctx.author.id in blacklisted:
            return False
        return True

    async def init(self, con):
        """Required for the DB."""
        await con.set_type_codec(
            typename='json',
            encoder=ujson.dumps,
            decoder=ujson.loads,
            schema='pg_catalog'
        )

    async def _startup(self):
        """Opens the DB connection and creates giveaway waiting tasks after a cog restart."""
        try:
            self.db = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3, command_timeout=5, init=self.init)
        except ConnectionError:
            self.allow_interaction = False
            return
        giveaways = await self.config.giveaways()
        for mid, giveaway in giveaways.items():
            if giveaway['status'] == 'active':
                task = asyncio.create_task(self._await_giveaway(mid))
                self.tasks.append(task)
    
    @commands.group(aliases=["ga"])
    async def giveaway(self, ctx):
        pass
    
    @giveaway.command()
    async def create(self, ctx):
        if not self.allow_interaction or not await self._test_db():
            await ctx.send('This cog is currently disabled because I cannot access the database.')
            return
        try:
            #Q1
            await ctx.send("What roles are allowed to join? Enter \"none\", or role mentions or IDs seperated by a space (no text names).")
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if resp.content.lower() == "none":
                roles = None
            else:
                roles = []
                for role in resp.content.split(" "):
                    processed_role = role.replace("<@&", "").replace(">", "")
                    try:
                        processed_role = int(processed_role)
                    except ValueError:
                        await ctx.send(f"\"{role}\" is not a valid role mention or ID.", allowed_mentions=discord.AllowedMentions.none())
                        return
                    processed_role = ctx.guild.get_role(processed_role)
                    if not processed_role:
                        await ctx.send(f"\"{role}\" is not a valid role mention or ID.", allowed_mentions=discord.AllowedMentions.none())
                        return
                    roles.append(processed_role)
            
            #Q2
            await ctx.send("What pokemon are being given away? Enter \"none\", or IDs seperated by a space as they appear in your /p (not the global IDs).")
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if resp.content.lower() == "none":
                pokes = None
            else:
                pokes = []
                for poke in resp.content.split(" "):
                    processed_poke = poke.replace("<@&", "").replace(">", "")
                    try:
                        processed_poke = int(processed_poke)
                    except ValueError:
                        await ctx.send(f"\"{poke}\" is not a valid relative poke ID.", allowed_mentions=discord.AllowedMentions.none())
                        return
                    async with self.db.acquire() as pconn:
                        processed_poke = await pconn.fetchval("SELECT pokes[$1] FROM users WHERE u_id = $2", processed_poke, ctx.author.id)
                    if not processed_poke:
                        await ctx.send(f"\"{poke}\" is not a valid relative poke ID.", allowed_mentions=discord.AllowedMentions.none())
                        return
                    pokes.append(processed_poke)
            
            #Q3
            await ctx.send("How many credits are being given away? Enter \"none\", or a number.")
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if resp.content.lower() == "none":
                creds = None
            else:
                try:
                    creds = int(resp.content)
                except ValueError:
                    await ctx.send(f"\"{resp.content}\" is not a valid amount of credits.", allowed_mentions=discord.AllowedMentions.none())
                    return
                if creds < 0:
                    await ctx.send("You cannot giveaway a negative number of credits.")
                    return
                async with self.db.acquire() as pconn:
                    bal = await pconn.fetchval("SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id)
                if bal is None or bal < creds:
                    await ctx.send("You don't have enough credits for that!")
                    return
            
            if not pokes and not creds:
                await ctx.send("You have nothing to giveaway!")
                return
            
            #Q4
            await ctx.send(
                "How many winners should their be? If there is more than one winner, credits will be "
                "evenly split between winners and pokemon will be split evenly between winners in the "
                "order they were added. The number of pokemon added must be a multiple of the number of winners."
            )
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            try:
                winners = int(resp.content)
            except ValueError:
                await ctx.send(f"\"{resp.content}\" is not a valid amount of credits.", allowed_mentions=discord.AllowedMentions.none())
                return
            if winners <= 0:
                await ctx.send("You cannot giveaway to less than one winner.")
                return
            if pokes and len(pokes) % winners != 0:
                await ctx.send("The number of pokemon is not a multiple of the number of winners.")
                return
            
            #Q5
            await ctx.send("How long should the giveaway last for?")
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            td = commands.converter.parse_timedelta(resp.content)
            if not td:
                await ctx.send(f"\"{resp.content}\" is not a valid amount of time.", allowed_mentions=discord.AllowedMentions.none())
            
            #Q6
            await ctx.send("What channel should the giveaway be posted in?")
            resp = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            try:
                channel = await discord.ext.commands.converter.TextChannelConverter().convert(ctx, resp.content)
            except discord.ext.commands.ChannelNotFound:
                await ctx.send("That is not a valid text channel.")
                return
            
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return
        
        end = (datetime.datetime.utcnow() + td).timestamp()
        
        giveaway = {
            'author': ctx.author.id,
            'channel': channel.id,
            'status': 'active',
            'end': end,
            'pokes': pokes,
            'creds': creds,
            'winners': winners,
            'roles': [x.id for x in roles],
            'formatted_roles': ", ".join([x.name for x in roles]),
            'entries': [],
        }
        embed, view = await self._build_embed(giveaway)
        message = await channel.send(embed=embed, view=view)
        
        await self.config.giveaways.set_raw(str(message.id), value=giveaway)
        
        async with self.db.acquire() as pconn:
            if creds:
                await pconn.execute("UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2", creds, ctx.author.id)
            if pokes:
                for poke in pokes:
                    await pconn.execute("UPDATE users SET pokes = array_remove(pokes, $1) WHERE u_id = $2", poke, ctx.author.id)

        task = asyncio.create_task(self._await_giveaway(str(message.id)))
        self.tasks.append(task)
        await ctx.send('Giveaway created.')
    
    @giveaway.command()
    async def endearly(self, ctx):
        ...
    
    @giveaway.command()
    async def cancel(self, ctx):
        ...
    
    @commands.admin()
    @giveaway.command()
    async def blacklist(self, ctx, user_id: int):
        """Blacklist a user from using the cog."""
        if user_id in self.bot.owner_ids:
            await ctx.send("Nice try.")
            return
        if user_id == ctx.author.id:
            await ctx.send("No seppuku...")
            return
        async with self.config.blacklisted() as bl:
            if user_id in bl:
                await ctx.send("That user is already blacklisted.")
                return
            bl.append(user_id)
        await ctx.send(f"Blacklisted `{user_id}`.")
    
    @commands.admin()
    @giveaway.command()
    async def unblacklist(self, ctx, user_id: int):
        """Unblacklist a user from using the cog."""
        if user_id == ctx.author.id:
            await ctx.send("No saving yourself...")
            return
        async with self.config.blacklisted() as bl:
            if user_id not in bl:
                await ctx.send("That user is not blacklisted.")
                return
            bl.remove(user_id)
        await ctx.send(f"Unblacklisted `{user_id}`.")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if not interaction.message or not interaction.user:
            return
        mid = str(interaction.message.id)
        async with self.lock:
            try:
                giveaway = await self.config.giveaways.get_raw(mid)
            except KeyError:
                return
            if giveaway['status'] != 'active':
                await interaction.response.send_message('That giveaway is no longer active!', empirical=True)
                return
            if giveaway['author'] == interaction.user.id:
                await interaction.response.send_message('You cannot enter your own giveaway!', empirical=True)
                return
            if interaction.user.id in giveaway['entries']:
                await interaction.response.send_message('You are already entered in the giveaway!', empirical=True)
                return
            if giveaway['roles'] and not set(giveaway['roles']) & set([x.id for x in interaction.user.roles]):
                await interaction.response.send_message('You do not have any of the roles required for this giveaway!', empirical=True)
            giveaway['entries'].append(interaction.user.id)
            await self.config.giveaways.set_raw(mid, 'entries', value=giveaway['entries'])
        await interaction.response.send_message('You have been entered into the giveaway, good luck!', empirical=True)
    
    async def _build_embed(self, giveaway):
        """Creates an embed that represents a given giveaway."""
        colors = {'active': discord.Color.green(), 'ended': discord.Color.red(), 'canceled': discord.Color.dark_red()}
        author = self.bot.get_user(giveaway['author'])
        embed = discord.Embed(
            title=f'Giveaway by {author.name}',
            color=colors[giveaway['status']],
            timestamp=datetime.datetime.fromtimestamp(giveaway['end'])
        )
        if giveaway['pokes']:
            embed.add_field(name="Pokes", value=len(giveaway['pokes']))
        if giveaway['creds']:
            embed.add_field(name="Credits", value=giveaway['creds'])
        if giveaway['roles']:
            embed.add_field(name="Required role", value=giveaway['formatted_roles'])
        embed.add_field(name="Number of Winners", value=giveaway['winners'])
        if giveaway['status'] == 'active':
            t = 'Giveaway ends'
            view = GiveawayView()
        else:
            t = 'Giveaway ended'
            view = None
        embed.set_footer(text=t)
        return embed, view

    async def _update_giveaway(self, mid):
        """Updates the giveaway message for a given giveaway."""
        giveaway = await self.config.giveaways.get_raw(mid)
        embed, view = await self._build_embed(giveaway)
        channel = self.bot.get_channel(giveaway['channel'])
        if not channel:
            return
        try:
            message = await channel.fetch_message(giveaway['message'])
            await message.edit(embed=embed, view=view)
        except discord.errors.HTTPException:
            return

    async def _await_giveaway(self, mid):
        """Waits for the amount of time a given giveaway has remaining."""
        async with self.lock:
            end = await self.config.giveaways.get_raw(mid, 'end')
        time = end - datetime.datetime.utcnow().timestamp()
        while time > 0:
            await asyncio.sleep(time)
            async with self.lock:
                end = await self.config.giveaways.get_raw(mid, 'end')
            time = end - datetime.datetime.utcnow().timestamp()
        await self._end_giveaway(mid)

    async def _end_giveaway(self, mid):
        """Ends a given giveaway."""
        if not self.allow_interaction or not await self._test_db():
            return
        async with self.lock:
            giveaway = await self.config.giveaways.get_raw(mid)
            if not giveaway['status'] == 'active':
                return
            await self.config.giveaways.set_raw(mid, 'status', value='ended')
            
            giveaway = await self.config.giveaways.get_raw(mid)
            
        channel = self.bot.get_channel(giveaway['channel'])
        await self._update_giveaway(mid)
        entries = list(set(giveaway['entries']))
        creds = giveaway['creds']
        pokes = giveaway['pokes']
        winners = giveaway['winners']
        author = self.bot.get_user(giveaway['author'])
        if not author:
            author = giveaway['author']
        # Special case handling for when there are no winners
        if not entries:
            async with self.db.acquire() as pconn:
                if creds:
                    await pconn.execute("UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2", creds, giveaway['author'])
                if pokes:
                    for poke in pokes:
                        await pconn.execute("UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2", poke, giveaway['author'])
            if channel:
                await channel.send(f'{author}\'s giveaway has ended.\nThere were no entries.')
            return
        
        pokes_per_person = 0
        creds_per_person = 0
        if pokes:
            pokes_per_person = len(pokes) // winners
        if creds:
            creds_per_person = creds // winners
        # Special case handling for when there are less entries than winners
        if len(entries) < winners:
            async with self.db.acquire() as pconn:
                if pokes:
                    idx = len(entries) * pokes_per_person
                    pokes, returned_pokes = pokes[:idx], pokes[idx:]
                    for poke in returned_pokes:
                        await pconn.execute("UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2", poke, giveaway['author'])
                if creds:
                    returned_creds = (winners - len(entries)) * creds_per_person
                    await pconn.execute("UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2", returned_creds, giveaway['author'])
            winners = len(entries)
        winners = random.sample(entries, winners)
        win_text = []
        for idx, winner in enumerate(winners):
            name = self.bot.get_user(winner)
            if name:
                name = name.mention
            else:
                name = str(winner)
            win_text.append(name)
            if creds_per_person:
                await pconn.execute("UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2", creds_per_person, winner)
            if pokes_per_person:
                for i in range(pokes_per_person):
                    await pconn.execute("UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2", pokes[(idx * pokes_per_person) + i], winner)
                    
        win_text = ", ".join(win_text)
        
        if channel:
            await channel.send(f'{author}\'s giveaway has ended.\nThe winners are {win_text}.')

    def cog_unload(self):
        """Closes giveaway tasks on cog unload."""
        for task in self.tasks:
            try:
                task.cancel()
            except Exception:
                pass
        task = asyncio.create_task(self._shutdown())
        
    async def _shutdown(self):
        """Close the DB connection when unloading the cog."""
        if self.db:
            await self.db.close()

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
