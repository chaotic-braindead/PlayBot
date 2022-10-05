import discord
import os
import pafy
import pyjokes
import re
import spoti
import urllib
import urllib.parse
import urllib.request
import wikipedia
from discord.ext import commands
from discord import FFmpegPCMAudio
from lyrics_extractor import SongLyrics

client = commands.Bot(command_prefix=";")
queues = {}
txt_ch_and_guild_id = {}
current = {}

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

__SPOTIFY_CLIENT_ID = os.environ.get("PLAYBOT_SPOTI_ID")
__SPOTIFY_CLIENT_SECRET = os.environ.get("PLAYBOT_SPOTI_SECRET")


def generate_msg(msg=None, title_msg=None, colr=discord.Colour.red()):

    if not title_msg and msg:
        return discord.Embed(description=msg, color=colr)
    elif not msg and title_msg:
        return discord.Embed(title=title_msg, color=colr)
    else:
        return discord.Embed(title=title_msg, description=msg, color=colr)


def add(ctx, song_title, source=None):
    global current
    if source:
        if ctx.channel.id in queues:
            queues[ctx.channel.id][song_title] = source
        else:
            queues[ctx.channel.id] = {song_title: source}
    else:
        current[ctx.channel.id] = song_title


def play_song(ctx, song_source, song_title, final_link):
    voice = ctx.guild.voice_client
    channel = client.get_channel(ctx.channel.id)
    client.loop.create_task(
        channel.send(
            embed=generate_msg(f"🎶 Now playing: **{song_title}** 🎶\n{final_link}")
        )
    )
    voice.play(song_source, after=lambda x=None: check_queue(ctx, ctx.channel.id))


def search_for_link(play_name, spoti_link=None):
    link = None
    if spoti_link:
        link = spoti_link
    else:
        query = urllib.parse.urlencode({"search_query": play_name + "audio"})
        html = urllib.request.urlopen("https://www.youtube.com/results?" + query)
        results = re.findall(
            r"url\"\:\"\/watch\?v\=(.*?(?=\"))",
            html.read().decode(),
        )
        i = 0
        p = pafy.new(results[i])
        while p.length > 900:
            i += 1
            p = pafy.new(results[i])

        audio = p.getbestaudio()
        queued_song = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
        next_in_queue_title = p.title
        link = f"https://www.youtube.com/watch?v={results[i]}"
    return (queued_song, next_in_queue_title, link)


def show_queue(ctx):
    queue_list = list(queues[ctx.channel.id].keys())
    channel = client.get_channel(ctx.channel.id)
    songs = list(f"• {queue_list[i]}" for i in range(len(queue_list)))
    string = "\n".join(songs)
    if string:
        client.loop.create_task(
            channel.send(embed=generate_msg(title_msg="**Queued songs**:", msg=string))
        )
    else:
        client.loop.create_task(
            channel.send(embed=generate_msg(title_msg=f"**Queued songs**:", msg="None"))
        )


def check_queue(ctx, id):
    channel = client.get_channel(ctx.channel.id)
    try:
        global current
        voice = ctx.guild.voice_client
        voice.stop()
        value = list(queues[id].keys())[0]
        source = queues[id][value]
        client.loop.create_task(
            channel.send(embed=generate_msg(f"🎶 Now playing: **{value}** 🎶"))
        )
        voice.play(source, after=lambda x=None: check_queue(ctx, ctx.channel.id))
        current[ctx.channel.id] = value
        queues[id].pop(value)
    except KeyError:
        client.loop.create_task(channel.send(embed=generate_msg(f"Queue has stopped.")))


@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status.idle, activity=discord.Game(";helpme | @raffy")
    )
    print(f"Logged in as {client.user}")


@client.command(help="Say hello to PlayBot!")
async def hello(ctx):
    return await ctx.reply(
        embed=generate_msg(
            f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type `;helpme`"
        )
    )


@client.command(aliases=["current"], help="Shows the title of the current song playing")
async def now(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]

    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        return await ctx.send(
            embed=generate_msg(f"🎶 Now playing: **{current[ctx.channel.id]}** 🎶")
        )

    return await ctx.send(embed=generate_msg(f"No song is playing"))


@client.command(help="Lets me tell you programming jokes")
async def joke(ctx):
    joke = pyjokes.get_joke()
    return await ctx.send(embed=generate_msg(joke))


@client.command(
    aliases=["wiki"],
    help="Lets me tell you something about any topic (sometimes inaccurate!)",
)
async def summary(ctx, *args):
    topic = " ".join(args)
    info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
    return await ctx.send(embed=generate_msg(info))


@client.command(help="Another help function")
async def helpme(ctx):
    with open(r"C:\Users\raf\Desktop\Github\PlayBot\help.txt") as f:
        return await ctx.send(
            embed=generate_msg(title_msg="__List of commands__", msg=f.read())
        )


@client.command(aliases=["start"], help="Lets me join your current voice channel")
async def join(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice and not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[1]))

    if ctx.message.guild.id not in txt_ch_and_guild_id:
        txt_ch_and_guild_id[ctx.message.guild.id] = (
            ctx.channel.id,
            str(ctx.channel),
        )

    if not ctx.voice_client and ctx.author.voice:
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
        return await ctx.send(embed=generate_msg(ERROR_MSGS[3]))

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[2]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    if ctx.message.guild.id in txt_ch_and_guild_id:
        txt_ch_and_guild_id.pop(ctx.message.guild.id)

    channel = ctx.message.author.voice.channel

    if ctx.channel.id in queues:
        queues.pop(ctx.channel.id)

    await ctx.guild.voice_client.disconnect()
    return await ctx.send(embed=generate_msg(f"Left **{channel}** voice channel."))


@client.command(help="Pauses the current song")
async def pause(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        return await ctx.send(
            embed=generate_msg(f"Paused **{current[ctx.channel.id]}**")
        )

    return await ctx.send(embed=generate_msg("There is no song being played"))


@client.command(aliases=["continue", "res"], help="Resumes the paused song")
async def play(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_paused():
        voice.resume()
        return await ctx.send(
            embed=generate_msg(f"Resumed **{current[ctx.channel.id]}**")
        )

    return await ctx.send(embed=generate_msg("There is no audio currently playing"))


@client.command(aliases=["next"], help="Skip to the next song in your queue")
async def skip(ctx):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=ERROR_MSGS[3])

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        return voice.stop()

    await ctx.reply(embed=generate_msg("Can't skip because no song is playing"))


@client.command(help="Search for a specific song")
async def search(ctx, *args):
    if txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice and not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[1]))

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
                add(ctx, newsong.title)
                return play_song(ctx, newsource, newsong.title, final_link)

            await ctx.send(embed=generate_msg(f"Added to queue: **{newsong.title}**"))

            add(ctx, newsong.title, newsource)
            show_queue(ctx)

        return await ctx.send(embed=generate_msg("Cancelled search"))


@client.command(help="Lets me play a song in your current voice channel")
async def song(ctx, *args):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice and not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[1]))

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

        if play_check.is_playing():
            return await ctx.send(
                embed=generate_msg(
                    "There is a song currently playing. To add a song to a queue, use the `;q` command. To skip to the next queued song, use the `;skip` command."
                )
            )

        song, title, link = None, None, None
        if "https://open.spotify.com" in play_name:
            track_id = play_name[31 : play_name.index("?")]

            access_token = spoti.SpotifyAPI.extract_access_token(
                __SPOTIFY_CLIENT_ID, __SPOTIFY_CLIENT_SECRET
            )
            spotify = spoti.SpotifyAPI(access_token)
            track_name = spotify.get(track_id)
            song, title, link = search_for_link(track_name, play_name)

        elif "https://www.youtube.com/" not in play_name:
            song, title, link = search_for_link(play_name)

        elif "https://www.youtube.com/" in play_name:
            yt_link = pafy.new(play_name)
            audio = yt_link.getbestaudio()
            song = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
            title = yt_link.title

        add(ctx, title)
        play_song(ctx, song, title, link)


@client.command(aliases=["queue", "add"], help="Adds a song to the queue ")
async def q(ctx, *args):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    q_name = " ".join(args)
    voice_status = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if ctx.message.guild.id not in txt_ch_and_guild_id:
        txt_ch_and_guild_id[ctx.message.guild.id] = (ctx.channel.id, str(ctx.channel))

    queued_song, next_in_queue_title, link = None, None, None
    if "https://open.spotify.com" in q_name:
        track_id = q_name[31 : q_name.index("?")]
        access_token = spoti.SpotifyAPI.extract_access_token(
            __SPOTIFY_CLIENT_ID, __SPOTIFY_CLIENT_SECRET
        )
        spotify = spoti.SpotifyAPI(access_token)
        track_name = spotify.get(track_id)
        queued_song, next_in_queue_title, link = search_for_link(track_name, q_name)

    elif "/watch?v=" not in q_name:
        queued_song, next_in_queue_title, link = search_for_link(q_name)

    elif "/watch?v=" in q_name:
        link = q_name
        yt_new_queue = pafy.new(link)
        yt_audio_queue = yt_new_queue.getbestaudio()
        queued_song = FFmpegPCMAudio(yt_audio_queue.url, **FFMPEG_OPTIONS)
        next_in_queue_title = yt_new_queue.title

    add(ctx, next_in_queue_title, queued_song)

    if not voice_status.is_playing() and not voice_status.is_paused():
        queues[ctx.channel.id].pop(next_in_queue_title)
        return play_song(ctx, queued_song, next_in_queue_title, link)

    await ctx.send(
        embed=generate_msg(
            f"Added to queue: **{next_in_queue_title}**\n{link}",
        )
    )
    show_queue(ctx)


@client.command(aliases=["end", "quit"], help="Stops current song and clears queue")
async def stop(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if not voice.is_playing() and not voice.is_paused():
        return await ctx.send(
            embed=generate_msg("Can't use command because no song is playing")
        )

    if ctx.channel.id in queues:
        queues[ctx.channel.id].clear()

    voice.stop()
    return await ctx.send(
        embed=generate_msg("Current song stopped and all queues removed")
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
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    if queues[ctx.channel.id]:
        queue_list = list(queues[ctx.channel.id].keys())
        songs = list(f"**{i+1}** : {queue_list[i]}" for i in range(len(queue_list)))
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
        index = int(msg.content)
        if index > 0 and index <= len(songs):
            chosen = queue_list[index - 1]
            await ctx.send(embed=generate_msg(f"Removed **{chosen}** from queue"))
            queues[ctx.channel.id].pop(chosen)

            show_queue(ctx)

        return await ctx.send(embed=generate_msg(f"**No queue removed**"))

    return await ctx.reply(embed=generate_msg("**No more queues to remove**"))


@client.command(aliases=["list", "sq", "vq", "view"], help="Views queued songs")
async def qs(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[3]))

    elif (
        txt_ch_and_guild_id
        and ctx.message.guild.id in txt_ch_and_guild_id
        and channel_id != ctx.channel.id
    ):
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    queue_list = list(queues[ctx.channel.id].keys())
    songs = list(f"• {queue_list[i]}" for i in range(len(queue_list)))
    string = "\n".join(songs)
    if string:
        return await ctx.send(
            embed=generate_msg(title_msg="**Queued songs**:", msg=string)
        )

    return await ctx.send(
        embed=generate_msg(title_msg=f"**Queued songs**:", msg="None")
    )


@client.command()
async def previous(ctx):  # TODO goes back to previous song
    pass


@client.command(help="Shows lyrics of current song playing (sometimes inaccurate)")
async def lyrics(ctx):
    if txt_ch_and_guild_id and ctx.message.guild.id in txt_ch_and_guild_id:
        channel_id, channel_name = txt_ch_and_guild_id[ctx.message.guild.id]
    if "bot" not in str(ctx.channel):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[3]))

    elif channel_id != ctx.channel.id:
        return await ctx.reply(
            embed=generate_msg(f"{ERROR_MSGS[4]} **#{channel_name}**")
        )

    if not ctx.voice_client:
        return await ctx.send(embed=generate_msg(ERROR_MSGS[2]))

    if not ctx.author.voice:
        return await ctx.reply(embed=generate_msg(ERROR_MSGS[1]))

    if not (
        ctx.author.voice.channel
        and ctx.author.voice.channel == ctx.voice_client.channel
    ):
        return await ctx.send(embed=generate_msg(ERROR_MSGS[5]))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if not voice.is_playing() and not voice.is_paused():
        return await ctx.send(embed=generate_msg("There is no song playing"))

    extract_lyrics = SongLyrics(
        os.environ.get("GCS_API_KEY"), os.environ.get("GCS_ENGINE_ID")
    )
    lyrics = extract_lyrics.get_lyrics(current[ctx.channel.id])
    lyr = lyrics["lyrics"].replace("\\n", "\n")

    if len(lyr) + len(current[ctx.channel.id]) <= 2000:
        return await ctx.send(
            embed=generate_msg(f"**{current[ctx.channel.id]}**\n{lyr}")
        )

    lyr1 = lyr[: len(lyr) // 2]
    lyr2 = lyr[len(lyr) // 2 :]

    if len(lyr2) > 2000:
        lyr3 = lyr2[: len(lyr2) // 2]
        lyr4 = lyr2[len(lyr2) // 2 :]
        await ctx.send(embed=generate_msg(f"**{current[ctx.channel.id]}**\n{lyr}"))
        await ctx.send(embed=generate_msg(lyr3))
        return await ctx.send(embed=generate_msg(lyr4))

    await ctx.send(embed=generate_msg(f"**{current[ctx.channel.id]}**\n{lyr1}"))
    return await ctx.send(embed=generate_msg(f"{lyr2}"))


@client.command(help="Deletes a specified number of messages in a channel")
async def cls(ctx, arg: int):
    num = 1 + arg
    return await ctx.channel.purge(limit=num)


@client.event
async def on_message(message):
    msg = message.content.lower()
    mention = message.author.mention

    for key in KEY_WORDS.keys():
        if key in msg:
            return await message.channel.send(
                embed=generate_msg(f"{KEY_WORDS[key]} {mention}!")
            )
    return await client.process_commands(message)


@lyrics.error
async def info_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        return await ctx.send(embed=generate_msg("Lyrics are currently unavailable"))


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return await ctx.reply(
            embed=generate_msg(
                "Invalid command. Having trouble? Use the `;helpme` command."
            )
        )


client.run(os.environ.get("DISCORD"))
