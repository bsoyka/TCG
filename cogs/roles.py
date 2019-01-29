from discord.ext import commands
import discord


class Roles:
    def __init__(self, bot):
        self.bot = bot

    MESSAGE_ID = 539680327614857227
    PYTHON_HELPER = 501896375982751744
    JAVASCRIPT_HELPER = 501896261310480385
    ANNOUNCEMENTS_MEMBER = 515920621163642917
    CODER = 501892380925100043

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

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_role_action(payload, 'add')

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


def setup(bot):
    bot.add_cog(Roles(bot))
