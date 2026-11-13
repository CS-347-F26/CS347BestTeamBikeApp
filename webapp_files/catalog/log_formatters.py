import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    fields = (
        "event",
        "request_id",
        "method",
        "path",
        "status",
        "duration_ms",
        "user_id",
        "route_id",
        "route_name",
        "source",
    )

    def format(self, record):
        data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.fields:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False, default=str)
