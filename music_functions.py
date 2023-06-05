import discord
import time
import os
import spoti
import re
import urllib
import urllib.parse
import urllib.request
import youtube_dl
from discord import FFmpegPCMAudio
from discord.ext import commands
from general_functions import generate_msg
from lyrics_extractor import SongLyrics


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.queues = {}
        self.current = {}
        self.txt_ch_and_guild_id = {}

        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        self.ERROR_MSGS = {
            1: "You're not in a voice channel! Having trouble? Use the `;helpme` command.",
            2: "I am not in a voice channel! Having trouble? Use the `;helpme` command.",
            3: "Join/create a text channel containing the word **bot** in order to play a song.",
            4: "You must switch to this text channel in order to use song commands:",
            5: "We must be in the same voice channel.",
            6: "I am already in a voice channel.",
        }
        self.__SPOTIFY_CLIENT_ID = os.environ.get("PLAYBOT_SPOTI_ID")
        self.__SPOTIFY_CLIENT_SECRET = os.environ.get("PLAYBOT_SPOTI_SECRET")
        self.__SPOTIFY_ACCESS_TOKEN = None

    def search_song(self, query, spoti_link=None):
        search = urllib.parse.urlencode({"search_query": query + "audio"})
        html = urllib.request.urlopen("https://www.youtube.com/results?" + search)
        results = re.findall(
            r"url\"\:\"\/watch\?v\=(.*?(?=\"))",
            html.read().decode(),
        )
        audio = None
        next_in_queue_title = None
        
        with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
            info = ydl.extract_info("https://www.youtube.com/watch?v=" + results[0], download=False)
            audio = info['formats'][0]['url']
            next_in_queue_title = info['title']

        if(audio is None):
            return
        
        queued_song = FFmpegPCMAudio(audio, **self.FFMPEG_OPTIONS)
        link = f"https://www.youtube.com/watch?v={results[0]}"
        
        if spoti_link:
            next_in_queue_title = query
            link = spoti_link
        
        return (queued_song, next_in_queue_title, link)

    def add_to_queue(self, ctx, song_title, source=None):
        if source:
            if ctx.channel.id in self.queues:
                self.queues[ctx.channel.id][song_title] = source
            else:
                self.queues[ctx.channel.id] = {song_title: source}
        else:
            self.current[ctx.channel.id] = song_title

    def play_song(self, ctx, song_source, song_title, final_link):
        voice = ctx.guild.voice_client
        channel = self.bot.get_channel(ctx.channel.id)

        self.bot.loop.create_task(
            channel.send(
                embed=generate_msg(f"🎶 Now playing: **{song_title}** 🎶\n{final_link}")
            )
        )
        voice.play(
            song_source, after=lambda x=None: self.check_queue(ctx, ctx.channel.id)
        )

    def check_queue(self, ctx, id):
        channel = self.bot.get_channel(ctx.channel.id)
    
        voice = ctx.guild.voice_client
        voice.stop()
        value = list(self.queues[id].keys())
        if not value:
            self.bot.loop.create_task(
            channel.send(embed=generate_msg(f"Queue has stopped."))
        )
            return
        source = self.queues[id][value[0]]
        self.bot.loop.create_task(
            channel.send(embed=generate_msg(f"🎶 Now playing: **{value[0]}** 🎶"))
        )
        voice.play(
            source, after=lambda x=None: self.check_queue(ctx, ctx.channel.id)
        )
        self.current[ctx.channel.id] = value[0]
        self.queues[id].pop(value[0])
        

    def show_queue(self, ctx):
        queue_list = list(self.queues[ctx.channel.id].keys())
        channel = self.bot.get_channel(ctx.channel.id)
        songs = list(f"• {queue_list[i]}" for i in range(len(queue_list)))
        string = "\n".join(songs) if songs else "None"
        self.bot.loop.create_task(
            channel.send(
                embed=generate_msg(title_msg="**Queued songs**:", msg=string)
            )
        )
     

    @commands.command(aliases=["start"], help="Lets me join your current voice channel")
    async def join(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice and not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[1]))

        if ctx.message.guild.id not in self.txt_ch_and_guild_id:
            self.txt_ch_and_guild_id[ctx.message.guild.id] = (
                ctx.channel.id,
                str(ctx.channel),
            )

        if not bool(ctx.voice_client) and bool(ctx.author.voice):
            channel = ctx.message.author.voice.channel
            print(ctx.message.author.voice.channel)
            await channel.connect()
            
            await ctx.send(
                embed=generate_msg(
                    f"Joined 🔉**{channel}** via **#{str(ctx.channel)}**.\n\n**Note**: Song commands for this session will only be valid in mentioned text channel."
                )
            )

    @commands.command(help="Lets me leave the voice channel")
    async def leave(self, ctx):
        if self.txt_ch_and_guild_id:
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[3]))

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[2]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        if ctx.message.guild.id in self.txt_ch_and_guild_id:
            self.txt_ch_and_guild_id.pop(ctx.message.guild.id)

        channel = ctx.message.author.voice.channel

        if ctx.channel.id in self.queues:
            self.queues.pop(ctx.channel.id)
        
        await ctx.voice_client.disconnect()
        return await ctx.send(embed=generate_msg(f"Left **{channel}** voice channel."))

    @commands.command(aliases=["continue", "res"], help="Resumes the paused song")
    async def play(self, ctx):
        if self.txt_ch_and_guild_id:
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice.is_paused():
            voice.resume()
            return await ctx.send(
                embed=generate_msg(f"Resumed **{self.current[ctx.channel.id]}**")
            )

        return await ctx.send(embed=generate_msg("There is no audio currently playing"))

    @commands.command(help="Pauses the current song")
    async def pause(self, ctx):
        if self.txt_ch_and_guild_id:
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            return await ctx.send(
                embed=generate_msg(f"Paused **{self.current[ctx.channel.id]}**")
            )

        return await ctx.send(embed=generate_msg("There is no song being played"))

    @commands.command(aliases=["next"], help="Skip to the next song in your queue")
    async def skip(self, ctx):
        if self.txt_ch_and_guild_id:
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=self.ERROR_MSGS[3])

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            return voice.stop()

        await ctx.reply(embed=generate_msg("Can't skip because no song is playing"))

    @commands.command(
        aliases=["end", "quit"], help="Stops current song and clears queue"
    )
    async def stop(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if not voice.is_playing() and not voice.is_paused():
            return await ctx.send(
                embed=generate_msg("Can't use command because no song is playing")
            )

        if ctx.channel.id in self.queues:
            self.queues[ctx.channel.id].clear()

        voice.stop()
        return await ctx.send(
            embed=generate_msg("Current song stopped and all queues removed")
        )

    @commands.command(help="Lets me play a song in your current voice channel")
    async def song(self, ctx, *args):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice and not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[1]))

        if not ctx.voice_client and ctx.author.voice:
            await self.join(ctx)

        if (
            not ctx.voice_client
            and ctx.author.voice
            or ctx.author.voice
            and ctx.voice_client
        ):
            play_name = " ".join(args)
            if ctx.message.guild.id not in self.txt_ch_and_guild_id:
                self.txt_ch_and_guild_id[ctx.message.guild.id] = (
                    ctx.channel.id,
                    str(ctx.channel),
                )
           
            play_check = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            if play_check.is_playing():
                return await ctx.send(
                    embed=generate_msg(
                        "There is a song currently playing. To add a song to a queue, use the `;q` command. To skip to the next queued song, use the `;skip` command."
                    )
                )

            song, title, link = None, None, None

            if "https://open.spotify.com" in play_name:
                track_id = play_name[31 : play_name.index("?")]
                if(self.__SPOTIFY_ACCESS_TOKEN is None):
                    self.__SPOTIFY_ACCESS_TOKEN = spoti.SpotifyAPI.extract_access_token(
                        self.__SPOTIFY_CLIENT_ID, self.__SPOTIFY_CLIENT_SECRET
                    )

                spotify = spoti.SpotifyAPI(self.__SPOTIFY_ACCESS_TOKEN)
                track_name = spotify.get(track_id)
                song, title, link = self.search_song(track_name, play_name)

            elif "https://www.youtube.com/" not in play_name:
                song, title, link = self.search_song(play_name)

            elif "https://www.youtube.com/" in play_name:
                audio = None
                with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                    info = ydl.extract_info(play_name, download=False)
                    audio = info['formats'][0]['url']
                    title = info['title']
                song = FFmpegPCMAudio(audio, **self.FFMPEG_OPTIONS)
                link = play_name
            
            self.add_to_queue(ctx, title)
            self.play_song(ctx, song, title, link)

    @commands.command(aliases=["queue", "add"], help="Adds a song to the queue")
    async def q(self, ctx, *args):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        q_name = " ".join(args)
        voice_status = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if ctx.message.guild.id not in self.txt_ch_and_guild_id:
            self.txt_ch_and_guild_id[ctx.message.guild.id] = (
                ctx.channel.id,
                str(ctx.channel),
            )

        queued_song, next_in_queue_title, link = None, None, None
        if "https://open.spotify.com" in q_name:
            track_id = q_name[31 : q_name.index("?")]
            if(self.__SPOTIFY_ACCESS_TOKEN is None):
                self.__SPOTIFY_ACCESS_TOKEN = spoti.SpotifyAPI.extract_access_token(
                    self.__SPOTIFY_CLIENT_ID, self.__SPOTIFY_CLIENT_SECRET
                )
            spotify = spoti.SpotifyAPI(self.__SPOTIFY_ACCESS_TOKEN)
            track_name = spotify.get(track_id)
            queued_song, next_in_queue_title, link = self.search_song(
                track_name, q_name
            )

        elif "/watch?v=" not in q_name:
            queued_song, next_in_queue_title, link = self.search_song(q_name)

        elif "/watch?v=" in q_name:
            link = q_name
            next_in_queue_title = None
            with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                info = ydl.extract_info(q_name, download=False)
                yt_audio_queue = info['formats'][0]['url']
                next_in_queue_title = info['title']
                
            queued_song = FFmpegPCMAudio(yt_audio_queue, **self.FFMPEG_OPTIONS)

        self.add_to_queue(ctx, next_in_queue_title, queued_song)

        if not voice_status.is_playing() and not voice_status.is_paused():
            self.queues[ctx.channel.id].pop(next_in_queue_title)
            return self.play_song(ctx, queued_song, next_in_queue_title, link)

        await ctx.send(
            embed=generate_msg(
                f"Added to queue: **{next_in_queue_title}**\n{link}",
            )
        )
        self.show_queue(ctx)

    @commands.command(help="Search for a specific song")
    async def search(self, ctx, *args):
        if self.txt_ch_and_guild_id:
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice and not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[1]))

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
            if ctx.message.guild.id not in self.txt_ch_and_guild_id:
                self.txt_ch_and_guild_id[ctx.message.guild.id] = (
                    ctx.channel.id,
                    str(ctx.channel),
                )

            play_check = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            query_stringyt = urllib.parse.urlencode({"search_query": play_name})
            html_contentyt = urllib.request.urlopen(
                "https://www.youtube.com/results?" + query_stringyt
            )
            search_resultsyt = re.findall(
                r"url\"\:\"\/watch\?v\=(.*?(?=\"))", html_contentyt.read().decode()
            )

            
            list1 = []
            links = []
            with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                offset = 0
                for i in range(10):
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={search_resultsyt[i]}", download=False)
                    title = info['title']
                    duration = info['duration']
                    if(info['id'] not in links):
                        list1.append(
                            f"**{i+1-offset}** : {title} **[{time.strftime('%H:%M:%S', time.gmtime(duration))}]**"
                        )
                        links.append(info['id'])
                    else:
                        offset += 1
                            

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

            msg = await self.bot.wait_for("message", check=check)
            if int(msg.content) > 0 and int(msg.content) <= len(list1):
                with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={links[int(msg.content) - 1]}", download=False)
                    title = info['title']
                    duration = info['duration']
                    audio = info['formats'][0]['url']
                    
                newsource = FFmpegPCMAudio(audio, **self.FFMPEG_OPTIONS)
                final_link = f"https://www.youtube.com/watch?v={links[int(msg.content) - 1]}"

                if not play_check.is_playing() and not play_check.is_paused():
                    self.add_to_queue(ctx, title)
                    return self.play_song(ctx, newsource, title, final_link)

                await ctx.send(
                    embed=generate_msg(f"Added to queue: **{title}**")
                )

                self.add_to_queue(ctx, title, newsource)
                return self.show_queue(ctx)

            return await ctx.send(embed=generate_msg("Cancelled search"))

    @commands.command(
        aliases=["current"], help="Shows the title of the current song playing"
    )
    async def now(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]

        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            return await ctx.send(
                embed=generate_msg(
                    f"🎶 Now playing: **{self.current[ctx.channel.id]}** 🎶"
                )
            )

        return await ctx.send(embed=generate_msg(f"No song is playing"))

    @commands.command(
        aliases=["remove", "rem", "r"], help="Lets you remove a song from the queue"
    )
    async def rq(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        if self.queues[ctx.channel.id]:
            queue_list = list(self.queues[ctx.channel.id].keys())
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

            msg = await self.bot.wait_for("message", check=check)
            index = int(msg.content)
            if index > 0 and index <= len(songs):
                chosen = queue_list[index - 1]
                await ctx.send(embed=generate_msg(f"Removed **{chosen}** from queue"))
                self.queues[ctx.channel.id].pop(chosen)

                return self.show_queue(ctx)

            return await ctx.send(embed=generate_msg(f"**No queue removed**"))

        return await ctx.reply(embed=generate_msg("**No more queues to remove**"))

    @commands.command(aliases=["list", "sq", "vq", "view"], help="Views queued songs")
    async def qs(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[3]))

        elif (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
            and channel_id != ctx.channel.id
        ):
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        queue_list = list(self.queues[ctx.channel.id].keys())
        songs = list(f"• {queue_list[i]}" for i in range(len(queue_list)))
        string = "\n".join(songs)
        if string:
            return await ctx.send(
                embed=generate_msg(title_msg="**Queued songs**:", msg=string)
            )

        return await ctx.send(
            embed=generate_msg(title_msg=f"**Queued songs**:", msg="None")
        )

    @commands.command(
        help="Shows lyrics of current song playing (sometimes inaccurate)"
    )
    async def lyrics(self, ctx):
        if (
            self.txt_ch_and_guild_id
            and ctx.message.guild.id in self.txt_ch_and_guild_id
        ):
            channel_id, channel_name = self.txt_ch_and_guild_id[ctx.message.guild.id]
        if "bot" not in str(ctx.channel):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[3]))

        elif channel_id != ctx.channel.id:
            return await ctx.reply(
                embed=generate_msg(f"{self.ERROR_MSGS[4]} **#{channel_name}**")
            )

        if not ctx.voice_client:
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[2]))

        if not ctx.author.voice:
            return await ctx.reply(embed=generate_msg(self.ERROR_MSGS[1]))

        if not (
            ctx.author.voice.channel
            and ctx.author.voice.channel == ctx.voice_client.channel
        ):
            return await ctx.send(embed=generate_msg(self.ERROR_MSGS[5]))

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if not voice.is_playing() and not voice.is_paused():
            return await ctx.send(embed=generate_msg("There is no song playing"))

        extract_lyrics = SongLyrics(
            os.environ.get("GCS_API_KEY"), os.environ.get("GCS_ENGINE_ID")
        )
        lyrics = extract_lyrics.get_lyrics(self.current[ctx.channel.id])
        lyr = lyrics["lyrics"].replace("\\n", "\n")
        print(lyr)

        if len(lyr) + len(self.current[ctx.channel.id]) <= 2000:
            return await ctx.send(
                embed=generate_msg(f"**{self.current[ctx.channel.id]}**\n{lyr}")
            )

        lyr1 = lyr[: len(lyr) // 2]
        lyr2 = lyr[len(lyr) // 2 :]

        if len(lyr2) > 2000:
            lyr3 = lyr2[: len(lyr2) // 2]
            lyr4 = lyr2[len(lyr2) // 2 :]
            await ctx.send(
                embed=generate_msg(f"**{self.current[ctx.channel.id]}**\n{lyr}")
            )
            await ctx.send(embed=generate_msg(lyr3))
            return await ctx.send(embed=generate_msg(lyr4))

        await ctx.send(
            embed=generate_msg(f"**{self.current[ctx.channel.id]}**\n{lyr1}")
        )
        return await ctx.send(embed=generate_msg(f"{lyr2}"))

    @lyrics.error
    async def info_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            return await ctx.send(
                embed=generate_msg("Lyrics are currently unavailable")
            )
