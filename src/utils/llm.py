import re
import logging

from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)


DATABASE_SCHEMA = """
База данных содержит две таблицы:

1. Таблица `videos` (итоговая статистика по видео):
   - id (String, PRIMARY KEY) - идентификатор видео
   - creator_id (String) - идентификатор креатора
   - video_created_at (DateTime) - дата и время публикации видео
   - views_count (Integer) - финальное количество просмотров
   - likes_count (Integer) - финальное количество лайков
   - comments_count (Integer) - финальное количество комментариев
   - reports_count (Integer) - финальное количество жалоб
   - created_at (DateTime) - время создания записи
   - updated_at (DateTime) - время обновления записи

2. Таблица `video_snapshots` (почасовые замеры статистики):
   - id (String, PRIMARY KEY) - идентификатор снапшота
   - video_id (String, FOREIGN KEY -> videos.id) - ссылка на видео
   - views_count (Integer) - текущее количество просмотров на момент замера
   - likes_count (Integer) - текущее количество лайков на момент замера
   - comments_count (Integer) - текущее количество комментариев на момент замера
   - reports_count (Integer) - текущее количество жалоб на момент замера
   - delta_views_count (Integer) - приращение просмотров с прошлого замера
   - delta_likes_count (Integer) - приращение лайков с прошлого замера
   - delta_comments_count (Integer) - приращение комментариев с прошлого замера
   - delta_reports_count (Integer) - приращение жалоб с прошлого замера
   - created_at (DateTime) - время замера (раз в час)
   - updated_at (DateTime) - время обновления записи

Важно:
- Для итоговых значений используй таблицу `videos`
- Для динамики/прироста используй таблицу `video_snapshots` и поля delta_*
- Для фильтрации по дате используй поля video_created_at (в videos) или created_at (в snapshots)
- Для фильтрации по креатору используй creator_id в таблице videos
"""

SYSTEM_PROMPT = f"""Ты - помощник для генерации SQL запросов к базе данных аналитики видео.

{DATABASE_SCHEMA}

Твоя задача:
1. Понять запрос пользователя на русском языке
2. Сгенерировать правильный SQL запрос (PostgreSQL)
3. Вернуть ТОЛЬКО SQL запрос без дополнительных объяснений

Правила:
- Используй только SELECT запросы
- Запрос должен возвращать одно число (результат агрегации: COUNT, SUM, AVG и т.д.)
- Если нужна сумма - используй SUM()
- Если нужен счетчик - используй COUNT()
- Если нужен прирост - используй SUM() по полям delta_* из video_snapshots
- Если нужна средняя - используй AVG()
- Если нужен максимум/минимум - используй MAX()/MIN()
- Для фильтрации по дате используй WHERE с условиями на дату
- Для фильтрации по креатору используй WHERE creator_id = '...'
- Всегда используй корректные имена таблиц и полей

Примеры:
- "Сколько всего видео?" -> SELECT COUNT(*) FROM videos;
- "Сколько просмотров у всех видео?" -> SELECT SUM(views_count) FROM videos;
- "Сколько лайков у креатора abc123?" -> SELECT SUM(likes_count) FROM videos WHERE creator_id = 'abc123';
- "Какой прирост просмотров за последний час?" -> SELECT SUM(delta_views_count) FROM video_snapshots WHERE created_at >= NOW() - INTERVAL '1 hour';
- "Сколько комментариев у видео с id xyz?" -> SELECT comments_count FROM videos WHERE id = 'xyz';

Верни ТОЛЬКО SQL запрос, без markdown форматирования, без объяснений."""


def generate_sql_query(user_query: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        temperature=0.7,
    )
    
    sql_query = response.choices[0].message.content.strip()
    
    if sql_query.startswith("```"):
        lines = sql_query.split("\n")
        sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
    
    return sql_query.strip()


def validate_sql_query(sql: str) -> bool:
    
    
    sql_upper = sql.upper().strip()
    
    if not sql_upper.startswith("SELECT"):
        logger.warning(f"Query does not start with SELECT: {sql_upper[:50]}")
        return False
    
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            logger.warning(f"Dangerous keyword found: {keyword}")
            return False
    
    return True