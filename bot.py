import random
from pokedex import pokedex
import datetime
import asyncio
import re
import os
import discord
from github import Github
import dateparser
EDT = datetime.timezone(datetime.timedelta(hours=-4))
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials

# comment out between uploading
# import config
# token = config.discord_token
# github = Github(config.github_token)
# calendar = GoogleCalendar("andrewyu41213@gmail.com")


token = Credentials(
    token=os.getenv('token'),
    refresh_token=os.getenv('refresh_token'),
    client_id=os.getenv('client_id'),
    client_secret=os.getenv('client_secret'),
    scopes=['https://www.googleapis.com/auth/calendar'],
    token_uri='https://oauth2.googleapis.com/token'
)
calendar = GoogleCalendar(credentials=token)
token = os.getenv('config.token')
github = Github(os.getenv('github_token'))


repository = github.get_user().get_repo('TreeBot')
mention_search = re.compile('<@!?(\d+)>')
client = discord.Client(intents=discord.Intents.all())
pokedex = pokedex.Pokedex()
snipe_author = {}
snipe_content = {}
editsnipe_before = {}
editsnipe_after = {}
editsnipe_author = {}
empty_char = '\u200b'

#new read and udpate functions for updating github repo
def read(filename):
    file = repository.get_contents(filename)
    return eval(file.decoded_content.decode())

def update(filename, dictionary, message='updated from python'):
    contents = repository.get_contents(filename)
    repository.update_file(contents.path, message, str(dictionary), contents.sha)

def parseDate(string, eastern=True):
    if(eastern): return dateparser.parse(string).astimezone(EDT)
    else: return dateparser.parse(string)

def removeCommand(string):
    index = None
    for c in string:
        if(c.isspace()):
            index = string.index(c)
    return string[index + 1:] if index != None else None

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
    #display help message with all commands
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
        embed.add_field(name='!editsnipe', value='see recently edited messages')
        embed.add_field(name='!pin', value="specify 'from' or 'to' to get pinned messages from one channel sent to another")
        embed.add_field(name='!remind', value='be reminded of something')
        embed.add_field(name=empty_char, value="See the ReadMe [here](https://github.com/Andrew923/TreeBot#readme) to view usage syntax", inline=False)
        await message.channel.send(embed=embed)

    elif message.content.lower() == 'hello':
        await message.channel.send('Hello!')

    elif message.content.startswith('!say'):
        await message.channel.send(removeCommand(message.content))

    elif message.content.startswith('!pokemon'):
        pokemontime = read('pokemontime.json')
        try:
            if pokemontime[str(message.author.id)] < datetime.datetime.now():
                pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
                await message.channel.send("Good job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
                await message.channel.send(pokemon['sprite'])
                pokemontime[str(message.author.id)] = datetime.datetimenow() + datetime.timedelta(minutes=60)
                update('pokemontime.json', pokemontime)
            else:
                time = datetime.datetime.strptime(str(pokemontime[str(message.author.id)] - datetime.datetime.now()), '%H:%M:%S.%f')
                await message.channel.send("You gotta wait " + time.strftime('%#M minutes and %#S seconds') + " to catch another pokemon bro")
        except KeyError:
            pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
            await message.channel.send("Good job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
            await message.channel.send(pokemon['sprite'])
            pokemontime[str(message.author.id)] = datetime.datetime.now() + datetime.timedelta(minutes=60)
            update('pokemontime.json', pokemontime)

    elif message.content.startswith('!random message' or '!randommessage'):
        message = random.choice(message.channel.history(limit=300).flatten())
        await message.channel.send(message.content + '\n' + message.jump_url)

    elif message.content.startswith('!time' or 'what time is it' or "what's the time"):
        if (random.randint(1,3) != 1):
            await message.channel.send("The time is " + datetime.datetime.now().astimezone(EDT).strftime("%#I:%M %p"))
        else:
            await message.channel.send("time for you to get a watch hahaha")

    elif message.content.startswith('!store'):
        stored_message = removeCommand(message.content)
        storage = read('storage.json')
        storage[str(message.author.id)] = stored_message
        update('storage.json', storage)
        await message.channel.send("Stored: " + stored_message)
    
    elif message.content.startswith('!retrieve'):
        storage = read('storage.json')
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
            update('remind.json', remind)
            await channel.send("You will now receive notifications when pokemons are ready")
        elif message.content[-3:] == 'off':
            remind = read('remind.json')
            remind[str(message.author.id)] = "nah"
            update('remind.json', remind)
            await channel.send("You will no longer receive notifications when pokemons are ready")
        else:
            await message.channel.send("Please specify whether to turn this setting 'on' or 'off'")

    #snipe
    elif message.content.startswith('!snipe'):
        try:
            em = discord.Embed(color=0x03c6fc, title = f"Last deleted message in #{message.channel.name}", description = snipe_content[message.channel.id])
            em.set_footer(text = f"This message was sent by {snipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send("Nobody deleted any shit")
    
    #editsnipe
    elif message.content.startswith('!editsnipe'):
        try:
            em = discord.Embed(color=0x03c6fc, title = f"Last edited message in #{message.channel.name}")
            em.add_field(name='Before:', value = editsnipe_before[message.channel.id])
            em.add_field(name='After:', value = editsnipe_after[message.channel.id])
            em.set_footer(text = f"This message was edited by {editsnipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send("No edits")
    
    #pins
    elif message.content.startswith('!pin'):
        if 'from' in message.content:
            pins = read('pins.json')
            pins['from'].append(message.channel.id)
            update('pins.json', pins)
            await message.channel.send('Pins will be read from this channel')
        elif 'to' in message.content:
            pins = read('pins.json')
            pins['to'].append(message.channel.id)
            update('pins.json', pins)
            await message.channel.send('Pins will be posted to this channel')
    
    elif message.content.startswith('!remind' or '!reminder'):
        s = removeCommand(message.content)
        time, reminder = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
        await asyncio.sleep(int((time - datetime.datetime.now()).total_seconds()))
        await message.channel.send(f"{message.author.mention} {reminder}")

    elif message.content.startswith('!event'):
        if(',' not in message.content):
            await message.channel.send("Please use a comma to separate the event time and event title")
        elif(message.content.count(',') > 1):
            s = removeCommand(message.content)
            start, s = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
            end, title = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
            calendar.add_event(Event(title, start = start, end = end))
            embed = discord.Embed(color=0x03c6fc, title='New Event')
            embed.add_field(name=title,value=f"From: {start.strftime('%#m/%#d %#I:%M %p')}\nTo: {end.strftime('%#m/%#d %#I:%M %p')}")
            await message.channel.send(embed=embed)
        else:
            s = removeCommand(message.content)
            time, title = parseDate(s[:s.find(',')]).date(), s[s.find(',') + 1:]
            calendar.add_event(Event(title, start = time, end = time+datetime.timedelta(days=1)))
            embed = discord.Embed(color=0x03c6fc, title='New Event')
            embed.add_field(name=title,value=f"Date: {time.strftime('%#m/%#d')}")
            await message.channel.send(embed=embed)
    
    elif message.content.startswith('!delete' or '!deleteevent'):
        s = removeCommand(message.content)
        channel = message.channel
        if(s == None):
            day = datetime.datetime.now().astimezone(EDT).date()
        else:
            day = parseDate(s).date()
        eventcount = 0
        embed = discord.Embed(color=0x03c6fc, title='Delete which event?', description='Type the number corresponding to the event')
        count = 0
        for event in calendar[day:day]:
            count += 1
            if(event.location == None):
                embed.add_field(name=f"{count} " + event.summary,
                    value = f"From: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)
            else:
                embed.add_field(name=f"{count} " + event.summary,
                    value = f"Location: {event.location}\nFrom: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)   
        embed.set_footer(text="Type 'Cancel' to stop")
        await message.channel.send(embed=embed)
        def check(m):
            if(m.content.lower() == 'cancel'):
                return True
            return m.content.isdigit() and m.channel == channel and (int(m.content) <= count)
        msg = await client.wait_for('message', check=check)
        if(msg.content.lower() == 'cancel'):
            await message.channel.send("Cancelled")
        else:
            msg = int(msg.content)
            count = 0
            for event in calendar[day:day]:
                count += 1
                if(count == msg):
                    calendar.delete_event(event)
                    title, time = event.summary, event.start       
            embed = discord.Embed(color=0x03c6fc, title='Event Deleted')
            embed.add_field(name=title,value=f"Date: {time.strftime('%#m/%#d')}")
            await message.channel.send(embed=embed)

    elif message.content.startswith('!schedule'):
        s = removeCommand(message.content)
        if(s == None):
            day = datetime.datetime.now().astimezone(EDT).date()
        else:
            day = parseDate(s, False).date()
        eventcount = 0
        for event in calendar[day:day]: eventcount += 1
        s = '' if(eventcount == 1) else 's'
        embed = discord.Embed(color=0x03c6fc, title='Schedule', description=f"{eventcount} event{s} on {day.strftime('%#m/%#d')}")
        for event in calendar[day:day]:
            if(event.location == None):
                embed.add_field(name=event.summary,
                    value = f"From: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)
            else:
                embed.add_field(name=event.summary,
                    value = f"Location: {event.location}\nFrom: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)
        await message.channel.send(embed=embed)

    elif message.content.startswith('!python') and message.author.id == 177962211841540097:
        try:
            await message.channel.send(eval(removeCommand(message.content)))
        except:
            await message.channel.send("Something went wrong")



#snipe (for deleted messages)
@client.event
async def on_message_delete(message):
    snipe_content[message.channel.id] = message.content
    snipe_author[message.channel.id] = message.author
    await asyncio.sleep(120)
    del snipe_author[message.channel.id]
    del snipe_content[message.channel.id]

@client.event
async def on_message_edit(before, after):
    #edit snipe (check if content changed)
    if before.content != after.content:
        editsnipe_before[before.channel.id] = before.content
        editsnipe_after[before.channel.id] = after.content
        editsnipe_author[before.channel.id] = before.author
        await asyncio.sleep(120)
        del editsnipe_before[before.channel.id]
        del editsnipe_after[before.channel.id]
        del editsnipe_author[before.channel.id]
    #pins (check if something pinned)
    if not before.pinned and after.pinned:
        channel = after.channel
        pins = read('pins.json')
        if(channel.id in pins['from']):
            embed=discord.Embed(color=0x03c6fc, description=after.content)
            embed.set_author(name=after.author.display_name, icon_url=after.author.avatar)
            embed.add_field(name=empty_char, value=f"[Jump to Message]({after.jump_url})")
            await client.get_channel(pins['to'][pins['from'].index(channel.id)]).send(embed=embed)
            await after.unpin()


client.run(token)