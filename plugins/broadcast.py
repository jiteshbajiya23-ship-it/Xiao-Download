import asyncio
import datetime
import logging
import time

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

from database.users_chats_db import db
from xiaobhai.util.access import ADMIN_F
from xiaobhai.util.logger import log_event, now_ist


@Client.on_message(filters.command("broadcast") & filters.private & ADMIN_F)
async def pm_broadcast(bot, message):
    # Usage: reply to any message with /broadcast
    b_msg = message.reply_to_message
    if not b_msg:
        return await message.reply_text("📢 Reply to the message you want to send with /broadcast.")

    users = await db.get_all_users()
    sts = await message.reply_text("📢 Broadcasting your message…")
    start_time = time.time()
    total_users = await db.total_users_count()
    done = blocked = deleted = failed = success = 0

    async for user in users:
        if "id" in user:
            ok, reason = await broadcast_messages(int(user["id"]), b_msg)
            if ok:
                success += 1
            elif reason == "Blocked":
                blocked += 1
            elif reason == "Deleted":
                deleted += 1
            else:
                failed += 1
        else:
            failed += 1
        done += 1
        if not done % 20:
            try:
                await sts.edit(
                    parse_mode=enums.ParseMode.HTML, text=f"📢 <b>Broadcast in progress</b>\n━━━━━━━━━━━━━━━━━━\n👥 Total users: {total_users}\n"
                    f"⏳ Completed: {done} / {total_users}\n✅ Success: {success}\n"
                    f"🚫 Blocked: {blocked}\n🗑 Deleted: {deleted}"
                )
            except Exception:
                pass

    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(
        parse_mode=enums.ParseMode.HTML, text=f"✅ <b>Broadcast completed</b> in {time_taken}\n━━━━━━━━━━━━━━━━━━\n👥 Total users: {total_users}\n"
        f"⏳ Completed: {done} / {total_users}\n✅ Success: {success}\n🚫 Blocked: {blocked}\n"
        f"🗑 Deleted: {deleted}\n⚠️ Failed: {failed}"
    )
    await log_event(f"📢 <b>Broadcast finished</b>\n━━━━━━━━━━━━━━━━━━\nBy: <code>{message.from_user.id}</code>\n"
                    f"✅ Success: <code>{success}</code>\n🚫 Blocked: <code>{blocked}</code>\n"
                    f"🗑 Deleted: <code>{deleted}</code>\n⚠️ Failed: <code>{failed}</code>\n"
                    f"⏱ Time: <code>{time_taken}</code>\n🕒 <i>{now_ist()}</i>")


async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(getattr(e, "value", None) or getattr(e, "x", 5))
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} removed from DB (deleted account).")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} PeerIdInvalid")
        return False, "Error"
    except Exception:
        return False, "Error"
