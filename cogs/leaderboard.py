import discord
from discord.ext import commands
from cogs.utils import db


class LeaderboardDB(db.Table, table_name='leaderboard'):
    id = db.PrimaryKeyColumn()

    user_id = db.Column(db.Integer(big=True))
    guild_id = db.Column(db.Integer(big=True))
    game = db.Column(db.String())
    attempts = db.Column(db.Integer())
    wrong = db.Column(db.Integer())
    correct = db.Column(db.Integer())
    games = db.Column(db.Integer())
    record = db.Column(db.Numeric())


class Leaderboard:
    def __init__(self, bot):
        self.bot = bot
        self.games = ['guess', 'reacttest', 'hangman', 'trivia', 'clashtrivia', 'riddle']

    @commands.group(invoke_without_command=True)
    async def leaderboard(self, ctx, game: str = None):
        """Sends leaderboard for a specific game. Server and game specific.
            PARAMETERS: [game] - name of the game you want leaderboard for
            EXAMPLE: `leaderboard guess`
            RESULT: Leaderboard for the `guess` command"""
        if not game:
            games = '\n'.join(self.games)
            return await ctx.send(f"Please choose a game type. These include: {games}\n...more coming soon!")

        return await self.get_leaderboard_guild(game, ctx)

    @leaderboard.command()
    async def all(self, ctx, game: str = None):
        """Gives leaderboard for all servers the bot is in/whom play the game
            PARAMETERS: [game] - name of the game you want leaderboard for
            EXAMPLE: `leaderboard all guess`
            RESULT: Leaderboard for all servers who have played the `guess` game"""
        if not game:
            # need to choose a game
            games = '\n'.join(self.games)
            return await ctx.send(f"Please choose a game type. These include: {games}\n...more coming soon!")

        return await self.get_leaderboard_all(game, ctx)

    @commands.command()
    async def gamestats(self, ctx, user: discord.Member = None):
        """Gives stats for games a user has played.
            PARAMETERS: [user] - @mention, nick#discrim, id
            EXAMPLE: `gamestats @mathsman`
            RESULT: Returns @mathsman's stats for games he has played"""
        if not user:
            user = ctx.author

        await self.get_leaderboard_user(user, ctx)

    async def get_leaderboard_all(self, gamecom, ctx):
        # emojis we're gonna use for leaderboard. This one is for
        # all guilds
        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{CLAPPING HANDS SIGN}',
            '\N{CLAPPING HANDS SIGN}'
        )
        embed = discord.Embed(colour=discord.Colour.dark_gold())

        query = """
                SELECT user_id, record FROM leaderboard 
                WHERE game = $1 ORDER BY record ASC LIMIT 5;
                """
        records = await ctx.db.fetch(query, gamecom)

        value = '\n'.join(f'{lookup[i]} <@{users[i]}>: {record[i]}'
                          for (index, (users, record)) in enumerate(records)) or 'No Records'
        embed.add_field(name="Top Records", value=value, inline=True)

        query = """
                SELECT user_id, games FROM leaderboard 
                WHERE game = $1 ORDER BY games DESC LIMIT 5;
                """
        games = await self.bot.pool.fetch(query, gamecom)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {game}'
                          for (index, (users, game)) in enumerate(games)) or 'No Records'
        embed.add_field(name="Top games played", value=value, inline=True)

        query = """
                SELECT user_id, attempts FROM leaderboard 
                WHERE game = $1 ORDER BY attempts DESC LIMIT 5;
                """
        attempts = await ctx.db.fetch(query, gamecom)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {attempt}'
                          for (index, (users, attempt)) in enumerate(attempts)) or 'No Records'

        # fix embed formatting so attempts + correct + incorrect on seperate line from records and games played
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name="Total attempts", value=value, inline=True)

        query = """
                SELECT user_id, correct FROM leaderboard 
                WHERE game = $1 ORDER BY correct DESC LIMIT 5;
                """
        correct = await ctx.db.fetch(query, gamecom)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {corrects}'
                          for (index, (users, corrects)) in enumerate(correct)) or 'No Records'
        embed.add_field(name="Total correct answers", value=value, inline=True)

        query = """
                SELECT user_id, wrong FROM leaderboard 
                WHERE game = $1 ORDER BY wrong DESC LIMIT 5;
                """
        wrong = await ctx.db.fetch(query, gamecom)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {wrongs}'
                          for (index, (users, wrongs)) in enumerate(wrong)) or 'No Records'

        embed.add_field(name="Total incorrect answers", value=value, inline=True)
        embed.set_author(name=f"Leaderboard - {gamecom}")
        await ctx.send(embed=embed)

    async def get_leaderboard_guild(self, gamecom, ctx):
        # same but for a guild rather than global (all guilds)
        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{CLAPPING HANDS SIGN}',
            '\N{CLAPPING HANDS SIGN}'
        )
        embed = discord.Embed(colour=discord.Colour.dark_gold())

        query = """
                SELECT user_id, record FROM leaderboard 
                WHERE game = $1 AND guild_id = $2 ORDER BY record ASC LIMIT 5;
                """
        records = await self.bot.pool.fetch(query, gamecom, ctx.guild.id)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {record}'
                          for (index, (users, record)) in enumerate(records)) or 'No Records'
        embed.add_field(name="Top Records", value=value, inline=True)

        query = """
                SELECT user_id, games FROM leaderboard 
                WHERE game = $1 AND guild_id = $2 ORDER BY games DESC LIMIT 5;
                """
        games = await self.bot.pool.fetch(query, gamecom, ctx.guild.id)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {game}'
                          for (index, (users, game)) in enumerate(games)) or 'No Records'
        embed.add_field(name="Top games played", value=value, inline=True)

        query = """
                SELECT user_id, attempts FROM leaderboard 
                WHERE game = $1 AND guild_id = $2 ORDER BY attempts DESC LIMIT 5;
                """
        attempts = await self.bot.pool.fetch(query, gamecom, ctx.guild.id)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {attempt}'
                          for (index, (users, attempt)) in enumerate(attempts)) or 'No Records'
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name="Total attempts", value=value, inline=True)

        query = """
                SELECT user_id, correct FROM leaderboard 
                WHERE game = $1 AND guild_id = $2 ORDER BY correct DESC LIMIT 5;
                """
        correct = await self.bot.pool.fetch(query, gamecom, ctx.guild.id)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {corrects}'
                          for (index, (users, corrects)) in enumerate(correct)) or 'No Records'
        embed.add_field(name="Total correct answers", value=value, inline=True)

        query = """
                SELECT user_id, wrong FROM leaderboard 
                WHERE game = $1 AND guild_id = $2 ORDER BY wrong DESC LIMIT 5;
                """
        wrong = await self.bot.pool.fetch(query, gamecom, ctx.guild.id)

        value = '\n'.join(f'{lookup[index]} <@{users}>: {wrongs}'
                          for (index, (users, wrongs)) in enumerate(wrong)) or 'No Records'
        embed.add_field(name="Total incorrect answers", value=value, inline=True)
        embed.set_author(name=f"Leaderboard - {gamecom}")
        await ctx.send(embed=embed)

    async def get_leaderboard_user(self, user, ctx):
        # same but for a user
        lookup = (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
            '\N{CLAPPING HANDS SIGN}',
            '\N{CLAPPING HANDS SIGN}'
        )
        embed = discord.Embed(colour=discord.Colour.dark_gold())

        query = """
                SELECT game, record FROM leaderboard 
                WHERE user_id = $1 ORDER BY record ASC LIMIT 5;
                """

        records = await self.bot.pool.fetch(query, user.id)

        value = '\n'.join(f'{lookup[index]} {users}: {record}'
                          for (index, (users, record)) in enumerate(records)) or 'No Records'
        embed.add_field(name="Top Records", value=value, inline=True)

        query = """
                SELECT game, games FROM leaderboard 
                WHERE user_id = $1 ORDER BY games DESC LIMIT 5;
                """
        games = await self.bot.pool.fetch(query, user.id)

        value = '\n'.join(f'{lookup[index]} {users}: {game}'
                          for (index, (users, game)) in enumerate(games)) or 'No Records'
        embed.add_field(name="Top games played", value=value, inline=True)

        query = """
                SELECT game, attempts FROM leaderboard 
                WHERE user_id = $1 ORDER BY attempts DESC LIMIT 5;
                """
        attempts = await self.bot.pool.fetch(query, user.id)

        value = '\n'.join(f'{lookup[index]} {users}: {attempt}'
                          for (index, (users, attempt)) in enumerate(attempts)) or 'No Records'
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name="Total attempts", value=value, inline=True)

        query = """
                SELECT game, correct FROM leaderboard 
                WHERE user_id = $1 ORDER BY correct DESC LIMIT 5;
                """
        correct = await self.bot.pool.fetch(query, user.id)

        value = '\n'.join(f'{lookup[index]} {users}: {corrects}'
                          for (index, (users, corrects)) in enumerate(correct)) or 'No Records'
        embed.add_field(name="Total correct answers", value=value, inline=True)

        query = """
                SELECT game, wrong FROM leaderboard 
                WHERE user_id = $1 ORDER BY wrong DESC LIMIT 5;
                """
        wrong = await self.bot.pool.fetch(query, user.id)

        value = '\n'.join(f'{lookup[index]} {users}: {wrongs}'
                          for (index, (users, wrongs)) in enumerate(wrong)) or 'No Records'
        embed.add_field(name="Total incorrect answers", value=value, inline=True)
        embed.set_author(name=f"Leaderboard - {user.display_name}#{user.discriminator}")
        await ctx.send(embed=embed)

    async def into_leaderboard(self, game, record, attempts, wrong, correct, guild_id, user_id):
        # insert stuff into leaderboard table in db. Any command that is on the leaderboard will insert stuff into here
        # on completion of command
        # author id
        # string to return. will add record if applicable
        ret = ''

        query = """
                SELECT record, games, attempts, wrong, correct 
                FROM leaderboard WHERE user_id = $1 AND game = $2 
                AND guild_id = $3;
                """
        dump = await self.bot.pool.fetchrow(query, user_id, game, guild_id)

        if dump:
            # if the record is less than old one in db
            if isinstance(record, int):
                if dump['record'] > record:
                    query = """
                            UPDATE leaderboard SET record = $1 
                            WHERE user_id = $2 AND game = $3 AND guild_id = $4;
                            """
                    await self.bot.pool.execute(query, record, user_id, game, guild_id)

                    # add to return string
                    units = 'seconds' if game == 'reacttest' else 'attempts'
                    ret += f"Congratulations! You have broken your previous record of {dump['record']} {units} :tada:"

            # update a player's game in leaderboard adding corrects/attempts/games etc
            if isinstance(attempts, int):
                attempts = dump['attempts'] + attempts
            else:
                attempts = 0
            if isinstance(wrong, int):
                wrong = dump['wrong'] + wrong
            else:
                wrong = 0
            if isinstance(correct, int):
                correct = dump['correct'] + correct
            else:
                correct = 0

            query = """
                    UPDATE leaderboard SET games = $1,
                    attempts = attempts + 1, wrong = $3, correct = $4 
                    WHERE user_id = $5 AND game = $6 AND guild_id = $7;
                    """
            await self.bot.pool.execute(query, attempts, wrong,
                                        correct, user_id, game, guild_id)

            # return the return string (if applicable else returns empty string)
            return ret

        else:
            if not isinstance(attempts, int):
                attempts = 0
            if not isinstance(wrong, int):
                wrong = 0
            if not isinstance(correct, int):
                correct = 0
            if not isinstance(record, int):
                record = 0
            # if first time playing add userid with stuff to game to db
            query = """
                    INSERT INTO leaderboard VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
                    """
            await self.bot.pool.execute(query, user_id, guild_id, game,
                                        record, 1, attempts, wrong, correct)

            ret += f'This must be your first time playing! Congratulations, your record was recorded.' \
                   f' Check the leaderboard to see if you got anywhere'
            return ret


def setup(bot):
    bot.add_cog(Leaderboard(bot))
