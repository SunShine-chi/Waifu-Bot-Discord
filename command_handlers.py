import discord
import asyncio

async def handle_hello(ctx_or_interaction):
    guild = getattr(ctx_or_interaction, "guild", None)
    emojis = getattr(guild, "emojis", []) if guild else []
    msg = f"Hello, I'm Nắng's wife! {emojis[0]}" if emojis else "Hello, I'm Nắng's wife!"
    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(msg)
    elif hasattr(ctx_or_interaction, "response"):
        await ctx_or_interaction.response.send_message(msg)

async def handle_goodbye(ctx_or_interaction):
    msg = "Bye bye, My Darling!"
    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(msg)
    elif hasattr(ctx_or_interaction, "response"):
        await ctx_or_interaction.response.send_message(msg)

async def handle_join(ctx_or_interaction, bot=None, AUDIO_WELCOME=None):
    is_slash = hasattr(ctx_or_interaction, '_interaction')
    if is_slash:
        await ctx_or_interaction.send('Đang kết nối vào voice channel, vui lòng chờ...')
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
        await ctx_or_interaction.send('Đang rời khỏi voice channel, vui lòng chờ...')
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