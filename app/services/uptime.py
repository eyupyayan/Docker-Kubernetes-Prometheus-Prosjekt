from datetime import datetime, timezone

_started = datetime.now(timezone.utc)

def started_at():
    return _started

def uptime_seconds() -> int:
    delta = datetime.now(timezone.utc) - _started
    return int(delta.total_seconds())
