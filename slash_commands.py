import discord
from discord import app_commands
from bot import handle_hello, handle_goodbye, handle_join, handle_leave

# Lưu ý: Các slash command không thể join/leave voice channel như prefix command do hạn chế context của interaction.
def setup_slash_commands(bot):
    @bot.tree.command(name="hello", description="Say hello")
    async def hello_slash(interaction: discord.Interaction):
        await handle_hello(interaction)

    @bot.tree.command(name="goodbye", description="Say goodbye ")
    async def goodbye_slash(interaction: discord.Interaction):
        await handle_goodbye(interaction)

    @bot.tree.command(name="join", description="Join thethe voice channel")
    async def join_slash(interaction: discord.Interaction):
        await handle_join(interaction)

    @bot.tree.command(name="leave", description="Leave the voice channel")
    async def leave_slash(interaction: discord.Interaction):
        await handle_leave(interaction)

