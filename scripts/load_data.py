import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from src.database.models import Video, VideoSnapshot
from src.database.db import get_db_session


sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python scripts/load_data.py <path_to_json_file>")
        logger.error("Example:")
        logger.error("  python scripts/load_data.py data/videos.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    logger.info(f"Loading data from {json_path}...")
    try:
        load_json_to_db(json_path)
        logger.info("Data successfully loaded!")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        sys.exit(1)




def parse_datetime(dt_str: str) -> datetime:
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
    raise ValueError(f"Unable to parse date: {dt_str}")


def load_json_to_db(json_path: str | Path) -> None:
    json_path = Path(json_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data['videos'], list):
        raise ValueError("JSON must contain an array of video objects")
    
    with get_db_session() as db:
        for video_data in data['videos']:
            logger.info(f"Loading video: {video_data['id']}")
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
        
        logger.info(f"Loaded {len(data)} videos to database")

if __name__ == "__main__":
    main()

