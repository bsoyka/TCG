from discord.ext import commands
import discord
import asyncio
from cogs.games import Leaderboard
from cogs.utils import db


class AllJokes(db.Table, table_name='jokes'):
    id = db.PrimaryKeyColumn()

    category = db.Column(db.String, index=True)
    title = db.Column(db.String)
    body = db.Column(db.String)


class DadJokes(db.Table):
    id = db.PrimaryKeyColumn()

    joke = db.Column(db.String())


class SavedJokes(db.Table):
    id = db.PrimaryKeyColumn()

    category = db.Column(db.String)
    title = db.Column(db.String)
    body = db.Column(db.String)
    joke_id = db.Column(db.Integer)
    score = db.Column(db.Integer)


class Riddles(db.Table):
    id = db.PrimaryKeyColumn()

    riddle = db.Column(db.String)
    answer = db.Column(db.String)
    used = db.Column(db.Integer, default=0)


class SavedRiddles(db.Table):
    id = db.PrimaryKeyColumn()

    userid = db.Column(db.Integer(big=True))
    riddle_number = db.Column(db.Integer)
    question = db.Column(db.String)
    answer = db.Column(db.String)


class Jokes:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dadjoke(self, ctx, jokeid: int = None):
        """Gives you a dad joke
            PARAMETERS: optional: [joke id] - for getting a previous joke you liked via id.
            EXAMPLE: `dadjoke` or `dadjoke 432`
            RESULT: Shows a random dad-joke or the joke with id `432`"""
        # if no joke id
        if jokeid:
            query = "SELECT id, joke FROM dadjokes WHERE `id` = $1"
            dump = await ctx.db.fetchrow(query, jokeid)

        else:
            query = "SELECT id, joke FROM dadjokes ORDER BY RANDOM() LIMIT 1"
            dump = await ctx.db.fetchrow(query)

        embed = discord.Embed(colour=0x00ffff)
        embed.set_author(name=dump['joke'], icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"Like that dad joke? The ID was: {dump['id']}. Powered by https://icanhazdadjoke.com/")
        await ctx.send(embed=embed)

    @commands.command()
    async def joke(self, ctx, *, category: str=None):
        """Gives you a random joke. Can include category - find these with `joke categories`
            PARAMETERS: optional: [category] - a joke with that category
            EXAMPLE: `joke` or `joke Knock Knock`
            RESULT: Random joke or random Knock Knock joke"""

        if not category:
            query = "SELECT * FROM jokes ORDER BY RANDOM() LIMIT 1"
            dump = await ctx.db.fetchrow(query)

        else:
            # if they want to know available categories
            if category == 'category':
                query = "SELECT DISTINCT category FROM jokes"
                dump = await ctx.db.fetch(query)

                desc = '\n'.join(n[0] for n in dump)

                embed = discord.Embed(colour=0x00ff00)

                embed.set_author(name="Categories for the joke commands", icon_url=ctx.author.avatar_url)
                embed.add_field(name='\u200b', value=desc)
                embed.set_footer(text=f"Type `{ctx.prefix}joke [category]` to get a joke of that category!",
                                 icon_url=self.bot.user.avatar_url)

                return await ctx.send(embed=embed)

            query = "SELECT * FROM jokes WHERE category = $1 ORDER BY RANDOM() LIMIT 1"
            dump = await ctx.db.fetchrow(query, category)

        if not dump:
            embed = discord.Embed(colour=0xff0000)
            embed.set_author(name="Category not found", icon_url=ctx.author.avatar_url)
            embed.description = f'Find all categories with `{ctx.prefix}joke categories` command'
            return await ctx.send(embed=embed)

        # otherwise post joke
        embed = discord.Embed(colour=0x00ffff)
        embed.set_author(name=f"{dump['title']}", icon_url=ctx.author.avatar_url)
        embed.description = dump['body']
        embed.set_footer(text=f"Category: {dump['category']}, ID: {dump['id']}.",
                         icon_url=self.bot.user.avatar_url)
        msg = await ctx.send(embed=embed)

        # idk why this is here since jokes are that shitty all over anyways
        # def check(reaction, user):
        #     # check if reacter is author and emoji is star
        #     return user.id != self.bot.user.id and str(reaction.emoji) == '\N{WHITE MEDIUM STAR}'
        # await msg.add_reaction('\N{WHITE MEDIUM STAR}')
        #
        # score = 0
        # while True:
        #     try:
        #         # 10min timeout to get a like for the joke
        #         reaction = await self.bot.wait_for('reaction_add', check=check, timeout=600)
        #         score += 1
        #
        #     except asyncio.TimeoutError:
        #         # when timeout if it has been liked
        #         if score > 0:
        #             # i dont have a command to get this yet but w/e
        #             async with aiosqlite.connect(db_path) as db:
        #                 await db.execute("INSERT INTO savedjokes VALUES (Null, :cat, :tit, :body, :jokeid, :score)",
        #                                  {'cat': dump[0][1], 'tit': dump[0][2], 'body': dump[0][3], 'jokeid': dump[0][0],
        #                                   'score': score})
        #                 await db.commit()
        #             embed = discord.Embed(colour=0x00ff00)
        #             embed.set_author(name=f"Joke ID {dump[0][0]} was saved with {score} votes!",
        #                              icon_url=self.bot.avatar_url)
        #             await ctx.send(embed=embed)
        #             break

    @commands.command()
    async def insult(self, ctx, user: discord.Member = None):
        """Insults someone
            PARAMETERS: [user] - @mention, nick#discrim, id
            EXAMPLE: `insult @mathsman`
            RESULT: @mathsman would recieve a gutwrenching insult"""
        # if they didnt ping someone I will insult them
        if not user:
            user = ctx.author

        query = """
                SELECT body FROM jokes WHERE category = 'Insults'
                AND title = 'Stupid Stuff' ORDER BY RANDOM() LIMIT 1
                """
        dump = await ctx.db.fetchrow(query)

        await ctx.send(f"{user.mention}, {dump['body']}")
        # await msg.add_reaction('\N{WHITE MEDIUM STAR}')
        #
        # def check(reaction, user):
        #     return user.id != self.bot.user.id and str(reaction.emoji) == '\N{WHITE MEDIUM STAR}'
        #
        # score = 0
        # while True:
        #     try:
        #         reaction = await self.bot.wait_for('reaction_add', check=check, timeout=600)
        #         score += 1
        #         print(score)
        #     except asyncio.TimeoutError:
        #         if score > 0:
        #             async with aiosqlite.connect(db_path) as db:
        #                 await db.execute("INSERT INTO savedjokes VALUES (Null, :cat, :tit, :body, :jokeid, :score)",
        #                                  {'cat': dump[0][1], 'tit': dump[0][2], 'body': dump[0][3], 'jokeid': dump[0][0],
        #                                   'score': score})
        #                 await db.commit()
        #             embed = discord.Embed(colour=0x00ff00)
        #             embed.set_author(name=f"Insult ID {dump[0][0]} was saved with {score} votes!",
        #                              icon_url=ctx.author.avatar_url)
        #             await ctx.send(embed=embed)
        #             break

    @commands.command()
    async def riddle(self, ctx, number: int=None):
        """Gives you a riddle. You can get a riddle with the id. You have 60sec or can give up with `idk` (no prefix).
            PARAMETERS: optional: [number] - id of a riddle
            EXAMPLE: `riddle` or `riddle 1325`
            RESULT: Gives you a random or number 1325 riddle. You have 60sec to type correct answer (no prefix/command)"""
        counter = 0
        # if no riddle number/id get random riddle
        if not number:
            query = "SELECT * FROM riddles ORDER BY RANDOM() LIMIT 1;"
        else:
            query = f"SELECT * FROM riddles WHERE id={number}"

        riddle = await ctx.db.fetchrow(query)

        # check if reply is author
        def check(user):
            if (user is None) or (user.author.id != ctx.author.id):
                return False
            else:
                return True

        # send the riddle
        lb = Leaderboard(ctx)
        embed = discord.Embed(colour=0x00ffff)
        embed.set_author(name=riddle['riddle'], icon_url=ctx.author.avatar_url)
        embed.set_footer(text="You have 60 seconds to type the correct answer. If you give up, type `idk`")
        send = await ctx.send(embed=embed)
        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                # wait for a reply + add to counter (attempts) if reply
                counter += 1

                # if correct
                if msg.content.lower() == riddle['answer']:
                    embed = discord.Embed(colour=0x00ff00)
                    embed.set_author(name="Correct!", icon_url=ctx.author.avatar_url)
                    embed.title = riddle['riddle']
                    embed.description = riddle['answer']
                    embed.set_footer(text=f"Like this riddle? The number was {riddle['id']}. "
                                          f"Type `{ctx.prefix}riddle {riddle['id']}` to get it again")
                    # put into leaderboard
                    intolb = await lb.into_leaderboard(game='riddle', record=counter, attempts=counter,
                                                       wrong=counter - 1, correct=1, guildid=ctx.guild.id,
                                                       id=ctx.author.id)
                    # if there is something them set empty title and response value
                    if intolb:
                        embed.add_field(name='\u200b', value=intolb)
                    await ctx.send(embed=embed)
                    # exit command
                    return
                # if they throw in the towel exit while true
                if msg.content == 'idk':
                    break
                else:
                    # wrong answer
                    await ctx.send("Eh, I don't think it was that. Try again!")
            # timeout
            except asyncio.TimeoutError:
                break
        # give them the answer and insert fails into leaderboard
        embed = discord.Embed(colour=0xff0000)
        embed.set_author(name="The answer was: ")
        embed.title = riddle['answer']
        embed.set_footer(text=f"Like this riddle? The number was {riddle['id']}. "
                              f"Type `{ctx.prefix}riddle {riddle['id']}` to get it again,",
                         icon_url=ctx.author.avatar_url)

        intolb = await lb.into_leaderboard(game='riddle', record=counter or 1, attempts=counter or 1,
                                           wrong=counter or 1, correct=0, guildid=ctx.guild.id,
                                           id=ctx.author.id)
        if intolb:
            embed.description = intolb
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Jokes(bot))
