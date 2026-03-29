from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def wait_for(url: str, *, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            fetch(url)
            return
        except Exception as error:  # pragma: no cover - exercised in CI only
            last_error = error
            time.sleep(3)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    wait_for(f"{base_url}/healthz")

    root_payload = fetch(base_url)
    health_payload = fetch(f"{base_url}/api/v1/health")
    docs_payload = fetch(f"{base_url}/docs")

    if "AegisCore" not in root_payload:
        raise RuntimeError("Frontend root response did not include the expected AegisCore marker")
    if '"status":"ok"' not in health_payload.replace(" ", ""):
        raise RuntimeError("API health response did not report ok status")
    if "swagger" not in docs_payload.lower():
        raise RuntimeError("Docs endpoint did not return the Swagger UI")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as error:  # pragma: no cover - exercised in CI only
        raise SystemExit(f"Smoke test failed: {error}") from error
