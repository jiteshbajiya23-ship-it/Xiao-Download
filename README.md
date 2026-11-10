# Xiao Bhai Download Bot

File bhejo → **fast download link** (sirf download, stream nahi). Made for https://xiaobhaidonghua.com

- Link ek **sundar download page** par khulta hai aur download khud start hota hai (black screen / Google nahi)
- **Multi force-sub**, **2 min me 1 link** per user, start image + buttons
- **Saare logs STORAGE channel me** (new user, /start, link, force-sub, ban, errors…)
- Owner / admin commands bot ke andar se (redeploy ki zarurat nahi)

---------------------------------------------------------------------

## 1) Kya kya chahiye (7 cheezein)

| # | Cheez | Kaha se milegi |
|---|-------|----------------|
| 1 | **API_ID** | https://my.telegram.org → login → **API development tools** → app banao → *App api_id* |
| 2 | **API_HASH** | Wahi page → *App api_hash* |
| 3 | **BOT_TOKEN** | Telegram me **@BotFather** → `/newbot` |
| 4 | **STORAGE_CHANNEL** | Neeche step 2 |
| 5 | **DATABASE_URI** | MongoDB Atlas (neeche step 3) |
| 6 | **OWNER_ID** | Apna Telegram ID (@userinfobot ya bot me `/id`) |
| 7 | Render account + GitHub repo | render.com / github.com |

> API_ID aur API_HASH **zaroori** hain (bot Telegram se direct file stream karta hai, sirf BOT_TOKEN se kaam nahi chalega).

## 2) Storage channel (files + logs yahi)

1. Telegram me ek **naya PRIVATE channel** banao (naam kuch bhi, jaise "Xiao Storage").
2. Channel → Administrators → **bot ko admin banao** with: **Post Messages** + **Delete Messages** (revoke ke liye).
3. Channel ka **ID** nikalo (`-100` se shuru hota hai):
   - **Easy:** channel me koi message likho → usko **@username_to_id_bot** (ya @getidsbot) ko forward karo → ID dega.
   - **Ya:** web.telegram.org/k me channel kholo, address bar me `#-100xxxxxxxxxx` dikhega.
   - Bot chalne ke baad: channel ka koi **text message bot ko forward** karo (admin se) → bot ID bata dega.
4. Ye ID `STORAGE_CHANNEL` me daalo.

**Yahi channel kya karta hai:**
- Jo file user bhejta hai uski copy yaha store hoti hai, aur download link isi se file nikaalta hai.
  ⚠️ Is channel se files **delete mat karo** — delete = link band (ye `/revoke` ka tarika bhi hai).
- Saare **logs** bhi yahi aate hain (neeche list).

## 3) MongoDB (free)

1. https://www.mongodb.com/atlas → free cluster (M0).
2. **Database Access** → user banao (username + password; password me `@ : /` jaise special characters mat rakhna).
3. **Network Access** → **Add IP** → `0.0.0.0/0` (Render ka IP badalta rehta hai).
4. **Connect → Drivers** → connection string copy karo, `<password>` ki jagah apna password.
   `mongodb+srv://user:password@cluster0.xxxx.mongodb.net/` → `DATABASE_URI`.

## 4) Render par deploy

1. Ye folder GitHub par push karo (private repo bhi chalega).
2. render.com → **New → Web Service** → repo chuno → **Runtime: Docker** → Plan **Free**.
   (Ya **New → Blueprint** — `render.yaml` use ho jayega.)
3. **Environment Variables** me ye daalo:

| Name | Required | Value |
|------|----------|-------|
| `API_ID` | ✅ | my.telegram.org wala number |
| `API_HASH` | ✅ | my.telegram.org wala hash |
| `BOT_TOKEN` | ✅ | BotFather ka token |
| `STORAGE_CHANNEL` | ✅ | `-100xxxxxxxxxx` |
| `DATABASE_URI` | ✅ | MongoDB string |
| `OWNER_ID` | ✅ | tumhara Telegram ID |
| `ADMINS` | ❌ | extra admins (space se alag) |
| `FORCE_SUB_CHANNELS` | ❌ | `@ongoingdonghuachat @donghuagalaxy1 @xiao_botz` |
| `RATE_LIMIT_SECONDS` | ❌ | default `120` |
| `REDIRECT_AFTER_SECONDS` | ❌ | default `0` (download page par hi rehna) |
| `START_IMAGE` | ❌ | default `https://imgyx.pages.dev/vfoEY` |
| `RENDER_API_KEY`, `RENDER_SERVICE_ID` | ❌ | `/restart` se full redeploy ke liye |

   `URL` set karne ki zarurat **nahi** — Render khud `RENDER_EXTERNAL_URL` deta hai.
4. **Deploy**. Logs me `MongoDB connected ✅` aur `Web server running` dikhna chahiye, aur storage channel me **"Bot restarted"** message aayega.
5. Check: `https://<tumhara-app>.onrender.com/health` → `{"status":"ok"}`.
6. **Free plan sleep karta hai** (15 min idle). Bot khud ping karta hai; phir bhi **UptimeRobot** se `https://<app>.onrender.com/health` ko har 5 min ping lagao.

## 5) Force-sub channels

- Bot ko **har channel me admin** banao (member check ke liye).
- `FORCE_SUB_CHANNELS` env me daalo, **ya** bot me owner `/addfsub @channel` se live add kare. `/fsublist`, `/delfsub`.
- `/health` me har force-sub channel ka check dikhta hai.

## 6) Start image

Telegram ko **direct image link** chahiye (`.jpg/.png`). Agar `imgyx` link image na de, bot text-only start bhejega.
Fix: bot ko koi photo bhejo → us photo par reply karke **/setstart**.

---------------------------------------------------------------------

## Commands

**Users:** `/start`, `/id`

**Admins** (+ owner):
| Command | Kaam |
|---------|------|
| `/status` `/health` `/ping` `/errors` | bot ki condition |
| `/users` | total + latest 10 users |
| `/userinfo <id>` | user ki detail (links, joined, limit) |
| `/resetlimit <id>` | user ka 2-min limit hata do |
| `/ban <id> [reason]` `/unban <id>` `/banlist` | ban system |
| `/revoke <link ya id>` | download link band |
| `/broadcast` | kisi message par reply karke sabko bhejo |
| `/setstart` | photo par reply → start image change |
| `/help` | list |

**Owner only:**
| Command | Kaam |
|---------|------|
| `/addadmin <id>` `/deladmin <id>` `/admins` | admins manage |
| `/setlimit <seconds>` | limit badlo (0 = band) |
| `/addfsub <@ch / -100id>` `/delfsub` `/fsublist` | force-sub manage |
| `/restart` | redeploy / restart |

Admins par 2-min limit lagu nahi hoti. Commands ID ke liye message par reply bhi kar sakte ho.

## Storage channel me kya kya log aata hai

- 🔄 Bot restarted
- 🆕 **New user joined** — naam, username, ID, total users
- ▶️ **Bot started** — kisne /start kiya (new / returning)
- 🔒 Force-sub pending / ✅ Force-sub completed
- 🔗 **Link generated** — user + file name + size (Download / Revoke buttons ke saath)
- 🚫 Ban / unban, ♻️ limit reset, 🛡 admin add/remove, ⏱ limit change, 🔒 force-sub change
- 📢 Broadcast result
- 🚨 Errors

## Download link kaise kaam karta hai

- User ko milta hai `https://app/dl/<id>/<name>?hash=…` → **download page** (progress, buttons, website/channel links)
- Page andar se `https://app/file/<id>/<name>?hash=…` se file **save** karwata hai (attachment, isliye page black nahi hota)
- Galat / revoke link → sundar error page

## Problem aaye to

| Problem | Fix |
|---------|-----|
| Bot reply nahi karta | `BOT_TOKEN` / `API_ID` / `API_HASH` check karo; Render logs dekho |
| Logs / "Bot restarted" channel me nahi aata | Bot channel me **admin** nahi hai ya `STORAGE_CHANNEL` ID galat hai |
| Link banta hai par file nahi khulti | `URL` galat/khali; ya storage channel se file delete ho gayi |
| MongoDB error | Atlas Network Access `0.0.0.0/0`, password me special characters |
| Force-sub kaam nahi kar raha | Bot har channel me admin ho; `/health` chalao |
| Start image nahi aati | direct `.jpg/.png` link ya `/setstart` |
| Telegram ke andar download na ho | Link ko Chrome / Safari me kholo (page me ye tip likha hai) |
