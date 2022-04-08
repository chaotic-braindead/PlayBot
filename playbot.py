import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import urllib.request
import urllib.parse
import pafy
import re
import time

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
client = commands.Bot(command_prefix='!')
queues = {}
key_words = {'good bot': 'Why thank you,', 'bad bot': "I'm sorry. I'll do better next time,"}

def check_queue(ctx, id):
  voice_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
  
  if len(queues[id]) != 0:
    print(len(queues[id]))
    time.sleep(1.5)
    voice = ctx.guild.voice_client
    # voice_check.stop()
    source = queues[id].pop(0)
    player = voice.play(source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))
    print(queues)
  
def remove(ctx, id):
  if len(queues[id]) != 0:
    queues[id].pop(len(queues[id])-1)
  # if not voice_check.is_playing():
  #   player = voice.play(source)
    # voice.play(source)
  
def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client.is_connected()

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
    if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      voice = await channel.connect()
      await ctx.send(f"Joined **{channel}**")

    else:
      await ctx.send(f"You must first join a voice channel, {ctx.author.mention}!")

@client.command()
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

@client.command()
async def resume(ctx):
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
async def play(ctx, song):
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
      query_stringyt = urllib.parse.urlencode({"search_query" : song})
      html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
      search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
      await ctx.send(f"Now playing: http://www.youtube.com/watch?v={search_resultsyt[0]}")

      newsong = pafy.new(search_resultsyt[0]) 
      audio = newsong.getbestaudio() 
      newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
      time.sleep(1)
      print(ctx.message.guild.id)
      time.sleep(1)
      voice.play(newsource, after=lambda x=None: check_queue(ctx, ctx.message.guild.id)) 
      
    else:
      await ctx.send('There is a song currently playing.\n To add something to your queue, use the **!q** command.\n To skip to the next song in queue, use the **!skip** command')
  
    

@client.command()
async def q(ctx, song):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
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
      print(queued_song)
    
    else:
      queues[guild_id] = [queued_song]
    
    await ctx.send(f"Next in queue: http://www.youtube.com/watch?v={results_queue[0]}")

  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command()
async def skip(ctx):
  if not ctx.voice_client:
    await ctx.send(f"I am not in a voice channel, {ctx.author.mention}! Having trouble? Use the **!helpme** command. ")

  if ctx.author.voice:
    # if len(queues) != 0:
      voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
      voice.stop()
      check_queue(ctx, ctx.message.guild.id)

    # else:
      # await ctx.send("Can't skip because there's no song in queue")

  else:
    await ctx.send(f"You're not in a voice channel, {ctx.author.mention}!")

@client.command()
async def rq(ctx):
  remove(ctx, ctx.message.guild.id)
  await ctx.send('Removed last song from queue')

@client.command()
async def previous(ctx): #TODO goes back to previous song
  pass

@client.command()
async def qremove(ctx): #TODO removes song from queue
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