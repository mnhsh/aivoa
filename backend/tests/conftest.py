import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DATABASE = Path(tempfile.gettempdir()) / f"aivoa-test-{os.getpid()}.db"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = ""
os.environ["SQLITE_FALLBACK_PATH"] = str(TEST_DATABASE)


def pytest_sessionfinish() -> None:
    TEST_DATABASE.unlink(missing_ok=True)
