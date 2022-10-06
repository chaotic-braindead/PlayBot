import discord
import pyjokes
import wikipedia
from discord.ext import commands


def generate_msg(msg=None, title_msg=None, colr=discord.Colour.red()):

    if not title_msg and msg:
        return discord.Embed(description=msg, color=colr)
    elif not msg and title_msg:
        return discord.Embed(title=title_msg, color=colr)
    else:
        return discord.Embed(title=title_msg, description=msg, color=colr)


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Say hello to PlayBot!")
    async def hello(self, ctx):
        return await ctx.reply(
            embed=generate_msg(
                f"Hello, {ctx.message.author.mention}! If you need help with my commands, just type `;helpme`"
            )
        )

    @commands.command(help="Lets me tell you programming jokes")
    async def joke(self, ctx):
        joke = pyjokes.get_joke()
        return await ctx.send(embed=generate_msg(joke))

    @commands.command(
        aliases=["wiki"],
        help="Lets me tell you something about any topic (sometimes inaccurate!)",
    )
    async def summary(self, ctx, *args):
        topic = " ".join(args)
        info = wikipedia.summary(topic, auto_suggest=False, sentences=2)
        return await ctx.send(embed=generate_msg(info))

    @commands.command(help="Another help function")
    async def helpme(self, ctx):
        with open(r"C:\Users\raf\Desktop\Github\PlayBot\help.txt") as f:
            return await ctx.send(
                embed=generate_msg(title_msg="__List of commands__", msg=f.read())
            )

    @commands.command(help="Deletes a specified number of messages in a channel")
    async def cls(self, ctx, arg: int):
        num = 1 + arg
        return await ctx.channel.purge(limit=num)
