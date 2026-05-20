import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from discord import app_commands
import database
import config
from utils.embeds import success_embed, error_embed, info_embed
import pytz
from datetime import datetime

def format_local_time(dt: datetime, tz_name: str) -> str:
    """
    Formats a datetime in the given timezone into a user-friendly 12-hour format.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    local_dt = dt.astimezone(pytz.timezone(tz_name))
    return local_dt.strftime("%I:%M %p")

class ClockCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clockin", description="Start a work session")
    async def clockin(self, interaction: discord.Interaction):
        # Acknowledge the interaction
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        username = interaction.user.display_name
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            # Check for existing open session
            open_sess = await database.get_open_session(self.bot.db_pool, user_id, guild_id)
            if open_sess:
                clock_in_formatted = format_local_time(open_sess["clock_in_time"], config.TIMEZONE)
                embed = error_embed(
                    "Already Clocked In",
                    f"You already have an active work session! You clocked in at **{clock_in_formatted}**.\n"
                    f"Please clock out using `/clockout` before starting a new session."
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Start new session
            new_sess = await database.create_session(
                self.bot.db_pool, user_id, username, guild_id, config.TIMEZONE
            )
            clock_in_formatted = format_local_time(new_sess["clock_in_time"], config.TIMEZONE)
            
            embed = success_embed(
                "Clocked In!",
                f"Your work session has started.\n"
                f"**Time:** {clock_in_formatted} (IST)\n"
                f"**Date:** {new_sess['date'].strftime('%Y-%m-%d')}"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="clockout", description="End the active session")
    async def clockout(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            # Check if clocked in
            open_sess = await database.get_open_session(self.bot.db_pool, user_id, guild_id)
            if not open_sess:
                embed = error_embed(
                    "Not Clocked In",
                    "You do not have an active work session. Use `/clockin` to start working!"
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Close session
            closed_sess = await database.close_session(
                self.bot.db_pool, open_sess["id"], open_sess["clock_in_time"]
            )
            
            total_minutes = float(closed_sess["duration_minutes"])
            hours = int(total_minutes // 60)
            mins = int(total_minutes % 60)
            duration_str = f"**{hours}h {mins}m**" if hours > 0 else f"**{mins}m**"
            
            clock_in_str = format_local_time(closed_sess["clock_in_time"], config.TIMEZONE)
            clock_out_str = format_local_time(closed_sess["clock_out_time"], config.TIMEZONE)
            
            embed = success_embed(
                "Clocked Out!",
                f"Successfully saved your work session.\n"
                f"**Clocked In:** {clock_in_str}\n"
                f"**Clocked Out:** {clock_out_str}\n"
                f"**Total Duration:** {duration_str}"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="status", description="See your current session state and live duration")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            open_sess = await database.get_open_session(self.bot.db_pool, user_id, guild_id)
            if not open_sess:
                embed = info_embed(
                    "WorkClock Status",
                    f"**State:** `🔴 Clocked Out`\n\nUse `/clockin` to start a new work session."
                )
                await interaction.followup.send(embed=embed)
                return
            
            clock_in = open_sess["clock_in_time"]
            if clock_in.tzinfo is None:
                clock_in = clock_in.replace(tzinfo=pytz.utc)
            
            now_utc = datetime.now(pytz.utc)
            duration = now_utc - clock_in
            total_minutes = duration.total_seconds() / 60.0
            
            hours = int(total_minutes // 60)
            mins = int(total_minutes % 60)
            duration_str = f"**{hours}h {mins}m**" if hours > 0 else f"**{mins}m**"
            
            clock_in_str = format_local_time(clock_in, config.TIMEZONE)
            
            embed = info_embed("WorkClock Status")
            embed.description = "**State:** `🟢 Active Session`"
            embed.add_field(name="Clocked In At", value=f"{clock_in_str} (IST)", inline=True)
            embed.add_field(name="Current Duration", value=duration_str, inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(ClockCog(bot))
