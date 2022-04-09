from ast import alias
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import urllib.request
import urllib.parse
import pafy
import re
import time
import pyjokes
import wikipedia
import urllib
import json

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
client = commands.Bot(command_prefix='!')
queues = {}
titles = []
key_words = {'good bot': 'Why thank you,', 'bad bot': "I'm sorry. I'll do better next time,"}

def check_queue(ctx, id):
  voice_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
  
  if len(queues[id]) != 0:
    
    time.sleep(1.5)
    voice = ctx.guild.voice_client
    source = queues[id].pop(0)
    player = voice.play(source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))
    
def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client.is_connected()

def scrape_info(url):
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % url}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data['title']

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game('!helpme || @raffy'))
    print(f'Logged in as {client.user}')

@client.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type **!helpme**")

@client.command()
async def joke(ctx):
  joke = pyjokes.get_joke()
  await ctx.send(joke)

@client.command()
async def summary(ctx, *args):
  topic = ""

  for arg in args:
    topic += arg 

  info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
  await ctx.send(info)

@client.command()
async def helpme(ctx):
  with open(r'C:\Users\raf\Desktop\Github\PlayBot\help.txt') as f:
    await ctx.send(f.read())

@client.command(aliases=['start'])
async def join(ctx):
    if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      voice = await channel.connect()
      await ctx.send(f"Joined **{channel}**")

    else:
      await ctx.send(f"You must first join a voice channel, {ctx.author.mention}!")

@client.command(aliases=['end','done'])
async def leave(ctx):
    if ctx.voice_client:
      await ctx.guild.voice_client.disconnect()
      await ctx.send("I have left the voice channel")

    else:
      await ctx.send(f"I am not in a voice channel, {ctx.author.mention}")

@client.command()
async def pause(ctx):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
      voice.pause()
      await ctx.send("Song paused")

    else: 
      await ctx.send("There is no song being played")

  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command(aliases=['continue', 'res'])
async def play(ctx):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_paused():
      voice.resume()
      await ctx.send("Song resumed")

    else: 
      await ctx.send("There is no currently playing audio")
  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command()
async def stop(ctx):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    await ctx.send(f"Current song stopped")
  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")
    
@client.command()
async def song(ctx, *args):
  play_name = ""

  for arg in args:
    play_name += arg 

  if not ctx.voice_client and ctx.author.voice:
    channel = ctx.message.author.voice.channel
    voice_connect = await channel.connect()
    await ctx.send(f"Joined **{channel}**")
    
  if not ctx.author.voice:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

  else:
    time.sleep(1.5)
    voice = ctx.guild.voice_client
    play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
    
    if not play_check.is_playing():
      query_stringyt = urllib.parse.urlencode({"search_query" : play_name})
      html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
      search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
      
      i = 0
      newsong = pafy.new(search_resultsyt[i]) 
      if newsong.length >= 600:
        i += 1
      newsong = pafy.new(search_resultsyt[i])
      audio = newsong.getbestaudio() 
      newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
      time.sleep(1)
      # print(ctx.message.guild.id)
      voice.play(newsource, after=lambda x=None: check_queue(ctx, ctx.message.guild.id)) 
      final_link = f"http://www.youtube.com/watch?v={search_resultsyt[i]}"
      await ctx.send(f"Now playing: **{scrape_info(search_resultsyt[i])}**\n{final_link}")
      
    else:
      await ctx.send('There is a song currently playing.\nTo __add something__ to your queue, use the **!q** command.\nTo __skip to the next song__ in queue, use the **!skip** command')
   
@client.command(aliases=['queue','add'])
async def q(ctx, *args):
  q_name = ""

  for arg in args:
    q_name += arg 

  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")
  else:
    if ctx.author.voice:
      voice = ctx.guild.voice_client
      query_queue = urllib.parse.urlencode({"search_query" : q_name})
      html_queue = urllib.request.urlopen("https://www.youtube.com/results?"+query_queue)
      results_queue = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_queue.read().decode())

      i = 0
      next_in_queue = pafy.new(results_queue[i]) 
      if next_in_queue.length >= 600:
        i += 1
      next_in_queue = pafy.new(results_queue[i]) 
      audio_queue = next_in_queue.getbestaudio() 
      queued_song = FFmpegPCMAudio(audio_queue.url, **FFMPEG_OPTIONS)

      guild_id = ctx.message.guild.id

      if guild_id in queues:
        queues[guild_id].append(queued_song)
        titles.append(scrape_info(results_queue[i]))
      
      else:
        queues[guild_id] = [queued_song]
        titles.append(scrape_info(results_queue[i]))
      
      await ctx.send(f"Next in queue: **{scrape_info(results_queue[i])}**\nhttp://www.youtube.com/watch?v={results_queue[i]}")
      await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")
    else:
      await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command(aliases=['next'])
async def skip(ctx):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
      voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
      voice.stop()
      check_queue(ctx, ctx.message.guild.id)

  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command(aliases=['remove', 'rem'])
async def rq(ctx):
  if ctx.author.voice:
    if queues[ctx.message.guild.id] != [] and titles != []:
      try:
        queues[ctx.message.guild.id].pop(len(queues[ctx.message.guild.id])-1)
        await ctx.send(f'Removed **{titles[-1]}** from queue')
        titles.pop()
        await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")
      except IndexError:
        queues[ctx.message.guild.id].pop(len(queues[ctx.message.guild.id]))
        await ctx.send(f'Removed **{titles[-1]}** from queue')
        titles.pop()
        await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")
    else:
      await ctx.send("No more queues to remove")

@client.command(aliases=['list', 'sq', 'vq'])
async def qs(ctx):
  await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")
@client.command()
async def previous(ctx): #TODO goes back to previous song
  pass

@client.event
async def on_message(message):
    msg = message.content.lower()
    mention = message.author.mention

    for _, key in enumerate(key_words.keys()):
      if key in msg:
        await message.channel.send(f'{key_words[key]} {mention}!')

    await client.process_commands(message)

    
client.run(os.environ.get('DISCORD'))