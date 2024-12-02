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
    global is_ready

    voice_client = ctx.guild.voice_client  # Trạng thái voice của bot trong server hiện tại
    author_voice_state = ctx.author.voice  # Trạng thái voice của người gọi lệnh

    # Kiểm tra nếu người gọi lệnh không ở phòng voice nào
    if not author_voice_state:
        await ctx.send(f"{ctx.author.mention} Anh giờ đang ở đâu, em hiện không thấy anh~~~")
        return


    # Kiểm tra nếu bot đã kết nối với phòng voice
    if voice_client and voice_client.is_connected():
        # Nếu bot đang ở cùng phòng voice với người gọi lệnh
        if author_voice_state.channel == voice_client.channel:
            await ctx.send(f"{ctx.author.mention} Em đang ở đây với anh mà~")
            return
        else:
            # Bot ở một phòng voice khác
            await ctx.send(f"{ctx.author.mention} Em đang ở {voice_client.channel.name} mất rùi~")
            return
        
    # Kiểm tra nếu `current_text_channels` đã được thiết lập rồi
    if ctx.guild.id in current_text_channels:
        # Nếu người dùng không gọi lệnh từ kênh chat đã liên kết của voice room
        if ctx.channel != current_text_channels[ctx.guild.id]:
            await ctx.send(f"{ctx.author.mention} Mình đang không chung thế giới với nhau rùi...")
            return

    # Kết nối vào phòng voice của người gọi lệnh
    try:
        channel = author_voice_state.channel
        current_voice_channels[ctx.guild.id] = channel
        current_text_channels[ctx.guild.id] = ctx.channel
        await channel.connect()
        await ctx.send(f"{ctx.author.mention} Em nè, em nè!")

        # Phát âm thanh chào mừng
        audio_file_path = 'audio/Halo_HuTao.mp3'
        voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice_client.play(discord.FFmpegPCMAudio(audio_file_path), after=lambda e: print('Done playing'))

        # Đợi cho âm thanh phát xong
        while voice_client.is_playing():
            await asyncio.sleep(1)

        # Sau khi phát xong, bot sẵn sàng xử lý tin nhắn
        is_ready = True
        await ctx.send("Em đã sẵn sàng để nói chuyện rồi nè <3 !")
    except discord.ClientException:
        await ctx.send("Em đang ở trong vòng tay người khác rồi!")
    except Exception as e:
        await ctx.send(f"Em đã bị lỗi rồi, huhu!: {e}")




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


# Loại bỏ, không đọc emoji
def remove_emoji(content):
    """Loại bỏ emoji Unicode và emoji tùy chỉnh trong nội dung tin nhắn."""
    # Loại bỏ emoji Unicode
    content_no_unicode_emoji = emoji.replace_emoji(content, replace="")

    # Loại bỏ emoji tùy chỉnh (emoji tĩnh, bản thường) có kiểu cú pháp <:emoji_name:id>
    content_no_custom_emoji = re.sub(r'<:(\w+):(\d+)>', '', content_no_unicode_emoji)

    # Loại bỏ emoji động có kiểu cú pháp <a:emoji_name:id>
    content_no_animated_emoji = re.sub(r'<a:(\w+):(\d+)>', '', content_no_custom_emoji)

    return content_no_animated_emoji


async def process_message_queue(guild_id):
    """Xử lý hàng đợi tin nhắn cho từng server."""
    global last_user, is_playing, is_reading

    is_reading[guild_id] = True

    while not message_queues[guild_id].empty():
        message = await message_queues[guild_id].get()

        username = message.author.display_name
        content = message.content

        # Loại bỏ emoji trong nội dung tin nhắn
        content = remove_emoji(content)

        # Xử lý mentions bằng tên hiển thị
        for mention in message.mentions:
            content = content.replace(mention.mention, mention.display_name)

        # # Thay thế emoji tùy chỉnh bằng tên hiển thị (hoặc bỏ luôn nếu không cần)
        # def replace_custom_emoji(match):
            
        #     emoji_name = match.group(1)  # Lấy tên emoji
        #     return f"emoji {emoji_name}"  # Sửa lại cách đọc

        # print(replace_custom_emoji)
        # content = re.sub(r'<:(\w+):(\d+)>', replace_custom_emoji, content)

        # Kiểm tra nếu tin nhắn là chứa đường link
        url_pattern = re.compile(r'(https?://\S+|www\.\S+)')  # Biểu thức chính quy phát hiện đường link (URL)
        if url_pattern.search(content):
            content = "đây là đường link đó"

        # Bỏ qua tin nhắn trống sau khi xử lý
        if not content.strip():
            continue

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
# @client.event
# async def on_voice_state_update(member, before, after):
#     global current_voice_channels, last_user, is_playing, is_ready
#     if member.guild.id in current_voice_channels and member.guild.voice_client:
#         voice_client = member.guild.voice_client

#         # Kiểm tra xem có còn ai trong kênh không
#         if len(voice_client.channel.members) == 1:  # Chỉ còn bot
#             await voice_client.disconnect()
#             del current_voice_channels[member.guild.id]
#             del current_text_channels[member.guild.id]
#             last_user = None
#             is_playing = False
#             is_ready = False  # Đặt lại trạng thái sẵn sàng

@client.event
async def on_voice_state_update(member, before, after):
    global current_voice_channels, last_user, is_playing, is_ready

    voice_client = member.guild.voice_client

    # Kiểm tra xem bot có đang ở trong voice channel không và cập nhật trạng thái
    if voice_client:
        # Nếu không còn ai trong voice channel ngoài bot, bot sẽ tự động thoát
        if len(voice_client.channel.members) == 1: #Chỉ còn bot
            await voice_client.disconnect()
            del current_voice_channels[member.guild.id]
            del current_text_channels[member.guild.id]
            last_user = None
            is_playing = False
            is_ready = False

    # Kiểm tra trạng thái của người dùng
    if member == client.user and before.channel is not None and after.channel is None:
        # Nếu bot bị ngắt kết nối đột ngột, cập nhật lại trạng thái
        if member.guild.id in current_voice_channels:
            del current_voice_channels[member.guild.id]
            del current_text_channels[member.guild.id]
            last_user = None
            is_playing = False
            is_ready = False




#Chạy oken
client.run(TOKEN)