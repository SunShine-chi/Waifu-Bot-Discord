import discord
from discord import app_commands
from command_handlers import handle_hello, handle_goodbye, handle_join, handle_leave
from bot import AUDIO_WELCOME, AUDIO_GOODBYE

# Lưu ý: Các slash command không thể join/leave voice channel như prefix command do hạn chế context của interaction.
def setup_slash_commands(bot):
    @bot.tree.command(name="hello", description="Say hello")
    async def hello_slash(interaction: discord.Interaction):
        await handle_hello(interaction)

    @bot.tree.command(name="goodbye", description="Say goodbye")
    async def goodbye_slash(interaction: discord.Interaction):
        await handle_goodbye(interaction)

    @bot.tree.command(name="join", description="Join the voice channel you are in")
    async def join_slash(interaction: discord.Interaction):
        # Tạo một context giả giống ctx cho handle_join
        class FakeCtx:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.author = interaction.user
                self.channel = interaction.channel
                self.send = interaction.response.send_message
                self.bot = bot
        fake_ctx = FakeCtx(interaction)
        await handle_join(fake_ctx, bot=bot, AUDIO_WELCOME=AUDIO_WELCOME)

    @bot.tree.command(name="leave", description="Leave the voice channel if bot is in")
    async def leave_slash(interaction: discord.Interaction):
        class FakeCtx:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.author = interaction.user
                self.channel = interaction.channel
                self.send = interaction.response.send_message
                self.bot = bot
        fake_ctx = FakeCtx(interaction)
        await handle_leave(fake_ctx, bot=bot, AUDIO_GOODBYE=AUDIO_GOODBYE)

