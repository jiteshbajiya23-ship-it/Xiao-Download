<div align="center">

# ⚡ Xiao Bhai Download Bot

**Send a file 📤 → get a fast download link 🔗 → download instantly ⚡**

A Telegram bot that turns any video, audio or file into a clean, direct download link.
Built for [🌐 xiaobhaidonghua.com](https://xiaobhaidonghua.com)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Pyrogram](https://img.shields.io/badge/Pyrogram-Telegram-26A5E4?logo=telegram&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)

</div>

---

## ✨ Features

| | Feature | Details |
|---|---|---|
| 🎨 | **Beautiful download page** | The link opens a clean page and the download starts on its own, with no black screen and no redirect to Google |
| 🔒 | **Multi force-sub** | Users must join your channels first, and membership is re-checked live on every file, so leaving a channel locks them out again |
| ⏱ | **Rate limit** | 1 link per 2 minutes per user (change it live with `/setlimit`) |
| 🛡 | **Role-based commands** | Users, moderators and the owner each see only their own commands |
| 📜 | **Full logging** | New users, links, bans, force-sub and errors all go to your storage channel |
| 🖼 | **Custom start image** | Change it from inside the bot with `/setstart` |
| ♻️ | **Live control** | Admins, bans, limits and force-sub channels change without a redeploy |

---

## 🚀 Quick Start

### 1️⃣ What you need

| # | Item | Where to get it |
|---|------|-----------------|
| 1 | 🔑 **API_ID** | [my.telegram.org](https://my.telegram.org) → *API development tools* → create an app |
| 2 | 🔐 **API_HASH** | Same page as above |
| 3 | 🤖 **BOT_TOKEN** | [@BotFather](https://t.me/BotFather) → `/newbot` |
| 4 | 📦 **STORAGE_CHANNEL** | Step 2 below |
| 5 | 🍃 **DATABASE_URI** | MongoDB Atlas, step 3 below |
| 6 | 👑 **OWNER_ID** | Your Telegram ID (send `/id` to the bot) |
| 7 | ☁️ **Render + GitHub** | [render.com](https://render.com) / [github.com](https://github.com) |

> ⚠️ `API_ID` and `API_HASH` are **required**. The bot streams files straight from Telegram, so `BOT_TOKEN` alone is not enough.

### 2️⃣ Storage channel 📦

1. Create a **new private channel** on Telegram (for example "Xiao Storage").
2. Add your bot as an **admin** with **Post Messages** and **Delete Messages** permissions.
3. Get the channel ID (it starts with `-100`):
   - 💡 **Easiest:** once the bot is running, forward any **text message** from the channel to the bot (as an admin) and it replies with the ID.
   - 🌐 **Or:** open the channel in [web.telegram.org/k](https://web.telegram.org/k) and read `#-100xxxxxxxxxx` from the address bar.
4. Put that ID in `STORAGE_CHANNEL`.

**What this channel does:**
- 📁 Receives every file users send, **forwarded from the original message** so you can see who sent it, and the download link streams from it.
  ⚠️ **Never delete files from this channel.** Deleting a file kills its link (this is also how `/revoke` works).
- 📜 Receives all bot logs (full list below).

### 3️⃣ MongoDB 🍃 (free)

1. Create a free **M0** cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
2. **Database Access** → create a user. Avoid special characters like `@ : /` in the password.
3. **Network Access** → **Add IP** → `0.0.0.0/0` (Render's IP changes).
4. **Connect → Drivers** → copy the connection string and replace `<password>` with yours.
   `mongodb+srv://user:password@cluster0.xxxx.mongodb.net/` goes in `DATABASE_URI`.

### 4️⃣ Deploy on Render ☁️

1. Push this repo to GitHub (private works fine).
2. On Render: **New → Web Service** → pick the repo → **Runtime: Docker** → Plan **Free**.
   (Or use **New → Blueprint** and `render.yaml` is picked up automatically.)
3. Add these **environment variables**:

| Name | Required | Value |
|------|:--------:|-------|
| `API_ID` | ✅ | Number from my.telegram.org |
| `API_HASH` | ✅ | Hash from my.telegram.org |
| `BOT_TOKEN` | ✅ | Token from BotFather |
| `STORAGE_CHANNEL` | ✅ | `-100xxxxxxxxxx` |
| `DATABASE_URI` | ✅ | MongoDB connection string |
| `OWNER_ID` | ✅ | Your Telegram ID |
| `ADMINS` | ➖ | Extra moderator IDs, separated by spaces |
| `FORCE_SUB_CHANNELS` | ➖ | e.g. `@ongoingdonghuachat @donghuagalaxy1 @xiao_botz` |
| `RATE_LIMIT_SECONDS` | ➖ | Default `120` |
| `REDIRECT_AFTER_SECONDS` | ➖ | Default `0` (stay on the download page) |
| `LINK_EXPIRY_HOURS` | ➖ | Download links die after this many hours. Default `2` |
| `LINK_SECRET` | ➖ | Signs the links. Empty = `BOT_TOKEN` is used |
| `START_IMAGE` | ➖ | Direct image link (`.jpg` / `.png`) |
| `RENDER_API_KEY`, `RENDER_SERVICE_ID` | ➖ | Enables a full redeploy from `/restart` |

> 🌐 You don't need to set `URL`. Render provides `RENDER_EXTERNAL_URL` automatically.

4. Click **Deploy**. In the logs you should see `MongoDB connected ✅` and `Web server running`, and a **"Bot restarted"** message appears in your storage channel.
5. ✅ Health check: `https://<your-app>.onrender.com/health` should return `{"status":"ok"}`.
6. 😴 The free plan **sleeps after 15 minutes** of inactivity. The bot pings itself, but you should also add an [UptimeRobot](https://uptimerobot.com) monitor for `https://<your-app>.onrender.com/health` every 5 minutes.

### 5️⃣ Force-sub channels 🔒

- Make the bot an **admin in every channel** so it can check membership.
- Add channels with the `FORCE_SUB_CHANNELS` variable, **or** live from the bot with `/addfsub @channel`.
- Manage them with `/fsublist` and `/delfsub`. `/health` also checks each channel.

### 6️⃣ Start image 🖼

Telegram needs a **direct image link** (`.jpg` / `.png`). If the link doesn't return an image, the bot falls back to a text-only start message.
**Fix:** send any photo to the bot, then reply to it with `/setstart`.

---

## 🤖 Commands

Each role sees only its own commands:

- **Users** see the public commands in the menu and in `/help`.
- **Moderators** also get commands tagged `Moderator ·` in the menu.
- **The owner** also gets commands tagged `Owner ·`.

If someone uses a command above their role, the bot replies: ⛔ *You are not an admin / owner.*

### 🙋 Everyone

| Command | What it does |
|---------|--------------|
| `/start` | Open the home screen |
| `/id` | Show your Telegram ID |
| `/help` | Show the commands available to you |

### 🛡 Moderators (admins + owner)

| Command | What it does |
|---------|--------------|
| `/status` `/health` `/ping` `/errors` | Bot condition and diagnostics |
| `/users` | Total users plus the latest 10 |
| `/userinfo <id>` | User details (links, joined date, limit) |
| `/resetlimit <id>` | Reset a user's link limit |
| `/ban <id> [reason]` `/unban <id>` `/banlist` | Ban system |
| `/revoke <link or id>` | Disable a download link |
| `/broadcast` | Reply to a message to send it to every user |
| `/setstart` | Reply to a photo to change the start image |

### 👑 Owner only

| Command | What it does |
|---------|--------------|
| `/addadmin <id>` `/deladmin <id>` `/admins` | Manage moderators |
| `/setlimit <seconds>` | Change the link limit (`0` = off) |
| `/addfsub <@channel / -100id>` `/delfsub` `/fsublist` | Manage force-sub channels |
| `/restart` | Redeploy / restart the bot |

> ℹ️ The link limit doesn't apply to moderators. Most commands also work when you reply to a user's message.

---

## 📜 What gets logged to the storage channel

| | Event |
|---|---|
| 🔄 | Bot restarted |
| 🆕 | **New user joined** (name, username, ID, total users) |
| ▶️ | **Bot started** (new or returning user) |
| 🔒 / ✅ | Force-sub pending / completed |
| 🔗 | **Link generated** (user, file name, size, with Download and Revoke buttons) |
| 🚫 🛡 ⏱ | Bans and unbans, admin changes, limit changes, force-sub changes |
| 📢 | Broadcast results |
| 🚨 | Errors |

---

## 🔗 How the download link works

1. The user gets `https://app/dl/<id>/<name>?hash=…`, which opens the **download page** with a progress bar and links to your website and channels.
2. Behind the scenes the page fetches `https://app/file/<id>/<name>?hash=…` as an **attachment**, so the file is saved and the page never goes black.
3. A wrong or revoked link shows a friendly **error page**.

---

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| 🤖 Bot doesn't reply | Check `BOT_TOKEN`, `API_ID`, `API_HASH` and the Render logs |
| 📜 No logs / no "Bot restarted" message | The bot isn't an **admin** in the storage channel, or `STORAGE_CHANNEL` is wrong |
| 🔗 Link works but the file won't open | `URL` is wrong or empty, or the file was deleted from the storage channel |
| 🍃 MongoDB error | Atlas Network Access must allow `0.0.0.0/0`, and the password must not contain special characters |
| 🔒 Force-sub not working | Make the bot admin in every channel, then run `/health` |
| 🖼 Start image missing | Use a direct `.jpg` / `.png` link, or use `/setstart` |
| 📱 Download won't start inside Telegram | Open the link in **Chrome / Safari** (the page also says so) |

---

<div align="center">

Made with ❤️ for **[Xiao Bhai Donghua](https://xiaobhaidonghua.com)**
💬 [Discussion](https://t.me/ongoingdonghuachat) · 🎬 [Donghua](https://t.me/donghuagalaxy1) · 📢 [Updates](https://t.me/xiao_botz)

</div>
