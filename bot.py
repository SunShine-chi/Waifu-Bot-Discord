import discord
from discord.ext import commands
from gtts import gTTS
import os
from dotenv import load_dotenv
import tempfile
import asyncio
from collections import defaultdict
import emoji
import re
from keep_alive import keep_alive
keep_alive()


load_dotenv()

#Gọi token từ env nè:)
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError("Token không được tìm thấy! (.env).")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

current_voice_channels = {}
current_text_channels = {}


# Biến toàn cục cho hàng đợi tin nhắn và trạng thái đang phát
message_queues = defaultdict(asyncio.Queue)  # Một hàng đợi cho mỗi guild
is_reading = defaultdict(lambda: False)  # Đánh dấu trạng thái phát cho từng guild

# Biến để theo dõi người gửi và trạng thái phát giọng nói
last_user = None
is_playing = False

@client.event
async def on_ready():
    print("Vợ bạn đã sẵn sàng!")

#Just say hello
@client.command(name='hello')
async def Hello_command(ctx):
    if ctx.guild.emojis:
        first_emoji = ctx.guild.emojis[0]
        await ctx.send(f"Hello, I'm Nắng's wife! {first_emoji}")
    else:
        await ctx.send("Hello, I'm Nắng's wife!")

#Just say goodbye
@client.command(name='goodbye')
async def Goodbye_command(ctx):
    await ctx.send("Bye bye, My Darling!")


#Join voice room

# Thêm biến tạm để xác định Bot đã sẵn sàng để nói chuyện chưa
is_ready = False

@client.command(name='join')
async def Join_command(ctx):
    global is_ready  # Tham chiếu đến biến toàn cục

    # Đảm bảo kiểm tra trạng thái của bot trước khi tham gia voice channel
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()  # Ngắt kết nối nếu đang bị lỗi trạng thái

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.guild.id not in current_voice_channels:
            try:
                current_voice_channels[ctx.guild.id] = channel
                current_text_channels[ctx.guild.id] = ctx.channel
                await channel.connect()
                await ctx.send(f"{ctx.author.mention} Em nè, em nè!")

                # Phát âm thanh chào mừng
                audio_file_path = 'audio/Halo_HuTao.mp3'  # Đường dẫn tới file âm thanh chào
                voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
                voice_client.play(discord.FFmpegPCMAudio(audio_file_path), after=lambda e: print('Done playing'))

                # Đợi cho âm thanh phát xong
                while voice_client.is_playing():
                    await asyncio.sleep(1)

                # Sau khi âm thanh phát xong, mới cho phép bot xử lý tới các việc như đọc tin nhắn                
                is_ready = True # Đánh dấu, Set lại trạng thái là Bot đã sẵn sàng
                await ctx.send("Em đã sẵn sàng để nói chuyện rồi nè <3 !")

            except discord.ClientException:
                await ctx.send("Em đang ở trong vòng tay người khác rồi!")
            except Exception as e:
                await ctx.send(f"Em đã bị lỗi rồi, huhu!: {e}")
        else:
            await ctx.send(f"{ctx.author.mention} Xin lỗi anh nhiều, em ở nơi khác rồi ạ! Em đang ở [**{current_voice_channels[ctx.guild.id].name}**]({current_voice_channels[ctx.guild.id].jump_url}) nè!.")
    else:
        await ctx.send(f"{ctx.author.mention} Anh giờ đang ở đâu, em hiện không thấy anh~~~")


#Leave voice room
@client.command(name='leave')
async def Leave_command(ctx):
    if ctx.guild.id in current_voice_channels:

        voice_client = ctx.guild.voice_client
        
        # Dừng mọi hoạt động phát âm thanh
        if voice_client.is_playing():
            voice_client.stop()  # Dừng âm thanh đang phát
            
        # Phát âm thanh tạm biệt
        audio_file_path = 'audio/G9_HuTao.mp3'  # Đường dẫn tới file âm thanh tạm biệt
        voice_client.play(discord.FFmpegPCMAudio(audio_file_path), after=lambda e: print('Done playing'))

        # Đợi cho đến khi âm thanh phát xong
        while voice_client.is_playing():
            await asyncio.sleep(1)


        await ctx.guild.voice_client.disconnect()
        del current_voice_channels[ctx.guild.id]
        del current_text_channels[ctx.guild.id]
        await ctx.send("Giờ mình phải chia xa ư?")
    else:
        await ctx.send("Em đang không ở cùng ai khác đâu")

        
COMMAND_PREFIXES = ['!', '?', '.', '/']  # Đặt danh sách tiền tố ở đây


#Lọc các kí tự tiền tố dùng để gọi bot
def is_command(message):
    return len(message) > 1 and any(message.startswith(prefix) for prefix in COMMAND_PREFIXES)

#Đọc tin nhắn (Read Chat)
@client.event
async def on_message(message):
    global current_voice_channels, current_text_channels

    # Bỏ qua tin nhắn từ bot
    if message.author == client.user:
        return

    # Xử lý nếu là lệnh bot
    if is_command(message.content):
        await client.process_commands(message)
        return

    # Kiểm tra nếu bot đang ở voice channel và sẵn sàng đọc tin nhắn
    if (message.guild.id in current_voice_channels and
        message.author.voice and
        message.author.voice.channel == current_voice_channels[message.guild.id] and
        message.channel == current_text_channels[message.guild.id] and is_ready):
        
        # Thêm tin nhắn vào hàng đợi của guild
        await message_queues[message.guild.id].put(message)

        # Nếu bot không đọc tin nhắn nào, bắt đầu task xử lý tin nhắn
        if not is_reading[message.guild.id]:
            asyncio.create_task(process_message_queue(message.guild.id))

import emoji

async def process_message_queue(guild_id):
    """Xử lý hàng đợi tin nhắn cho từng server."""
    global last_user, is_playing, is_reading

    is_reading[guild_id] = True

    while not message_queues[guild_id].empty():
        message = await message_queues[guild_id].get()

        username = message.author.display_name
        content = message.content

        # Xử lý mentions bằng tên hiển thị
        for mention in message.mentions:
            content = content.replace(mention.mention, mention.display_name)

        # Thay thế emoji tùy chỉnh bằng tên hiển thị (hoặc bỏ luôn nếu không cần)
        def replace_custom_emoji(match):
            
            emoji_name = match.group(1)  # Lấy tên emoji
            return f"emoji {emoji_name}"  # Bạn có thể thay đổi cách đọc tại đây

        print(replace_custom_emoji)
        content = re.sub(r'<:(\w+):(\d+)>', replace_custom_emoji, content)

        # Xử lý emoji Unicode
        def clean_unicode_emoji(content):
            """Loại bỏ gạch dưới và đọc emoji Unicode."""
            demojized = emoji.demojize(content)  # Chuyển đọc từ id của emoji thành tên (như ":chin_chin:")
            cleaned = demojized.replace('_', ' ')  # Bỏ gạch dưới khoảng cách trong emoji (nếu có)
            return emoji.emojize(cleaned)  # Chuyển về dạng gốc nếu cần hoặc giữ nguyên dạng text ban đầu
        

        # Xử lý emoji Unicode (nếu cần, thay thế hoặc bỏ qua)
        # content = emoji.demojize(content)  # Chuyển emoji Unicode thành tên 
        content = clean_unicode_emoji(content)

        tts_text = f"{username} nói: {content}" if last_user != username or not is_playing else content
        tts = gTTS(text=tts_text, lang='vi')

        # Tạo file tạm để phát
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            tts.save(f"{temp_file.name}.mp3")
            voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice_client and voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio(f"{temp_file.name}.mp3", executable="ffmpeg"), after=lambda e: None)

                # Đợi phát xong
                while voice_client.is_playing():
                    await asyncio.sleep(1)

        # Cập nhật trạng thái
        last_user = username
        is_playing = True

    is_reading[guild_id] = False





                                            #------Version cũ khi đặt lại trạng thái của bot khi bot rời khởi phòng voice---------#
                                            
# @client.event
# async def on_voice_state_update(member, before, after):
#     global current_voice_channels, last_user, is_playing
#     if member.bot and before.channel is not None:
#         if member.guild.id in current_voice_channels:
#             del current_voice_channels[member.guild.id]
#             del current_text_channels[member.guild.id]
#             last_user = None  # Đặt lại người gửi (về "không có")
#             is_playing = False  # Đặt lại trạng thái phát (về "stop completely" <dừng lại hoàn toàn> cho tới khi được gọi vào tiếp 1 phòng voice nào đó)






                                                ##### #------Version mới khi đặt lại trạng thái của bot khi bot rời khởi phòng voice---------# #####
                                            
                                    ###---------------Update thêm khả năng TỰ ĐỘNG OUT PHÒNG VOICE nếu như không còn ai trong phòng voice đó------------------###
                                            # Có thể hiểu là: người dùng out hết khỏi phòng voice, member's quantity = 1 (nghĩa là chỉ còn 1 mình bot) #
                                                                        # ---> Sẽ tự động out khỏi phòng #
@client.event
async def on_voice_state_update(member, before, after):
    global current_voice_channels, last_user, is_playing, is_ready
    if member.guild.id in current_voice_channels and member.guild.voice_client:
        voice_client = member.guild.voice_client

        # Kiểm tra xem có còn ai trong kênh không
        if len(voice_client.channel.members) == 1:  # Chỉ còn bot
            await voice_client.disconnect()
            del current_voice_channels[member.guild.id]
            del current_text_channels[member.guild.id]
            last_user = None
            is_playing = False
            is_ready = False  # Đặt lại trạng thái sẵn sàng



#Run token bot
client.run(TOKEN)