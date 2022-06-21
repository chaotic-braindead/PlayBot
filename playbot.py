import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import urllib.request
import urllib.parse
import pafy
import re
import pyjokes
import wikipedia
import urllib
import spoti
from lyrics_extractor import SongLyrics

client = commands.Bot(command_prefix=";")
queues = {}
titles = {}
titles_on_song_command = {}
txt_ch_and_guild_id = {}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
ERROR_MSGS = {
    1: "You're not in a voice channel! Having trouble? Use the `;helpme` command.",
    2: "I am not in a voice channel! Having trouble? Use the `;helpme` command.",
    3: "Join/create a text channel containing the word **bot** in order to play a song.",
    4: "You must switch to this text channel in order to use song commands:",
    5: "We must be in the same voice channel.",
    6: "I am already in a voice channel.",
}

KEY_WORDS = {
    "good bot": "Why thank you,",
    "bad bot": "I'm sorry. I'll do better next time,",
}

__SPOTIFY_CLIENT_ID = "38f25146e683409c8cb596834e5ca70e"
__SPOTIFY_CLIENT_SECRET = "d69916c4275a40a7bac7caeb887b93f4"


def generate_msg(msg=None, title_msg=None, colr=discord.Colour.red()):

    if not title_msg and msg:
        return discord.Embed(description=msg, color=colr)
    elif not msg and title_msg:
        return discord.Embed(title=title_msg, color=colr)
    else:
        return discord.Embed(title=title_msg, description=msg, color=colr)


def add_to_queue(ctx, queued_song, song_title):
    guild_id = ctx.channel.id

    if guild_id in queues and guild_id in titles:
        queues[guild_id].append(queued_song)
        titles[guild_id].append(song_title)
    else:
        queues[guild_id] = [queued_song]
        titles[guild_id] = [song_title]


def add_to_now_playing(ctx, song_title, status):
    if "!q" in status:
        if ctx.channel.id in titles_on_song_command:
            titles_on_song_command[ctx.channel.id].append(song_title)
        else:
            titles_on_song_command[ctx.channel.id] = [song_title]
    elif "!skip" in status:
        titles_on_song_command[ctx.channel.id].pop(0)


def play_song(ctx, song_source, song_title, final_link):
    voice = ctx.guild.voice_client
    channel = client.get_channel(ctx.channel.id)
    client.loop.create_task(
        channel.send(
            embed=generate_msg(f"🎶 Now playing: **{song_title}** 🎶\n{final_link}")
        )
    )
    voice.play(song_source, after=lambda x=None: check_queue(ctx, ctx.channel.id))


def check_queue(ctx, id):
    try:
        if queues[id]:
            # time.sleep(1)
            voice = ctx.guild.voice_client
            voice.stop()
            source = queues[id].pop(0)
            channel = client.get_channel(ctx.channel.id)
            voice.play(source, after=lambda x=None: check_queue(ctx, ctx.channel.id))
            if titles:
                titles[ctx.channel.id].pop(0)
                titles_on_song_command[ctx.channel.id].pop(0)
                client.loop.create_task(
                    channel.send(
                        embed=generate_msg(
                            f"🎶 Now playing: **{titles_on_song_command[ctx.channel.id][0]}** 🎶"
                        )
                    )
                )
    except KeyError:
        try:
            titles_on_song_command[ctx.channel.id].pop(0)
            source = queues[id].pop(0)
            channel = client.get_channel(ctx.channel.id)
            embed2 = discord.Embed(
                description=f"Song queue finished.", color=discord.Colour.red()
            )
            client.loop.create_task(channel.send(embed=embed2))

        except (IndexError, KeyError):
            channel = client.get_channel(ctx.channel.id)
            embed3 = discord.Embed(
                description=f"Song queue finished.", color=discord.Colour.red()
            )
            client.loop.create_task(channel.send(embed=embed3))


@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status.idle, activity=discord.Game(";helpme | @raffy")
    )
    print(f"Logged in as {client.user}")


@client.command(help="Say hello to PlayBot!")
async def hello(ctx):
    await ctx.reply(
        embed=generate_msg(
            f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type `;helpme`"
        )
    )


@client.command(aliases=["current"], help="Shows the title of the current song playing")
async def now(ctx):
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        await ctx.send(
            embed=generate_msg(
                f"🎶 Now playing: **{titles_on_song_command[ctx.channel.id][0]}** 🎶"
            )
        )
    else:
        await ctx.send(embed=generate_msg(f"No song is playing"))


@client.command(help="Lets me tell you programming jokes")
async def joke(ctx):
    joke = pyjokes.get_joke()
    await ctx.send(embed=generate_msg(joke))


@client.command(
    aliases=["wiki"],
    help="Lets me tell you something about any topic (sometimes inaccurate!)",
)
async def summary(ctx, *args):
    topic = " ".join(args)
    info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
    await ctx.send(embed=generate_msg(info))


@client.command(help="Another help function")
async def helpme(ctx):
    with open(r"C:\Users\raf\Desktop\Github\PlayBot\help.txt") as f:
        await ctx.send(
            embed=generate_msg(title_msg="__List of commands__", msg=f.read())
        )


@client.command(aliases=["start"], help="Lets me join your current voice channel")
async def join(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.send(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(
            embed=generate_msg(
                f"{ERROR_MSGS[6]}\n\n**Note**: {ERROR_MSGS[4]} **#{channel_name}**"
            )
        )
        return
    elif (
        discord.utils.get(client.voice_clients, guild=ctx.guild).is_playing()
        and channel_id is ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[6]))
        return
    if not ctx.author.voice:
        await ctx.send(embed=generate_msg(ERROR_MSGS[1]))
        return

    txt_ch_and_guild_id[ctx.message.guild.id] = (ctx.channel.id, str(ctx.channel))
    channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.send(
        embed=generate_msg(
            f"Joined 🔉**{channel}** via **#{str(ctx.channel)}**.\n\n**Note**: Song commands for this session will only be valid in mentioned text channel."
        )
    )


@client.command(help="Lets me leave the voice channel")
async def leave(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.send(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return
    if ctx.message.guild.id in txt_ch_and_guild_id:
        txt_ch_and_guild_id.pop(ctx.message.guild.id)

    channel = ctx.message.author.voice.channel
    if ctx.channel.id in titles_on_song_command:
        titles_on_song_command.pop(ctx.channel.id)

    if ctx.channel.id in titles:
        titles.pop(ctx.channel.id)

    await ctx.guild.voice_client.disconnect()
    await ctx.send(embed=generate_msg(f"Left **{channel}** voice channel."))


@client.command(help="Pauses the current song")
async def pause(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send(
            embed=generate_msg(
                f"Paused **{titles_on_song_command[ctx.channel.id][0]}**"
            )
        )
    else:
        await ctx.send(embed=generate_msg("There is no song being played"))


@client.command(aliases=["continue", "res"], help="Resumes the paused song")
async def play(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_paused():
        voice.resume()
        await ctx.send(
            embed=generate_msg(
                f"Resumed **{titles_on_song_command[ctx.channel.id][0]}**"
            )
        )
    else:
        await ctx.send(embed=generate_msg("There is no audio currently playing"))


@client.command(aliases=["next"], help="Skip to the next song in your queue")
async def skip(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=ERROR_MSGS[3])
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        voice.stop()
    else:
        await ctx.reply(embed=generate_msg("Can't skip because no song is playing"))


@client.command(help="Search for a specific song")
async def search(ctx, *args):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.send(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.author.voice and not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[1]))
        return
    elif not ctx.voice_client and ctx.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.send(
            embed=generate_msg(
                f"Joined 🔉**{channel}** via **#{str(ctx.channel)}**.\n\n**Note**: Song commands for this session will only be valid in mentioned text channel."
            )
        )
    if (
        not ctx.voice_client
        and ctx.author.voice
        or ctx.author.voice
        and ctx.voice_client
    ):
        play_name = " ".join(args)
        if ctx.message.guild.id not in txt_ch_and_guild_id:
            txt_ch_and_guild_id[ctx.message.guild.id] = (
                ctx.channel.id,
                str(ctx.channel),
            )

        play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
        query_stringyt = urllib.parse.urlencode({"search_query": play_name})
        html_contentyt = urllib.request.urlopen(
            "https://www.youtube.com/results?" + query_stringyt
        )
        search_resultsyt = re.findall(
            r"url\"\:\"\/watch\?v\=(.*?(?=\"))", html_contentyt.read().decode()
        )
        list1 = []
        for i in range(10):
            try:
                newsong = pafy.new(search_resultsyt[i])
                list1.append(f"**{i+1}** : {newsong.title} **[{newsong.duration}]**")
            except ValueError:
                break

        results = "\n\n".join(list1)

        await ctx.send(
            embed=generate_msg(
                f"**Results for __{play_name}__. Type the number of your choice. Type 0 to cancel.**\n\n{results}"
            )
        )

        def check(msg):
            return (
                msg.author == ctx.author
                and msg.channel == ctx.channel
                and int(msg.content) in [i for i in range(len(list1))]
            )

        msg = await client.wait_for("message", check=check)
        if int(msg.content) > 0 and int(msg.content) <= len(list1):
            newsong = pafy.new(search_resultsyt[int(msg.content) - 1])
            audio = newsong.getbestaudio()
            newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
            final_link = f"https://www.youtube.com/watch?v={search_resultsyt[i]}"

            if not play_check.is_playing() and not play_check.is_paused():
                status = "!song"
                if ctx.channel.id in titles_on_song_command:
                    titles_on_song_command[ctx.channel.id].insert(0, newsong.title)
                else:
                    titles_on_song_command[ctx.channel.id] = [newsong.title]
                add_to_now_playing(ctx, newsong.title, status)
                play_song(ctx, newsource, newsong.title, final_link)
            else:
                status = "!q"
                await ctx.send(
                    embed=generate_msg(f"Added to queue: **{newsong.title}**")
                )
                add_to_queue(ctx, newsource, newsong.title)
                add_to_now_playing(ctx, newsong.title, status)
                songs = list(
                    f"• {titles[ctx.channel.id][i]}"
                    for i in range(len(titles[ctx.channel.id]))
                )
                string = "\n".join(songs)
                if string:
                    await ctx.send(
                        embed=generate_msg(title_msg="**Queued songs**:", msg=string)
                    )
                else:
                    await ctx.send(
                        embed=generate_msg(title_msg=f"**Queued songs**:", msg="None")
                    )

        else:
            await ctx.send(embed=generate_msg("Cancelled search"))


@client.command(help="Lets me play a song in your current voice channel")
async def song(ctx, *args):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.send(embed=generate_msg(ERROR_MSGS[3]))
        return

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.author.voice and not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not ctx.voice_client and ctx.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.send(
            embed=generate_msg(
                f"Joined 🔉**{channel}** via **#{str(ctx.channel)}**.\n\n**Note**: Song commands for this session will only be valid in mentioned text channel."
            )
        )

    if (
        not ctx.voice_client
        and ctx.author.voice
        or ctx.author.voice
        and ctx.voice_client
    ):
        play_name = " ".join(args)
        if ctx.message.guild.id not in txt_ch_and_guild_id:
            txt_ch_and_guild_id[ctx.message.guild.id] = (
                ctx.channel.id,
                str(ctx.channel),
            )

        play_check = discord.utils.get(client.voice_clients, guild=ctx.guild)
        status = "!song"

        def search_for_link(play_name, origin, **kwargs):
            query_stringyt = urllib.parse.urlencode(
                {"search_query": play_name + "audio"}
            )
            html_contentyt = urllib.request.urlopen(
                "https://www.youtube.com/results?" + query_stringyt
            )
            search_resultsyt = re.findall(
                r"url\"\:\"\/watch\?v\=(.*?(?=\"))",
                html_contentyt.read().decode(),
            )

            i = 0
            newsong = pafy.new(search_resultsyt[i])
            if newsong.length >= 600:
                i += 1

            newsong = pafy.new(search_resultsyt[i])
            audio = newsong.getbestaudio()
            newsource = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
            newsong_title = newsong.title
            if origin == "spotify":
                newsong_title = play_name
            if ctx.channel.id in titles_on_song_command:
                titles_on_song_command[ctx.channel.id].insert(0, newsong_title)
            else:
                titles_on_song_command[ctx.channel.id] = [newsong_title]

            final_link = f"https://www.youtube.com/watch?v={search_resultsyt[i]}"
            if origin == "youtube":
                add_to_now_playing(ctx, newsong.title, status)
                play_song(ctx, newsource, newsong.title, final_link)
            elif origin == "spotify":
                final_link = kwargs["link"]
                add_to_now_playing(ctx, play_name, status)
                play_song(ctx, newsource, play_name, final_link)

        if not play_check.is_playing():
            if "https://open.spotify.com" in play_name:
                track_id = play_name[31 : play_name.index("?")]

                access_token = spoti.SpotifyAPI.extract_access_token(
                    __SPOTIFY_CLIENT_ID, __SPOTIFY_CLIENT_SECRET
                )
                spotify = spoti.SpotifyAPI(access_token)
                track_name = spotify.get(track_id)
                search_for_link(track_name, "spotify", link=play_name)

            elif "https://www.youtube.com/" not in play_name:
                search_for_link(play_name, "youtube")

            elif "https://www.youtube.com/" in play_name:
                yt_link = pafy.new(play_name)
                audio = yt_link.getbestaudio()
                yt_link_play = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
                titles_on_song_command[ctx.channel.id].insert(0, yt_link.title)
                add_to_now_playing(ctx, yt_link.title, status)
                play_song(ctx, yt_link_play, yt_link.title, "")

        else:
            await ctx.send(
                embed=generate_msg(
                    "There is a song currently playing. To add a song to a queue, use the `;q` command. To skip to the next queued song, use the `;skip` command."
                )
            )


@client.command(aliases=["queue", "add"], help="Adds a song to the queue ")
async def q(ctx, *args):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    q_name = " ".join(args)
    voice_status = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if ctx.message.guild.id not in txt_ch_and_guild_id:
        txt_ch_and_guild_id[ctx.message.guild.id] = (ctx.channel.id, str(ctx.channel))

    status = "!q"
    if len(titles) < 20:

        def search_for_link(play_name, origin, **kwargs):
            query_queue = urllib.parse.urlencode({"search_query": play_name + "audio"})
            html_queue = urllib.request.urlopen(
                "https://www.youtube.com/results?" + query_queue
            )
            results_queue = re.findall(
                r"url\"\:\"\/watch\?v\=(.*?(?=\"))",
                html_queue.read().decode(),
            )
            i = 0
            next_in_queue = pafy.new(results_queue[i])
            if next_in_queue.length >= 600:
                i += 1
            next_in_queue = pafy.new(results_queue[i])
            audio_queue = next_in_queue.getbestaudio()
            queued_song = FFmpegPCMAudio(audio_queue.url, **FFMPEG_OPTIONS)
            next_in_queue_title = next_in_queue.title
            link = f"https://www.youtube.com/watch?v={results_queue[0]}"
            if origin == "spotify":
                next_in_queue_title = play_name
                link = kwargs["link"]
            return (queued_song, next_in_queue_title, link)

        queued_song, next_in_queue_title, link = None, None, None
        if "https://open.spotify.com" in q_name:
            track_id = q_name[31 : q_name.index("?")]
            access_token = spoti.SpotifyAPI.extract_access_token(
                __SPOTIFY_CLIENT_ID, __SPOTIFY_CLIENT_SECRET
            )
            spotify = spoti.SpotifyAPI(access_token)
            track_name = spotify.get(track_id)
            queued_song, next_in_queue_title, link = search_for_link(
                track_name, "spotify", link=q_name
            )

        elif "/watch?v=" not in q_name:
            queued_song, next_in_queue_title, link = search_for_link(q_name, "youtube")

        elif "/watch?v=" in q_name:
            link = q_name
            yt_new_queue = pafy.new(link)
            yt_audio_queue = yt_new_queue.getbestaudio()
            queued_song = FFmpegPCMAudio(yt_audio_queue.url, **FFMPEG_OPTIONS)
            next_in_queue_title = yt_new_queue.title

        add_to_queue(ctx, queued_song, next_in_queue_title)
        add_to_now_playing(ctx, next_in_queue_title, status)

        if not voice_status.is_playing() and not voice_status.is_paused():
            titles[ctx.channel.id].pop(0)
            play_song(ctx, queued_song, next_in_queue_title, link)

        else:
            await ctx.send(
                embed=generate_msg(
                    f"Added to queue: **{next_in_queue_title}**\n{link}",
                )
            )
            songs = list(
                f"• {titles[ctx.channel.id][i]}"
                for i in range(len(titles[ctx.channel.id]))
            )
            string = "\n".join(songs)
            await ctx.send(embed=generate_msg(title_msg="**Queued songs**", msg=string))
    else:
        await ctx.send(embed=generate_msg("Reached maximum queue limit"))


@client.command(aliases=["end", "quit"], help="Stops current song and clears queue")
async def stop(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing() or voice.is_paused():
        if ctx.channel.id in queues:
            queues[ctx.channel.id].clear()
        if ctx.channel.id in titles:
            titles.pop(ctx.channel.id)
        if ctx.channel.id in titles_on_song_command:
            titles_on_song_command.pop(ctx.channel.id)

        voice.stop()
        await ctx.send(
            embed=generate_msg("Current song stopped and all queues removed")
        )
    else:
        await ctx.send(
            embed=generate_msg("Can't use command because no song is playing")
        )


# @client.command() TODO clear command
# async def clear(ctx):


@client.command(
    aliases=["remove", "rem", "r"], help="Lets you remove a song from the queue"
)
async def rq(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return

    if queues[ctx.channel.id] and titles[ctx.channel.id]:
        songs = list(
            f"**{i+1}** : {titles[ctx.channel.id][i]}"
            for i in range(len(titles[ctx.channel.id]))
        )
        string = "\n\n".join(songs)
        await ctx.reply(
            embed=generate_msg(
                f"❌ **Type the position of the song to remove (0 to cancel):** ❌\n\n{string}"
            )
        )

        def check(msg):
            return (
                msg.author == ctx.author
                and msg.channel == ctx.channel
                and int(msg.content) in [i for i in range(20)]
            )

        msg = await client.wait_for("message", check=check)
        if int(msg.content) > 0 and int(msg.content) <= len(songs):
            queues[ctx.channel.id].pop(int(msg.content) - 1)
            await ctx.send(
                embed=generate_msg(
                    f"Removed **{titles[ctx.channel.id][int(msg.content)-1]}** from queue"
                )
            )
            titles[ctx.channel.id].pop(int(msg.content) - 1)
            titles_on_song_command[ctx.channel.id].pop(int(msg.content))
            songs = list(
                f"• {titles[ctx.channel.id][i]}"
                for i in range(len(titles[ctx.channel.id]))
            )
            string = "\n".join(songs)
            if string:
                await ctx.send(
                    embed=generate_msg(title_msg="**Queued songs**:", msg=string)
                )
            else:
                await ctx.send(
                    embed=generate_msg(title_msg="**Queued songs:**", msg="None")
                )

        else:
            await ctx.send(embed=generate_msg(f"**No queue removed**"))

    else:
        await ctx.reply(embed=generate_msg("**No more queues to remove**"))


@client.command(aliases=["list", "sq", "vq", "view"], help="Views queued songs")
async def qs(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return
    try:
        songs = list(
            f"• {titles[ctx.channel.id][i]}"
            for i in range(0, len(titles[ctx.channel.id]))
        )
        string = "\n".join(songs)
        if string:
            await ctx.send(
                embed=generate_msg(title_msg="**Queued songs**:", msg=string)
            )
        else:
            await ctx.send(
                embed=generate_msg(title_msg=f"**Queued songs**:", msg="None")
            )

    except:
        await ctx.send(embed=generate_msg(title_msg=f"**Queued songs**:", msg="None"))


@client.command()
async def previous(ctx):  # TODO goes back to previous song
    pass


@client.command(help="Shows lyrics of current song playing (sometimes inaccurate)")
async def lyrics(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        await ctx.send(embed=generate_msg(ERROR_MSGS[3]))
        return
    elif channel_id != ctx.channel.id:
        await ctx.reply(embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**"))
        return

    if not ctx.voice_client:
        await ctx.send(embed=generate_msg(ERROR_MSGS[2]))
        return

    if not ctx.author.voice:
        await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))
        return

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        await ctx.send(embed=generate_msg(ERROR_MSGS[5]))
        return

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing() or voice.is_paused():

        extract_lyrics = SongLyrics(
            os.environ.get("GCS_API_KEY"), os.environ.get("GCS_ENGINE_ID")
        )
        lyrics = extract_lyrics.get_lyrics(titles_on_song_command[ctx.channel.id][0])
        lyr = lyrics["lyrics"].replace("\\n", "\n")

        if len(lyr) + len(titles_on_song_command[ctx.channel.id][0]) <= 2000:
            await ctx.send(
                embed=generate_msg(
                    f"**{titles_on_song_command[ctx.channel.id][0]}**\n{lyr}"
                )
            )
        else:
            lyr1 = lyr[0 : len(lyr) // 2]
            lyr2 = lyr[len(lyr) // 2 :]

            if len(lyr2) > 2000:
                lyr3 = lyr2[0 : len(lyr2) // 2]
                lyr4 = lyr2[len(lyr2) // 2 :]
                await ctx.send(
                    embed=generate_msg(
                        f"**{titles_on_song_command[ctx.channel.id][0]}**\n{lyr}"
                    )
                )
                await ctx.send(embed=generate_msg(lyr3))
                await ctx.send(embed=generate_msg(lyr4))

            else:
                await ctx.send(
                    embed=generate_msg(
                        f"**{titles_on_song_command[ctx.channel.id][0]}**\n{lyr1}"
                    )
                )
                await ctx.send(embed=generate_msg(f"{lyr2}"))

    else:
        await ctx.send(embed=generate_msg("There is no song playing"))


@client.command(help="Deletes a specified number of messages in a channel")
async def cls(ctx, arg: int):
    num = 1 + arg
    await ctx.channel.purge(limit=num)


@client.event
async def on_message(message):
    msg = message.content.lower()
    mention = message.author.mention

    for key in KEY_WORDS.keys():
        if key in msg:
            await message.channel.send(
                embed=generate_msg(f"{KEY_WORDS[key]} {mention}!")
            )
    await client.process_commands(message)


@lyrics.error
async def info_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(embed=generate_msg("Lyrics are currently unavailable"))


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(
            embed=generate_msg(
                "Invalid command. Having trouble? Use the `;helpme` command."
            )
        )


client.run(os.environ.get("DISCORD"))
