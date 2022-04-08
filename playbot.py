import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import urllib.request
import urllib.parse
import pafy
import re

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
client = commands.Bot(command_prefix='!')
queues = {}
key_words = {'good bot': 'Why thank you,', 'bad bot': "I'm sorry. I'll do better next time,"}

def check_queue(ctx, id):
  voice_check = discord.utils.get(client.voice_clients, guild=ctx.guild)

  if queues[id] != []:
    voice = ctx.guild.voice_client
    source = queues[id].pop(0)
    player = voice.play(source)

  if not voice_check.is_playing():
    voice.play(source)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type **!helpme**")

@client.command()
async def helpme(ctx):
  with open('help.txt') as f:
    await ctx.send(f.read())

@client.command()
async def join(ctx):
    if(ctx.author.voice):
      channel = ctx.message.author.voice.channel
      voice = await channel.connect()

    else:
      await ctx.send("You must first join a voice channel")

@client.command()
async def leave(ctx):
    if(ctx.voice_client):
      await ctx.guild.voice_client.disconnect()
      await ctx.send("I have left the voice channel")

    else:
      await ctx.send("I am not in a voice channel, ya dingus")

@client.command()
async def pause(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

  if voice.is_playing():
    voice.pause()
    await ctx.send("Audio paused")

  else: 
    await ctx.send("There is no audio being played")

@client.command()
async def resume(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

  if voice.is_paused():
    voice.resume()
    await ctx.send("Audio resumed")

  else: 
    await ctx.send("There is no currently playing audio")

@client.command()
async def stop(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
  voice.stop()
  await ctx.send(f"Current song stopped")

@client.command()
async def play(ctx, song):
  if ctx.message.author.voice == None:
    await ctx.send("No Voice Channel", "You need to be in a voice channel to use this command!", ctx.author)
    return

  voice = ctx.guild.voice_client
  play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
  
  if not play_check.is_playing():
    query_stringyt = urllib.parse.urlencode({"search_query" : song})
    html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
    search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
    await ctx.send(f"Now playing: http://www.youtube.com/watch?v={search_resultsyt[0]}")

    newsong = pafy.new(search_resultsyt[0]) 
    audio = newsong.getbestaudio() 
    newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
    voice.play(newsource, after=lambda x=None: check_queue(ctx, ctx.message.guild.id)) 

  else:
    await ctx.send('There is a song currently playing.\n To add something to your queue, use the **!queue** command.\n To skip to the next song in queue, use the **!skip** command')

@client.command()
async def queue(ctx, song):
  voice = ctx.guild.voice_client
  query_queue = urllib.parse.urlencode({"search_query" : song})
  html_queue = urllib.request.urlopen("https://www.youtube.com/results?"+query_queue)
  results_queue = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_queue.read().decode())
  next_in_queue = pafy.new(results_queue[0]) 
  audio_queue = next_in_queue.getbestaudio() 
  queued_song = FFmpegPCMAudio(audio_queue.url, **FFMPEG_OPTIONS)

  guild_id = ctx.message.guild.id

  if guild_id in queues:
    queues[guild_id].append(queued_song)
  
  else:
    queues[guild_id] = [queued_song]
  
  await ctx.send(f"Next in queue: http://www.youtube.com/watch?v={results_queue[0]}")

@client.command()
async def skip(ctx):
  if len(queues) != 0:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    check_queue(ctx, ctx.message.guild.id)

  else:
    await ctx.send("Can't skip because there's no song in queue")

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