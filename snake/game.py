import asyncio
import numpy as np

import discord

from .emoji import Emoji
from .score import Score

class Game():
    """Inspired by https://github.com/jodylecompte/Anaconda for mechanics."""
    def __init__(self, size_x, size_y, ctx, bot):
        self.size_x, self.size_y = size_x, size_y
        self.ctx, self.bot = ctx, bot

        # starting position
        self.x, self.y = self.size_x//2, self.size_y//2
        # a list of x-coords and y-coords
        self.body = [[self.x], [self.y]]
        self.score = 0
        self.is_over = False
        self.apple = ()
        self.apple_eaten = True

        self.screen = np.full((size_x, size_y), Emoji.BLACK.value)

        self.embed = discord.Embed(
            title='A Game of Snake',
            type='rich',
            url='https://github.com/Snaptraks/SnakeBot',
            color=0x77B255,
        ).set_footer(
            text='Coded for Discord Hack Week by Snaptraks#2606',
        ).set_author(
            name=self.ctx.author.display_name,
            icon_url=self.ctx.author.avatar_url_as(static_format='png'),
        ).add_field(
            name='Personnal Best',
            value=Score.get((self.size_x, self.size_y), self.ctx.author.id),
        ).add_field(
            name='High Score',
            value=Score.get_top((self.size_x, self.size_y)),
        ).add_field(
            name=f'Score: {self.score}',
            value=self.display(),
            inline=False,
        )

        self.controls = (
            Emoji.LEFT.value,
            Emoji.UP.value,
            Emoji.DOWN.value,
            Emoji.RIGHT.value,
            Emoji.X.value,
        )

    async def play(self):
        message_game = await self.ctx.send(embed=self.embed)  # starting screen
        self.message_game = message_game
        for arrow in self.controls:
            await message_game.add_reaction(arrow)

        def check(reaction, user):
            return reaction.emoji in self.controls and\
                user == self.ctx.author

        # initial speed
        dx, dy = 0, -1

        while not self.is_over:
            try:
                reaction, user = await self.bot.wait_for('reaction_add',
                    timeout=1.5,
                    check=check)
            except asyncio.TimeoutError as e:
                pass
            else:
                await message_game.remove_reaction(reaction, user)

                if reaction.emoji == Emoji.UP.value:
                    dx, dy = 0, -1
                elif reaction.emoji == Emoji.DOWN.value:
                    dx, dy = 0, 1
                elif reaction.emoji == Emoji.RIGHT.value:
                    dx, dy = 1, 0
                elif reaction.emoji == Emoji.LEFT.value:
                    dx, dy = -1, 0
                elif reaction.emoji == Emoji.X.value:
                    await self.game_over('Cancelled game.')
                    continue

            self.move(dx, dy)

            # Detect collision with apple
            if (self.x, self.y) == self.apple:
                self.eat()

            # Spawn new apple if no win detected
            if self.score == self.size_x * self.size_y:
                # completed the game
                await self.update_display()
                await self.game_over('You Won!')
                continue
            elif self.apple_eaten:
                self.spawn_apple()

            # Detect collision with itself
            body = np.asarray(self.body).T
            body = body[:-1].tolist()
            head_in_body = [part == [self.x, self.y] for part in body]
            if any(head_in_body):
                await self.game_over('Hit itself.')
                continue

            # Detect collision with border
            if (self.x < 0 or
                self.x >= self.size_x or
                self.y < 0 or
                self.y >= self.size_y):
                # game over
                await self.game_over('Hit a wall.')
                continue

            # Update message with new game layout
            await self.update_display()

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.body[0].append(self.x)
        self.body[1].append(self.y)

        # move snake one block
        if len(self.body[0]) > self.score + 1:
            self.body[0] = self.body[0][1:]
            self.body[1] = self.body[1][1:]

    def eat(self):
        self.score += 1
        self.apple_eaten = True

    async def game_over(self, reason):
        self.is_over = True
        self.embed.insert_field_at(
            index=2,
            name='Cause of Death',
            value=reason,
            inline=False,
        )
        await self.message_game.edit(embed=self.embed)
        await self.message_game.clear_reactions()
        Score.save((self.size_x, self.size_y), self.ctx.author.id, self.score)

    def spawn_apple(self):
        body = np.asarray(self.body).T
        while True:
            apple = (
                np.random.randint(self.size_x),
                np.random.randint(self.size_y),
            )
            apple_in_body = [part == list(apple) for part in body.tolist()]
            if not any(apple_in_body):
                self.apple = apple
                self.apple_eaten = False
                return

    def display(self):
        self._reset_screen()
        # set Apple location
        if self.apple:
            self.screen[self.apple] = Emoji.APPLE.value
        # set Snake body
        self.screen[tuple(self.body)] = Emoji.SNAKE.value
        # set Snake face
        self.screen[(self.x, self.y)] = Emoji.DRAGON.value
        # Transpose (.T) the screen array to match horizontal-x vertical-y in
        # (x, y) order, unlike (i, j) for matrices
        str_screen = '\n'.join(''.join(line) for line in self.screen.T)
        return str_screen

    async def update_display(self):
        self.embed.set_field_at(
            index=2,
            name=f'Score: {self.score}',
            value=self.display(),
            inline=False,
        )
        await self.message_game.edit(embed=self.embed)

    def _reset_screen(self):
        self.screen = np.full((self.size_x, self.size_y), Emoji.BLACK.value)
