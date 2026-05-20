# WorkClock — Discord Work Time Tracker Bot
## Full Idea Description & Specification (AI IDE Prompt Document)

---

## Overview

WorkClock is a Discord bot built with **Python (discord.py)** that lets team members clock in and out of work directly from Discord. All session data is stored in **PostgreSQL via Supabase**. Managers and team leads get summary reports of who worked, when, and for how long — all without leaving Discord.

The bot is designed for small-to-medium intern/team environments where a lightweight, zero-friction time logger is preferred over heavyweight tools like Jira or Toggl.

---

## Core Features

### 1. Clock In / Clock Out
- `/clockin` — Starts a work session for the user. Records `user_id`, `username`, `clock_in_time`, and `date`.
- `/clockout` — Ends the active session. Records `clock_out_time` and computes `duration_minutes`.
- If a user tries to clock in while already clocked in, the bot responds with an error embed.
- If a user tries to clock out without being clocked in, same — error embed.

### 2. Session Status
- `/status` — Shows the user their current session state: whether they're clocked in, and how long they've been working so far (live duration).

### 3. Daily Summary (User)
- `/mysummary` — Shows the calling user their own work log for today: all sessions, total hours worked.

### 4. Team Report (Admin/Manager Only)
- `/teamreport [date]` — Shows all sessions for all users on a given date (defaults to today). Only accessible by users with a specific role (e.g., `@Manager` or `@Admin`). Output is a formatted embed table.

### 5. Weekly Summary
- `/weeklysummary [@user]` — Shows total hours worked across the last 7 days for a user. If no user is mentioned, shows the caller's own stats.

### 6. Leaderboard (Optional / Fun)
- `/leaderboard` — Shows top contributors by total hours this week across the team.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Bot framework | `discord.py` (v2.x, slash commands via `app_commands`) |
| Language | Python 3.11+ |
| Database | PostgreSQL (hosted on Supabase) |
| DB client | `asyncpg` (async PostgreSQL driver) |
| Environment config | `python-dotenv` |
| Hosting | Railway / Render / local machine (dev) |

---

## Database Schema

### Table: `work_sessions`

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
```

- `user_id` — Discord user snowflake ID (as string)
- `guild_id` — Discord server ID (supports multi-server deployment)
- `duration_minutes` — Computed on clock-out: `(clock_out_time - clock_in_time)` in minutes
- `date` — The calendar date of the session (for easy daily grouping)

### Indexes
```sql
CREATE INDEX idx_work_sessions_user_date ON work_sessions(user_id, date);
CREATE INDEX idx_work_sessions_guild_date ON work_sessions(guild_id, date);
```

---

## Project File Structure

```
workclock-bot/
├── bot.py                  # Entry point, loads cogs, connects to DB
├── config.py               # Loads env vars (token, DB URL, manager role ID)
├── database.py             # asyncpg pool setup, raw query helpers
├── cogs/
│   ├── clock.py            # /clockin, /clockout, /status commands
│   ├── reports.py          # /mysummary, /teamreport, /weeklysummary
│   └── leaderboard.py      # /leaderboard command
├── utils/
│   └── embeds.py           # Discord embed builder helpers
├── .env                    # Secrets (never commit)
├── requirements.txt
└── README.md
```

---

## Environment Variables (`.env`)

```
DISCORD_TOKEN=your_discord_bot_token
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
MANAGER_ROLE_ID=123456789012345678   # Discord role ID with report access
```

---

## Command Reference

| Command | Access | Description |
|---|---|---|
| `/clockin` | Everyone | Start a work session |
| `/clockout` | Everyone | End active session |
| `/status` | Everyone | See current session state |
| `/mysummary` | Everyone | Personal daily work log |
| `/weeklysummary [@user]` | Everyone | 7-day hours summary |
| `/teamreport [date]` | Manager role only | Full team session report |
| `/leaderboard` | Everyone | Top hours this week |

---

## Business Logic Details

### Clock-In Logic
1. Check if user has an open session (`clock_out_time IS NULL`) for today in the DB.
2. If yes → return error embed: "You're already clocked in."
3. If no → insert new row with `clock_in_time = NOW()`, `date = today`.
4. Return success embed with clock-in time.

### Clock-Out Logic
1. Fetch the user's open session (`clock_out_time IS NULL`).
2. If none → return error embed: "You haven't clocked in."
3. Compute `duration_minutes = (NOW() - clock_in_time) / 60`.
4. Update row: set `clock_out_time = NOW()`, `duration_minutes = computed`.
5. Return success embed with duration worked.

### Team Report Access Control
- Check `interaction.user.roles` for the manager role ID from config.
- If not found → ephemeral error: "You don't have permission."

---

## Embed Design Style

All bot responses use Discord embeds:
- **Success** → Green left bar, checkmark emoji, clean fields
- **Error** → Red left bar, ✗ emoji, short explanation
- **Info/Reports** → Blue/grey bar, tabular fields

---

## Error Handling

- DB connection failures → catch `asyncpg.PostgresError`, log to console, send user-facing "Database error, contact admin" embed.
- Unexpected exceptions → global `on_error` / `on_app_command_error` handler in `bot.py`.
- Double clock-in / clock-out → handled at business logic level (see above), not as exceptions.

---

## Deployment Notes

- Tested locally with Python venv.
- For production: deploy on **Railway** (free tier) or **Render**.
- Supabase free tier is sufficient for small teams (up to ~500MB storage).
- Bot needs only these Discord permissions: `Send Messages`, `Use Slash Commands`, `Embed Links`, `Read Message History`.
- Enable `applications.commands` scope when generating the OAuth2 invite link.

---

## Future Extensions (Nice to Haves)

- `/setbreak` and `/endbreak` — pause/resume sessions with break time tracking
- Automatic DM reminder if someone forgot to clock out (scheduled task via `discord.ext.tasks`)
- Google Sheets export via Sheets API
- Monthly PDF report generation
- `/project [name]` — tag sessions to specific projects
