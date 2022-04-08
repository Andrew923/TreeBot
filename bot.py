import discord
import random

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('!message'):
        messages = await message.channel.history(limit=500).flatten()
        await message.channel.send(random.choice(messages).content)
        await message.channel.send(random.choice(messages).embeds[0].to_dict())


client.run('OTYyMDUyNTUzMjIxMjE4MzA0.YlB7Qg.UUspoQO4rq8_1ea-eOAYAxtUmmU')