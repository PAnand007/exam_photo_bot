import os
import json
from dotenv import load_dotenv
from PIL import Image

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =====================
# LOAD ENV & TOKEN
# =====================

# Only use dotenv if BOT_TOKEN not already in environment
if not os.environ.get("BOT_TOKEN"):
    from dotenv import load_dotenv
    load_dotenv()  # loads local .env for development

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found. Add it to .env (local) or environment (Render)")


# =====================
# LOAD PRESETS
# =====================
with open("presets.json", "r") as f:
    PRESETS = json.load(f)

# =====================
# USER STATE
# =====================
user_state = {}

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[exam] for exam in PRESETS.keys()]
    await update.message.reply_text(
        "📋 Select Exam:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# HANDLE TEXT (EXAM + TYPE)
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Exam selected
    if text in PRESETS:
        user_state[user_id] = {"exam": text}
        await update.message.reply_text(
            "🖼 Select Image Type:",
            reply_markup=ReplyKeyboardMarkup(
                [["photo", "signature"]],
                resize_keyboard=True
            )
        )
        return

    # Image type selected
    if text in ["photo", "signature"] and user_id in user_state:
        user_state[user_id]["type"] = text
        await update.message.reply_text("📤 Upload your image now")
        return

# =====================
# HANDLE IMAGE
# =====================
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        await update.message.reply_text("⚠️ Please start with /start")
        return

    exam = user_state[user_id]["exam"]
    img_type = user_state[user_id]["type"]
    preset = PRESETS[exam][img_type]

    # Download image
    photo = update.message.photo[-1]
    file = await photo.get_file()

    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/{user_id}_input.jpg"
    output_path = f"temp/{user_id}_output.jpg"

    await file.download_to_drive(input_path)

    # Process image
    img = Image.open(input_path).convert("RGB")
    img = img.resize((preset["width"], preset["height"]))

    quality = 95
    while True:
        img.save(output_path, "JPEG", quality=quality)
        size_kb = os.path.getsize(output_path) / 1024
        if size_kb <= preset["max_kb"] or quality <= 20:
            break
        quality -= 5

    # Send result
    await update.message.reply_photo(
        photo=open(output_path, "rb"),
        caption=(
            f"✅ {exam} {img_type} ready\n"
            f"📐 {preset['width']}x{preset['height']} px\n"
            f"📦 ≤ {preset['max_kb']} KB"
        )
    )
async def error_handler(update, context):
    print("⚠️ Error occurred:", context.error)

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    app.add_error_handler(error_handler)  # 👈 ADD THIS

    print("🤖 Bot is running...")
    app.run_polling()


# =====================
# RUN
# =====================
if __name__ == "__main__":
    main()
# =====================

