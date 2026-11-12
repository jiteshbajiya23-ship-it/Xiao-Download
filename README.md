<div align="center">

# ⚡ Xiao Bhai Download Bot

**Send a file 📤 → get a fast download link 🔗 → download instantly ⚡**

A Telegram bot that turns any video, audio or file into a clean, direct download link.  
Built for [xiaobhaidonghua.com](https://xiaobhaidonghua.com)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Pyrogram](https://img.shields.io/badge/Pyrogram-Telegram-26A5E4?logo=telegram&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Kerit](https://img.shields.io/badge/Deploy-Kerit%20Cloud-0EA5E9)

</div>

---

## Features

| Feature | Details |
|---------|---------|
| Beautiful download page | Link opens a clean page and download starts automatically |
| Multi force-sub | Users must join your channels (live re-check) |
| Rate limit | 1 link per 2 minutes (change live with `/setlimit`) |
| Role-based commands | Users / Moderators / Owner see different menus |
| Full logging | All activity goes to your storage channel |
| Custom start image | Change with `/setstart` |
| Live control | Admins, bans, limits, force-sub without redeploy |

---

## Deploy on Kerit Cloud (Free)

### 1. What you need

| Item | Where to get it |
|------|-----------------|
| API_ID + API_HASH | [my.telegram.org](https://my.telegram.org) |
| BOT_TOKEN | [@BotFather](https://t.me/BotFather) |
| STORAGE_CHANNEL | Private channel (bot must be admin) |
| DATABASE_URI | Free MongoDB Atlas cluster |
| OWNER_ID | Your Telegram user ID |

### 2. Storage channel

Create a private channel → add the bot as **admin** with "Post Messages" permission.  
Copy the channel ID (starts with `-100`).  
**Never delete files** from this channel (it breaks links).

### 3. MongoDB Atlas (free)

1. Create free M0 cluster
2. Database Access → create user
3. Network Access → Add IP `0.0.0.0/0`
4. Copy the connection string

### 4. Deploy on Kerit

1. Push this repo to GitHub
2. Go to [Kerit Cloud](https://kerit.cloud) → create free server
3. Connect your GitHub repo **or** upload the files
4. Set **Start Command**:
   ```bash
   python bot.py
   ```
5. Add these Environment Variables:

| Name | Required | Example / Notes |
|------|:--------:|-----------------|
| `API_ID` | Yes | From my.telegram.org |
| `API_HASH` | Yes | From my.telegram.org |
| `BOT_TOKEN` | Yes | From BotFather |
| `STORAGE_CHANNEL` | Yes | `-100xxxxxxxxxx` |
| `DATABASE_URI` | Yes | MongoDB connection string |
| `OWNER_ID` | Yes | Your Telegram ID |
| `URL` | **Yes** | Your public URL (see below) |
| `ADMINS` | No | Extra admin IDs (space separated) |
| `FORCE_SUB_CHANNELS` | No | `@channel1 @channel2` |
| `PORT` | No | Default `8080` |
| `KEEP_ALIVE` | No | `true` (recommended) |

> **Important:** On Kerit you **must** set the `URL` variable to the public address of your bot (example: `https://your-subdomain.kerit.cloud/` or whatever domain Kerit gives you). Without it, download links will be broken.

6. Start the server. In logs you should see:
   - `MongoDB connected`
   - `Web server running on port ...`
   - A "Bot restarted" message in your storage channel

### 5. Keep it alive with UptimeRobot

Even though Kerit free claims no sleep, always add a monitor:

1. Go to [uptimerobot.com](https://uptimerobot.com) (free)
2. Add New Monitor → **HTTP(s)**
3. URL: `https://YOUR-BOT-URL/health`
4. Interval: every **5 minutes**

This hits the built-in `/health` endpoint and keeps the process active.

### 6. Force-sub channels

Make the bot admin in every force-sub channel, then either:

- Set `FORCE_SUB_CHANNELS` env, **or**
- Use `/addfsub @channel` live from the bot

---

## Commands

- **Users**: `/start` `/help` `/id`
- **Moderators**: `/status` `/health` `/ban` `/unban` `/broadcast` `/setstart` etc.
- **Owner**: `/addadmin` `/setlimit` `/addfsub` `/restart`

---

## Notes for Kerit Free (256 MB)

- The bot is already optimized for low RAM (`uvloop`, `MALLOC_ARENA_MAX=2`, no access logs).
- Avoid multi-client mode if you are on free plan.
- If the process gets killed for high memory, reduce concurrent downloads or upgrade.

---

## License

GPL-3.0 (see LICENSE)
