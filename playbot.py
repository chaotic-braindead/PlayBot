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
client = commands.Bot(command_prefix=';')
queues = {}
titles = []
titles_on_song_command = []
author_not_in_voice_channel = "You're not in a voice channel! Having trouble? Use the `;helpme` command."
bot_not_in_voice_channel = "I am not in a voice channel! Having trouble? Use the `;helpme` command."
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
    embed = discord.Embed(description = f"Now playing: **{song_title}\n{final_link}**", color = discord.Colour.red())
    client.loop.create_task(channel.send(embed=embed))
    # client.loop.create_task(channel.send(f"Now playing: **{song_title}\n{final_link}**"))
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
        embed = discord.Embed(description = f"Now playing: **{titles_on_song_command[0]}**", color = discord.Colour.red())
        client.loop.create_task(channel.send(embed=embed))
      else:
        pass

  except KeyError:
    try:
      titles_on_song_command.pop(0)
      source = queues[id].pop(0)
      channel = client.get_channel(961916690508161044)
      embed2 = discord.Embed(description = f"Song queue finished.", color = discord.Colour.red())
      client.loop.create_task(channel.send(embed=embed2))

    except (IndexError, KeyError):
      channel = client.get_channel(961916690508161044)
      embed3 = discord.Embed(description = f"Song queue finished.", color = discord.Colour.red())
      client.loop.create_task(channel.send(embed=embed3))

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game('!helpme | @raffy'))
    print(f'Logged in as {client.user}')

@client.command(help='Say hello to PlayBot!')
async def hello(ctx):
    embed = discord.Embed(description =f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type `;helpme`", color = discord.Colour.red())
    await ctx.reply(embed=embed)

@client.command(help='Shows the title of the current song playing')
async def now(ctx):
  voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
  if ctx.author.voice:
    if voice.is_playing() or voice.is_paused():
      embed = discord.Embed(description =f"Now playing: **{titles_on_song_command[0]}**", color = discord.Colour.red())
      await ctx.send(embed=embed)
    else:
      embed2 = discord.Embed(description =f"No song is playing", color = discord.Colour.red())
      await ctx.send(embed=embed2)
  else:
      embed3 = discord.Embed(description =author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.reply(embed=embed3)

@client.command(help='Lets me tell you programming jokes')
async def joke(ctx):
  joke = pyjokes.get_joke()
  embed = discord.Embed(description =joke, color = discord.Colour.red())
  await ctx.send(embed=embed)

@client.command(help='Lets me tell you something about any topic (sometimes inaccurate!)')
async def summary(ctx, *args):
  topic = ""

  for arg in args:
    topic += arg 

  info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
  img = wikipedia.page(topic)
  url = img.images[0]
  embed = discord.Embed(description =info, color = discord.Colour.red())
  embed.set_thumbnail(url=url)
  await ctx.send(embed=embed)

@client.command(help='Another help function')
async def helpme(ctx):
  with open(r'C:\Users\raf\Desktop\Github\PlayBot\help.txt') as f:
    embed = discord.Embed(title = '__List of commands__', description = f.read(), color = discord.Colour.red())
    await ctx.send(embed=embed)

@client.command(aliases=['start'], help='Lets me join your current voice channel')
async def join(ctx):
     user = ctx.message.author
     vc = user.voice.channel

     if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      voice = await channel.connect()
      embed = discord.Embed(description = f'Joined **{channel}**', color = discord.Colour.red())
      await ctx.send(embed=embed)

     else:
      embed2 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.send(embed=embed2) 

    #   await ctx.send(f"Joined **{channel}**")
    # else:
    #   await ctx.reply(author_not_in_voice_channel)

@client.command(help='Lets me leave the voice channel')
async def leave(ctx):
    if ctx.voice_client:
      channel = ctx.message.author.voice.channel
      await ctx.guild.voice_client.disconnect()
      embed = discord.Embed(description = f'Left **{channel}**', color = discord.Colour.red())
      await ctx.send(embed=embed)
    else:
      failed = discord.Embed(description =bot_not_in_voice_channel, color = discord.Colour.red())
      await ctx.send(embed=failed)

@client.command(help='Pauses the current song')
async def pause(ctx):
  if not ctx.voice_client:
    not_in_voice =  discord.Embed(description =bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=not_in_voice)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
      voice.pause()
      embed = discord.Embed(description = f'Paused **{titles_on_song_command[0]}**', color = discord.Colour.red())
      await ctx.send(embed=embed)
    else: 
      failed = discord.Embed(description ='There is no song being played', color = discord.Colour.red())
      await ctx.send(embed=failed)

  else:
    not_in_voice =  discord.Embed(description =author_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=not_in_voice)

@client.command(aliases=['continue', 'res'], help='Resumes the paused song')
async def play(ctx):
  if not ctx.voice_client:
    not_in_voice =  discord.Embed(description =bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=embed)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_paused():
      voice.resume()
      embed =  discord.Embed(description =f'Resumed **{titles_on_song_command[0]}**', color = discord.Colour.red())
      await ctx.send(embed=embed)
    else: 
      nonplay =  discord.Embed(description ='There is no audio currently playing', color = discord.Colour.red())
      await ctx.send(embed=nonplay)

  else:
    failed =  discord.Embed(description =author_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=failed)

@client.command(aliases=['next'], help='Skip to the next song in your queue')
async def skip(ctx):
  if not ctx.voice_client:
    not_in_voice =  discord.Embed(description =bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=not_in_voice)

  if ctx.author.voice:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
      voice.stop()
    else:
      not_in_voice =  discord.Embed(description ="Can't skip because no song is playing", color = discord.Colour.red())
      await ctx.reply(embed=not_in_voice)

  else:
    not_in_voice =  discord.Embed(description =author_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=not_in_voice)

@client.command(help = 'Search for a specific song')
async def search(ctx, *args):
  play_name = ""

  for arg in args:
    play_name += f"{arg} "
  
  if not ctx.voice_client:
    if ctx.author.voice:
      channel = ctx.message.author.voice.channel
      titles_on_song_command.clear()
      titles.clear()
      voice_connect = await channel.connect()
      embed = discord.Embed(description = f'Joined **{channel}**', color = discord.Colour.red())
      await ctx.send(embed=embed)

    else:
      embed2 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.send(embed=embed2)

  voice = ctx.guild.voice_client
  play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
  query_stringyt = urllib.parse.urlencode({"search_query" : play_name})
  html_contentyt = urllib.request.urlopen("https://www.youtube.com/results?"+query_stringyt)
  search_resultsyt = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_contentyt.read().decode())
  list1 = []
  for i in range(0, 10):
    try:
        newsong = pafy.new(search_resultsyt[i])
        list1.append(f"**{i+1}** : {newsong.title} **[{newsong.duration}]**")
    except ValueError:
        continue

  results = '\n\n'.join(list1)

  embed = discord.Embed(description=f'**Type the number of your choice. Type 0 to cancel.**\n\n{results}', color = discord.Colour.red())
  await ctx.send(embed=embed)

  def check(msg):
    return msg.author == ctx.author and msg.channel == ctx.channel and int(msg.content) in [i for i in range(len(list1))]

  msg = await client.wait_for("message", check=check)
  if int(msg.content) != 0:
    newsong = pafy.new(search_resultsyt[int(msg.content)-1])
    audio = newsong.getbestaudio() 
    newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
    final_link = f"https://www.youtube.com/watch?v={search_resultsyt[i]}"
    
    if not play_check.is_playing() and not play_check.is_paused():
        status = '!song'
        titles_on_song_command.insert(0, newsong.title)
        add_to_now_playing(newsong.title, status)
        play_song(ctx, newsource, newsong.title, final_link)
    else:
        status = '!q'
        embed2 = discord.Embed(description = f"Added to queue: **{newsong.title}**", color = discord.Colour.red())
        await ctx.send(embed=embed2)
        add_to_queue(ctx, newsource, newsong.title)
        add_to_now_playing(newsong.title, status)
        songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
        string = '\n'.join(songs)
        if string != '':
            embed3 = discord.Embed(title= '**Queued songs**:', description =string, color = discord.Colour.red())
            await ctx.send(embed=embed3)
        else:
            embed4 = discord.Embed(title=f"**Queued songs**:", description =  "None", color = discord.Colour.red())
            await ctx.send(embed=embed4)


  else:
    embed2 = discord.Embed(description = 'Cancelled search', color=discord.Colour.red())
    await ctx.send(embed=embed2)

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
      embed = discord.Embed(description = f'Joined **{channel}**', color = discord.Colour.red())
      await ctx.send(embed=embed)

    else:
      embed2 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.send(embed=embed2)

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
      play_song(ctx, yt_link_play, yt_link.title, "")

  else:
    embed = discord.Embed(description = "There is a song currently playing. To add a song to a queue, use the `;q` command. To skip to the next queued song, use the `;skip` command.", color = discord.Colour.red())
    await ctx.send(embed=embed)
    
@client.command(aliases=['queue','add'], help='Adds a song to the queue ')
async def q(ctx, *args):
  q_name = ""

  for arg in args:
    q_name += f"{arg} "

  if not ctx.voice_client:
    embed = discord.Embed(description =bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.send(embed=embed)
  else:
    if ctx.author.voice:
      voice_status = discord.utils.get(client.voice_clients, guild=ctx.guild)

      if len(titles) < 20:
        
        if 'https://www.youtube.com/' not in q_name:
          voice = ctx.guild.voice_client
          query_queue = urllib.parse.urlencode({"search_query" : q_name+'audio'})
          html_queue = urllib.request.urlopen("https://www.youtube.com/results?"+query_queue)
          results_queue = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_queue.read().decode())
          i = 0
          next_in_queue = pafy.new(results_queue[i])
          if next_in_queue.length >= 600:
            i += 1
          next_in_queue = pafy.new(results_queue[i])
          audio_queue = next_in_queue.getbestaudio() 
          queued_song = FFmpegPCMAudio(audio_queue.url, **FFMPEG_OPTIONS)
          link = f'https://www.youtube.com/watch?v={results_queue[0]}'
          status = '!q'
          
          add_to_queue(ctx, queued_song, next_in_queue.title)
          add_to_now_playing(next_in_queue.title, status)

          if not voice_status.is_playing() and not voice_status.is_paused():
            titles.pop(0)
            play_song(ctx, queued_song, next_in_queue.title, link)
          else:
            embed2 = discord.Embed(description = f"Added to queue: **{next_in_queue.title}**\nhttps://www.youtube.com/watch?v={results_queue[0]}", color = discord.Colour.red())
            await ctx.send(embed=embed2)
            songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
            str = '\n'.join(songs)
            if str != '':
              embed3 = discord.Embed(title=f"**Queued songs**:",description =str, color = discord.Colour.red())
              await ctx.send(embed=embed3)
              
            else:
              embed4 = discord.Embed(title=f"**Queued songs**:",description = f"**Queued songs**: None", color = discord.Colour.red())
              await ctx.send(embed=embed4)
          
        elif 'https://www.youtube.com/' in q_name:
          yt_new_queue = pafy.new(q_name) 
          yt_audio_queue = yt_new_queue.getbestaudio() 
          yt_queued_song = FFmpegPCMAudio(yt_audio_queue.url, **FFMPEG_OPTIONS)
          
          status = '!q'
          
          add_to_queue(ctx, yt_queued_song, yt_new_queue.title)
          add_to_now_playing(yt_new_queue.title, status)

          songs2 = list(f'• {titles[i]}' for i in range(0,len(titles)))
          str2 = '\n'.join(songs2)
          
          if not voice_status.is_playing() and not voice_status.is_paused():
            titles.pop(0)
            play_song(ctx, yt_queued_song, yt_new_queue.title, "")

          else:
            embed5 = discord.Embed(title= 'Added to queue:',description = f"**{yt_new_queue.title}**", color = discord.Colour.red())
            await ctx.send(embed=embed5)
            embed8 = discord.Embed(title="**Queued songs**:",description=str2, color=discord.Colour.red())
            await ctx.send(embed=embed8)
      else:
        embed6 = discord.Embed(description = 'Reached maximum queue limit', color = discord.Colour.red())
        await ctx.send(embed=embed6)
    else:
      embed7 = discord.Embed(description =author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.reply(embed=embed7)

@client.command(aliases=['end', 'quit'], help='Stops current song and clears queue')
async def stop(ctx):
  if not ctx.voice_client:
    embed = discord.Embed(description = bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.send(embed=embed)

  if ctx.author.voice:
      voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

      if voice.is_playing() or voice.is_paused():
        # titles_on_song_command.pop(0)
        queues[ctx.message.guild.id].clear()
        titles.clear()
        titles_on_song_command.clear()
        voice.stop()
        embed2 = discord.Embed(description = 'Current song stopped and all queues removed', color = discord.Colour.red())
        await ctx.send(embed=embed2)
      else:
        embed3 = discord.Embed(description = "Can't use command because no song is playing", color = discord.Colour.red())
        await ctx.send(embed=embed3)

  else:
    embed4 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=embed4)

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
      str = '\n\n'.join(songs)
      embed = discord.Embed(description=f"**Type the position of the song to remove (0 to cancel):**\n\n{str}", color = discord.Colour.red())
      await ctx.reply(embed=embed)
      
      def check(msg):
          return msg.author == ctx.author and msg.channel == ctx.channel and int(msg.content) in [i for i in range(0,20)]

      msg = await client.wait_for("message", check=check)
      if int(msg.content) != 0:
        queues[ctx.message.guild.id].pop(int(msg.content)-1)
        embed2 = discord.Embed(description = f'Removed **{titles[int(msg.content)-1]}** from queue', color = discord.Colour.red())
        await ctx.send(embed=embed2)
        titles.pop(int(msg.content)-1)
        titles_on_song_command.pop(int(msg.content))
        songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
        string = '\n'.join(songs)
        if string != '':
          embed3 = discord.Embed(title='**Queued songs**:', description=string , color = discord.Colour.red())
          await ctx.send(embed=embed3)
        else:
          embed4 = discord.Embed(title = '**Queued songs:**', description = "None", color = discord.Colour.red())
          await ctx.send(embed=embed4)

      else:
        embed5 = discord.Embed(title = f"No queue removed", color = discord.Colour.red())
        await ctx.send(embed=embed5)

      # except IndexError:
      #   queues[ctx.message.guild.id].pop(len(queues[int(msg.content)]))
      #   await ctx.send(f'Removed **{titles[int(msg.content)-1]}** from queue')
      #   titles.pop()
      #   await ctx.send(f"**Queued songs**: {list(titles[i] for i in range(0,len(titles)))}")

    else:
      embed6 = discord.Embed(description = "No more queues to remove", color = discord.Colour.red())
      await ctx.reply(embed=embed6)

  else:
    embed7 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=embed7)

@client.command(aliases=['list', 'sq', 'vq', 'view'], help='Views queued songs')
async def qs(ctx):
  if ctx.voice_client:
    if ctx.author.voice:
      songs = list(f'• {titles[i]}' for i in range(0,len(titles)))
      string = '\n'.join(songs)
      if string != '':
        embed = discord.Embed(title= '**Queued songs**:', description =string, color = discord.Colour.red())
        await ctx.send(embed=embed)
      else:
        embed2 = discord.Embed(title=f"**Queued songs**:", description =  "None", color = discord.Colour.red())
        await ctx.send(embed=embed2)
    else:
      embed3 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.reply(embed=embed3)
  else:
    embed4 = discord.Embed(description = bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.reply(embed=embed4)

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
          embed = discord.Embed(description = f"**{titles_on_song_command[0]}**\n{lyr}", color = discord.Colour.red())
          await ctx.send(embed=embed)
        else:
          lyr1 = lyr[0:len(lyr)//2]
          lyr2 = lyr[len(lyr)//2:]

          if len(lyr2) > 2000:
            lyr3 = lyr2[0:len(lyr2)//2]
            lyr4 = lyr2[len(lyr2)//2:]
            embed2 = discord.Embed(description = f"**{titles_on_song_command[0]}**\n{lyr}", color = discord.Colour.red())
            embed3 = discord.Embed(description = lyr3, color = discord.Colour.red())
            embed4 = discord.Embed(description = lyr4, color = discord.Colour.red())
            await ctx.send(embed=embed2)
            await ctx.send(embed=embed3)
            await ctx.send(embed=embed4)

          else:
            embed5 = discord.Embed(description = f"**{titles_on_song_command[0]}**\n{lyr1}", color = discord.Colour.red())
            embed6 = discord.Embed(description = f"{lyr2}", color = discord.Colour.red())
            await ctx.send(embed=embed5)
            await ctx.send(embed=embed6)
          
      else:
        embed7 = discord.Embed(description = "There is no song playing", color = discord.Colour.red())
        await ctx.send(embed=embed7)

    else:
      embed8 = discord.Embed(description = author_not_in_voice_channel, color = discord.Colour.red())
      await ctx.reply(embed=embed8)
  else:
    embed9 = discord.Embed(description = bot_not_in_voice_channel, color = discord.Colour.red())
    await ctx.send(embed=embed9)

@client.command(help='Deletes a specified number of messages in a channel')
async def cls(ctx, *args:int):
  num = 1
  for arg in args:
    num += arg
  await ctx.channel.purge(limit=num)

@client.event
async def on_message(message):
    msg = message.content.lower()
    mention = message.author.mention

    for _, key in enumerate(key_words.keys()):
      if key in msg:
        embed = discord.Embed(description = f'{key_words[key]} {mention}!', color = discord.Colour.red())
        await message.channel.send(embed=embed)
    await client.process_commands(message)

@lyrics.error
async def info_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(description = 'Lyrics are currently unavailable', color = discord.Colour.red())
        await ctx.send(embed=embed)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(description = 'Invalid command. Having trouble? Use the `;helpme` command.', color = discord.Colour.red())
        await ctx.reply(embed=embed)

client.run(os.environ.get('DISCORD'))