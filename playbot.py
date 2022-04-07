import discord
import os
import requests
import urllib.request
import urllib.parse
import re
import time

client = discord.Client()
key_words = {'good bot': 'aww, thanks,', 'bad bot': "I'm sorry. I'll do better next time,"}

def getsong(req):
      query_stringyt = urllib.parse.urlencode({"search_query" : req})
      html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
      search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
      got_song = f"http://www.youtube.com/watch?v={search_resultsyt[0]}"

      query_stringspoti = urllib.parse.urlencode({"search_query" : req})
      html_contentspoti = urllib.request.urlopen("https://open.spotify.com/search/"+query_stringspoti)
      search_resultsspoti = re.findall(r'url\":\"?si=', html_contentspoti.read().decode())

      if search_resultsyt:
        return got_song
      if search_resultsspoti:
        return f"https://open.spotify.com/track/{search_resultsspoti[0]}"
  
def getqueue(queue): #TODO improve queue function since the whole thing sleeps when it is called
  time.sleep(5)
  return getsong(queue)
  
@client.event
async def on_ready():
  print(f'Logged on as {client.user}!')

@client.event
async def on_message(message):

  if message.author == client.user:
    return
    
  msg = message.content.lower()
  mention = message.author.mention

  if msg.startswith('!hello'):
    await message.channel.send(f'Hello {mention}!')
  
  if msg.startswith('!play'):
    req = msg[6:]
    await message.channel.send(f"Here's your song, {mention}!\n{getsong(req)}")
  
  if msg.startswith('!q'):
    queue = msg[3:]
    await message.channel.send(f"{mention}, your next in queue:\n{getqueue(queue)}")

  for _, key in enumerate(key_words.keys()):
    if key in msg:
      await message.channel.send(f'{key_words[key]} {mention}!')

# async def on_message_delete(message): TODO bot messages the author of a detected deleted message 
#   mention = message.author.mention
#   if message.author == client.user:
#     return

#   await message.channel.send(f'What are you hiding, {mention}?')
  
client.run(os.environ.get('DISCORD'))
