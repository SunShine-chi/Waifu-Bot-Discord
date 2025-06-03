import discord
from discord import app_commands

# Lưu ý: Các slash command không thể join/leave voice channel như prefix command do hạn chế context của interaction.
def setup_slash_commands(bot):
    @bot.tree.command(name="hello", description="Say hello with a slash command!")
    async def hello_slash(interaction: discord.Interaction):
        if interaction.guild and interaction.guild.emojis:
            await interaction.response.send_message(f"Hello, I'm Nắng's wife! {interaction.guild.emojis[0]}")
        else:
            await interaction.response.send_message("Hello, I'm Nắng's wife!")

    @bot.tree.command(name="goodbye", description="Say goodbye with a slash command!")
    async def goodbye_slash(interaction: discord.Interaction):
        await interaction.response.send_message("Bye bye, My Darling!")

    @bot.tree.command(name="join", description="Join your voice channel and play a welcome sound (slash version, chỉ thông báo)")
    async def join_slash(interaction: discord.Interaction):
        # Slash command không join voice được như prefix command, chỉ thông báo
        await interaction.response.send_message("(Slash) Hãy dùng lệnh prefix như !join hoặc /join truyền thống nhé!")

    @bot.tree.command(name="leave", description="Leave the voice channel and play a goodbye sound (slash version, chỉ thông báo)")
    async def leave_slash(interaction: discord.Interaction):
        await interaction.response.send_message("(Slash) Hãy dùng lệnh prefix như !leave hoặc /leave truyền thống nhé!")

    # Thêm các slash command khác tại đây nếu muốn 