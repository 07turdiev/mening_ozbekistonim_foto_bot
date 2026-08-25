"""Botni ishga tushirishdan oldingi tekshiruv: python selftest.py

Telegram serveriga ulanmaydi — faqat kod, baza va validatorlarni sinaydi.
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "000000:TEST")
os.environ.setdefault("ADMIN_IDS", "1")

OK, FAIL = "  [OK]  ", "  [XATO]"
errors: list[str] = []


def check(name: str, fn):
    try:
        fn()
        print(OK, name)
    except AssertionError as exc:
        print(FAIL, name, "->", exc)
        errors.append(f"{name}: {exc}")
    except Exception as exc:
        print(FAIL, name, "->", repr(exc))
        errors.append(f"{name}: {exc!r}")


def main() -> int:
    print("\n=== 1. Modullar ===")

    def imports():
        import bot, database, handlers.admin, handlers.user, keyboards, texts  # noqa: F401
        import utils.export, utils.validators  # noqa: F401
    check("Barcha modullar import qilinadi", imports)

    from config import cfg
    import database as db
    from utils.validators import (
        validate_description, validate_fio, validate_phone,
        validate_place, validate_shot_date, validate_title,
    )

    print("\n=== 2. Sozlamalar ===")
    check("Tanlov muddati to‘g‘ri", lambda: (_ for _ in ()).throw(AssertionError("start > end"))
          if cfg.start_date > cfg.end_date else None)
    print(f"         muddat: {cfg.start_date} .. {cfg.end_date} | bugun: {cfg.today()} | "
          f"qabul ochiq: {cfg.is_open()}")
    print(f"         talab: {cfg.min_width}x{cfg.min_height} px, max {cfg.max_file_mb} MB, "
          f"{cfg.max_photos} ta surat")

    print("\n=== 3. Validatorlar ===")

    def v_fio():
        assert validate_fio("Aliyev Sardor Baxtiyorovich")[0]
        assert not validate_fio("Ali")[0]
        assert not validate_fio("Aliyev123")[0]
        assert not validate_fio("Sardor")[0]
    check("F.I.Sh.", v_fio)

    def v_phone():
        assert validate_phone("901234567")[1] == "+998901234567"
        assert validate_phone("+998 90 123 45 67")[1] == "+998901234567"
        assert validate_phone("998901234567")[1] == "+998901234567"
        assert not validate_phone("123")[0]
    check("Telefon raqami", v_phone)

    def v_date():
        assert validate_shot_date("15.06.2025")[1] == "15.06.2025"
        assert validate_shot_date("15/06/2025")[0]
        assert not validate_shot_date("31.02.2025")[0]
        assert not validate_shot_date("kecha")[0]
        assert not validate_shot_date("01.01.2099")[0]
    check("Sana", v_date)

    def v_rest():
        assert validate_title("Registon tongi")[0]
        assert not validate_title("A")[0]
        assert validate_place("Samarqand shahri, Registon maydoni")[0]
        assert not validate_place("Sm")[0]
        assert not validate_description("Juda qisqa izoh")[0]
        assert validate_description(
            "Ushbu kadr Registon maydonida tong palet nurlari ostida olingan. "
            "Meni bu lahzaning sokinligi hayratga soldi."
        )[0]
    check("Nom, joy, izoh", v_rest)

    print("\n=== 4. Fotosurat tekshiruvi ===")

    def v_photo():
        from PIL import Image
        from utils.validators import check_photo_file
        tmp = Path(tempfile.mkdtemp())

        small = tmp / "small.jpg"
        Image.new("RGB", (1200, 800), "navy").save(small, "JPEG")
        res = check_photo_file(small, small.stat().st_size)
        assert not res.ok, "kichik surat rad etilishi kerak edi"

        big = tmp / "big.jpg"
        Image.new("RGB", (cfg.min_width, cfg.min_height), "teal").save(big, "JPEG", quality=90)
        res = check_photo_file(big, big.stat().st_size)
        assert res.ok, f"katta surat qabul qilinishi kerak edi: {res.error}"
        assert len(res.file_hash) == 64

        png = tmp / "wrong.png"
        Image.new("RGB", (cfg.min_width, cfg.min_height), "gray").save(png, "PNG")
        assert not check_photo_file(png, png.stat().st_size).ok, "PNG rad etilishi kerak edi"
    check("O‘lcham, format va hash", v_photo)

    print("\n=== 5. Ma’lumotlar bazasi ===")

    async def db_flow():
        db_backup = cfg.db_path
        object.__setattr__(cfg, "db_path", Path(tempfile.mkdtemp()) / "test.db")
        try:
            await db.init_db()
            await db.upsert_user(555, "tester")
            await db.set_agreement(555)
            await db.save_profile(555, "Testov Test", "+998901112233")
            assert await db.is_registered(555)

            pid = await db.add_photo({
                "user_id": 555, "file_id": "F1", "file_unique": "U1", "file_hash": "h" * 64,
                "file_name": "a.jpg", "file_path": "a.jpg", "width": 4000, "height": 3000,
                "file_size": 5_000_000, "has_exif": 1, "exif_info": "Make: Canon",
                "title": "Test surat", "place": "Toshkent", "shot_date": "01.01.2025",
                "description": "Izoh " * 12, "status": "pending",
            })
            assert pid > 0
            assert await db.count_active_photos(555) == 1
            assert await db.find_duplicate("h" * 64) is not None
            await db.set_status(pid, "approved", 1)
            row = await db.get_photo(pid)
            assert row["status"] == "approved" and row["fio"] == "Testov Test"
            assert (await db.stats())["approved"] == 1
            assert await db.search_users("Testov")
            await db.set_setting("paused", "1")
            assert await db.acceptance_paused()

            from utils.export import build_excel
            xlsx = build_excel(await db.all_photos_full())
            assert xlsx.exists() and xlsx.stat().st_size > 0
            xlsx.unlink()
        finally:
            object.__setattr__(cfg, "db_path", db_backup)

    check("Baza + Excel eksport", lambda: asyncio.run(db_flow()))

    print("\n" + "=" * 46)
    if errors:
        print(f"XATOLIKLAR: {len(errors)} ta")
        for e in errors:
            print(" -", e)
        return 1
    print("Barcha tekshiruvlar muvaffaqiyatli o‘tdi.")
    print("Endi .env faylini to‘ldiring va `python bot.py` buyrug‘ini bering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
