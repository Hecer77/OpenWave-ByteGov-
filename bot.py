from threading import Thread
from flask import Flask as BotFlask, request as bot_request, jsonify as bot_jsonify
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN = os.getenv("TOKEN")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")

import json
import httpx
from database import init_db, muraciet_elave_et, gunluk_muraciet_sayi
from ai_service import ai_analiz, ai_foto_analiz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

PROBLEM_NOV, PROBLEM_ACIQLA, PHOTO, LOCATION = range(4)

problem_novleri = [
    ["Su problemi", "Isiq problemi"],
    ["Yol problemi", "Zibil problemi"],
    ["Diger"]
]


async def foto_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["foto_path"] = None
    await update.message.reply_text(
        "Sekil olmadan davam edilir.\n"
        "Yerinizi gonderin: Paperclip -> Location"
    )
    return LOCATION



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Openwave Narimanov rayonu muraciet botuna xos geldiniz.\n\nProblem novunu secin:",
        reply_markup=ReplyKeyboardMarkup(problem_novleri, one_time_keyboard=True)
    )
    return PROBLEM_NOV


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "OpenWave Narimanov Muraciet Botu\n\n"
        "Asagidaki problemleri bize bildire bilersiniz:\n"
        "- Yol problemi (cuxur, asfalt)\n"
        "- Su problemi (boru, kanalizasiya)\n"
        "- Isiq problemi (direk, kuce isigi)\n"
        "- Temizlik (zibil)\n"
        "- Agac (tehlikeli, devrilmis)\n\n"
        "Muraciet etmek ucun /start yazin."
    )


async def problem_nov_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nov"] = update.message.text
    await update.message.reply_text("Problemi qisaca aciqlayin:")
    return PROBLEM_ACIQLA


async def problem_aciqla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    aciqla = update.message.text
    aciqla_lower = aciqla.lower()

    # Kod seveviyyesinde yoxlama - yer sorulmadan
    aciq_spam = ["pulum yoxdur", "pul yoxdur", "borc", "masinim xarab",
                 "issiz", "dalaş", "munaqise", "tixac", "park problemi",
                 "qonsu", "ses-kuy", "komek edin", "usagim", "xeste",
                 "hasta", "doktor", "yardim edin", "allah xetrine"]

    for soz in aciq_spam:
        if soz in aciqla_lower:
            await update.message.reply_text(
                "Muracietiniz qebul edilmedi.\n\n"
                "Sebeb: Bu problem bizim xidmet sahemize aid deyil.\n\n"
                "Yalniz bu problemleri qebul edirik:\n"
                "Yol, su, isiq, temizlik, agac problemleri."
            )
            return ConversationHandler.END

    # Cox qisa metn
    if len(aciqla.strip()) < 10:
        await update.message.reply_text(
            "Zehmet olmasa problemi daha aydin aciqlayin.\n"
            "Meselan: 'Nizami kucesinde iri cuxur var'"
        )
        return PROBLEM_ACIQLA

    nov = context.user_data["nov"]
    await update.message.reply_text("Muracietiniz analiz edilir...")

    try:
        analiz = ai_analiz(nov, aciqla)

        if analiz.get("saxta_muraciet"):
            sebeb = analiz.get("red_sebebi", "Namelum sebeb")
            red_sayi = context.user_data.get("red_sayi", 0) + 1
            context.user_data["red_sayi"] = red_sayi

            if red_sayi >= 2:
                await update.message.reply_text(
                    "Muracietiniz qebul edilmedi.\n\n"
                    f"Sebeb: {sebeb}\n\n"
                    "Zehmet olmasa yalniz kommunal problemleri bildirin."
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "Muracietiniz aydin deyil.\n\n"
                    f"Sebeb: {sebeb}\n\n"
                    "Zehmet olmasa daha aydin aciqlayin.\n"
                    "Meselan: 'Nizami kucesinde iri cuxur var'"
                )
                return PROBLEM_ACIQLA

        # Analiz ugurlu olduqda, yadda saxlayiriq
        context.user_data["aciqla"] = aciqla
        context.user_data["analiz"] = analiz

        await update.message.reply_text(
            "Tesekkurler! Indi problemi gosteren SEKIL gonderin.\n"
            "Sekil gondermek istemirseniz /skip yazin."
        )
        return PHOTO

    except Exception as e:
        print(f"AI analiz xetasi: {e}")
        # Default fallback
        analiz = {
            "prioritet": "NORMAL",
            "mesul_sobe": "Diger",
            "qisa_xulase": aciqla[:30],
            "saxta_muraciet": False,
            "red_sebebi": ""
        }
        context.user_data["aciqla"] = aciqla
        context.user_data["analiz"] = analiz

        await update.message.reply_text(
            "Tesekkurler! Indi problemi gosteren SEKIL gonderin.\n"
            "Sekil gondermek istemirseniz /skip yazin."
        )
        return PHOTO


async def foto_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sekil qebul edildi, analiz edilir...")

    foto = update.message.photo[-1]
    foto_file = await foto.get_file()
    foto_path = f"photos/{update.message.from_user.id}_{foto.file_id}.jpg"
    await foto_file.download_to_drive(foto_path)

    try:
        foto_analiz = ai_foto_analiz(foto_path)

        if not foto_analiz.get("problem_var"):
            import os
            os.remove(foto_path)
            await update.message.reply_text(
                "Sekilde kommunal infrastruktur problemi askar edilmedi.\n\n"
                f"Sebeb: {foto_analiz.get('red_sebebi', 'Namelum')}\n\n"
                "Zehmet olmasa problemi gosteren sekil gonderin."
            )
            return PHOTO

        context.user_data["foto_path"] = foto_path
        await update.message.reply_text(
            "Sekil qebul edildi! Indi yerinizi gonderin.\n"
            "Telegramda: Paperclip -> Location"
        )
        return LOCATION

    except Exception as e:
        print(f"Foto analiz xetasi: {e}")
        context.user_data["foto_path"] = foto_path
        await update.message.reply_text(
            "Sekil qebul edildi! Indi yerinizi gonderin.\n"
            "Telegramda: Paperclip -> Location"
        )
        return LOCATION


async def location_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    nov = context.user_data["nov"]
    foto_path = context.user_data.get("foto_path")
    aciqla = context.user_data["aciqla"]
    user_id = str(update.message.from_user.id)

    await update.message.reply_text("Muracietiniz qeyde alinir...")

    try:
        analiz = context.user_data.get("analiz")
        if not analiz:
            analiz = ai_analiz(nov, aciqla)

        prioritet_emoji = "🔴" if analiz["prioritet"] == "TECILI" else "🟡" if analiz["prioritet"] == "NORMAL" else "🟢"
        muraciet_no = str(update.message.from_user.id)[-4:]

        print(f"YENİ MÜRACİƏT | #{muraciet_no} | {nov} | {analiz['prioritet']} | {analiz['mesul_sobe']} | {loc.latitude},{loc.longitude}")

        muraciet_elave_et(
            user_id=user_id,
            nov=nov,
            aciqla=aciqla,
            prioritet=analiz["prioritet"],
            mesul_sobe=analiz["mesul_sobe"],
            xulase=analiz["qisa_xulase"],
            lat=loc.latitude,
            lon=loc.longitude,
            foto_yol=foto_path
        )

        await update.message.reply_text(
            f"Muracietiniz qebul edildi!\n\n"
            f"No: #{muraciet_no}\n"
            f"Prioritet: {prioritet_emoji} {analiz['prioritet']}\n"
            f"Mesul sobe: {analiz['mesul_sobe']}\n\n"
            f"En qisa zamanda baxilacaq!"
        )

    except Exception as e:
        print(f"Xeta: {e}")
        await update.message.reply_text("Muracietiniz qebul edildi! Tesekkurler.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Muraciet legv edildi.")
    return ConversationHandler.END

bot_app = BotFlask(__name__)
telegram_app = None

@bot_app.route("/send_message", methods=["POST"])
def send_message():
    data = bot_request.json
    user_id = data.get("user_id")
    message = data.get("message")
    
    if user_id and message:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": message},
                timeout=10
            )
        except Exception as e:
            print(f"Error sending message: {e}")
            return bot_jsonify({"ok": False, "error": str(e)}), 500
    
    return bot_jsonify({"ok": True})

def run_bot_api():
    bot_app.run(port=5001, debug=False)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, start)
    ],
    states={
        PROBLEM_NOV: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_nov_al)],
        PROBLEM_ACIQLA: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_aciqla)],
        PHOTO: [
            MessageHandler(filters.PHOTO, foto_al),
            CommandHandler("skip", foto_skip)
        ],
        LOCATION: [MessageHandler(filters.LOCATION, location_al)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
   
    
    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_cmd))
    print("Bot ise dusdu...")
    global telegram_app
    telegram_app = app

    Thread(target=run_bot_api, daemon=True).start()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()