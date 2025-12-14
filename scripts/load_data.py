import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_data.py <path_to_json_file>")
        print("\nExample:")
        print("  python scripts/load_data.py data/videos.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    
    print(f"Загрузка данных из {json_path}...")
    try:
        load_json_to_db(json_path)
        print("\n✅ Данные успешно загружены!")
    except Exception as e:
        print(f"\n❌ Ошибка при загрузке данных: {e}")
        sys.exit(1)


import json
from datetime import datetime
from pathlib import Path
import logging

from src.database.models import Video, VideoSnapshot
from src.database.db import get_db_session

logger = logging.getLogger(__name__)


def parse_datetime(dt_str: str) -> datetime:
    """Парсит строку даты в datetime объект"""
    from datetime import timezone
    
    formats = [
        "%Y-%m-%dT%H:%M:%S+00:00",
        "%Y-%m-%dT%H:%M:%S.%f+00:00",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            if dt_str.endswith('Z'):
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    raise ValueError(f"Не удалось распарсить дату: {dt_str}")


def load_json_to_db(json_path: str | Path) -> None:
    json_path = Path(json_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"Файл не найден: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data['videos'], list):
        raise ValueError("JSON должен содержать массив объектов videos")
    
    with get_db_session() as db:
        for video_data in data['videos']:
            logger.info(f"Loading video: {video_data['id']}")
            # Создаем видео
            video = Video(
                id=video_data["id"],
                creator_id=video_data["creator_id"],
                video_created_at=parse_datetime(video_data["video_created_at"]),
                views_count=video_data.get("views_count", 0),
                likes_count=video_data.get("likes_count", 0),
                comments_count=video_data.get("comments_count", 0),
                reports_count=video_data.get("reports_count", 0),
            )
            db.add(video)
            
            # Создаем снапшоты
            snapshots = video_data['snapshots']
            for snapshot_data in snapshots:
                snapshot = VideoSnapshot(
                    id=snapshot_data["id"],
                    video_id=video.id,
                    views_count=snapshot_data.get("views_count", 0),
                    likes_count=snapshot_data.get("likes_count", 0),
                    comments_count=snapshot_data.get("comments_count", 0),
                    reports_count=snapshot_data.get("reports_count", 0),
                    delta_views_count=snapshot_data.get("delta_views_count", 0),
                    delta_likes_count=snapshot_data.get("delta_likes_count", 0),
                    delta_comments_count=snapshot_data.get("delta_comments_count", 0),
                    delta_reports_count=snapshot_data.get("delta_reports_count", 0),
                    created_at=parse_datetime(snapshot_data["created_at"]),
                )
                db.add(snapshot)
        
        print(f"Загружено {len(data)} видео в базу данных")

if __name__ == "__main__":
    main()

