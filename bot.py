import os
import json
from PIL import Image
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# =====================
# LOAD ENV & TOKEN
# =====================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# =====================
# LOAD PRESETS
# =====================
with open("presets.json", "r") as f:
    PRESETS = json.load(f)

# =====================
# USER STATE MEMORY
# =====================
user_state = {}

# =====================
# /start
# =====================
def start(update: Update, context: CallbackContext):
    keyboard = [[exam] for exam in PRESETS.keys()]
    update.message.reply_text(
        "📋 Select Exam:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# HANDLE TEXT (EXAM / TYPE)
# =====================
def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text

    # Exam selected
    if text in PRESETS:
        user_state[user_id] = {"exam": text}
        update.message.reply_text(
            "🖼 Select Image Type:",
            reply_markup=ReplyKeyboardMarkup([["photo", "signature"]], resize_keyboard=True)
        )
        return

    # Image type selected
    if text in ["photo", "signature"] and user_id in user_state:
        user_state[user_id]["type"] = text
        update.message.reply_text("📤 Upload your image now")

# =====================
# HANDLE IMAGE
# =====================
def handle_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in user_state:
        update.message.reply_text("⚠️ Please start with /start")
        return

    exam = user_state[user_id]["exam"]
    img_type = user_state[user_id]["type"]
    preset = PRESETS[exam][img_type]

    try:
        photo = update.message.photo[-1]
        file = photo.get_file()
        os.makedirs("temp", exist_ok=True)
        input_path = f"temp/{user_id}_input.jpg"
        output_path = f"temp/{user_id}_output.jpg"
        file.download(input_path)

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
        update.message.reply_photo(
            photo=open(output_path, "rb"),
            caption=(
                f"✅ {exam} {img_type} ready\n"
                f"📐 {preset['width']}x{preset['height']} px\n"
                f"📦 ≤ {preset['max_kb']} KB"
            )
        )
    except Exception as e:
        update.message.reply_text("⚠️ Something went wrong while processing your image.")
        print(f"Error: {e}")
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass

# =====================
# ERROR HANDLER
# =====================
def error(update: Update, context: CallbackContext):
    print(f"⚠️ Error: {context.error}")

# =====================
# MAIN
# =====================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))
    dp.add_error_handler(error)

    print("🤖 Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
