from cogs.utils import db

from discord.ext import commands

import discord
import re

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


class Misc:
    def __init__(self, bot):
        self.bot = bot

    MESSAGE_ID = 539680327614857227
    PYTHON_HELPER = 501896375982751744
    JAVASCRIPT_HELPER = 501896261310480385
    ANNOUNCEMENTS_MEMBER = 515920621163642917
    CODER = 501892380925100043

    USER_COUNT_CHANNEL = 515036392762376212
    BOT_COUNT_CHANNEL = 515036393362292746
    MEMBER_COUNT_CHANNEL = 515036392233893888
    MEMBER_GOAL_CHANNEL = 539709682848235520
    NEW_MEMBER_CHANNEL = 501873813408186380
    INFO_CHANNEL = 530941832549367820
    MEMBER_ROLE = 501872002680750100
    BOTS_ROLE = 501873192869298176

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def update_channels(self, ctx):
        """Update the member count channels manually
        """
        await self._update_channels(ctx.author)
        await self._update_channels(ctx.me)
        await ctx.tick()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def update_member_goal(self, ctx, number: int):
        """Update the member goal count channel.

        You must pass in a number for the goal to be

        Eg. `update_member_goal 200` to update the goal to be 200 members
        """
        channel = ctx.guild.get_channel(self.MEMBER_GOAL_CHANNEL)
        await channel.edit(name=f'Member Goal: {number}',
                           reason=f'Command by {ctx.author.display_name}#{ctx.author.discriminator}')
        await ctx.tick()

    @commands.command()
    async def members(self, ctx):
        """Receive a current list of members"""
        member_count = [n for n in ctx.guild.members if not n.bot]
        bot_count = [n for n in ctx.guild.members if n.bot]
        total_count = ctx.guild.members

        e = discord.Embed(colour=discord.Colour.blue())
        e.title = 'Member Count'
        e.description = f':person_with_blond_hair: Member Count: {len(member_count)}\n' \
                        f':robot: Bot Count: {len(bot_count)}\n' \
                        f':baggage_claim: Total: {len(total_count)}'
        await ctx.send(embed=e)

    @commands.command()
    async def pyhelper(self, ctx):
        """Give yourself the Python Helper role"""
        role = ctx.guild.get_role(self.PYTHON_HELPER)
        await ctx.author.add_roles(role, reason='Auto Role') \
            if role not in ctx.author.roles else await ctx.author.remove_roles(role, reason='Auto Role')
        await ctx.tick()

    @commands.command()
    async def jshelper(self, ctx):
        """Give yourself the JavaScript Helper role"""
        role = ctx.guild.get_role(self.JAVASCRIPT_HELPER)
        await ctx.author.add_roles(role, reason='Auto Role') \
            if role not in ctx.author.roles else await ctx.author.remove_roles(role, reason='Auto Role')
        await ctx.tick()

    @commands.command()
    async def coder(self, ctx):
        """Give yourself the Coder role"""
        role = ctx.guild.get_role(self.CODER)
        await ctx.author.add_roles(role, reason='Auto Role') \
            if role not in ctx.author.roles else await ctx.author.remove_roles(role, reason='Auto Role')
        await ctx.tick()

    @commands.command()
    async def announcements(self, ctx):
        """Give yourself the Announcements Member role"""
        role = ctx.guild.get_role(self.ANNOUNCEMENTS_MEMBER)
        await ctx.author.add_roles(role, reason='Auto Role') \
            if role not in ctx.author.roles else await ctx.author.remove_roles(role, reason='Auto Role')
        await ctx.tick()


    @commands.group()
    async def poll(self, ctx):
        """Group: create a simple poll, add a response or see stats"""
        pass

    @poll.command()
    async def simple(self, ctx, title: str,
                     emojis: commands.Greedy[UnicodeEmojiConverter], *, options: str):
        """Create a simple poll

        Your title must be wrapped in " " quotes if it is more than one word.

        Emojis must be either unicode or a custom emoji.

        Options *must* be seperated by a comma

        Eg. `poll simple "This is my title" :x: :cry: :crystal_ball: Cross option, crying second, crystal ball emoji`

        If you have an unequal number of emojis and options,
        I will either fill in emojis to fill in the gap, or delete emojis if there is too many

        Eg 2. `poll simple` Title :x: :cry: :my_custom_emoji: cross, cry, my custom emoji option`
        """
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
        """Choose an option for a poll

        You must pass in the message ID of the poll you are trying to vote on

        You must pass in either the emoji or the content (exactly) of the poll you want to vote on

        Eg. `poll choose 3456339185234 :x:`
        Eg.2 `poll choose 139372959214 this is the second option`"""
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
        """Get stats for a poll

        You must pass in the message ID of the poll you want to fetch
        """
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
        await self.reaction_role_action(payload, 'add')
        await self.reaction_action(payload)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_role_action(payload, 'add')

    async def reaction_role_action(self, payload, add_delete):
        if payload.message_id != self.MESSAGE_ID:
            return

        reactions = {'\N{PUBLIC ADDRESS LOUDSPEAKER}': self.ANNOUNCEMENTS_MEMBER,
                     '\N{DESKTOP COMPUTER}': self.CODER,
                     'python:513877036058542090': self.PYTHON_HELPER,
                     'javascript:513877604437065728': self.JAVASCRIPT_HELPER}
        if str(payload.emoji) not in reactions.keys():
            return

        role_id = reactions[str(payload.emoji)]
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)

        try:
            await member.add_roles(role, reason='Reaction roles') \
                if add_delete == 'add' else await member.remove_roles(role, reason='Reaction roles')
        except:
            return

        e = discord.Embed(colour=discord.Colour.green())
        e.description = f"You were {'given' if add_delete == 'add' else 'removed from'}" \
                        f" the {role.name} role. {'Remove' if add_delete == 'add' else 'Add'} " \
                        f"the {payload.emoji} reaction to {'remove' if add_delete == 'add' else 'Add'} the role"
        try:
            await member.send(embed=e)
        except:
            pass

    async def on_member_join(self, member):
        await self._update_channels(member)
        await self.member_welcomer(member, True)
        await self.give_roles(member)

    async def on_member_remove(self, member):
        await self._update_channels(member)
        await self.member_welcomer(member, False)

    async def _update_channels(self, member):
        if member.bot:
            bot_count = [n for n in member.guild.members if n.bot]
            channel = member.guild.get_channel(self.BOT_COUNT_CHANNEL)
            await channel.edit(name=f'Bot Count: {len(bot_count)}', reason='Bot Joined')
        else:
            user_count = [n for n in member.guild.members if not n.bot]
            channel = member.guild.get_channel(self.USER_COUNT_CHANNEL)
            await channel.edit(name=f'User Count: {len(user_count)}', reason='Member Joined')

        member_count = channel.guild.members
        channel = member.guild.get_channel(self.MEMBER_COUNT_CHANNEL)
        await channel.edit(name=f'Member Count: {len(member_count)}', reason="User Joined")

    async def member_welcomer(self, member, join_leave: bool):
        e = discord.Embed(colour=discord.Colour.green() if join_leave else discord.Colour.red())
        e.set_author(name='New Member' if join_leave else 'Member Left')
        e.set_image(url=member.avatar_url)

        if join_leave:
            e.description = f'Welcome to **The Coding Group**, {member.mention} \nWe hope you enjoy your time here!'
        else:
            e.description = f'{member.mention} just left. :cry:'

        e.set_footer(text=f'Member Count: {len(member.guild.members)}')

        channel = member.guild.get_channel(self.NEW_MEMBER_CHANNEL)
        await channel.send(embed=e)

        if member.bot and join_leave:
            e = discord.Embed(colour=discord.Colour.green())
            e.description = 'Welcome! Please make sure you check out the rules ' \
                            f'and any reaction roles you would like in <#{self.INFO_CHANNEL}>. ' \
                            f'\n\nWe hope you enjoy your stay!'
            try:
                await member.send(embed=e)
            except:
                pass

    async def give_roles(self, member):
        if member.bot:
            role = member.guild.get_role(self.BOTS_ROLE)
            await member.add_roles(role, reason='Auto Role on Join')
        else:
            role = member.guild.get_role(self.MEMBER_ROLE)
            await member.add_roles(role, reason='Auto Role on Join')

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
    bot.add_cog(Misc(bot))
