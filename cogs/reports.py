import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from discord import app_commands
import database
import config
from utils.embeds import success_embed, error_embed, info_embed
import pytz
from datetime import datetime, timedelta

def format_time_only(dt: datetime, tz_name: str) -> str:
    """
    Helper to format datetime to HH:MM AM/PM in the target timezone.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    local_dt = dt.astimezone(pytz.timezone(tz_name))
    return local_dt.strftime("%I:%M %p")

def format_duration(minutes: float) -> str:
    """
    Converts duration in decimal minutes to a clean readable string.
    """
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

class ReportsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mysummary", description="View your daily work log and total hours for today")
    async def mysummary(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            sessions = await database.get_user_today_summary(self.bot.db_pool, user_id, guild_id, config.TIMEZONE)
            
            tz = pytz.timezone(config.TIMEZONE)
            today_str = datetime.now(tz).strftime('%A, %b %d, %Y')
            
            if not sessions:
                embed = info_embed(
                    "Today's Summary",
                    f"No work sessions recorded for today, **{today_str}**."
                )
                await interaction.followup.send(embed=embed)
                return
            
            total_minutes = 0.0
            session_list = []
            
            for idx, sess in enumerate(sessions, 1):
                in_time = sess["clock_in_time"]
                out_time = sess["clock_out_time"]
                
                in_str = format_time_only(in_time, config.TIMEZONE)
                
                if out_time:
                    out_str = format_time_only(out_time, config.TIMEZONE)
                    dur = float(sess["duration_minutes"])
                    total_minutes += dur
                    dur_str = format_duration(dur)
                    session_list.append(f"`Session {idx}:` {in_str} - {out_str} ({dur_str})")
                else:
                    # Active session
                    if in_time.tzinfo is None:
                        in_time = in_time.replace(tzinfo=pytz.utc)
                    elapsed = (datetime.now(pytz.utc) - in_time).total_seconds() / 60.0
                    total_minutes += elapsed
                    session_list.append(f"`Session {idx}:` {in_str} - *Active* ({format_duration(elapsed)} elapsed)")
            
            embed = info_embed(
                f"Your Today's Summary",
                f"Work log for **{today_str}**"
            )
            embed.add_field(name="Sessions Logged", value="\n".join(session_list), inline=False)
            embed.add_field(name="Total Time Worked", value=f"🏆 **{format_duration(total_minutes)}**", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="weeklysummary", description="View 7-day total hours summary")
    @app_commands.describe(user="The user to view weekly hours for (optional)")
    async def weeklysummary(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        
        target_user = user or interaction.user
        user_id = str(target_user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            sessions = await database.get_user_weekly_summary(self.bot.db_pool, user_id, guild_id, config.TIMEZONE)
            
            tz = pytz.timezone(config.TIMEZONE)
            today = datetime.now(tz).date()
            start_date = today - timedelta(days=6)
            
            # Group sessions by date
            daily_totals = {start_date + timedelta(days=i): 0.0 for i in range(7)}
            
            total_weekly_minutes = 0.0
            
            for sess in sessions:
                sess_date = sess["date"]
                if sess_date in daily_totals:
                    out_time = sess["clock_out_time"]
                    if out_time:
                        dur = float(sess["duration_minutes"])
                        daily_totals[sess_date] += dur
                        total_weekly_minutes += dur
                    else:
                        # Active session: calculate elapsed till now
                        in_time = sess["clock_in_time"]
                        if in_time.tzinfo is None:
                            in_time = in_time.replace(tzinfo=pytz.utc)
                        elapsed = (datetime.now(pytz.utc) - in_time).total_seconds() / 60.0
                        daily_totals[sess_date] += elapsed
                        total_weekly_minutes += elapsed
            
            embed = info_embed(
                f"Weekly Hours Summary",
                f"7-Day work report for **{target_user.display_name}**\n"
                f"Period: *{start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}*"
            )
            
            breakdown = []
            for day, minutes in daily_totals.items():
                day_name = day.strftime('%a (%b %d)')
                dur_str = format_duration(minutes) if minutes > 0 else "`0m`"
                
                # Highlight today
                if day == today:
                    breakdown.append(f"👉 **{day_name}:** {dur_str}")
                else:
                    breakdown.append(f"📅 **{day_name}:** {dur_str}")
            
            embed.description += "\n\n" + "\n".join(breakdown)
            embed.add_field(
                name="Total Hours Worked", 
                value=f"⏱️ **{format_duration(total_weekly_minutes)}**", 
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="teamreport", description="View team work sessions on a specific date")
    @app_commands.describe(date="The date to view report for in YYYY-MM-DD format (defaults to today)")
    async def teamreport(self, interaction: discord.Interaction, date: str = None):
        await interaction.response.defer(ephemeral=False)
        
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            if date:
                try:
                    target_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
                except ValueError:
                    embed = error_embed(
                        "Invalid Date",
                        "Please provide a valid date in **YYYY-MM-DD** format."
                    )
                    await interaction.followup.send(embed=embed)
                    return
            else:
                target_date = datetime.now(tz).date()
                
            sessions = await database.get_team_report(self.bot.db_pool, guild_id, target_date)
            date_display = target_date.strftime('%A, %b %d, %Y')
            
            if not sessions:
                embed = info_embed(
                    "Team Work Report",
                    f"No work sessions recorded for **{date_display}**."
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Build monospaced report table
            header = f"{'Member':<15} | {'In':<8} | {'Out':<8} | {'Duration':<8}\n"
            divider = f"{'-'*16}+{'-'*10}+{'-'*10}+{'-'*9}\n"
            table_lines = [header, divider]
            
            total_team_minutes = 0.0
            
            for sess in sessions:
                user = sess["username"]
                if len(user) > 14:
                    user = user[:12] + ".."
                    
                in_str = format_time_only(sess["clock_in_time"], config.TIMEZONE)
                
                out_time = sess["clock_out_time"]
                if out_time:
                    out_str = format_time_only(out_time, config.TIMEZONE)
                    dur = float(sess["duration_minutes"])
                    total_team_minutes += dur
                    dur_str = format_duration(dur)
                else:
                    out_str = "Active"
                    in_time = sess["clock_in_time"]
                    if in_time.tzinfo is None:
                        in_time = in_time.replace(tzinfo=pytz.utc)
                    elapsed = (datetime.now(pytz.utc) - in_time).total_seconds() / 60.0
                    total_team_minutes += elapsed
                    dur_str = format_duration(elapsed)
                    
                table_lines.append(f"{user:<15} | {in_str:<8} | {out_str:<8} | {dur_str:<8}\n")
                
            table_str = "".join(table_lines)
            
            embed = info_embed(
                f"Team Work Report",
                f"Sessions for **{date_display}**"
            )
            embed.add_field(
                name="Work Log Table", 
                value=f"```text\n{table_str}```", 
                inline=False
            )
            embed.add_field(
                name="Total Team Logged Hours", 
                value=f"📈 **{format_duration(total_team_minutes)}**", 
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReportsCog(bot))
