import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
_manager_role_id_str = os.getenv("MANAGER_ROLE_ID")

if not DISCORD_TOKEN:
    raise ValueError("Error: DISCORD_TOKEN is not set in the environment or .env file.")

if not SUPABASE_DB_URL:
    raise ValueError("Error: SUPABASE_DB_URL is not set in the environment or .env file.")

if not _manager_role_id_str:
    raise ValueError("Error: MANAGER_ROLE_ID is not set in the environment or .env file.")

try:
    MANAGER_ROLE_ID = int(_manager_role_id_str)
except ValueError:
    raise ValueError(f"Error: MANAGER_ROLE_ID '{_manager_role_id_str}' must be a valid integer ID.")

# Optional settings
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

_test_guild_id_str = os.getenv("TEST_GUILD_ID")
TEST_GUILD_ID = None
if _test_guild_id_str:
    try:
        TEST_GUILD_ID = int(_test_guild_id_str)
    except ValueError:
        print(f"Warning: TEST_GUILD_ID '{_test_guild_id_str}' is not a valid integer. It will be ignored.")
