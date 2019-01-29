import discord
from discord.ext import commands
import asyncio
from cogs.utils import checks, db, time


class MemberId(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            # try to convert using normal discord.Member converter
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            # otherwise try to just get id
            try:
                return int(argument, base=10)
            # if that fails its not an id
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or user id.")

        else:
            # if author it bot owner, guild owner or has roles higher than person they're affecting
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument("You cant do this your "
                                           "top role is less than the person you're trying to affect")

            return m.id

# if its ban command and they're already kicked then we cant ping them or user member : discord.Member as they're
# not in server anymore or it's cache


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            member = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            member = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if member is None:
            raise commands.BadArgument(f'{argument} is not a valid user id')

        return member


# override default reason for kick/ban etc
class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        reason = f'{ctx.author} - ({ctx.author.id}), Reason: {argument}'
        # make sure does not exceed 512 char limit
        if len(reason) > 512:
            raise commands.BadArgument("Reason is too long")
        return reason


class Mod:
    def __init__(self, bot):
        self.bot = bot

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason: ActionReason=None):
        """Kick a member with optional reason

        You must have `kick_members` permission to run this command
        """
        # set reason if none supplied
        if reason is None:
            reason = f'Removed by {ctx.author} ({ctx.author.id})'
        # kick
        await user.kick(reason=reason)
        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def masskick(self, ctx, users: commands.Greedy[discord.Member], *, reason: ActionReason=None):
        """Mass kicks members with optional reason

        Pass in as many members as you wish, eg.

        `masskick @member @member2 @member3 @member4 for a reason`


        You must have `kick_members` permission to run this command
        """
        # set reason if none supplied
        if reason is None:
            reason = f'Removed by {ctx.author} ({ctx.author.id})'
        # kick
        for member in users:
            await member.kick(reason=reason)
        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: MemberId, *, reason: ActionReason=None):
        """Ban a member with optional reason

        You must have `ban_members` permission to run this command
        """
        # set reason if none supplied
        if reason is None:
            reason = f'Banned by {ctx.author} ({ctx.author.id})'
        # ban
        await ctx.guild.ban(discord.Object(id=user), reason=reason)
        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: MemberId, durarion: time.FutureTime, *, reason: ActionReason = None):
        """Temporarily ban a member with optional reason

        The duration could be a time in UTC, a number of min/hour/days away, or any readable format.

        eg. `tempban @member until tommorow at 5pm for this reason`

        or `tempban USERID 5 days spamming mentions

        You must have `ban_members` permission to run this command
        """
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        reminder = self.bot.get_cog('Reminder')

        await ctx.guild.ban(discord.Object(id=member), reason=reason)
        timer = await reminder.create_timer(durarion.dt, 'tempban', ctx.guild.id, ctx.author.id, member,
                                            connection=ctx.db)
        await ctx.send(f'Banned ID {member} for {time.human_timedelta(durarion.dt)}.')

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def softban(self, ctx, user: MemberId, *, reason: ActionReason=None):
        """Softban a member. This will kick the member while removing their messages

        You must have `kick_members` permissions to use this command
        """
        # set reason if none supplied
        if reason is None:
            reason = f'Softban by {ctx.author} ({ctx.author.id})'
        # ban
        obj = discord.Object(id=user)
        await ctx.guild.ban(obj, reason=reason)
        await ctx.guild.unban(obj, reason=reason)

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx, users: commands.Greedy[MemberId], *, reason: ActionReason=None):
        """Mass ban multiple members with an optional reason

        eg. `massban @member1 @member2 USERID3 @member4 for mention spamming`

        You must have `ban_members` permission"""
        # set reason if none supplied
        if reason is None:
            reason = f'Banned by {ctx.author} ({ctx.author.id})'

        for user in users:
            await ctx.guild.ban(discord.Object(id=user), reason=reason)

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: BannedMember, *, reason: ActionReason=None):
        """Unban a member with optional reason

        You must have `ban_members` permission to run this command
        """
        if not reason:
            reason = f'Unbanned by {ctx.author} ({ctx.author.id})'

        await ctx.guild.unban(user=user.user, reason=reason)

        if user.reason:
            await ctx.send(f"Unbanned {user.user.name} ({user.user.id}) - banned for {user.reason}")
        else:
            await ctx.send(f"Unbanned {user.user.name} ({user.user.id})")

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: discord.Member, durarion: time.FutureTime, *, reason: ActionReason=None):
        """Temporarily mute a member with optional reason

        The duration could be a time in UTC, a number of min/hour/days away, or any readable format.

        eg. `tempmute @member until tommorow at 5pm for this reason`

        or `tempmute USERID 5 days spamming mentions

        You must have `manage_messages` permission to run this command
        """
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        reminder = self.bot.get_cog('Reminder')

        await member.add_roles(muted_role, reason=reason)
        timer = await reminder.create_timer(durarion.dt, 'tempmute', ctx.guild.id, ctx.author.id, member.id,
                                            connection=ctx.db)
        await ctx.send(f'Muted {member.mention} for {time.human_timedelta(durarion.dt)}.')

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason: ActionReason=None):
        """Mute a member with optional reason

        You must have `manage_messages` permission to run this command
        """
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await member.add_roles(muted_role, reason=reason)

        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: ActionReason=None):
        """Unmute a member with optional reason

        You must have `manage_messages` permission to run this command
        """
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await member.remove_roles(muted_role, reason=reason)

        await ctx.tick()

    async def on_tempban_timer_complete(self, timer):
        guild_id, mod_id, member_id = timer.args

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            # RIP
            return

        moderator = guild.get_member(mod_id)
        if moderator is None:
            try:
                moderator = await self.bot.get_user_info(mod_id)
            except:
                # request failed somehow
                moderator = f'Mod ID {mod_id}'
            else:
                moderator = f'{moderator} (ID: {mod_id})'
        else:
            moderator = f'{moderator} (ID: {mod_id})'

        reason = f'Automatic unban from timer made on {timer.created_at} by {moderator}.'
        await guild.unban(discord.Object(id=member_id), reason=reason)

    async def on_tempmute_timer_complete(self, timer):

        guild_id, mod_id, member_id = timer.args

        print(guild_id, mod_id, member_id)
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            # RIP
            return

        muted_role = discord.utils.get(guild.roles, name='Muted')

        moderator = guild.get_member(mod_id)
        if moderator is None:
            try:
                moderator = await self.bot.get_user_info(mod_id)
            except:
                # request failed somehow
                moderator = f'Mod ID {mod_id}'
            else:
                moderator = f'{moderator} (ID: {mod_id})'
        else:
            moderator = f'{moderator} (ID: {mod_id})'

        reason = f'Automatic unmute from timer made on {timer.created_at} by {moderator}.'
        await guild.get_member(member_id).remove_roles(muted_role, reason=reason)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, num_messages: int=100):
        """Purge between 1 and 100 messages from the channel

        You must have `manage_messages` permissions"""
        if num_messages > 100:
            num_messages = 100
        try:
            deleted = await ctx.channel.purge(limit=num_messages)
        except discord.Forbidden:
            raise commands.BadArgument("I don't have `manage_messages` permission to run this command!")

        msg = await ctx.send(f"Purged {len(deleted)} messages from this channel!")
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, num_messages: int, *users):
        try:
            to_clean = [(await commands.MemberConverter().convert(ctx, user)) for user in users]
        except commands.BadArgument:
            try:
                to_clean = [(await commands.RoleConverter().convert(ctx, user)) for user in users]
            except commands.BadArgument:
                print(users)
                if users[0] in ['bots', 'humans']:
                    to_clean = []
                    members = ctx.channel.members
                    if users[0] == 'bots':
                        for m in members:
                            if m.bot:
                                to_clean.append(m)
                    if users[0] == 'humans':
                        for m in members:
                            if not m.bot:
                                to_clean.append(m)
                else:
                    raise commands.BadArgument("That was not a correct mention(s), role(s) or `bots` or `humans`")

        if num_messages > 100:
            num_messages = 100

        def check(m):
            return m.author in to_clean
        try:
            deleted = await ctx.channel.purge(limit=num_messages, check=check)
        except discord.Forbidden:
            raise discord.Forbidden("I don't have the required `manage_messages` permission to run this command!")

        send = await ctx.send(f"Deleted {len(deleted)} messages from `{[n.name for n in to_clean]}`.")
        await asyncio.sleep(5)
        await send.delete()


def setup(bot):
    bot.add_cog(Mod(bot))
