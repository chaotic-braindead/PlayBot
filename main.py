import discord
import os
from discord.ext import commands
from general_functions import General
from music_functions import Music
from general_functions import generate_msg

client = commands.Bot(command_prefix=";")
KEY_WORDS = {
    "good bot": "Why thank you,",
    "bad bot": "I'm sorry. I'll do better next time,",
}

client.add_cog(General(client))
client.add_cog(Music(client))


@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status.idle, activity=discord.Game(";helpme | @raffy")
    )
    print(f"Logged in as {client.user}")


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


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return await ctx.reply(
            embed=generate_msg(
                "Invalid command. Having trouble? Use the `;helpme` command."
            )
        )


client.run(os.environ.get("DISCORD"))
