import asyncio
import numpy as np

import discord
from discord.ext import commands

from .emoji import Emoji
from .game import Game
from .score import Score


class Snake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, size_x=10, size_y=10):
        """Starts a game of Snake!"""
        # MAX SIZE IN NORMAL MESSAGE: 198 emojis (18 x 11)
        # MIN SIZE OF 5, BECAUSE OTHERWISE IT IS SMALL
        if size_x > 18:
            size_x = 18
        elif size_x < 5:
            size_x = 5
        if size_y > 11:
            size_y = 11
        elif size_y < 5:
            size_y = 5

        print('Starting game')
        game = Game(size_x, size_y, ctx, self.bot)
        await game.play()
        print('Game ended.')

    @commands.command()
    async def personnalbest(self, ctx, size_x: int = None, size_y: int = None):
        """Displays your personnal best in a given size, or all of them."""
        str_best = []
        dict_best = {}
        if size_x is None and size_y is None:
            for size in Score.high_scores.keys():
                try:
                    score = Score.high_scores[size][ctx.author.id]
                    str_best.append(f'**{size[0]}x{size[1]}**: {score}')
                    dict_best[f'{size[0]}x{size[1]}'] = score
                except KeyError as e:
                    # KeyError on user ID.
                    pass
        elif size_x is None or size_y is None:
            await ctx.send('Use either both `size_x` and `size_y`, or none.')
            return
        else:
            try:
                score = Score.high_scores[(size_x, size_y)][ctx.author.id]
                str_best.append(f'**{size_x}x{size_y}**: {score}')
                dict_best[f'{size_x}x{size_y}'] = score
            except KeyError as e:
                pass

        if len(str_best) == 0:
            str_best = ['No high scores registered yet.']

        e = discord.Embed(
            title='A Game of Snake',
            description='Personnal Best',
            type='rich',
            url='https://github.com/Snaptraks/SnakeBot',
            color=0x77B255,
        ).set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.avatar_url_as(static_format='png'),
        ).set_footer(
            text='Coded for Discord Hack Week by Snaptraks#2606',
        )
        if len(dict_best) != 0:
            for s in dict_best:
                e.add_field(
                    name=s,
                    value=dict_best[s],
                )
        else:
            e.add_field(
                name='No high scores registered yet.',
                value='Start a game with `!play`.',
            )

        await ctx.send(embed=e)


    @commands.command(aliases=['highscores'])
    async def highscore(self, ctx, size_x: int = None, size_y: int = None):
        """Displays the top players and scores in a given size, or all of them.
        """
        dict_top = {}
        if size_x is None and size_y is None:
            for size in Score.high_scores.keys():
                top_users = Score.get_top_users(size)
                score = Score.get_top(size)
                dict_top[f'{size[0]}x{size[1]} ({score})'] = \
                    '\n'.join(self.bot.get_user(uid).display_name \
                    for uid in top_users)
        elif size_x is None or size_y is None:
            await ctx.send('Use either both `size_x` and `size_y`, or none.')
            return
        else:
            top_users = Score.get_top_users((size_x, size_y))
            score = Score.get_top((size_x, size_y))
            dict_top[f'{size_x}x{size_y} ({score})'] = \
                '\n'.join(self.bot.get_user(uid).display_name \
                for uid in top_users)

        e = discord.Embed(
            title='A Game of Snake',
            description='High Scores',
            type='rich',
            url='https://github.com/Snaptraks/SnakeBot',
            color=0x77B255,
        ).set_footer(
            text='Coded for Discord Hack Week by Snaptraks#2606',
        )
        if len(dict_top) != 0:
            for s in dict_top:
                e.add_field(
                    name=s,
                    value=dict_top[s],
                )
        else:
            e.add_field(
                name='No high scores registered yet.',
                value='Start a game with `!play`.',
            )

        await ctx.send(embed=e)
