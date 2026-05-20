import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from discord import app_commands
import database
import config
from utils.embeds import success_embed, error_embed, info_embed
import pytz
from datetime import datetime, timedelta

def format_duration(minutes: float) -> str:
    """
    Converts duration in decimal minutes to a clean readable string.
    """
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the weekly work hours leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            records = await database.get_weekly_leaderboard(self.bot.db_pool, guild_id, config.TIMEZONE)
            
            tz = pytz.timezone(config.TIMEZONE)
            today = datetime.now(tz).date()
            start_date = today - timedelta(days=6)
            
            period_str = f"*{start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}*"
            
            if not records:
                embed = info_embed(
                    "Weekly Leaderboard",
                    f"No recorded work sessions for the week of {period_str}."
                )
                await interaction.followup.send(embed=embed)
                return
                
            leaderboard_lines = []
            medals = ["🥇", "🥈", "🥉"]
            
            for idx, row in enumerate(records, 1):
                username = row["username"]
                total_minutes = float(row["total_minutes"])
                duration_str = format_duration(total_minutes)
                
                if idx <= 3:
                    medal = medals[idx - 1]
                    leaderboard_lines.append(f"{medal} **{username}** — {duration_str}")
                else:
                    leaderboard_lines.append(f"👤 `{idx:02d}.` **{username}** — {duration_str}")
                    
            embed = info_embed(
                "🏆 WorkClock Leaderboard",
                f"Top contributors this week ({period_str}):\n\n" + "\n".join(leaderboard_lines)
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
