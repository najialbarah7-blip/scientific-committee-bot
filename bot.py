







import os
import json
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7721143402

USERS_FILE = "users.json"

buttons = [    ["📚 مشاركة محاضرات", "📝 مشاركة نماذج الامتحانات"],
    ["📖 مشاركة الملخصات", "❓ إرسال استفسار"],
    ["📎 مشاركة ملف", "📞 التواصل مع اللجنة"],
]

keyboard = ReplyKeyboardMarkup(
    buttons,
    resize_keyboard=True
)

SERVICES = [
    "📚 مشاركة محاضرات",
    "📝 مشاركة نماذج الامتحانات",
    "📖 مشاركة الملخصات",
    "❓ إرسال استفسار",
    "📎 مشاركة ملف",
    "📞 التواصل مع اللجنة",
]


# =========================
# حفظ وقراءة المستخدمين
# =========================

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            users,
            file,
            ensure_ascii=False,
            indent=2
        )


def register_user(user):
    users = load_users()
    user_id = str(user.id)

    is_new = user_id not in users

    if is_new:
        users[user_id] = {
            "id": user.id,
            "name": user.full_name,
            "username": user.username,
            "first_seen": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        save_users(users)

    return is_new


# =========================
# البداية
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    # تسجيل المستخدم
    is_new = register_user(user)

    # إشعار المشرف بالمستخدم الجديد
    if is_new and chat_id != ADMIN_ID:
        username = (
            f"@{user.username}"
            if user.username
            else "لا يوجد"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "👤 مستخدم جديد دخل إلى البوت\n\n"
                f"الاسم: {user.full_name}\n"
                f"Username: {username}\n"
                f"ID: {user.id}"
            ),
        )

    # لوحة المشرف
    if chat_id == ADMIN_ID:
        await update.message.reply_text(
            "👑 مرحبًا بك في لوحة إدارة البوت.\n\n"
            "📢 لإرسال إعلان لجميع المستخدمين:\n"
            "/broadcast نص الإعلان"
        )
        return

    await update.message.reply_text(
        f"أهلًا بك {user.first_name} 🌷\n\n"
        "🤖 بوت اللجنة العلمية المركزية\n"
        "كلية مجتمع الدرب - ذمار\n\n"
        "اختر الخدمة المطلوبة من القائمة:",
        reply_markup=keyboard,
    )


# =========================
# معرفة ID
# =========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 معرف المحادثة الخاص بك هو:\n"
        f"{update.effective_chat.id}"
    )


# =========================
# التواصل مع اللجنة
# =========================

async def contact_info(update: Update):
    await update.message.reply_text(
        "📞 للتواصل مع اللجنة العلمية\n\n"
        "👤 الاسم: ناجي البرح\n"
        "🏛️ الصفة: نائب اللجنة العلمية\n\n"
        "📱 الهاتف:\n"
        "+967 777 124 827\n\n"
        "🔵 Telegram:\n"
        "t.me/najialbarah"
    )


# =========================
# استقبال الرسائل
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    # تسجيل المستخدم
    register_user(user)

    # =========================
    # رسائل المشرف
    # =========================

    if chat_id == ADMIN_ID:

        # إذا كان المشرف يرد Reply على رسالة مستخدم
        if update.message.reply_to_message:

            replied = update.message.reply_to_message

            # البحث عن ID داخل الرسالة التي وصلته
            target_id = None

            if replied.text:
                for line in replied.text.splitlines():
                    if line.startswith("🆔 ID:"):
                        try:
                            target_id = int(
                                line.replace("🆔 ID:", "").strip()
                            )
                        except ValueError:
                            pass

            if target_id:
                try:
                    await context.bot.copy_message(
                        chat_id=target_id,
                        from_chat_id=ADMIN_ID,
                        message_id=update.message.message_id,
                    )

                    await update.message.reply_text(
                        "✅ تم إرسال ردك إلى المستخدم."
                    )

                except Exception as e:
                    await update.message.reply_text(
                        f"❌ تعذر إرسال الرد.\n{e}"
                    )

            else:
                await update.message.reply_text(
                    "⚠️ لم أتمكن من معرفة المستخدم.\n"
                    "استخدم Reply على رسالة معلومات المستخدم."
                )

            return

        return

    # =========================
    # زر التواصل
    # =========================

    if update.message.text == "📞 التواصل مع اللجنة":
        await contact_info(update)
        return

    # =========================
    # اختيار خدمة
    # =========================

    if update.message.text in SERVICES:

        service = update.message.text

        context.user_data["service"] = service

        await update.message.reply_text(
            f"تم اختيار: {service}\n\n"
            "أرسل الآن المحتوى أو الرسالة المطلوبة، "
            "وسيتم إرسالها إلى اللجنة العلمية المركزية."
        )

        return

    # =========================
    # محتوى المستخدم
    # =========================

    service = context.user_data.get("service")

    if not service:

        await update.message.reply_text(
            "يرجى اختيار إحدى الخدمات من القائمة أولًا.",
            reply_markup=keyboard,
        )

        return

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    # معلومات المستخدم
    info = (
        "📩 رسالة جديدة إلى اللجنة العلمية المركزية\n\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: {chat_id}\n"
        f"📌 الخدمة: {service}"
    )

    # إرسال معلومات المستخدم
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=info,
    )

    # إرسال المحتوى الأصلي
    await context.bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=chat_id,
        message_id=update.message.message_id,
    )

    # =========================
    # الرد للمستخدم
    # =========================

    if service == "❓ إرسال استفسار":

        await update.message.reply_text(
            "✅ تم إرسال طلبك بنجاح إلى اللجنة العلمية المركزية.\n"
            "سيتم الاطلاع عليه والرد عليك عند الإمكان.",
            reply_markup=keyboard,
        )

    else:

        await update.message.reply_text(
            "🌷 شكرًا لك على مشاركتك.\n\n"
            "نقدّر جهودك ومساهمتك في إثراء المحتوى "
            "العلمي وخدمة زملائك الطلاب.\n\n"
            "جزيل الشكر والتقدير لك ❤️",
            reply_markup=keyboard,
        )

    # إنهاء الخدمة الحالية
    context.user_data.pop("service", None)


# =========================
# نشر إعلان لجميع المستخدمين
# =========================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.id != ADMIN_ID:
        return

    if not context.args:

        await update.message.reply_text(
            "استخدم الأمر بهذا الشكل:\n\n"
            "/broadcast نص الإعلان"
        )

        return

    announcement = " ".join(context.args)

    users = load_users()

    sent = 0
    failed = 0

    for user_id in users:

        try:

            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    "📢 إعلان من اللجنة العلمية المركزية\n\n"
                    f"{announcement}"
                ),
            )

            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        "📊 تم الانتهاء من نشر الإعلان.\n\n"
        f"✅ تم الإرسال إلى: {sent}\n"
        f"❌ تعذر الإرسال إلى: {failed}"
    )


# =========================
# تشغيل البوت
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في Termux."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("myid", myid)
    )

    app.add_handler(
        CommandHandler("broadcast", broadcast)
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message,
        )
    )

    print("🤖 البوت يعمل الآن...")

public_domain = os.getenv("KOYEB_PUBLIC_DOMAIN")
if not public_domain:
    raise RuntimeError("KOYEB_PUBLIC_DOMAIN غير موجود.")

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.getenv("PORT", "10000")),
    url_path="webhook",
    webhook_url=f"https://{public_domain}/webhook",
)
if __name__ == "__main__":
    main()
