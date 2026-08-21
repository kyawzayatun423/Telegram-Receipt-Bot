"""
MLBB Order Receipt Bot
=======================

Flow:
  1. Customer sends payment screenshot + caption (or plain text) in the group,
     e.g.  "1354119674 15566 86 Diamonds"
  2. Bot parses the UID from it:
        UID = everything except the last two words   -> "1354119674 15566"
     (the customer's own "86 Diamonds" part is kept only as a fallback —
     see step 3.)
  3. Only the admin (Telegram user id 7978208335) can reply to that customer
     message with the Order typed right after the command:
        /.86 Diamonds    -> Approve, Order = "86 Diamonds"
        /-86 Diamonds    -> Reject,  Order = "86 Diamonds"
     (a space after /. or /- also works: "/. 86 Diamonds")
     If the admin sends bare "/." or "/-" with no order text, the bot falls
     back to whatever order text it auto-parsed from the customer's
     original message.
  4. Bot posts the final receipt (reply to the customer's original message)
     with the admin-supplied Order, Yangon time, an auto-generated serial,
     and a fixed "User" field.

Only the configured ADMIN_ID can trigger approve/reject. Everyone else's
"/." or "/-" replies are ignored.
"""

import logging
import os
import random
import re
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ----------------------------------------------------------------------
# CONFIG — edit these three values (or set them as environment variables)
# ----------------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7978208335"))
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "0"))  # 0 = allow any chat (not recommended)

RECEIPT_USER_NAME = "𝑲𝑶 𝑵𝑨𝑰𝑵𝑮"
YANGON_TZ = pytz.timezone("Asia/Yangon")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mlbb-order-bot")

# In-memory store: {customer_message_id: {"uid":..., "order":..., "customer_message_id":...}}
# NOTE: this resets if the bot restarts. Swap for a small SQLite/JSON store if you need
# orders to survive restarts.
pending_orders: dict[int, dict] = {}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def parse_order(text: str):
    """
    Parse '1354119674 15566 86 Diamonds' -> ("1354119674 15566", "86 Diamonds")

    Rule: the LAST TWO whitespace-separated tokens are the Order
    (a number + a unit word, e.g. "86 Diamonds"). Everything before that
    is the UID (can itself contain multiple number groups, e.g. two UID
    parts as in the example).
    """
    if not text:
        return None
    tokens = text.strip().split()
    if len(tokens) < 3:
        return None

    order_amount, order_name = tokens[-2], tokens[-1]
    if not order_amount.isdigit():
        return None

    uid_tokens = tokens[:-2]
    if not uid_tokens:
        return None

    uid = " ".join(uid_tokens)
    order = f"{order_amount} {order_name}"
    return uid, order


# Matches "/.", "/-" optionally followed directly (or after a space) by order text.
# Group 1 = "/." or "/-", Group 2 = whatever order text the admin typed (may be empty).
ADMIN_DECISION_RE = re.compile(r"^(/\.|/-)\s*(.*)$", re.DOTALL)


def parse_admin_decision(text: str):
    """
    '/.86 Diamonds' -> ('/.', '86 Diamonds')
    '/- 86 Diamonds' -> ('/-', '86 Diamonds')
    '/.'             -> ('/.', '')
    'hello'          -> None
    """
    if not text:
        return None
    match = ADMIN_DECISION_RE.match(text.strip())
    if not match:
        return None
    command, order_text = match.group(1), match.group(2).strip()
    return command, order_text


def make_serial() -> str:
    today = datetime.now(YANGON_TZ).strftime("%Y%m%d")
    rand5 = "".join(random.choices("0123456789", k=5))
    return f"{today}-{rand5}"


def make_time_str() -> str:
    return datetime.now(YANGON_TZ).strftime("%I:%M:%S %p")


def build_receipt(uid: str, order: str, situation: str) -> str:
    serial = make_serial()
    time_str = make_time_str()
    return (
        "#Order Receipt -MLBB\n\n"
        f"UID      : {uid}\n"
        f"Order    : {order}\n"
        f"Serial   : {serial}\n"
        f"Time     : {time_str}\n"
        f"User     : {RECEIPT_USER_NAME}\n"
        f"Situation: {situation}"
    )


def in_target_group(chat_id: int) -> bool:
    return GROUP_CHAT_ID == 0 or chat_id == GROUP_CHAT_ID


# ----------------------------------------------------------------------
# Handlers
# ----------------------------------------------------------------------
async def handle_customer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture customer order messages (photo+caption or plain text)."""
    msg = update.effective_message
    if not msg or not msg.chat:
        return
    if not in_target_group(msg.chat_id):
        return
    if msg.from_user and msg.from_user.id == ADMIN_ID:
        return  # admin messages are handled separately

    text = msg.caption or msg.text
    parsed = parse_order(text)
    if not parsed:
        return  # not an order-looking message, ignore silently

    uid, order = parsed
    pending_orders[msg.message_id] = {
        "uid": uid,
        "order": order,
        "customer_message_id": msg.message_id,
    }
    logger.info("Captured order msg_id=%s uid=%s order=%s", msg.message_id, uid, order)


async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin replies to a customer's order message with:
        /.<order text>   -> Approve   (e.g. "/.86 Diamonds")
        /-<order text>   -> Reject    (e.g. "/-86 Diamonds")
    The order text right after the command is what's used in the receipt's
    Order field. If no order text is given, falls back to the order the bot
    auto-parsed from the customer's original message (if any).
    """
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        return
    if not in_target_group(msg.chat_id):
        return
    if not msg.from_user or msg.from_user.id != ADMIN_ID:
        return  # only the configured admin can approve/reject

    decision = parse_admin_decision(msg.text)
    if not decision:
        return
    command, order_text = decision

    replied_id = msg.reply_to_message.message_id
    order = pending_orders.get(replied_id)
    if not order:
        await msg.reply_text(
            "⚠️ ဒီ Order ကို Bot က မမှတ်မိပါ (customer ရဲ့ message ကို reply လုပ်ပြီး /.86 Diamonds လိုမျိုး ခေါ်ပါ)။"
        )
        return

    # Prefer the order text the admin typed; fall back to the auto-parsed one.
    final_order = order_text or order.get("order")
    if not final_order:
        await msg.reply_text(
            "⚠️ Order text မပါပါ။ ဥပမာ- /.86 Diamonds လို့ ရေးပေးပါ (Order ကို command နောက်မှာ ထည့်ပါ)။"
        )
        return

    situation = "Approve" if command == "/." else "Reject"
    receipt = build_receipt(order["uid"], final_order, situation)

    await context.bot.send_message(
        chat_id=msg.chat_id,
        text=receipt,
        reply_to_message_id=order["customer_message_id"],
    )

    del pending_orders[replied_id]  # prevent double approve/reject on same order


# ----------------------------------------------------------------------
# App wiring
# ----------------------------------------------------------------------
def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit("BOT_TOKEN not set. Set the BOT_TOKEN environment variable.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Admin decision handler must be checked first (more specific: reply + admin only)
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.REPLY & filters.User(user_id=ADMIN_ID),
            handle_admin_decision,
        )
    )

    # Any non-admin photo/text message is a candidate order message
    app.add_handler(
        MessageHandler(
            (filters.PHOTO | filters.TEXT) & ~filters.User(user_id=ADMIN_ID),
            handle_customer_message,
        )
    )

    logger.info("Bot starting… admin_id=%s group_chat_id=%s", ADMIN_ID, GROUP_CHAT_ID or "ANY")
    app.run_polling()


if __name__ == "__main__":
    main()
