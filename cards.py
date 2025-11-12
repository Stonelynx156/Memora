import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone,timedelta
from typing import Dict

def _now() -> datetime:
    return datetime.now(timezone.utc)

def human_date(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts)
    except ValueError:
        return iso_ts
    return dt.timezone().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class Card:
    id : str
    front : str
    back : str
    interval : int = 1
    ease_factor : float = 2.5
    repetitions : int = 0
    due : str = _now().isoformat()