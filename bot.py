import discord
from discord.ext import commands
from gtts import gTTS
import os
from dotenv import load_dotenv
import tempfile
import asyncio
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
    global current_voice_channels, current_text_channels, last_user, is_playing

    if message.author == client.user:
        return

    # Kiểm tra xem tin nhắn có phải là lệnh không
    if is_command(message.content):
        await client.process_commands(message)
        return   

    if message.content.lower() == "anh ken là kiểu người gì?":
        await message.channel.send("Anh Ken là đồ tồi, đồi tồi tệ, tồi tệ nhất trên đời")

    if (message.guild.id in current_voice_channels and
            message.author.voice and
            message.author.voice.channel == current_voice_channels[message.guild.id] and
            message.channel == current_text_channels[message.guild.id] and is_ready): # <=== Chỉ xử lí phần đọc chat khi BOT READY: SẴN SÀNG # Chỉ xử lý khi bot đã sẵn sàng):
                                                                                                                ### VERRY IMPORTANT ###
        username = message.author.display_name
        tts_text = f"{username} nói: {message.content}"
        
        # Kiểm tra xem có phải người này là người đang nhắn trước đó không
        if last_user == username and is_playing:
            # Nếu là người nhắn liên tiếp, chỉ đọc nội dung
            tts = gTTS(text=message.content, lang='vi')
        else:
            # Nếu là người vừa nhắn hoặc người khác nhắn cắt ngang, đọc lại cả tên giới thiệu như bình thường
            tts = gTTS(text=tts_text, lang='vi')
            is_playing = True  # Đánh dấu là đang phát giọng nói đọc tin nhắn
            last_user = username  # Cập nhật lại người gửi tin nhắn

        # Tạo và phát file âm thanh
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            tts.save(f"{temp_file.name}.mp3")
            voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice_client and voice_client.is_connected():

                # Play audio (text chat -> file audio.mp3)  của  Ver 1.2.1
                # voice_client.play(discord.FFmpegPCMAudio(f"{temp_file.name}.mp3", executable="E:/ffmpeg/bin/ffmpeg.exe"), after=lambda e: print('Done playing'))

                # Play audio (text chat -> file audio.mp3)  của  Ver 1.2.2
                voice_client.play(discord.FFmpegPCMAudio(f"{temp_file.name}.mp3", executable="ffmpeg"), after=lambda e: print('Done playing'))


                # Đợi cho đến khi âm thanh phát xong
                while voice_client.is_playing():
                    await asyncio.sleep(1)
            else:
                await message.channel.send(f"{message.author.mention} Em không có đang ở trong kênh voice đâu.")

    await client.process_commands(message)




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