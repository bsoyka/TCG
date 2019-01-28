from discord.ext import commands

import re


class COCError(commands.CheckFailure):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def is_owner_pred(ctx):
    if ctx.author.id in ctx.bot.owners:
        return True

    return False


def is_owner():
    def pred(ctx):
        return is_owner_pred(ctx)

    return commands.check(pred)


def manage_roles():
    def pred(ctx):
        if is_owner_pred(ctx):
            return True

        if ctx.guild is None:
            return False

        return ctx.channel.permissions_for(ctx.author).manage_roles

    return commands.check(pred)


def manage_server():
    def pred(ctx):
        if is_owner_pred(ctx):
            return True

        if not ctx.guild:
            return False

        return ctx.channel.permissions_for(ctx.author).manage_guild

    return commands.check(pred)


def manage_channels():
    def pred(ctx):
        if is_owner_pred(ctx):
            return True

        if not ctx.guild:
            return False

        return ctx.channel.permissions_for(ctx.author).manage_channels

    return commands.check(pred)


def restricted_channel(*channel_ids):
    def pred(ctx):
        if is_owner_pred(ctx):
            return True

        if ctx.channel.id in channel_ids:
            return True

        return False

    return commands.check(pred)
