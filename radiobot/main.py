import discord
from discord.ext import commands
from .db import initialize_sql, DBSession
from .db.radios import Radio
from argparse import ArgumentParser

bot = commands.Bot(command_prefix="r!")

@bot.command(aliases=["p"])
async def play(ctx: commands.Context, radio_name: str):
    from sqlalchemy.orm.exc import NoResultFound
    import sys

    query = DBSession.query(Radio)
    try:
        radio = query.filter(Radio.guild_id == ctx.guild.id) \
            .filter(Radio.radio_name == radio_name) \
            .one()

        ctx.voice_client.play(discord.FFmpegPCMAudio(str(radio.radio_url), stderr=sys.stdout))
    except NoResultFound:
        await ctx.send("No radio named '{}' was found!".format(radio_name))

@bot.command(aliases=["a"])
async def add(ctx: commands.Context, radio_name: str, radio_url: str):
    radio = Radio(ctx.guild.id, radio_name, radio_url)
    DBSession.add(radio)
    DBSession.commit()
    await ctx.send("👍")

@bot.command(aliases=["s"])
async def stop(ctx: commands.Context):
    if ctx.voice_client is not None:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        await ctx.voice_client.disconnect()

    await ctx.send("👍")

@bot.command(aliases=["l"])
async def list(ctx: commands.Context):
    query = DBSession.query(Radio)
    radios = query.filter(Radio.guild_id == ctx.guild.id).all()

    if len(radios) == 0:
        await ctx.send("No radios added!")
        return

    text = "Radios available:\n```\n"
    for radio in radios:
        text += "{}\n".format(radio.radio_name)
    text += "```"
    
    await ctx.send(text)

@play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    
    if ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

@bot.listen("on_voice_state_update")
async def check_for_voice_inactivity(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState):
    voice_client = member.guild.voice_client
    if voice_client is None or not voice_client.is_connected():
        # We're not connected to this server, just ignore.
        return
    
    channel_members = voice_client.channel.members
    if all(member.bot for member in channel_members):
        # If all the members in the voice chat are bots, disconnect.
        await voice_client.disconnect()        

def setup_database():
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///radiobot.db")
    initialize_sql(engine)

    from .db import meta

def create_argument_parser():
    parser = ArgumentParser()
    parser.add_argument("token", type=str, help="Discord bot token.")
    return parser

def main():
    setup_database()
    parser = create_argument_parser()
    args = parser.parse_args()
    
    bot.run(args.token)

if __name__ == "__main__":
    main()