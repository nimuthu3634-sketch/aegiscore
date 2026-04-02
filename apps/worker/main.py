from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from rq import Worker  # noqa: E402
from app.workers.queue import get_redis_connection  # type: ignore  # noqa: E402


def main() -> None:
    redis_connection = get_redis_connection()
    Worker(["ml"], connection=redis_connection).work()


if __name__ == "__main__":
    main()
