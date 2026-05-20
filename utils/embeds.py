import discord
from datetime import datetime

def success_embed(title: str, description: str) -> discord.Embed:
    """
    Creates a standardized green Discord embed indicating success.
    """
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x2ecc71,  # Emerald Green
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="WorkClock • Success")
    return embed

def error_embed(title: str, description: str) -> discord.Embed:
    """
    Creates a standardized red Discord embed indicating error.
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xe74c3c,  # Alizarin Red
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="WorkClock • Error")
    return embed

def info_embed(title: str, description: str = None) -> discord.Embed:
    """
    Creates a standardized blue Discord embed indicating info / report data.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=0x3498db,  # Peter River Blue
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="WorkClock • Report")
    return embed
