from pokedex import pokedex
import random
pokedex = pokedex.Pokedex()
pokemon = pokedex.get_pokemon_by_number(random.randint(1,807))[0]
print(pokemon['name'])


#html session stuff that didn't work
# from requests_html import HTMLSession
# URL = "http://toastybot.com/inventory?id=177962211841540097&name=AndrewYu&avatar=https://cdn.discordapp.com/avatars/177962211841540097/891d6c6089bb63597a9d978054ee500a.webp"
# session = HTMLSession()
# r = session.get(URL)
# r.html.render()
# print(r.html.text)