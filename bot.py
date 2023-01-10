import random, datetime, asyncio, re, os, platform
from pokedex import pokedex
import discord, wolframalpha, requests
from github import Github
import dateparser
EDT = datetime.timezone(datetime.timedelta(hours=-4))
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from canvasapi import Canvas
from pyowm.owm import OWM
from pydictionary import Dictionary
from serpapi import GoogleSearch
from art import *

# checks platform
if platform.uname().node == 'Andrew':
    import config
    token = config.discord_token
    github = Github(config.github_token)
    calendar = GoogleCalendar("andrewyu41213@gmail.com")
    canvas = Canvas('https://canvas.cmu.edu/', config.API_KEY)
    owm = OWM(config.weather)
    wolfram = wolframalpha.Client(config.wolf)
    headers = {"X-RapidAPI-Key": config.rapidapi,
        "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com"}
    serpapi = config.serpapi
else:
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
    canvas = Canvas('https://canvas.cmu.edu/', os.getenv('canvasapikey'))
    owm = OWM(os.getenv('weatherkey'))
    wolfram = wolframalpha.Client(os.getenv('wolf'))
    headers = {"X-RapidAPI-Key": os.getenv('rapidapi'),
        "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com"}
    serpapi = os.getenv('serpapi')

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
user = canvas.get_current_user()
courses = [canvas.get_course(31318), canvas.get_course(31146), canvas.get_course(30417)]
mgr = owm.weather_manager()

#read and udpate functions for updating github repo
def read(filename):
    file = repository.get_contents(filename)
    return eval(file.decoded_content.decode())

def update(filename, dictionary, message='updated from python'):
    contents = repository.get_contents(filename)
    repository.update_file(contents.path, message, str(dictionary), contents.sha)

#should fix time zone issues
def parseDate(string):
    return dateparser.parse(string)

def removeCommand(string, count=1):
    return ' '.join(string.split()[count:])

def canvasEmbed(iterable, title, count = False, emptyName=True):
    n = 0
    embed = discord.Embed(color=0x03c6fc,title=str(title))
    for thing in iterable:
        n += 1
        if(count): thing = f"{n}. {thing}"
        embed.add_field(name=empty_char,value=thing,inline=False) if emptyName else embed.add_field(name=thing,value=empty_char,inline=False)
    embed.set_footer(text="Type 'Cancel' to stop")
    return embed

def urbandefine(s):
    response = requests.request("GET", "https://mashape-community-urban-dictionary.p.rapidapi.com/define",
                                headers=headers, params={"term":s})
    if eval(response.text)['list'] == list(): return discord.Embed(color=0x03c6fc, title=f'Definition of {s}', description="Nothing found :(")
    result = eval(response.text)['list'][0]
    embed = discord.Embed(color=0x03c6fc, title=f'Definition of {s}', description=result['definition'])
    embed.add_field(name="Example", value = ' '.join(result['example'].split()), inline=False)
    embed.add_field(name=empty_char, value=f"[Urban Dictionary]({result['permalink']})")
    return embed

def ascii(text, size='random'):
    if size.lower().startswith('s'): font='random-small'
    elif size.lower().startswith('m'): font='random-medium'
    elif size.lower().startswith('l'): font='random-large'
    else: font=size
    return text2art(text, font)

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
    elif message.content.lower().startswith('!help'):
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
        embed.add_field(name='!weather', value="See weather at a location that is setup on first time a user calls or when '!weather setup' is called")
        embed.add_field(name='!define', value='Defines word')
        embed.add_field(name='wolf', value='calls Wolfram Alpha')
        embed.set_footer(text="See the ReadMe [here](https://github.com/Andrew923/TreeBot#readme) to view usage syntax")
        await message.channel.send(embed=embed)

    elif message.content.lower() == 'hello':
        await message.channel.send('Hello!')

    elif message.content.lower().startswith('!say'):
        await message.channel.send(removeCommand(message.content.lower()))

    elif message.content.lower().startswith('!pokemon'):
        pokemontime = read('pokemontime.json')
        try:
            if pokemontime[str(message.author.id)] < datetime.datetime.now():
                pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
                await message.channel.send("Good job, " + message.author.mention + " you caught " + pokemon['name'] + "!")
                await message.channel.send(pokemon['sprite'])
                pokemontime[str(message.author.id)] = datetime.datetime.now() + datetime.timedelta(minutes=60)
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

    elif message.content.lower().startswith('!random message' or '!randommessage'):
        message = random.choice(message.channel.history(limit=300).flatten())
        await message.channel.send(message.content.lower() + '\n' + message.jump_url)

    elif message.content.lower().startswith('!time') or message.content.lower().startswith('what time is it') or message.content.lower().startswith("what's the time"):
        if (random.randint(1,3) != 1):
            await message.channel.send("The time is " + datetime.datetime.now().astimezone(EDT).strftime("%#I:%M %p"))
        else:
            await message.channel.send("time for you to get a watch hahaha")

    elif message.content.lower().startswith('!store'):
        stored_message = removeCommand(message.content.lower())
        storage = read('storage.json')
        storage[str(message.author.id)] = stored_message
        update('storage.json', storage)
        await message.channel.send("Stored: " + stored_message)
    
    elif message.content.lower().startswith('!retrieve'):
        storage = read('storage.json')
        try:
            await message.channel.send(storage[str(message.author.id)])
        except KeyError:
            await message.channel.send("Nothing is stored")
        except discord.errors.HTTPException:
            await message.channel.send("Nothing is stored")

    #pokemon reminder
    elif message.content.lower().startswith('!remindpokemon'):
        channel = message.channel
        if message.content.lower()[-3:] == ' on':
            remind = read('remind.json')
            remind[str(message.author.id)] = "yes"
            update('remind.json', remind)
            await channel.send("You will now receive notifications when pokemons are ready")
        elif message.content.lower()[-3:] == 'off':
            remind = read('remind.json')
            remind[str(message.author.id)] = "nah"
            update('remind.json', remind)
            await channel.send("You will no longer receive notifications when pokemons are ready")
        else:
            await message.channel.send("Please specify whether to turn this setting 'on' or 'off'")

    #snipe
    elif message.content.lower().startswith('!snipe'):
        try:
            description = snipe_content[message.channel.id]
            if 'https://' in description:
                em = discord.Embed(color=0x03c6fc, title = f"Last deleted message in #{message.channel.name}")
                em.set_image(url = description)
            else:
                em = discord.Embed(color=0x03c6fc, title = f"Last deleted message in #{message.channel.name}", description = snipe_content[message.channel.id])
            em.set_footer(text = f"This message was sent by {snipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send("Nobody deleted any shit")
    
    #editsnipe
    elif message.content.lower().startswith('!editsnipe'):
        try:
            em = discord.Embed(color=0x03c6fc, title = f"Last edited message in #{message.channel.name}")
            em.add_field(name='Before:', value = editsnipe_before[message.channel.id])
            em.add_field(name='After:', value = editsnipe_after[message.channel.id])
            em.set_footer(text = f"This message was edited by {editsnipe_author[message.channel.id]}")
            await message.channel.send(embed = em)
        except KeyError:
            await message.channel.send("No edits")
    
    #pins
    elif message.content.lower().startswith('!pin'):
        if 'from' in message.content.lower():
            pins = read('pins.json')
            pins['from'].append(message.channel.id)
            update('pins.json', pins)
            await message.channel.send('Pins will be read from this channel')
        elif 'to' in message.content.lower():
            pins = read('pins.json')
            pins['to'].append(message.channel.id)
            update('pins.json', pins)
            await message.channel.send('Pins will be posted to this channel')
    
    elif message.content.lower().startswith('!remind'):
        s = removeCommand(message.content.lower())
        time, reminder = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
        await message.channel.send(f"You will be reminded to {reminder} at {time.strftime('%#m/%#d %#I:%M %p')}")
        await asyncio.sleep(int((time - datetime.datetime.now()).total_seconds()))
        await message.channel.send(f"{message.author.mention} {reminder}")

    elif message.content.lower().startswith('!event'):
        if(',' not in message.content.lower()):
            await message.channel.send("Please use a comma to separate the event time and event title")
        elif(message.content.lower().count(',') > 1):
            s = removeCommand(message.content.lower())
            start, s = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
            end, title = parseDate(s[:s.find(',')]), s[s.find(',') + 1:]
            calendar.add_event(Event(title, start = start, end = end))
            embed = discord.Embed(color=0x03c6fc, title='New Event')
            embed.add_field(name=title,value=f"From: {start.strftime('%#m/%#d %#I:%M %p')}\nTo: {end.strftime('%#m/%#d %#I:%M %p')}")
            await message.channel.send(embed=embed)
        else:
            s = removeCommand(message.content.lower())
            time, title = parseDate(s[:s.find(',')]).date(), s[s.find(',') + 1:]
            calendar.add_event(Event(title, start = time, end = time+datetime.timedelta(days=1)))
            embed = discord.Embed(color=0x03c6fc, title='New Event')
            embed.add_field(name=title,value=f"Date: {time.strftime('%#m/%#d')}")
            await message.channel.send(embed=embed)
    
    elif message.content.lower().startswith('!delete'):
        s = removeCommand(message.content.lower())
        channel = message.channel
        author = message.author
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
                embed.add_field(name=f"{count}. " + event.summary,
                    value = f"From: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)
            else:
                embed.add_field(name=f"{count}. " + event.summary,
                    value = f"Location: {event.location}\nFrom: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)   
        embed.set_footer(text="Type 'Cancel' to stop")
        await message.channel.send(embed=embed)
        def check(m):
            if(m.content.lower() == 'cancel'):
                return True
            return m.content.isdigit() and m.channel == channel and (int(m.content) <= count) and m.author == author
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

    elif message.content.lower().startswith('!update'):
        s = removeCommand(message.content.lower())
        channel = message.channel
        author = message.author
        if(s == None):
            day = datetime.datetime.now().astimezone(EDT).date()
        else:
            day = parseDate(s).date()
        eventcount = 0
        embed = discord.Embed(color=0x03c6fc, title='Update which event?', description='Type the number corresponding to the event')
        count = 0
        for event in calendar[day:day]:
            count += 1
            if(event.location == None):
                embed.add_field(name=f"{count}. " + event.summary,
                    value = f"From: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)
            else:
                embed.add_field(name=f"{count}. " + event.summary,
                    value = f"Location: {event.location}\nFrom: {event.start.strftime('%#I:%M %p')}\nTo: {event.end.strftime('%#I:%M %p')}" ,inline=False)   
        embed.set_footer(text="Type 'Cancel' to stop")
        await message.channel.send(embed=embed)
        def check(m):
            if(m.content.lower() == 'cancel'):
                return True
            return m.content.isdigit() and m.channel == channel and (int(m.content) <= count) and m.author == author
        msg = await client.wait_for('message', check=check)
        if(msg.content.lower() == 'cancel'):
            await message.channel.send("Cancelled")
        else:
            msg = int(msg.content)
            count = 0
            for ev in calendar[day:day]:
                count += 1
                if(count == msg):
                    event = ev     
            embed = discord.Embed(color=0x03c6fc, title='Update Event')
            embed.add_field(name=event.summary,value=f"Start: {event.start.strftime('%#m/%#d %#I:%M %p')}\nEnd: {event.end.strftime('%#m/%#d %#I:%M %p')}")
            embed.set_footer(text="Type 'Cancel' to stop")
            await message.channel.send(embed=embed)
            def check(m):
                if(m.content.lower() == 'cancel'):
                    return True
                return m.channel == channel and m.author == author
            msg = await client.wait_for('message', check=check)
            if(msg.content.lower() == 'cancel'):
                await message.channel.send("Cancelled")
            else:
                if 'start' in msg.content:
                    s = msg.content.lower().replace('start', '').strip()
                    event.start = parseDate(s)
                elif 'end' in msg.content:
                    s = msg.content.lower().replace('end', '').strip()
                    event.end = parseDate(s)
                elif 'summary' in msg.content:
                    s = msg.content.lower().replace('summary', '').strip()
                    event.summary = s
                elif 'location' in msg.content:
                    s = msg.content.lower().replace('location', '').strip()
                    event.location = s
                elif 'description' in msg.content:
                    s = msg.content.lower().replace('description', '').strip()
                    event.description = s
                calendar.update_event(event)
                embed = discord.Embed(color=0x03c6fc, title='Event Updated')
                embed.add_field(name=event.summary,value=f"Start: {event.start.strftime('%#m/%#d %#I:%M %p')}\nEnd: {event.end.strftime('%#m/%#d %#I:%M %p')}")
                await message.channel.send(embed=embed)

    elif message.content.lower().startswith('!schedule'):
        s = removeCommand(message.content.lower())
        if(s == None):
            day = datetime.datetime.now().astimezone(EDT).date()
        else:
            day = parseDate(s).date()
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
    
    elif message.content.lower().startswith('!canvas'):
        s = removeCommand(message.content.lower())
        channel = message.channel
        author = message.author
        embed = discord.Embed(color=0x03c6fc,title='Courses')
        count = 0
        for course in courses:
            count += 1
            embed.add_field(name=empty_char, value=f"{count}. {course.course_code} {course.name}")
        embed.set_footer(text="Type 'Cancel' to stop")
        await message.channel.send(embed=embed)
        def check(m):
            if(m.content.lower() == 'cancel'):
                return True
            return m.content.isdigit() and m.channel == channel and (int(m.content) <= count) and m.author == author
        msg = await client.wait_for('message', check=check)
        if(msg.content.lower() == 'cancel'):
            await message.channel.send("Cancelled")
        else:
            msg = int(msg.content)
            count = 0
            for c in courses:
                count += 1
                if(count == msg):
                    course = c
            embed = canvasEmbed(["'Assignments' or 'Modules'"], course.name, False, False)
            await message.channel.send(embed=embed)
            def check(m):
                if(m.content.lower() == 'cancel'):
                    return True
                return m.content.isalpha() and m.channel == channel and m.author == author
            msg = await client.wait_for('message', check=check)
            msg = msg.content
            if(msg.lower() == 'a' or 'assignment' in msg.lower()):
                embed = canvasEmbed(course.get_assignments(), course.name, True)
                await message.channel.send(embed=embed)
                def check(m):
                    if(m.content.lower() == 'cancel'):
                        return True
                    return m.content.isdigit() and m.channel == channel and m.author == author
                msg = await client.wait_for('message', check=check)
                if(msg.content.lower() == 'cancel'):
                    await message.channel.send("Cancelled")
                else:
                    msg = int(msg.content)
                    count = 0
                    for a in course.get_assignments():
                        count += 1
                        if(count == msg):
                            assignment = a
                    s = assignment.description
                    while '<' in s:
                        s = s[:s.index('<')] + s[s.index('>') + 1:]
                    s = s.replace("&nbsp;", '')
                    embed = discord.Embed(color=0x03c6fc,title=assignment.name, description=s)
                    await message.channel.send(embed=embed)
            elif(msg.lower() == 'm' or 'module' in msg.lower()):
                embed = canvasEmbed(course.get_modules(), course.name)
                embed.add_field(name=empty_char,value=f"[Canvas Link](https://canvas.cmu.edu/courses/{course.id}/modules)")
                embed.remove_footer()
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("I think something went wrong")

    elif message.content.lower().startswith('eval'):
        try:
            await message.channel.send(eval(removeCommand(message.content.lower()).strip()))
        except:
            await message.channel.send("Something went wrong")

    elif message.content.lower().startswith('exec') and message.author.id == 177962211841540097:
        try:
            exec(removeCommand(message.content.lower()).strip())  
            await message.channel.send("Comand Executed")
        except:
            await message.channel.send("Something went wrong")

    elif message.content.lower().startswith('!w'):
        wDict = read('weather.json')
        if 'in' in message.content.lower():
            place = removeCommand(message.content.lower().replace(' in ', ' ')).strip()
        #setup location
        elif message.author.id not in wDict or 'setup' in message.content:
            await message.channel.send("Setting up location. Please enter city name or coordinates (lat, lon).")
            def check(m):
                if(m.content.lower() == 'cancel'):
                    return True
                return m.channel == message.channel and m.author == message.author
            msg = await client.wait_for('message', check=check)
            if(msg.content.lower() == 'cancel'):
                await message.channel.send("Cancelled")
            elif(msg.content.isalpha()):
                place = msg.content
                wDict[message.author.id] = place
                update('weather.json', wDict)
            else:
                msg = msg.content
                try:
                    lat, lon = float(msg[:msg.index(',')]), float(msg[msg.index(',')+1:])
                except:
                    await message.channel.send("Something went wrong")
                geomgr = owm.geocoding_manager()
                place = geomgr.reverse_geocode(lat, lon)[0].name
                wDict[message.author.id] = place
                update('weather.json', wDict)
        else:
            place = wDict[message.author.id]
        coords = owm.geocoding_manager().geocode(place)[0]
        one_call = mgr.one_call(coords.lat, coords.lon)
        #defaults to daily forecast
        if 'forecast' not in message.content.lower():
            curr = one_call.current
            today = one_call.forecast_daily[0]
            embed = discord.Embed(color=0x03c6fc, title=f'Weather in {place}', description=curr.detailed_status)
            embed.set_thumbnail(url=curr.weather_icon_url())
            curr_temp = curr.temperature('fahrenheit')
            s = f"Low: {today.temperature('fahrenheit')['min']} °F High: {today.temperature('fahrenheit')['max']} °F"
            embed.add_field(name=f"Temperature: {curr_temp['temp']} °F (Feels like: {curr_temp['feels_like']} °F)",value=s, inline=False)
            if today.rain != {}:
                times = []
                for i in range(24):
                    hour = one_call.forecast_hourly[i]
                    time = datetime.datetime.fromtimestamp(hour.ref_time)
                    if hour.rain != {} and (time.strftime('%d') == datetime.datetime.now().strftime('%d')):
                        times.append(time.strftime('%#I %p'))
                embed.add_field(name="It will rain today!", value=f"Times: {', '.join(times)}")
            await message.channel.send(embed=embed)
        #gives weather forecast, defaults daily
        else:
            if 'tomorrow'in message.content.lower():
                iters = 1
            elif message.content.lower().split()[-1].isdigit():
                iters = int(message.content.lower().split()[-1])
            else:
                iters = 4 
            for i in range(1, iters + 1):
                embed = discord.Embed(color=0x03c6fc) if i != 1 else discord.Embed(color=0x03c6fc, title=f'Forecast for {place}')
                day = one_call.forecast_daily[i]
                embed.set_thumbnail(url=day.weather_icon_url())
                date = datetime.datetime.fromtimestamp(day.ref_time).strftime('%b %#d')
                embed.add_field(name=date,
                                    value = f"Low: {day.temperature('fahrenheit')['min']} °F High: {day.temperature('fahrenheit')['max']} °F")
                await message.channel.send(embed=embed)

    #Generates tinyurl links
    elif message.content.lower().startswith('tinyurl') or message.content.lower().startswith('url'):
        if 'tinyurl' in message.content:
            s = message.content.lower().replace('tinyurl','').strip()
        else:
            s = message.content.lower().replace('url','').strip()
        s = ('-').join(s.split())
        await message.channel.send(f'https://www.tinyurl.com/{s}')

    #defines words
    elif message.content.lower().startswith('!define') or message.content.lower().startswith('define') or \
         (message.content.lower().startswith('what does') and message.content.lower().endswith('mean')):
        if 'define' in message.content.lower():
            s = removeCommand(message.content)
        else:
            s = ' '.join(message.content.lower().split()[2:-1])
        count = 0
        embed = discord.Embed(color=0x03c6fc, title=f'Definition of {s}')
        for definition in Dictionary(s, 5).meanings():
            count += 1
            embed.add_field(name = empty_char, value = f"{count}. {definition}", inline=False)
        if count == 0: 
            embed = urbandefine(s)
        await message.channel.send(embed=embed)

    #urban dictionary
    elif message.content.lower().startswith('urban') or message.content.lower().startswith('!urban'):
        embed = urbandefine(removeCommand(message.content))
        await message.channel.send(embed=embed)

    #wolfram alpha
    elif message.content.lower().startswith('wolf'):
        try:
            s = removeCommand(message.content)
            results = wolfram.query(s)
            embed = discord.Embed(color=0x03c6fc, title=f'{s.title()}')
            for pod in results.pods:
                title = pod.title
                description = ''
                for sub in pod.subpods:
                    if 'plot' in title.lower():
                        embed.set_image(url=sub['img']['@src'])
                    if sub.plaintext == None: continue
                    else:
                        description += sub.plaintext + '\n'
                if description == '': continue
                if 'result' in title.lower() or 'solutions' in title.lower():
                    description = '`' + description + '`'
                embed.add_field(name=title, value=description, inline=False)
            await message.channel.send(embed=embed)
        except:
            await message.channel.send("idk man")

    elif message.content.lower().startswith('!search'):
        query = removeCommand(message.content)
        params = {"q": query, "tbm": "isch", "api_key": serpapi}
        dict = GoogleSearch(params).get_dict()
        index = random.randint(0, 5)
        try: link = dict['images_results'][index]['thumbnail']
        except: link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Twemoji_1f4a9.svg/176px-Twemoji_1f4a9.svg.png'
        embed = discord.Embed(color=0x03c6fc, title=f'{query.capitalize()}', 
                              description=f"[Google]({dict['search_information']['menu_items'][0]['link']})")
        embed.set_image(url=link)
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('!ascii'):
        s = removeCommand(message.content).split()
        if s[-1] in 'smallmediumlarge': size=s.pop()
        else: size='random'
        await message.channel.send('```' + ascii(' '.join(s), size) + '```')


#snipe (for deleted messages)
@client.event
async def on_message_delete(message):
    if message.attachments != []:
        snipe_content[message.channel.id] = message.attachments[0].url
    else:
        snipe_content[message.channel.id] = message.content.lower()
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
            if after.attachments != []:
                embed=discord.Embed(color=0x03c6fc)
                embed.set_image(url=after.attachments[0].url)
            else:
                embed=discord.Embed(color=0x03c6fc, description=after.content)
            embed.set_author(name=after.author.display_name, icon_url=after.author.avatar)
            embed.add_field(name=empty_char, value=f"[Jump to Message]({after.jump_url})")
            await client.get_channel(pins['to'][pins['from'].index(channel.id)]).send(embed=embed)
            await after.unpin()


client.run(token)
