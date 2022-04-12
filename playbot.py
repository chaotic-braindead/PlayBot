from ast import alias
from calendar import c
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
from lyrics_extractor import SongLyrics

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
client = commands.Bot(command_prefix='!')
queues = {}
titles = []
titles_on_song_command = []
author_not_in_voice_channel = "You're not in a voice channel! Having trouble? Use the **!helpme** command."
bot_not_in_voice_channel = "I am not in a voice channel! Having trouble? Use the **!helpme** command."
key_words = {'good bot': 'Why thank you,', 'bad bot': "I'm sorry. I'll do better next time,"}

def add_to_queue(ctx, queued_song, song_title):
    guild_id = ctx.message.guild.id

    if guild_id in queues:
        queues[guild_id].append(queued_song)
        titles.append(song_title)
    else:
        queues[guild_id] = [queued_song]
        titles.append(song_title)

def add_to_now_playing(song_title, status):
    if '!q' in status:
        titles_on_song_command.append(song_title)
    elif "!skip" in status:
        titles_on_song_command.pop(0)

def play_song(ctx, song_source, song_title, final_link):
    voice = ctx.guild.voice_client
    channel = client.get_channel(961916690508161044)
    client.loop.create_task(channel.send(f"Now playing: **{song_title}\n{final_link}**"))
    voice.play(song_source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))

def check_queue(ctx, id):
  try:
    voice_check = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if queues[id] != []:
      time.sleep(1)
      voice = ctx.guild.voice_client
      voice.stop()
      source = queues[id].pop(0)
      channel = client.get_channel(961916690508161044)
      voice.play(source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))
      if len(titles) != 0:
        titles.pop(0)
        titles_on_song_command.pop(0)
        client.loop.create_task(channel.send(f"Now playing: **{titles_on_song_command[0]}**"))
      else:
        pass

  except KeyError:
    try:
      titles_on_song_command.pop(0)
      source = queues[id].pop(0)
      channel = client.get_channel(961916690508161044)
      client.loop.create_task(channel.send(f"Song queue finished."))

    except (IndexError, KeyError):
      channel = client.get_channel(961916690508161044)
      client.loop.create_task(channel.send(f"Song queue finished."))

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game('!helpme || @raffy'))
    print(f'Logged in as {client.user}')

@client.command(help='Say hello to PlayBot!')
async def hello(ctx):
    await ctx.reply(f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type **!helpme**", mention_author=False)

@client.command(help='Shows the title of the current song playing')
async def now(ctx):
  voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
  if ctx.author.voice:
    if voice.is_playing() or voice.is_paused():
      await ctx.send(f"Now playing: **{titles_on_song_command[0]}**")
    else:
      await ctx.send(f"No song is playing")

  else:
      await ctx.reply(author_not_in_voice_channel)

@client.command(help='Lets me tell you programming jokes')
async def joke(ctx):
  joke = pyjokes.get_joke()
  await ctx.send(joke)

@client.command(help='Lets me tell you something about any topic (sometimes inaccurate!)')
async def summary(ctx, *args):
  topic = ""

  for arg in args:
    topic += arg 

  info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
  await ctx.send(info)

@client.command(help='Another help function')
async def helpme(ctx):
  with open(r'C:\Users\raf\Desktop\Github\PlayBot\help.txt') as f:
    await ctx.send(f.read())

@client.command(aliases=['start'], help='Lets me join your current voice channel')
async def join(ctx):
     user = ctx.message.author
     vc = user.voice.channel

     if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      voice = await channel.connect()
      await ctx.send(f"Joined **{channel}**")

     else:
      await ctx.reply(author_not_in_voice_channel)

    #   await ctx.send(f"Joined **{channel}**")
    # else:
    #   await ctx.reply(author_not_in_voice_channel)

@client.command(help='Lets me leave the voice channel')
async def leave(ctx):
    if ctx.voice_client:
      await ctx.guild.voice_client.disconnect()
      await ctx.send("I have left the voice channel")
    else:
      await ctx.reply(bot_not_in_voice_channel)

@client.command(help='Pauses the current song')
async def pause(ctx):
  if not ctx.voice_client:
    await ctx.reply(bot_not_in_voice_channel)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
      voice.pause()
      await ctx.send("Song paused")
    else: 
      await ctx.send("There is no song being played")

  else:
    await ctx.reply(author_not_in_voice_channel)

@client.command(aliases=['continue', 'res'], help='Resumes the paused song')
async def play(ctx):
  if not ctx.voice_client:
    await ctx.reply(bot_not_in_voice_channel)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_paused():
      voice.resume()
      await ctx.send("Song resumed")
    else: 
      await ctx.send("There is no currently playing audio")

  else:
    await ctx.reply(author_not_in_voice_channel)

@client.command(aliases=['next'], help='Skip to the next song in your queue')
async def skip(ctx):
  if not ctx.voice_client:
    await ctx.reply(bot_not_in_voice_channel)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
      voice.stop()
    else:
      await ctx.reply(f"Can't skip because no song is playing")

  else:
    await ctx.reply(author_not_in_voice_channel)
    
@client.command(help='Lets me play a song in your current voice channel')
async def song(ctx, *args):
  play_name = ""

  for arg in args:
    play_name += f"{arg} "
  
  if not ctx.voice_client:
    if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      titles_on_song_command.clear()
      titles.clear()
      voice_connect = await channel.connect()
      await ctx.send(f"Joined **{channel}**")  

    else:
      await ctx.reply(author_not_in_voice_channel)

  voice = ctx.guild.voice_client
  play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
  
  if not play_check.is_playing():
    if 'https://www.youtube.com/' not in play_name:
      query_stringyt = urllib.parse.urlencode({"search_query" : play_name + 'audio'})
      html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
      search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
      
      i = 0
      newsong = pafy.new(search_resultsyt[i]) 
      if newsong.length >= 600:
        i += 1

      newsong = pafy.new(search_resultsyt[i])
      audio = newsong.getbestaudio() 
      newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
      titles_on_song_command.insert(0, newsong.title)

      time.sleep(1.25)
      
      final_link = f"https://www.youtube.com/watch?v={search_resultsyt[i]}"
      
      status = '!song'
      add_to_now_playing(newsong.title, status)
      play_song(ctx, newsource, newsong.title, final_link)

    elif 'https://www.youtube.com/' in play_name:
      yt_link = pafy.new(play_name) 
      audio = yt_link.getbestaudio() 
      yt_link_play = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
      titles_on_song_command.insert(0, yt_link.title)

      time.sleep(1.25)
      status = '!song'
      add_to_now_playing(yt_link.title, status)
      play_song(ctx, yt_link_play, yt_link.title, play_name)

  else:
    await ctx.reply("There is a song currently playing. To add a song to a queue, use the **!q** command. To skip to the next queued song, use the **!skip** command.")
    
@client.command(aliases=['queue','add'], help='Adds a song to the queue ')
async def q(ctx, *args):
  q_name = ""

  for arg in args:
    q_name += f"{arg} "

  if not ctx.voice_client:
    await ctx.send(bot_not_in_voice_channel)
  else:
    if ctx.author.voice:
      voice_status = discord.utils.get(client.voice_clients, guild=ctx.guild)

      if len(titles) < 20:
        
        if 'https://www.youtube.com/' not in q_name:
          voice = ctx.guild.voice_client
          query_queue = urllib.parse.urlencode({"search_query" : q_name+'audio'})
          html_queue = urllib.request.urlopen("https://www.youtube.com/results?"+query_queue)
          results_queue = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_queue.read().decode())

          next_in_queue = pafy.new(results_queue[0]) 
          audio_queue = next_in_queue.getbestaudio() 
          queued_song = FFmpegPCMAudio(audio_queue.url, **FFMPEG_OPTIONS)
          link = f'https://www.youtube.com/watch?v={results_queue[0]}'
          status = '!q'
          
          add_to_queue(ctx, queued_song, next_in_queue.title)
          add_to_now_playing(next_in_queue.title, status)

          if not voice_status.is_playing():
            titles.pop(0)
            play_song(ctx, queued_song, next_in_queue.title, link)
          else:
            await ctx.send(f"Added to queue: **{next_in_queue.title}**\nhttps://www.youtube.com/watch?v={results_queue[0]}")
            songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
            str = '\n'.join(songs)
            if str != '':
              await ctx.send(f"**Queued songs**:\n{str} ")
            else:
              await ctx.send(f"**Queued songs**: None")

          
        elif 'https://www.youtube.com/' in q_name:
          yt_new_queue = pafy.new(q_name) 
          yt_audio_queue = yt_new_queue.getbestaudio() 
          yt_queued_song = FFmpegPCMAudio(yt_audio_queue.url, **FFMPEG_OPTIONS)
          
          status = '!q'
          
          add_to_queue(ctx, yt_queued_song, yt_new_queue.title)
          add_to_now_playing(yt_new_queue.title, status)

          songs2 = list(f'• {titles[i]}\n' for i in range(0,len(titles)))
          str2 = '\n'.join(songs2)
          
          if not voice_status.is_playing():
            titles.pop(0)
            play_song(ctx, yt_queued_song, yt_new_queue.title, "")

          else:

            await ctx.send(f"Added to queue: **{yt_new_queue.title}**")
            await ctx.send(f"**Queued songs**:\n{str2} ")

          
   
      else:
        await ctx.send(f"Reached maximum queue limit")
    else:
      await ctx.reply(author_not_in_voice_channel)

@client.command(aliases=['end', 'quit'], help='Stops current song and clears queue')
async def stop(ctx):
  if not ctx.voice_client:
    await ctx.reply(bot_not_in_voice_channel)

  if ctx.author.voice:
      voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

      if voice.is_playing() or voice.is_paused():
        # titles_on_song_command.pop(0)
        queues[ctx.message.guild.id].clear()
        titles.clear()
        titles_on_song_command.clear()
        voice.stop()
        await ctx.send('Current song stopped and all queues removed')
      else:
        await ctx.send("Can't use command because no song is playing")

  else:
    await ctx.reply(author_not_in_voice_channel)

# @client.command() TODO revise clear command 
# async def clear(ctx):
#   if not ctx.voice_client:
#     await ctx.reply(bot_not_in_voice_channel)

#   if ctx.author.voice:
#       voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
#       if queues[ctx.message.guild.id] != [] and titles != []:

#         if voice.is_playing() or voice.is_paused() or not voice.is_playing():
#           # titles_on_song_command.pop(0)
#           queues[ctx.message.guild.id].clear()
#           titles.clear()
#           titles_on_song_command.clear()
#           await ctx.send('All queues removed')
          
#       elif queues[ctx.message.guild.id] == [] and titles == []:
#           await ctx.send("Can't use command because there are no more songs in queue")
      
#   else:
#     await ctx.reply(author_not_in_voice_channel)

@client.command(aliases=['remove', 'rem', 'r'], help='Lets you remove a song from the queue')
async def rq(ctx):
  if ctx.author.voice:
    if queues[ctx.message.guild.id] != [] and titles != []:
      # try:
      songs = list(f'**{i+1}** : {titles[i]}' for i in range(0, len(titles)))
      str = '\n'.join(songs)
      await ctx.send(f"Type the position of the song to remove (0 to cancel):\n{str}")
      
      def check(msg):
          return msg.author == ctx.author and msg.channel == ctx.channel and int(msg.content) in [i for i in range(0,20)]

      msg = await client.wait_for("message", check=check)
      if int(msg.content) != 0:
        queues[ctx.message.guild.id].pop(int(msg.content)-1)
        await ctx.send(f'Removed **{titles[int(msg.content)-1]}** from queue')
        titles.pop(int(msg.content)-1)
        titles_on_song_command.pop(int(msg.content))
        songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
        str = '\n'.join(songs)
        if str != '':
          await ctx.send(f"**Queued songs**:\n{str} ")
        else:
          await ctx.send(f"**Queued songs**: None")

      else:
        await ctx.send(f"No queue removed")

      # except IndexError:
      #   queues[ctx.message.guild.id].pop(len(queues[int(msg.content)]))
      #   await ctx.send(f'Removed **{titles[int(msg.content)-1]}** from queue')
      #   titles.pop()
      #   await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")

    else:
      await ctx.send("No more queues to remove")

  else:
    await ctx.reply(author_not_in_voice_channel)

@client.command(aliases=['list', 'sq', 'vq', 'view'], help='Views queued songs')
async def qs(ctx):
  if ctx.voice_client:
    if ctx.author.voice:
      songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
      str = '\n'.join(songs)
      if str != '':
        await ctx.send(f"**Queued songs**:\n{str} ")
      else:
        await ctx.send(f"**Queued songs**: None")
    else:
      await ctx.reply(author_not_in_voice_channel)
  else:
    await ctx.reply(bot_not_in_voice_channel)

@client.command()
async def previous(ctx): #TODO goes back to previous song
  pass

@client.command(help='Shows lyrics of current song playing (sometimes inaccurate)')
async def lyrics(ctx):
  if ctx.voice_client:
    if ctx.author.voice:
      voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

      if voice.is_playing() or voice.is_paused():
        
        extract_lyrics = SongLyrics(os.environ.get("GCS_API_KEY"), os.environ.get("GCS_ENGINE_ID"))
        lyrics = extract_lyrics.get_lyrics(titles_on_song_command[0])
        lyr = lyrics['lyrics'].replace('\\n', '\n')

        if len(lyr)+len(titles_on_song_command[0]) <= 2000:
          await ctx.send(f"**{titles_on_song_command[0]}**\n{lyr}")
        else:
          lyr1 = lyr[0:len(lyr)//2]
          lyr2 = lyr[len(lyr)//2:]

          if len(lyr2) > 2000:
            lyr3 = lyr2[0:len(lyr2)//2]
            lyr4 = lyr2[len(lyr2)//2:]
            await ctx.send(f"**{titles_on_song_command[0]}**\n{lyr1}")
            await ctx.send(lyr3)
            await ctx.send(lyr4)

          else:
            await ctx.send(f"**{titles_on_song_command[0]}**\n{lyr1}")
            await ctx.send(lyr2)
          
      else:
        await ctx.send("There is no song playing")

    else:
      await ctx.reply(author_not_in_voice_channel)
  else:
    await ctx.reply(bot_not_in_voice_channel)


@client.command(help='Deletes a specified number of messages in a channel')
async def cls(ctx, *args:int):
  num = 1
  for arg in args:
    num += arg
  await ctx.channel.purge(limit=num)
  #  await ctx.send(f"Type the position of the song to remove (0 to cancel):\n{str}")
  #  def check(msg):
  #       return msg.author == ctx.author and msg.channel == ctx.channel and int(msg.content) in [i for i in range(0,20)]
   
  #  msg = await client.wait_for("message", check=check)
@client.event
async def on_message(message):
    msg = message.content.lower()
    mention = message.author.mention

    for _, key in enumerate(key_words.keys()):
      if key in msg:
        await message.channel.send(f'{key_words[key]} {mention}!')

    await client.process_commands(message)

@lyrics.error
async def info_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send('Lyrics are currently unavailable')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply('Invalid command. Having trouble? Use the **!helpme** command.')

client.run(os.environ.get('DISCORD'))