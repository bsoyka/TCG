import discord
from cogs.utils.profane_words import PROFANE_WORDS
import asyncio


class AutoMod:
    def __init__(self, bot):
        self.bot = bot
        self.SAFE_CHANNELS = []
        self.SAFE_MEMBERS = []

    async def on_message(self, message):
        if message.channel.id in self.SAFE_CHANNELS:
            return
        if message.author.id in self.SAFE_MEMBERS:
            return

        if any(message.content in s for s in PROFANE_WORDS):
            await asyncio.sleep(1)
            await message.delete()

            e = discord.Embed(colour=discord.Colour.red())
            e.description = 'Your message has been deleted. \n\n' \
                            'Please refrain from using such vulgar language.\n\n ' \
                            'You can find the list of words considered "profane" ' \
                            '[here](https://github.com/KanoComputing/nodejs-profanity-util/' \
                            'blob/master/lib/swearwords.json)' \
                            '\n\nIf you think one is incorrect, please DM a mod. Thank You.'
            await message.author.send(embed=e)

    async def on_member_update(self, before, after):
        if before.nickname == after.nickname:
            return
        if before.id in self.SAFE_MEMBERS:
            return

        if any(after.nickname in s for s in PROFANE_WORDS):
            await asyncio.sleep(1)
            await after.edit(nick='Censored Name')

            e = discord.Embed(colour=discord.Colour.red())
            e.description = 'Your nickname has been changed\n\n' \
                            'Please refrain from using such vulgar language.\n\n ' \
                            'You can find the list of words considered "profane" ' \
                            '[here](https://github.com/KanoComputing/nodejs-profanity-util/' \
                            'blob/master/lib/swearwords.json)' \
                            '\n\nIf you think one is incorrect, please DM a mod. Thank You.\n\n' \
                            'You Are free to change your nickname back to an appropriate name'
            await after.send(embed=e)

    async def on_member_join(self, member):
        if member.id in self.SAFE_MEMBERS:
            return

        if any(member.nickname in s for s in PROFANE_WORDS):
            await asyncio.sleep(1)
            await member.edit(nick='Censored Name')

            e = discord.Embed(colour=discord.Colour.red())
            e.description = 'Your nickname has been changed\n\n' \
                            'Please refrain from using such vulgar language.\n\n ' \
                            'You can find the list of words considered "profane" ' \
                            '[here](https://github.com/KanoComputing/nodejs-profanity-util/' \
                            'blob/master/lib/swearwords.json)' \
                            '\n\nIf you think one is incorrect, please DM a mod. Thank You.\n\n' \
                            'You Are free to change your nickname back to an appropriate name'
            await member.send(embed=e)


def setup(bot):
    bot.add_cog(AutoMod(bot))
