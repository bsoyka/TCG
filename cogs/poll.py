from discord.ext import commands
import discord
import re
from cogs.utils import db, checks
import emoji as emoj


class Poll(db.Table):
    id = db.PrimaryKeyColumn

    guild = db.Column(db.Integer(big=True))
    author = db.Column(db.Integer(big=True))
    message = db.Column(db.Integer(big=True))

    title = db.Column(db.String())
    active = db.Column(db.Boolean())


class PollsReactions(db.Table, table_name='polls_reactions'):
    id = db.PrimaryKeyColumn

    message = db.Column(db.Integer(big=True))
    emoji = db.Column(db.String())
    emoji_id = db.Column(db.Integer(big=True))
    function = db.Column(db.String)
    votes = db.Column(db.Integer())


class PollsUsers(db.Table, table_name='polls_users'):
    id = db.PrimaryKeyColumn

    message = db.Column(db.Integer(big=True))
    user_id = db.Column(db.Integer(big=True))
    emoji = db.Column(db.String())


class UnicodeEmojiConverter(commands.Converter):
    async def convert(self, ctx, argument):
        unicode_emoji = emoj.emojize(argument)
        uc = unicode_emoji.encode('unicode-escape').decode('ASCII')
        match = re.match(r'[\\U]', uc)
        if match:
            emoji = unicode_emoji
            return emoji

        try:
            custom_emoji = await commands.EmojiConverter().convert(ctx, argument)
            return custom_emoji

        except commands.BadArgument:
            pass

        raise commands.BadArgument('Not ok')


class UnicodeEmoji:
    def __init__(self, name):
        self.name = name

class Polls:
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def poll(self, ctx):
        pass

    @poll.command()
    async def simple(self, ctx, title: str,
                     emojis: commands.Greedy[UnicodeEmojiConverter], *, options: str):
        filler_emojis = [
            '1\u20e3',
            '2\u20e3',
            '3\u20e3',
            '4\u20e3',
            '5\u20e3',
            '6\u20e3',
            '7\u20e3',
            '8\u20e3',
            '9\u20e3',
        ]
        options_list = options.split(',')

        if len(emojis) < len(options_list):
            emojis.extend(filler_emojis[:len(emojis) - len(options_list)])

        if len(emojis) > len(options_list):
            emojis = emojis[:len(options_list) - len(emojis)]

        content = '\n'.join(f'{emojis[index]} {options_list[index]}: `0 votes`'
                            for index in range(len(options_list)))

        e = discord.Embed(colour=discord.Colour.blue())
        e.title = title
        e.description = content
        msg = await ctx.send(embed=e)

        for em in emojis:
            await msg.add_reaction(em)

        emoji_names = []
        for n in emojis:
            if isinstance(n, discord.Emoji):
                emoji_names.append((n.name, n.id))
                continue

            emoji = emoj.demojize(n).replace(':', '')
            emoji_names.append((emoji, 0))

        query = "INSERT INTO poll (guild, author, message, title, active) VALUES ($1, $2, $3, $4, $5)"
        await ctx.db.execute(query, ctx.guild.id, ctx.author.id, msg.id, title, True)

        query = "INSERT INTO polls_reactions (message, emoji, emoji_id,  function, votes) VALUES ($1, $2, $3, $4, $5)"

        for i in range(len(emojis)):
            await ctx.db.execute(query, msg.id, emoji_names[i][0], emoji_names[i][1], options_list[i], 0)

    @poll.command()
    async def choose(self, ctx, message: int, *, to_choose):
        data = {'message_id': message,
                'channel_id': ctx.channel.id,
                'guild_id': ctx.guild.id,
                'user_id': ctx.author.id}

        try:
            name = await UnicodeEmojiConverter().convert(ctx, to_choose)
            emoji = UnicodeEmoji(name=name)
            payload = discord.RawReactionActionEvent(data=data, emoji=emoji)
            return await self.reaction_action(payload)

        except commands.BadArgument:
            pass

        query = "SELECT emoji FROM polls_reactions WHERE function = $1 AND message = $2"
        dump = await ctx.db.fetchrow(query, to_choose, message)

        if not dump:
            raise commands.BadArgument(f'Option {to_choose} not found.')

        emoji = UnicodeEmoji(name=emoj.emojize(dump[0]))
        payload = discord.RawReactionActionEvent(data=data, emoji=emoji)
        await self.reaction_action(payload)

        await ctx.tick()

    @poll.command()
    async def stats(self, ctx, message: int):
        query = "SELECT * FROM poll INNER JOIN polls_reactions " \
                "ON poll.message = polls_reactions.message WHERE poll.message = $1"
        dump = await ctx.db.fetch(query, message)

        query = "SELECT * FROM polls_users WHERE message = $1"
        userinfo = await ctx.db.fetch(query, message)

        overall = '\n'
        for n in dump:

            if n['emoji_id'] != 0:
                emoji = f"<:{n['emoji']}:{n['emoji_id']}>"
            else:
                emoji = emoj.emojize(f":{n['emoji']}:")
                emoji.replace(':', '')

            string = f"\n\n{emoji} `{n['function']}`\n"
            members = '\n'.join(f"  <@{i['user_id']}>" for i in userinfo if i['emoji'] == n['emoji']) or 'No Members'
            overall += (string + members)

        e = discord.Embed(colour=discord.Colour.blue())
        e.title = f"Poll Stats - {dump[0]['title']}"
        e.description = overall
        e.set_footer(text=f"Total Replies to Poll: {len(userinfo)}")
        await ctx.send(embed=e)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_action(payload)

    async def reaction_action(self, payload):
        author = self.bot.get_user(payload.user_id)
        if author.bot:
            return

        if isinstance(payload.emoji, discord.Emoji):
            emoji_name = payload.emoji.name.replace(':', '')
        else:
            emoji_name = emoj.demojize(payload.emoji.name).replace(':', '')

        query = "SELECT emoji FROM polls_users WHERE message = $1 AND user_id = $2"
        user_reactions = await self.bot.pool.fetchrow(query, payload.message_id, payload.user_id)

        message = await self.bot.get_channel(payload.channel_id).get_message(payload.message_id)

        if user_reactions:
            if user_reactions[0] == emoji_name:
                try:
                    await message.remove_reaction(payload.emoji,
                                                  self.bot.get_guild(payload.guild_id).get_member(payload.user_id))
                except (discord.InvalidArgument, discord.HTTPException):
                    pass
                return

            query1 = "UPDATE polls_reactions SET votes = votes - 1 WHERE emoji = $1 AND message = $2"
            query2 = "UPDATE polls_users SET emoji = $1 WHERE emoji = $2 AND message = $3"

            await self.bot.pool.execute(query1, user_reactions[0], payload.message_id)
            await self.bot.pool.execute(query2, emoji_name, user_reactions[0], payload.message_id)

        else:

            query = "INSERT INTO polls_users (message, user_id, emoji) VALUES ($1, $2, $3)"
            await self.bot.pool.execute(query, payload.message_id, payload.user_id, emoji_name)

        query = "SELECT emoji, emoji_id, function, title, votes FROM polls_reactions " \
                "INNER  JOIN poll ON polls_reactions.message = poll.message WHERE poll.message = $1"
        dump = await self.bot.pool.fetch(query, payload.message_id)

        for result in dump:
            if emoji_name == result['emoji']:
                break
        else:
            return

        info = []

        for n in dump:
            if n['emoji'] == emoji_name:
                votes = n['votes'] + 1
            else:
                votes = n['votes']

            if n['emoji_id'] != 0:
                emoji = f"<:{n['emoji']}:{n['emoji_id']}>"
            else:
                emoji = emoj.emojize(f":{n['emoji']}:")
                emoji.replace(':', '')

            options = n['function']
            info.append((emoji, options, votes))

        content = '\n'.join(f'{emoji} {options}: `{votes} votes`'
                            for (index, (emoji, options, votes)) in enumerate(info))

        e = discord.Embed(colour=discord.Colour.blue())
        e.title = dump[0]['title']
        e.description = content
        await message.edit(embed=e)

        query = "UPDATE polls_reactions SET votes = votes + 1 WHERE emoji = $1 AND message = $2"
        await self.bot.pool.execute(query, emoji_name, payload.message_id)

        try:
            await message.remove_reaction(payload.emoji,
                                          self.bot.get_guild(payload.guild_id).get_member(payload.user_id))
        except (discord.InvalidArgument, discord.HTTPException):
            pass


def setup(bot):
    bot.add_cog(Polls(bot))


