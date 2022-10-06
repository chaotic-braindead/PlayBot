import discord
import os
import pyjokes
import wikipedia
from discord.ext import commands
from msg_gen import *
from music_functions import Music

client = commands.Bot(command_prefix=";")

client.add_cog(Music(client))

KEY_WORDS = {
    "good bot": "Why thank you,",
    "bad bot": "I'm sorry. I'll do better next time,",
}


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


# @client.command() TODO clear command
# async def clear(ctx):


@client.command()
async def previous(ctx):  # TODO goes back to previous song
    pass


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


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return await ctx.reply(
            embed=generate_msg(
                "Invalid command. Having trouble? Use the `;helpme` command."
            )
        )


client.run(os.environ.get("DISCORD"))
