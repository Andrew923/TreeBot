import discord
import random
from pokedex import pokedex

client = discord.Client(intents=discord.Intents.all())
pokedex = pokedex.Pokedex()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('!say'):
        await message.channel.send(message.content.replace('!say', ''))

    if message.content.startswith('!pokemon'):
        pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
        await message.channel.send("Good fucking job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
        await message.channel.send(pokemon['sprite'])

    if message.content.startswith('!message'):
        messages = await message.channel.history(limit=300).flatten()
        await message.channel.send(random.choice(messages).content)


client.run('OTYyMDUyNTUzMjIxMjE4MzA0.YlB7Qg.UUspoQO4rq8_1ea-eOAYAxtUmmU')