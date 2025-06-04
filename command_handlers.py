import discord
import asyncio

async def handle_hello(ctx_or_interaction, bot=None):
    author_id = None
    if hasattr(ctx_or_interaction, "author"):
        author_id = ctx_or_interaction.author.id
    elif hasattr(ctx_or_interaction, "user"):
        author_id = ctx_or_interaction.user.id

    is_owner = False
    owner_id = None

    if bot:
        app_info = await bot.application_info()
        owner_id = app_info.owner.id
        if author_id == owner_id:
            is_owner = True

    if is_owner:
        guild = getattr(ctx_or_interaction, "guild", None)
        emojis = getattr(guild, "emojis", []) if guild else []
        msg = f"Ahola, my Darling! {emojis[0]}" if emojis else "Ahola, my Darling!"
    else:
        user_name = ctx_or_interaction.author.display_name if hasattr(ctx_or_interaction, "author") else ctx_or_interaction.user.display_name
        owner_mention = f"<@{owner_id}>" if owner_id else "chủ nhân của em"
        msg = f"Xin chào bạn {user_name} nha! Em là vợ của Nắng nè~~~! Đây là link tài khoản của anh {owner_mention} ấy á!:33"

    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(msg)
    elif hasattr(ctx_or_interaction, "response"):
        await ctx_or_interaction.response.send_message(msg)

async def handle_goodbye(ctx_or_interaction, bot=None):
    author_id = None
    if hasattr(ctx_or_interaction, "author"):
        author_id = ctx_or_interaction.author.id
    elif hasattr(ctx_or_interaction, "user"):
        author_id = ctx_or_interaction.user.id

    is_owner = False
    if bot:
        app_info = await bot.application_info()
        owner_id = app_info.owner.id
        if author_id == owner_id:
            is_owner = True

    if is_owner:
        msg = "Anh Nắng ngủ ngon ạ! Iu anh, Darling <3"
    else:
        user_name = ctx_or_interaction.author.display_name if hasattr(ctx_or_interaction, "author") else ctx_or_interaction.user.display_name
        msg = f"Ngủ ngon nha {user_name}, người có vẻ là bạn của Darling!"

    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(msg)
    elif hasattr(ctx_or_interaction, "response"):
        await ctx_or_interaction.response.send_message(msg)

async def handle_join(ctx_or_interaction, bot=None, AUDIO_WELCOME=None):
    is_slash = hasattr(ctx_or_interaction, '_interaction')
    if is_slash:
        await ctx_or_interaction.send('Anh gọi em hả~~~?')
    if hasattr(ctx_or_interaction, "author"):
        ctx = ctx_or_interaction
        guild_id = ctx.guild.id
        voice_client = ctx.guild.voice_client
        if not ctx.author.voice:
            await ctx.send(f"{ctx.author.mention} Anh giờ đang ở đâu, em hiện không thấy anh~~~")
            return
        voice_channel = ctx.author.voice.channel
        text_channel = ctx.channel
        if text_channel.name != voice_channel.name:
            await ctx.send(f"Anh chỉ được gọi em ở chat room **{voice_channel.name}** thôi nhé!")
            return
        if voice_client and voice_client.is_connected():
            if ctx.author.voice and ctx.author.voice.channel == voice_client.channel:
                await ctx.send(f"{ctx.author.mention} Em đang ở đây với anh mà~")
                return
            else:
                await voice_client.disconnect()
                if bot:
                    bot.current_voice_channels.pop(guild_id, None)
                    bot.current_text_channels.pop(guild_id, None)
        try:
            if bot:
                bot.current_voice_channels[guild_id] = voice_channel
                bot.current_text_channels[guild_id] = text_channel
            await voice_channel.connect()
            await ctx.send(f"{ctx.author.mention} Em nè, em nè!")
            voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if voice_client and AUDIO_WELCOME:
                voice_client.play(discord.FFmpegPCMAudio(AUDIO_WELCOME), after=lambda e: print('Done playing'))
                while voice_client.is_playing():
                    await asyncio.sleep(1)
            if bot:
                bot.is_ready = True
            await ctx.send("Em đã sẵn sàng để nói chuyện rồi nè <3 !")
        except discord.ClientException:
            await ctx.send("Em đang ở trong vòng tay người khác rồi!")
        except Exception as e:
            await ctx.send(f"Em đã bị lỗi rồi, huhu!: {e}")
    elif hasattr(ctx_or_interaction, "response") and not is_slash:
        await ctx_or_interaction.response.send_message(
            "Hãy dùng lệnh prefix như !join hoặc /join truyền thống nhé!"
        )

async def handle_leave(ctx_or_interaction, bot=None, AUDIO_GOODBYE=None):
    is_slash = hasattr(ctx_or_interaction, '_interaction')
    if is_slash:
        await ctx_or_interaction.send('Thật sao?~')
    if hasattr(ctx_or_interaction, "author"):
        ctx = ctx_or_interaction
        guild_id = ctx.guild.id
        voice_client = ctx.guild.voice_client
        if bot and guild_id in bot.current_voice_channels and voice_client:
            if voice_client.is_playing():
                voice_client.stop()
            if AUDIO_GOODBYE:
                voice_client.play(discord.FFmpegPCMAudio(AUDIO_GOODBYE), after=lambda e: print('Done playing'))
                while voice_client.is_playing():
                    await asyncio.sleep(1)
            await voice_client.disconnect()
            bot.current_voice_channels.pop(guild_id, None)
            bot.current_text_channels.pop(guild_id, None)
            await ctx.send("Giờ mình phải chia xa ư?")
        else:
            await ctx.send("Em đang không ở cùng ai khác đâu")
    elif hasattr(ctx_or_interaction, "response") and not is_slash:
        await ctx_or_interaction.response.send_message(
            "Hãy dùng lệnh prefix như !leave hoặc /leave truyền thống nhé!"
        )

async def handle_helphumi(ctx_or_interaction):
    help_message = (
        "Chào anh nha! Em là vợ của Nắng đây <3! Anh có thể dùng các lệnh sau để tương tác với em nhé :33:\n"
        "\n"  # Add an empty line for better readability
        "**`/hello` hoặc `!hello`**: Em sẽ chào hỏi anh đó!\n"
        "**`/goodbye` hoặc `!goodbye`**: Em sẽ tạm biệt anh đó!\n"
        "**`/join` hoặc `!join`**: Em sẽ vào kênh thoại anh đang ở và nói chuyện với anh đó!\n"
        "**`/leave` hoặc `!leave`**: Em sẽ rời kênh thoại và tạm biệt anh đó!\n"
        "\n"
        "Em rất vui được trò chuyện cùng anh. Anh còn muốn biết gì nữa không?"
    )
    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(help_message)
    elif hasattr(ctx_or_interaction, "response"):
        await ctx_or_interaction.response.send_message(help_message) 