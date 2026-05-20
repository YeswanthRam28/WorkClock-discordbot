# WorkClock Bot — Step-by-Step Build Guide

---

## Prerequisites

- Python 3.11+ installed
- A Discord account with access to Discord Developer Portal
- A Supabase account (free tier works)
- Basic terminal / command line familiarity

---

## PHASE 1 — Discord Bot Setup

### Step 1: Create the Bot on Discord Developer Portal

1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **"New Application"** → give it a name (e.g. `WorkClock`)
3. Go to the **"Bot"** tab on the left sidebar
4. Click **"Add Bot"** → confirm
5. Under **"Privileged Gateway Intents"**, enable:
   - `SERVER MEMBERS INTENT`
   - `MESSAGE CONTENT INTENT`
6. Click **"Reset Token"** → copy and save the token somewhere safe (you'll need it for `.env`)

### Step 2: Invite the Bot to Your Server

1. Go to the **"OAuth2"** tab → **"URL Generator"**
2. Under **Scopes**, check: `bot` and `applications.commands`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Embed Links`
   - `Use Slash Commands`
   - `Read Message History`
4. Copy the generated URL → open it in your browser → select your server → **Authorize**

### Step 3: Get Your Manager Role ID

1. In Discord, go to your server **Settings → Roles**
2. Right-click the manager/admin role → **"Copy Role ID"** (you may need Developer Mode on: User Settings → Advanced → Developer Mode)
3. Save this ID for `.env`

---

## PHASE 2 — Supabase Database Setup

### Step 4: Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) → **New Project**
2. Give it a name, set a strong DB password, pick the closest region
3. Wait for provisioning (~1 min)

### Step 5: Create the Database Table

1. In your Supabase project, go to **SQL Editor** (left sidebar)
2. Paste and run this SQL:

```sql
CREATE TABLE work_sessions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    clock_in_time TIMESTAMPTZ NOT NULL,
    clock_out_time TIMESTAMPTZ,
    duration_minutes NUMERIC(8, 2),
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_work_sessions_user_date ON work_sessions(user_id, date);
CREATE INDEX idx_work_sessions_guild_date ON work_sessions(guild_id, date);
```

3. Click **Run** — confirm the table appears under **Table Editor**

### Step 6: Get Your Database Connection String

1. Go to **Project Settings → Database**
2. Under **Connection string**, select **URI**
3. Copy the string — it looks like:
   `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
4. Replace `[YOUR-PASSWORD]` with your actual DB password
5. Save this for `.env`

---

## PHASE 3 — Local Project Setup

### Step 7: Create Project Folder & Virtual Environment

```bash
mkdir workclock-bot
cd workclock-bot
python -m venv venv

# Activate venv:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 8: Install Dependencies

```bash
pip install discord.py asyncpg python-dotenv
```

Create `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Step 9: Create the `.env` File

Create a file named `.env` in your project root:

```
DISCORD_TOKEN=your_discord_bot_token_here
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
MANAGER_ROLE_ID=your_manager_role_id_here
```

> **Never commit `.env` to Git.** Add it to `.gitignore` immediately.

### Step 10: Create `.gitignore`

```
venv/
.env
__pycache__/
*.pyc
```

---

## PHASE 4 — Build the Bot (Hand to AI IDE)

### Step 11: Set Up the File Structure

Create these files and folders manually (your AI IDE will fill them):

```
workclock-bot/
├── bot.py
├── config.py
├── database.py
├── cogs/
│   ├── __init__.py
│   ├── clock.py
│   ├── reports.py
│   └── leaderboard.py
├── utils/
│   ├── __init__.py
│   └── embeds.py
├── .env
├── .gitignore
└── requirements.txt
```

### Step 12: Use the AI IDE Prompt

Open your AI IDE (Cursor, Windsurf, etc.) and paste the contents of `bot_idea_description.md` as context. Then give it this implementation prompt:

---

**AI IDE Prompt to paste:**

> "Build the complete WorkClock Discord bot based on the spec above. Use `discord.py` v2.x with slash commands via `discord.app_commands`. Use `asyncpg` for async PostgreSQL queries with a connection pool initialized on bot startup. Structure the code across `bot.py`, `config.py`, `database.py`, `cogs/clock.py`, `cogs/reports.py`, `cogs/leaderboard.py`, and `utils/embeds.py` exactly as described.
>
> Key requirements:
> - All commands are slash commands
> - Clock-in/out logic must check for open sessions before inserting/updating
> - Team report requires manager role check via `interaction.user.roles`
> - All responses use Discord embeds (green for success, red for errors, blue for info)
> - Global error handler in `bot.py` for `on_app_command_error`
> - Load DB URL and token from environment variables via `python-dotenv`
> - The asyncpg pool must be created in `bot.py` on `on_ready` and passed to cogs"

---

## PHASE 5 — Run & Test

### Step 13: Run the Bot Locally

```bash
# Make sure venv is active
python bot.py
```

You should see in your terminal:
```
Logged in as WorkClock#1234
Synced X commands
DB pool connected
```

### Step 14: Test Each Command in Discord

Test in this order:
1. `/clockin` → should return green success embed with timestamp
2. `/clockin` again → should return red error "already clocked in"
3. `/status` → should show active session duration
4. `/clockout` → should return duration worked
5. `/clockout` again → should return red error "not clocked in"
6. `/mysummary` → should show today's session log
7. `/teamreport` (as manager) → should show full team table
8. `/weeklysummary` → should show 7-day total

### Step 15: Check Data in Supabase

Go to Supabase → **Table Editor → work_sessions** and verify rows are being inserted and updated correctly after each clock in/out.

---

## PHASE 6 — Deploy to Production

### Step 16: Deploy on Railway (Recommended for Free Hosting)

1. Push your project to a **GitHub repo** (make sure `.env` is in `.gitignore`)
2. Go to [https://railway.app](https://railway.app) → **New Project → Deploy from GitHub Repo**
3. Select your repo
4. In Railway's dashboard, go to **Variables** and add all your `.env` variables:
   - `DISCORD_TOKEN`
   - `SUPABASE_DB_URL`
   - `MANAGER_ROLE_ID`
5. Railway auto-detects Python. Add a `Procfile` in your project root:
   ```
   worker: python bot.py
   ```
6. Deploy → Railway starts the bot. Check the **Logs** tab to confirm it's running.

### Step 17: Verify in Discord

Run `/clockin` from Discord after deployment. Confirm the bot responds and the row appears in Supabase. You're live.

---

## Quick Reference — Common Issues

| Issue | Fix |
|---|---|
| `discord.errors.LoginFailure` | Check `DISCORD_TOKEN` in `.env` |
| `asyncpg.InvalidPasswordError` | Check `SUPABASE_DB_URL` password |
| Slash commands not showing | Run `await tree.sync()` in `on_ready`, wait up to 1 hour for global sync |
| `MissingPermissions` on team report | Check `MANAGER_ROLE_ID` matches the actual Discord role |
| Bot goes offline on Railway | Make sure you used `worker:` not `web:` in Procfile |

---

## What You'll Have at the End

- A fully functional Discord bot running 24/7
- Time tracking with clock in/out per user
- Daily and weekly summaries per user
- Manager-only team reports
- All data stored persistently in Supabase PostgreSQL
- Clean embed-based UI in Discord
