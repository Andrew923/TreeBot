import discord
import random
from pokedex import pokedex
from datetime import datetime
import json

client = discord.Client(intents=discord.Intents.all())
pokedex = pokedex.Pokedex()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == 'hello':
        await message.channel.send('Hello!')

    if message.content.startswith('!say'):
        await message.channel.send(message.content.replace('!say', ''))

    if message.content.startswith('!pokemon'):
        pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
        await message.channel.send("Good fucking job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
        await message.channel.send(pokemon['sprite'])

    if message.content.startswith('!message'):
        message = random.choice(message.channel.history(limit=300).flatten())
        await message.channel.send(message.content + '\n' + message.jump_url)

    if message.content.startswith('!time'):
        if (random.randint(1,3) != 1):
            await message.channel.send("The time is " + datetime.now().strftime("%H:%M:%S"))
        else:
            await message.channel.send("time for you to get a watch hahaha")

    if message.content.startswith('!store'):
        stored_message = message.content.replace('!store', '')
        with open('storage.json') as f:
            storage = json.load(f)
        storage[str(message.author.id)] = stored_message
        with open('storage.json', 'w') as f:
            json.dump(storage, f)
        await message.channel.send("Stored: " + stored_message)
    
    if message.content.startswith('!retrieve'):
        with open('storage.json') as f:
            storage = json.load(f)
        await message.channel.send(storage[str(message.author.id)])

    if message.content.startswith('!slideshow'):
        channel = message.channel
        index = 0
        left = '⏪'
        right = '⏩'
        list = ['page one', 'page two', 'page three', 'page four']
        msg = await channel.send(list[0])
        await msg.add_reaction(left)
        await msg.add_reaction(right)

        def check(reaction, user):
            return user == message.author
        
        while True:
            reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
            if (reaction.emoji == left and index != 0):
                await msg.edit(content=list[index-1])
                await msg.remove_reaction(left, user)
                index -= 1
            elif (reaction.emoji == left and index == 0):
                await msg.remove_reaction(left, user)
            elif (reaction.emoji == right and index != len(list) - 1):
                await msg.edit(content=list[index+1])
                await msg.remove_reaction(right, user)
                index += 1
            elif (reaction.emoji == right and index == len(list) - 1):
                await msg.remove_reaction(right, user)


client.run('OTYyMDUyNTUzMjIxMjE4MzA0.YlB7Qg.UUspoQO4rq8_1ea-eOAYAxtUmmU')