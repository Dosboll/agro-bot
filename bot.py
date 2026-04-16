import asyncio
from telegram import Bot
import aiohttp
from datetime import datetime

BOT_TOKEN = "8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA"
CHAT_ID = 8102460194

BASE_URL = "https://agropraktika.eu/vacancies"
CHECK_INTERVAL = 90
PAGES = 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

bot = Bot("8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA")

previous_status = {}
previous_vacancy_count = 0


def log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}", flush=True)


async def get_data(session):
    status = {}
    vacancy_count = 0

    for page in range(1, PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        log(f"Проверка страницы {page}")

        try:
            async with session.get(url, headers=HEADERS) as response:

                # если сайт блокирует
                if response.status == 403:
                    log("Ошибка 403 — сайт блокирует")
                    return None, None

                html = await response.text()
                html_lower = html.lower()

                # защита от пустой страницы
                if len(html) < 1000:
                    log("Слишком маленький HTML — пропуск")
                    return None, None

                # считаем вакансии
                count_on_page = html_lower.count('class="vacancy"')
                vacancy_count += count_on_page
                log(f"Вакансий на странице {page}: {count_on_page}")

                # проверка регистрации
                if "регистрация временно приостановлена" in html_lower:
                    status[page] = 1
                    log(f"Страница {page}: закрыто")
                else:
                    status[page] = 0
                    log(f"Страница {page}: ВОЗМОЖНО ОТКРЫТО")

        except Exception as e:
            log(f"Ошибка: {e}")
            return None, None

    return status, vacancy_count


async def check():
    global previous_status, previous_vacancy_count

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                log("Новая проверка сайта")
                current_status, vacancy_count = await get_data(session)

                if current_status is None:
                    log("Пропуск проверки")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                log(f"Всего вакансий сейчас: {vacancy_count}")

                # первый запуск
                if not previous_status:
                    previous_status = current_status
                    previous_vacancy_count = vacancy_count
                    log("Первичная проверка выполнена")

                else:
                    # регистрация открылась
                    for page in current_status:
                        if (
                            page in previous_status
                            and previous_status[page] == 1
                            and current_status[page] == 0
                        ):
                            log(f"🔥 ОТКРЫЛОСЬ на странице {page}")

                            for _ in range(3):
                                await bot.send_message(
                                    chat_id=CHAT_ID,
                                    text=f"🚨 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ!\nСтраница: {page}\n{BASE_URL}?page={page}"
                                )
                                await asyncio.sleep(1)

                    # добавили вакансию
                    if vacancy_count > previous_vacancy_count:
                        log("Добавлена новая вакансия")
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text="➕ Добавлена новая вакансия"
                        )

                    # удалили вакансию
                    if vacancy_count < previous_vacancy_count:
                        log("Удалили вакансию")
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text="➖ Вакансия удалена"
                        )

                    previous_status = current_status
                    previous_vacancy_count = vacancy_count

            except Exception as e:
                log(f"Критическая ошибка: {e}")
                await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка: {e}")

            log(f"Жду {CHECK_INTERVAL} секунд")
            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    log("Бот запущен")
    await bot.send_message(chat_id=CHAT_ID, text="Бот запущен и следит за Agropraktika 24/7")
    await check()


if __name__ == "__main__":
    asyncio.run(main())