import asyncio
from telegram import Bot
import aiohttp
import hashlib

BOT_TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = "6318865778"

URL = "https://www.agropraktika.eu/vacancies"
CHECK_INTERVAL = 120

bot = Bot(token=BOT_TOKEN)

previous_hash = None

async def check_vacancies():
    global previous_hash
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(URL) as response:
                    html = await response.text()
                    current_hash = hashlib.md5(html.encode()).hexdigest()

                    if previous_hash and current_hash != previous_hash:
                        await bot.send_message(chat_id=CHAT_ID, text="Страница вакансий обновилась!")

                    previous_hash = current_hash

            except Exception as e:
                await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

async def main():
    await bot.send_message(chat_id=CHAT_ID, text="Бот запущен и работает 24/7!")
    await check_vacancies()

if __name__ == "__main__":
    asyncio.run(main())
