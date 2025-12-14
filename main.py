import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.config import settings
from src.database.db import get_db_session
from src.utils.query_executor import execute_natural_language_query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    welcome_text = (
        f"Привет, {html.bold(message.from_user.full_name)}!\n\n"
        "Я бот для аналитики по видео. Задай мне вопрос на русском языке, "
        "и я найду нужную информацию в базе данных.\n\n"
        "Примеры запросов:\n"
        "• Сколько всего видео?\n"
        "• Сколько просмотров у всех видео?\n"
        "• Какой прирост лайков за последний час?\n"
        "• Сколько комментариев у креатора с id abc123?"
    )
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    help_text = (
        "Я понимаю запросы на русском языке и могу ответить на вопросы:\n\n"
        "📊 Статистика:\n"
        "• Сколько всего видео?\n"
        "• Сколько просмотров у всех видео?\n"
        "• Среднее количество лайков?\n\n"
        "👤 По креаторам:\n"
        "• Сколько видео у креатора с id ...?\n"
        "• Сколько просмотров у креатора ...?\n\n"
        "📈 Динамика:\n"
        "• Какой прирост просмотров за последний час?\n"
        "• Сколько новых лайков за сегодня?\n\n"
        "Просто напиши свой вопрос, и я найду ответ!"
    )
    await message.answer(help_text)


@dp.message()
async def query_handler(message: Message) -> None:
    user_query = message.text.strip()
    
    if not user_query:
        await message.answer("Пожалуйста, задай вопрос на русском языке.")
        return
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        with get_db_session() as db:
            result = execute_natural_language_query(db, user_query)
        
        await message.answer(str(result))
        
    except ValueError as e:
        logger.error(f"Error executing query: {e}")
        await message.answer(f"❌ Error processing query.\n\nError: {html.code(str(e))}\n\nTry reformulating the question or use /help for examples.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await message.answer("❌ Error processing query. Try later.")


async def main() -> None:
    logger.info("Запуск бота...")
    
    logger.info("Бот запущен и готов к работе")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        sys.exit(1)