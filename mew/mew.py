import discord
from redbot.core import commands
from discord.ext import tasks
from .checks import *

import asyncio
import asyncpg
import os
import random
import ujson
from motor.motor_asyncio import AsyncIOMotorClient
from redbot.core.utils.chat_formatting import pagify
import aiohttp
from tabulate import tabulate


REQUESTS_CHANNEL = 894732056645484544
DEV_CHANNEL = 728758254796275782
DATABASE_URL = os.environ["DATABASE_URL"]
#MONGO_URL = os.environ["MONGO_URL"]

class Mew(commands.Cog):
    """Mew"""
    def __init__(self, bot):
        self.bot = bot
        self.active_requests = {}
        self.db = None
 #       self.mongo = AsyncIOMotorClient(MONGO_URL).pokemon
        asyncio.create_task(self._startup())
        self.stats.start()
    
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
            self.db = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3, command_timeout=5, init=self.init)
        except ConnectionError:
            await self.bot.http.send_message(DEV_CHANNEL, "mew.py could not connect to postgres.")
            return

    @check_helper()
    @commands.command()
    async def listedit(self, ctx, row: int, *to_change):
        token = os.environ["SKY_LIST_KEY"]
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        json = {}

        if len(to_change) % 2:
            await ctx.send("Key-value pairs do not match up!")
            return
        for i in range(0, len(to_change), 2):
            key = to_change[i].lower()
            value = to_change[i + 1].lower()
            if key not in ("name", "link", "added?"):
                await ctx.send(f"Invalid key {key}.")
                return
            if key == "added?":
                if value[0] in ("t", "y"):
                    value = True
                elif value[0] in ("f", "n"):
                    value = False
                else:
                    await ctx.send(f"Value for {key} must be a boolean.")
                    return
            json[key] = value

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f'https://dev.mewbot.art/api/database/rows/table/105/{row}/?user_field_names=true',
                headers=headers,
                json=json
            ) as r:
                status = r.ok
                result = await r.text()
            if not status:
                await ctx.send(f"Something went wrong trying to edit that row.\n{result}"[:2000])
            else:
                await ctx.send("Row edited.")
            
    @check_helper()
    @commands.command()
    async def listadd(self, ctx, name: str, link: str, added: bool):
        token = os.environ["SKY_LIST_KEY"]
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        json = {
            "name": name,
            "link": link,
            "added?": added,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://dev.mewbot.art/api/database/rows/table/105/?user_field_names=true',
                headers=headers,
                json=json
            ) as r:
                status = r.ok
                result = await r.text()
            if not status:
                await ctx.send(f"Something went wrong trying to add that row.\n{result}"[:2000])
            else:
                await ctx.send("Row added.")

    @check_helper()
    @commands.command()
    async def listshow(self, ctx):
        token = os.environ["SKY_LIST_KEY"]
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        url = 'https://dev.mewbot.art/api/database/rows/table/105/?user_field_names=true'
        raw = []
        async with aiohttp.ClientSession() as session:
            for _ in range(25):
                async with session.get(url, headers=headers) as r:
                    data = await r.json()
                    raw.extend(data["results"])
                    url = data["next"]
                    if url is None:
                        break
        data = [(item["id"], item["name"], item["link"], item["added?"]) for item in raw]
        text = tabulate(data, headers=("ID", "name", "link", "added?"))
        paged = pagify(text)
        box_paged = (f'{"`" * 3}\n{x}{"`" * 3}' for x in paged)
        await ctx.send_interactive(box_paged)

    @check_gymauth()
    @commands.command()
    async def greason(self, ctx, *, args):
        """Send a reason for using a command."""
        await self.bot.http.send_message(
            REQUESTS_CHANNEL,
            f"GYM AUTH's REASON:{args}"
        )

    @check_gymauth()
    @commands.command()
    async def reward_poke(self, ctx, *, args):
        """Creates a new poke and gives it to the author."""
        args = args.lower().split()
        extras = ""
        shiny = "shiny" in args
        radiant = "radiant" in args
        boosted = "boosted" in args
        if shiny:
            extras += "shiny "
            args.remove("shiny")
        if radiant:
            extras += "radiant "
            args.remove("radiant")
        if boosted:
            extras += "boosted "
            args.remove("boosted")
        poke = "-".join(args).capitalize()
        async def callback():
            await self.create_poke(ctx.author.id, poke, shiny=shiny, radiant=radiant, boosted=boosted)
            await ctx.author.send("Reward poke accepted by admin")
            await self.bot.http.send_message(882419606134874192, f"{ctx.author} used reward_poke {extras}{args}")
        await self.make_request(ctx, callback)

    @check_admin()
    @commands.command()
    async def acceptrequest(self, ctx, request: int):
        """Accept a request to run a command."""
        if request not in self.active_requests:
            await ctx.send("That is not an active request. It may have expired or already been accepted.")
            return
        await ctx.send("Request accepted. Running the command.")
        func = self.active_requests[request]
        del self.active_requests[request]
        await func()
    
    async def make_request(self, ctx, callback):
        """Creates a request to run a command."""
        self.active_requests[ctx.message.id] = callback
        await ctx.send("Request made.")
        await self.bot.http.send_message(
            REQUESTS_CHANNEL,
            f"{ctx.author} wants to use `{ctx.message.content}`.\nAccept this request with"
        )
        await self.bot.http.send_message(
            REQUESTS_CHANNEL, 
            f"`{ctx.prefix}acceptrequest {ctx.message.id}`"
        )
    
    #async def create_poke(
    #    self,
    #    user_id: int,
    #    pokemon: str,
    #    *,
    #    boosted: bool = False,
    #    radiant: bool = False,
    #    shiny: bool = False,
    #    gender: str = None,
    #    level: int = 1
    #):
    #    """Creates a poke and gives it to user."""
    #    form_info = await self.mongo.forms.find_one({"identifier": pokemon.lower()})
    #    pokemon_info = await self.mongo.pfile.find_one({"id": form_info["pokemon_id"]})
    #    try:
    #        gender_rate = pokemon_info["gender_rate"]
    #    except Exception:
    #        return
#
    #    ab_ids = (
    #        await self.mongo
    #        .poke_abilities.find({"pokemon_id": form_info["pokemon_id"]})
    #        .to_list(length=3)
    #    )
    #    ab_ids = [doc["ability_id"] for doc in ab_ids]
#
    #    natlist = [
    #        "Lonely",
    #        "Brave",
    #        "Adamant",
    #        "Naughty",
    #        "Bold",
    #        "Relaxed",
    #        "Impish",
    #        "Lax",
    #        "Timid",
    #        "Hasty",
    #        "Jolly",
    #        "Naive",
    #        "Modest",
    #        "Mild",
    #        "Quiet",
    #        "Rash",
    #        "Calm",
    #        "Gentle",
    #        "Sassy",
    #        "Careful",
    #        "Bashful",
    #        "Quirky",
    #        "Serious",
    #        "Docile",
    #        "Hardy",
    #    ]
#
    #    min_iv = 12 if boosted else 1
    #    max_iv = 31 if boosted or random.randint(0, 1) else 29
    #    hpiv = random.randint(min_iv, max_iv)
    #    atkiv = random.randint(min_iv, max_iv)
    #    defiv = random.randint(min_iv, max_iv)
    #    spaiv = random.randint(min_iv, max_iv)
    #    spdiv = random.randint(min_iv, max_iv)
    #    speiv = random.randint(min_iv, max_iv)
    #    nature = random.choice(natlist)
    #    if not gender:
    #        if "idoran" in pokemon.lower():
    #            gender = pokemon[-2:]
    #        elif pokemon.lower() == "volbeat":
    #            gender = "-m"
    #        elif pokemon.lower() == "illumise":
    #            gender = "-f"
    #        elif pokemon.lower() == "gallade":
    #            gender = "-m"
    #        elif pokemon.lower() == "nidoking":
    #            gender = "-m"
    #        elif pokemon.lower() == "nidoqueen":
    #            gender = "-f"
    #        else:
    #            if gender_rate in (8, -1) and pokemon.capitalize() in (
    #                "Blissey",
    #                "Bounsweet",
    #                "Chansey",
    #                "Cresselia",
    #                "Flabebe",
    #                "Floette",
    #                "Florges",
    #                "Froslass",
    #                "Happiny",
    #                "Illumise",
    #                "Jynx",
    #                "Kangaskhan",
    #                "Lilligant",
    #                "Mandibuzz",
    #                "Miltank",
    #                "Nidoqueen",
    #                "Nidoran-f",
    #                "Nidorina",
    #                "Petilil",
    #                "Salazzle",
    #                "Smoochum",
    #                "Steenee",
    #                "Tsareena",
    #                "Vespiquen",
    #                "Vullaby",
    #                "Wormadam",
    #                "Meowstic-f",
    #            ):
    #                gender = "-f"
    #            elif gender_rate in (8, -1, 0) and not pokemon.capitalize() in (
    #                "Blissey",
    #                "Bounsweet",
    #                "Chansey",
    #                "Cresselia",
    #                "Flabebe",
    #                "Floette",
    #                "Florges",
    #                "Froslass",
    #                "Happiny",
    #                "Illumise",
    #                "Jynx",
    #                "Kangaskhan",
    #                "Lilligant",
    #                "Mandibuzz",
    #                "Miltank",
    #                "Nidoqueen",
    #                "Nidoran-f",
    #                "Nidorina",
    #                "Petilil",
    #                "Salazzle",
    #                "Smoochum",
    #                "Steenee",
    #                "Tsareena",
    #                "Vespiquen",
    #                "Vullaby",
    #                "Wormadam",
    #                "Meowstic-f",
    #            ):
    #                gender = "-m"
    #            else:
    #                gender = "-f" if random.randint(1, 10) == 1 else "-m"
    #    query2 = """
    #            INSERT INTO pokes (pokname, hpiv, atkiv, defiv, spatkiv, spdefiv, speediv, hpev, atkev, defev, spatkev, spdefev, speedev, pokelevel, moves, hitem, exp, nature, expcap, poknick, shiny, price, market_enlist, fav, ability_index, gender, caught_by, radiant)
#
    #            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28) RETURNING id
    #            """
    #    args = (
    #        pokemon.capitalize(),
    #        hpiv,
    #        atkiv,
    #        defiv,
    #        spaiv,
    #        spdiv,
    #        speiv,
    #        0,
    #        0,
    #        0,
    #        0,
    #        0,
    #        0,
    #        level,
    #        ["tackle", "tackle", "tackle", "tackle"],
    #        "None",
    #        1,
    #        nature,
    #        level ** 2,
    #        "None",
    #        shiny,
    #        0,
    #        False,
    #        False,
    #        random.randrange(len(ab_ids)),
    #        gender,
    #        user_id,
    #        radiant,
    #    )
    #    async with self.db.acquire() as pconn:
    #        pokeid = await pconn.fetchval(query2, *args)
    #        await pconn.execute(
    #            "UPDATE users SET pokes = array_append(pokes, $2) WHERE u_id = $1",
    #            user_id,
    #            pokeid,
    #        )
    #    return pokeid, gender, sum((hpiv, atkiv, defiv, spaiv, spdiv, speiv))
#
#

       

    @tasks.loop(minutes=9)
    async def stats(self):
        await asyncio.sleep(60)
        async with self.db.acquire() as pconn:
            amount = await pconn.fetchval("select mewcoins from users where u_id = 920827966928326686")
        guild = self.bot.get_guild(519466243342991360)
        if not guild:
            return
        channel = guild.get_channel(923019380122607677)
        if not channel:
            return
        await channel.edit(name=f"Raffle pot {amount}")

    def cog_unload(self):
        self.stats.cancel()
