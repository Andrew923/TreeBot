import random
from pokedex import pokedex
from datetime import datetime
import json
import asyncio
import re
import os
import discord
# import config
# token = config.token
token = os.getenv('config.token')

mention_search = re.compile('<@!?(\d+)>')
client = discord.Client(intents=discord.Intents.all())
pokedex = pokedex.Pokedex()
snipe_author = {}
snipe_content = {}
pin_from = []
pin_to = []  

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
    except:
        pass

    if message.author == client.user:
        return
    
    elif message.content.startswith('!help'):
        embed=discord.Embed(color=0x03c6fc)
        embed.set_author(name="Tree Commands:", icon_url="http://clipart-library.com/img1/1269981.png",
            url="https://github.com/Andrew923/TreeBot")
        embed.add_field(name='!help', value='Sends this message')
        embed.add_field(name='hello', value='I respond with hello')
        embed.add_field(name='!say', value='I repeat what you say')
        embed.add_field(name='!pokemon', value='Catch pokemons')
        embed.add_field(name='!random message', value='I send a random message from the last 300 messages')
        embed.add_field(name='!time', value='the time')
        embed.add_field(name='!store', value='store some message for later')
        embed.add_field(name='!retrieve', value='retrieve your stored stuff')
        embed.add_field(name='!remindpokemon', value='receive reminders for when you can catch pokemon from Toasty')
        embed.add_field(name='!snipe', value='see recently deleted messages')
        embed.add_field(name='!pin', value="specify 'from' or 'to' to get pinned messages from one channel sent to another")

        await message.channel.send(embed=embed)

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

    elif message.content.startswith('!random message' or '!randommessage'):
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
        try:
            await message.channel.send(storage[str(message.author.id)])
        except KeyError:
            await message.channel.send("Nothing is stored")
        except discord.errors.HTTPException:
            await message.channel.send("Nothing is stored")

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
            em = discord.Embed(title = f"Last deleted message in #{message.channel.name}", description = snipe_content[message.channel.id])
            em.set_footer(text = f"This message was sent by {snipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send("Nobody deleted any shit")

    elif message.content.startswith('!pin'):
        if 'from' in message.content:
            pin_from.append(message.channel.id)
            await message.channel.send('Pins will be read from this channel')
        elif 'to' in message.content:
            pin_to.append(message.channel.id)
            await message.channel.send('Pins will be posted to this channel')

@client.event
async def on_message_delete(message):
    snipe_content[message.channel.id] = message.content
    snipe_author[message.channel.id] = message.author
    await asyncio.sleep(100)
    del snipe_author[message.channel.id]
    del snipe_content[message.channel.id]

@client.event
async def on_message_edit(before, after):
    if not before.pinned and after.pinned:
        channel = after.channel
        if(channel.id in pin_from):
            embed=discord.Embed(color=0x03c6fc, description=after.content)
            embed.set_author(name=after.author.display_name, icon_url=after.author.avatar)
            await client.get_channel(pin_to[pin_from.index(channel.id)]).send(embed=embed)
            await after.unpin()

# @client.event
# async def on_guild_channel_pins_update(channel, last_pin):
#     print(f"channel: {channel}, {channel.id}, {pin_from}, {pin_to}")
#     if(channel.id in pin_from):
#         print(last_pin)
#         await pin_to[pin_from.index(channel.id)].send(last_pin.content)

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