
    @commands.command()
    async def tinyurl(self, ctx, *, link: str):
        '''Makes a link shorter using the tinyurl api'''
        await ctx.message.delete()
        url = 'http://tinyurl.com/api-create.php?url=' + link
        async with self.bot.session.get(url) as resp:
            new = await resp.text()
        emb = discord.Embed(color=random_color())
        emb.add_field(name="Original Link", value=link, inline=False)
        emb.add_field(name="Shortened Link", value=new, inline=False)
        emb.set_footer(text='Powered by tinyurl.com', icon_url='http://cr-api.com/static/img/branding/cr-api-logo.png')
        await ctx.send(embed=emb)

    @commands.command()
    async def hastebin(self, ctx, *, code):
        '''Hastebin-ify your code!'''
        code = utils.cleanup_code(code)
        async with self.bot.session.post("https://hastebin.com/documents", data=code) as resp:
            data = await resp.json()
            key = data['key']
        await ctx.send(f"Hastebin-ified! <https://hastebin.com/{key}.py>")

    @commands.command()
    async def datetime(self, ctx, tz=None):
        """Get the current date and time for a time zone or UTC."""
        now = datetime.datetime.now(tz=pytz.UTC)
        all_tz = 'https://github.com/cree-py/RemixBot/blob/master/data/timezones.json'
        if tz:
            try:
                now = now.astimezone(pytz.timezone(tz))
            except:
                em = discord.Embed(color=discord.Color.red())
                em.title = "Invalid timezone"
                em.description = f'Please take a look at the [list]({all_tz}) of timezones.'
                return await ctx.send(embed=em)
        await ctx.send(f'It is currently {now:%A, %B %d, %Y} at {now:%I:%M:%S %p}.')

    @commands.command(aliases=['urban'])
    async def ud(self, ctx, *, query):
        '''Search terms with urbandictionary.com'''
        em = discord.Embed(title=f'{query}', color=discord.Color.green())
        em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        em.set_footer(text='Powered by urbandictionary.com')
        defs = ud.define(query)
        try:
            res = defs[0]
        except IndexError:
            em.description = 'No results.'
            return await ctx.send(embed=em)
        em.description = f'**Definition:** {res.definition}\n**Usage:** {res.example}\n**Votes:** {res.upvotes}:thumbsup:{res.downvotes}:thumbsdown:'
        await ctx.send(embed=em)

    @commands.command(aliases=['wikipedia'])
    async def wiki(self, ctx, *, query):
        '''Search up something on wikipedia'''
        em = discord.Embed(title=str(query))
        em.set_footer(text='Powered by wikipedia.org')
        try:
            result = wikipedia.summary(query)
            if len(result) > 2000:
                em.color = discord.Color.red()
                em.description = f"Result is too long. View the website [here](https://wikipedia.org/wiki/{query.replace(' ', '_')}), or just google the subject."
                return await ctx.send(embed=em)
            em.color = discord.Color.green()
            em.description = result
            await ctx.send(embed=em)
        except wikipedia.exceptions.DisambiguationError as e:
            em.color = discord.Color.red()
            options = '\n'.join(e.options)
            em.description = f"**Options:**\n\n{options}"
            await ctx.send(embed=em)
        except wikipedia.exceptions.PageError:
            em.color = discord.Color.red()
            em.description = 'Error: Page not found.'
            await ctx.send(embed=em)
