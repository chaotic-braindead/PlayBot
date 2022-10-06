import discord


def generate_msg(msg=None, title_msg=None, colr=discord.Colour.red()):

    if not title_msg and msg:
        return discord.Embed(description=msg, color=colr)
    elif not msg and title_msg:
        return discord.Embed(title=title_msg, color=colr)
    else:
        return discord.Embed(title=title_msg, description=msg, color=colr)
