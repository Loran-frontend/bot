import os
import asyncio
import psycopg2
from flask import Flask, request
from telegram import Update, Bot

TOKEN = "8394612560:AAEA_-8I-TMpW7LxCEmGHBu8uWa6FMoHcJk"
PUBLIC_URL = "flaskapi-production-d315.up.railway.app"

WEBHOOK_PATH = f"/{TOKEN}"

app = Flask(__name__)
bot = Bot(TOKEN)

conn = psycopg2.connect(
    host="postgres.railway.internal",
    user="postgres",
    password="MMFkuYbxbnytTTTJERqNpGPlaSinIzwz",
    dbname="railway",
    port=5432
)

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.json, bot)
    asyncio.create_task(handle_update(update))
    return "OK"

async def handle_update(update: Update):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id  # Telegram ID

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT used, uuid FROM codes WHERE code=%s", (text,))
            row = cur.fetchone()

            if row is None:
                await bot.send_message(update.message.chat_id, "Код не найден.")
                return

            used, uuid = row
            if used:
                await bot.send_message(update.message.chat_id, "Код уже использован.")
                return

            cur.execute(
                "UPDATE codes SET used=true, telegram_id=%s WHERE code=%s",
                (user_id, text)
            )
            await bot.send_message(
                update.message.chat_id,
                f"Код принят! Ваш Telegram ID ({user_id}) привязан к UUID {uuid}."
            )


if __name__ == "__main__":
    asyncio.run(bot.set_webhook(f"{PUBLIC_URL}/{TOKEN}"))
    app.run(host="0.0.0.0", port=8001)
