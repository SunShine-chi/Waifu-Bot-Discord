# Standard library imports
import os
import tempfile
import asyncio
import re
from collections import defaultdict

# Third-party imports
import discord
from discord.ext import commands
from gtts import gTTS
from dotenv import load_dotenv
import emoji
from slash_commands import setup_slash_commands

# Local imports
from keep_alive import keep_alive

# =====================
# === Configuration ===
# =====================

COMMAND_PREFIXES = ['!', '?', '.', '/']
AUDIO_WELCOME = 'audio/Halo_HuTao.mp3'
AUDIO_GOODBYE = 'audio/G9_HuTao.mp3'

# =====================
# === Initialization ===
# =====================

keep_alive()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError("Token không được tìm thấy! (.env).")

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        setup_slash_commands(self)
        await self.tree.sync()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = MyBot(command_prefix=COMMAND_PREFIXES[0], intents=intents, case_insensitive=True)

# =====================
# === State Storage ===
# =====================

bot.current_voice_channels = {}
bot.current_text_channels = {}
bot.message_queues = defaultdict(asyncio.Queue)  # Queue per guild
bot.is_reading = defaultdict(lambda: False)      # Reading state per guild
bot.last_user = None
bot.is_playing = False
bot.is_ready = False

# =====================
# === Utils Section ===
# =====================

def is_command(message: str) -> bool:
    """Check if a message is a command based on prefixes."""
    return len(message) > 1 and any(message.startswith(prefix) for prefix in COMMAND_PREFIXES)

def remove_emoji(content: str) -> str:
    """Remove both Unicode and custom Discord emojis from content."""
    content = emoji.replace_emoji(content, replace="")
    content = re.sub(r'<:(\w+):(\d+)>', '', content)
    content = re.sub(r'<a:(\w+):(\d+)>', '', content)
    return content

def clean_unicode_emoji(content: str) -> str:
    """Convert Unicode emoji to text, remove underscores."""
    demojized = emoji.demojize(content)
    cleaned = demojized.replace('_', ' ')
    return emoji.emojize(cleaned)

# =====================
# === Events Section ===
# =====================

@bot.event
async def on_ready():
    print("Vợ bạn đã sẵn sàng!")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands
    if is_command(message.content):
        await bot.process_commands(message)
        return

    # Only read messages if bot is in the correct voice/text channel and ready
    guild_id = message.guild.id
    if (guild_id in bot.current_voice_channels and
        message.author.voice and
        message.author.voice.channel == bot.current_voice_channels[guild_id] and
        message.channel == bot.current_text_channels[guild_id] and bot.is_ready):
        await bot.message_queues[guild_id].put(message)
        if not bot.is_reading[guild_id]:
            asyncio.create_task(process_message_queue(guild_id))

@bot.event
async def on_voice_state_update(member, before, after):
    guild_id = member.guild.id
    voice_client = member.guild.voice_client

    # Auto-leave if alone in voice channel
    if voice_client and len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        bot.current_voice_channels.pop(guild_id, None)
        bot.current_text_channels.pop(guild_id, None)
        bot.last_user = None
        bot.is_playing = False
        bot.is_ready = False

    # If bot is disconnected, reset state
    if member == bot.user and before.channel and after.channel is None:
        bot.current_voice_channels.pop(guild_id, None)
        bot.current_text_channels.pop(guild_id, None)
        bot.last_user = None
        bot.is_playing = False
        bot.is_ready = False

# =====================
# === Commands Section ===
# =====================

@bot.command(name='hello')
async def hello_command(ctx):
    """Say hello with the first server emoji if available."""
    if ctx.guild and ctx.guild.emojis:
        await ctx.send(f"Hello, I'm Nắng's wife! {ctx.guild.emojis[0]}")
    else:
        await ctx.send("Hello, I'm Nắng's wife!")

@bot.command(name='goodbye')
async def goodbye_command(ctx):
    """Say goodbye."""
    await ctx.send("Bye bye, My Darling!")

@bot.command(name='join')
async def join_command(ctx):
    """Join the user's voice channel and play a welcome sound."""
    guild_id = ctx.guild.id
    voice_client = ctx.guild.voice_client

    # Kiểm tra user có ở voice không
    if not ctx.author.voice:
        await ctx.send(f"{ctx.author.mention} Anh giờ đang ở đâu, em hiện không thấy anh~~~")
        return

    voice_channel = ctx.author.voice.channel
    text_channel = ctx.channel

    # Chỉ cho phép gọi bot nếu tên text channel trùng với tên voice channel
    if text_channel.name != voice_channel.name:
        await ctx.send(f"Anh chỉ được gọi em ở chat room **{voice_channel.name}** thôi nhé!")
        return

    if voice_client and voice_client.is_connected():
        if ctx.author.voice and ctx.author.voice.channel == voice_client.channel:
            await ctx.send(f"{ctx.author.mention} Em đang ở đây với anh mà~")
            return
        else:
            await voice_client.disconnect()
            bot.current_voice_channels.pop(guild_id, None)
            bot.current_text_channels.pop(guild_id, None)

    try:
        bot.current_voice_channels[guild_id] = voice_channel
        bot.current_text_channels[guild_id] = text_channel
        await voice_channel.connect()
        await ctx.send(f"{ctx.author.mention} Em nè, em nè!")

        # Play welcome audio
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            voice_client.play(discord.FFmpegPCMAudio(AUDIO_WELCOME), after=lambda e: print('Done playing'))
            while voice_client.is_playing():
                await asyncio.sleep(1)

        bot.is_ready = True
        await ctx.send("Em đã sẵn sàng để nói chuyện rồi nè <3 !")
    except discord.ClientException:
        await ctx.send("Em đang ở trong vòng tay người khác rồi!")
    except Exception as e:
        await ctx.send(f"Em đã bị lỗi rồi, huhu!: {e}")

@bot.command(name='leave')
async def leave_command(ctx):
    """Leave the voice channel and play a goodbye sound."""
    guild_id = ctx.guild.id
    voice_client = ctx.guild.voice_client

    if guild_id in bot.current_voice_channels and voice_client:
        if voice_client.is_playing():
            voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio(AUDIO_GOODBYE), after=lambda e: print('Done playing'))
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()
        bot.current_voice_channels.pop(guild_id, None)
        bot.current_text_channels.pop(guild_id, None)
        await ctx.send("Giờ mình phải chia xa ư?")
    else:
        await ctx.send("Em đang không ở cùng ai khác đâu")

# =====================
# === Message Queue Processing ===
# =====================

async def process_message_queue(guild_id):
    """Process the message queue for a guild, reading messages aloud."""
    bot.is_reading[guild_id] = True
    while not bot.message_queues[guild_id].empty():
        message = await bot.message_queues[guild_id].get()
        username = message.author.display_name
        content = message.content
        content = remove_emoji(content)
        for mention in message.mentions:
            content = content.replace(mention.mention, mention.display_name)
        url_pattern = re.compile(r'(https?://\S+|www\.\S+)')
        if url_pattern.search(content):
            content = ""
        if not content.strip():
            continue
        content = clean_unicode_emoji(content)
        tts_text = f"{username} nói: {content}" if bot.last_user != username or not bot.is_playing else content
        tts = gTTS(text=tts_text, lang='vi')
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            tts.save(f"{temp_file.name}.mp3")
            voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)
            if voice_client and voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio(f"{temp_file.name}.mp3", executable="ffmpeg"), after=lambda e: None)
                while voice_client.is_playing():
                    await asyncio.sleep(1)
        bot.last_user = username
        bot.is_playing = True
    bot.is_reading[guild_id] = False

# =====================
# === Run the Bot ===
# =====================

bot.run(TOKEN)