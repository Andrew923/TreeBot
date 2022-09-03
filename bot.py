import discord
import random
from pokedex import pokedex
from datetime import datetime
import json
import asyncio
import re
# import config
# token = config.token
token = os.environ.get('config.token')

mention_search = re.compile('<@!?(\d+)>')
client = discord.Client(intents=discord.Intents.all())
pokedex = pokedex.Pokedex()
snipe_author = {}
snipe_content = {}

def read(file):
    with open(file) as f:
        return json.load(f)

def write(file, dictionary):
    with open(file, 'w') as f:
        json.dump(dictionary, f)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    try:
        embed = message.embeds[0].to_dict()
        user = client.get_user(int(mention_search.findall(embed['description'])[0]))
        remind = read('remind.json')
        if ("you've caught" in embed['description']) and (remind[str(user.id)] == "yes"):
            await asyncio.sleep(3*60*60)
            await message.channel.send(f"{user.mention}, it is time for you to catch the pokemon")
    except IndexError:
        pass

    if message.author == client.user:
        return

    elif message.content.lower() == 'hello':
        await message.channel.send('Hello!')

    elif message.content.startswith('!say'):
        await message.channel.send(message.content.replace('!say', ''))

    elif message.content.startswith('!pokemon'):
        pokemontime = read('pokemontime.json')
        if storage[str(message.author.id)] < datetime.now():
            pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
            await message.channel.send("Good fucking job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
            await message.channel.send(pokemon['sprite'])
            pokemontime[str(message.author.id)] = datetime.now() + timedelta(minutes=60)
        else:
            await message.channel.send("You gotta wait " + str(pokemontime[str(message.author.id)] - datetime.now()) + " to catch another pokemon bro")

    elif message.content.startswith('!message'):
        message = random.choice(message.channel.history(limit=300).flatten())
        await message.channel.send(message.content + '\n' + message.jump_url)

    elif message.content.startswith('!time'):
        if (random.randint(1,3) != 1):
            await message.channel.send("The time is " + datetime.now().strftime("%H:%M:%S"))
        else:
            await message.channel.send("time for you to get a watch hahaha")

    elif message.content.startswith('!store'):
        stored_message = message.content.replace('!store', '')
        with open('storage.json') as f:
            storage = json.load(f)
        storage[str(message.author.id)] = stored_message
        with open('storage.json', 'w') as f:
            json.dump(storage, f)
        await message.channel.send("Stored: " + stored_message)
    
    elif message.content.startswith('!retrieve'):
        with open('storage.json') as f:
            storage = json.load(f)
        await message.channel.send(storage[str(message.author.id)])

    #pokemon reminder
    elif message.content.startswith('!remindpokemon'):
        channel = message.channel
        if message.content[-3:] == ' on':
            remind = read('remind.json')
            remind[str(message.author.id)] = "yes"
            write('remind.json', remind)
            await channel.send("You will now receive notifications when pokemons are ready")
        elif message.content[-3:] == 'off':
            remind = read('remind.json')
            remind[str(message.author.id)] = "nah"
            write('remind.json', remind)
            await channel.send("You will no longer receive notifications when pokemons are ready")
        else:
            await message.channel.send("Please specify whether to turn this setting 'on' or 'off'")

    #snipe
    elif message.content.startswith('!snipe'):
        try:
            em = discord.Embed(name = f"Last deleted message in #{message.channel.name}", description = snipe_content[message.channel.id])
            em.set_footer(text = f"This message was sent by {snipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send(f"Nobody deleted any shit")


@client.event
async def on_message_delete(message):
    snipe_content[message.channel.id] = message.content
    snipe_author[message.channel.id] = message.author
    await asyncio.sleep(100)
    del snipe_author[message.channel.id]
    del snipe_content[message.channel.id]

# commenting out for now because reactions result in rate limits
    # if message.content.startswith('!slideshow'):
    #     channel = message.channel
    #     index = 0
    #     left = '⏪'
    #     right = '⏩'
    #     list = ['page one', 'page two', 'page three', 'page four']
    #     msg = await channel.send(list[0])
    #     await msg.add_reaction(left)
    #     await msg.add_reaction(right)

    #     def check(reaction, user):
    #         return user == message.author
        
    #     while True:
    #         reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
    #         if (reaction.emoji == left and index != 0):
    #             await msg.edit(content=list[index-1])
    #             await msg.remove_reaction(left, user)
    #             index -= 1
    #         elif (reaction.emoji == left and index == 0):
    #             await msg.remove_reaction(left, user)
    #         elif (reaction.emoji == right and index != len(list) - 1):
    #             await msg.edit(content=list[index+1])
    #             await msg.remove_reaction(right, user)
    #             index += 1
    #         elif (reaction.emoji == right and index == len(list) - 1):
    #             await msg.remove_reaction(right, user)


client.run(token)