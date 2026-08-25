"""Bot konfiguratsiyasi — barcha sozlamalar .env faylidan o'qiladi."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(" ", "").split(",") if x.lstrip("-").isdigit()]


def _date(raw: str, default: str) -> date:
    return datetime.strptime(raw or default, "%Y-%m-%d").date()


@dataclass(frozen=True)
class Config:
    token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: list[int] = field(default_factory=lambda: _int_list(os.getenv("ADMIN_IDS", "")))

    start_date: date = _date(os.getenv("START_DATE", ""), "2026-08-27")
    end_date: date = _date(os.getenv("END_DATE", ""), "2026-09-05")

    max_photos: int = int(os.getenv("MAX_PHOTOS", "3"))
    min_width: int = int(os.getenv("MIN_WIDTH", "3000"))
    min_height: int = int(os.getenv("MIN_HEIGHT", "2000"))
    max_file_mb: int = int(os.getenv("MAX_FILE_MB", "20"))

    channel_id: str = os.getenv("CHANNEL_ID", "").strip()
    channel_url: str = os.getenv("CHANNEL_URL", "").strip()
    archive_chat_id: str = os.getenv("ARCHIVE_CHAT_ID", "").strip()

    contact_info: str = os.getenv("CONTACT_INFO", "—")
    moderation: bool = os.getenv("MODERATION", "1") == "1"
    test_mode: bool = os.getenv("TEST_MODE", "0") == "1"
    tz_offset: int = int(os.getenv("TIMEZONE_OFFSET", "5"))

    db_path: Path = BASE_DIR / "contest.db"
    uploads_dir: Path = BASE_DIR / "uploads"
    exports_dir: Path = BASE_DIR / "exports"

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024

    @property
    def tz(self) -> timezone:
        return timezone(timedelta(hours=self.tz_offset))

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def today(self) -> date:
        return self.now().date()

    def is_open(self) -> bool:
        """Tanlov qabul muddati davom etayaptimi (TEST_MODE da doim ochiq)."""
        if self.test_mode:
            return True
        return self.start_date <= self.today() <= self.end_date

    def not_started(self) -> bool:
        return not self.test_mode and self.today() < self.start_date

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def validate(self) -> None:
        if not self.token or ":" not in self.token:
            raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan yoki noto'g'ri.")
        if not self.admin_ids:
            raise RuntimeError("ADMIN_IDS .env faylida ko'rsatilmagan.")
        if self.start_date > self.end_date:
            raise RuntimeError("START_DATE END_DATE dan keyin bo'lishi mumkin emas.")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


cfg = Config()
