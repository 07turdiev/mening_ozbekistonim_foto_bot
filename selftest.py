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

    def v_large():
        from PIL import Image
        from utils.validators import check_photo_file, oversize_hint
        # Yuqori o'lcham chegarasi bo'lmasligi kerak
        assert Image.MAX_IMAGE_PIXELS is None, \
            "Pillow'ning megapiksel chegarasi yirik kadrlarni rad etadi"
        tmp = Path(tempfile.mkdtemp()) / "large.jpg"
        Image.new("RGB", (6000, 4000), "olive").save(tmp, "JPEG", quality=90)
        res = check_photo_file(tmp, tmp.stat().st_size)
        assert res.ok, f"yirik surat qabul qilinishi kerak edi: {res.error}"
        assert (res.width, res.height) == (6000, 4000)
        # Hajm chegarasi esa saqlanadi va maslahat beradi
        res = check_photo_file(tmp, cfg.max_file_bytes + 1)
        assert not res.ok and "Piksel o‘lchamiga yuqori chegara yo‘q" in res.error, \
            "hajm oshganda maslahat ko‘rsatilmadi"
        tmp.unlink()
    check("Yirik o‘lcham cheklanmagan", v_large)

    def v_orientation():
        from PIL import Image
        from utils.validators import check_photo_file
        tmp = Path(tempfile.mkdtemp())

        def probe(w, h):
            p = tmp / f"{w}x{h}.jpg"
            Image.new("RGB", (w, h), "purple").save(p, "JPEG", quality=85)
            return check_photo_file(p, p.stat().st_size)

        # Vertikal (portret) kadr - uzun tomoni 4000, qisqasi 2250 -> qabul
        res = probe(2250, 4000)
        assert res.ok, f"vertikal kadr rad etildi: {res.error}"
        # Kvadrat kadr: 3000x3000 -> ikkala tomon ham yetarli
        assert probe(3000, 3000).ok, "kvadrat kadr rad etilmasligi kerak"
        # Uzun tomoni yetarli, qisqasi kam -> rad
        res = probe(1500, 4000)
        assert not res.ok, "qisqa tomoni kam kadr qabul qilinmasligi kerak"
        assert "qisqa tomoni" in res.error, "xato matni tushuntirmayapti"
        # Ikkala tomon ham kam -> rad
        assert not probe(2000, 1500).ok, "kichik kadr qabul qilinmasligi kerak"
    check("Vertikal va kvadrat kadrlar", v_orientation)

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

    print("\n=== 6. Albom / navbat mantiqi ===")

    async def queue_flow():
        from types import SimpleNamespace
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.base import StorageKey
        from aiogram.fsm.storage.memory import MemoryStorage
        import handlers.user as u

        class FakeMsg:
            def __init__(self, uid=1):
                self.from_user = SimpleNamespace(id=uid, username="t")
                self.chat = SimpleNamespace(id=uid)
                self.sent: list[str] = []

            async def answer(self, text="", **kw):
                self.sent.append(text)
                return self

            async def answer_document(self, *a, **kw):
                self.sent.append("<document>")
                return self

        counter = {"n": 0}

        async def fake_process(message, bot, known_hashes):
            counter["n"] += 1
            n = counter["n"]
            return {
                "file_id": f"F{n}", "file_unique": f"U{n}", "file_name": f"{n}.jpg",
                "tmp_path": "", "width": 4000, "height": 3000, "file_size": 1000,
                "has_exif": 1, "exif_info": "", "file_hash": f"{n}" * 64,
            }

        real_process, real_count = u.process_document, u.db.count_active_photos
        u.process_document = fake_process
        u.db.count_active_photos = lambda uid: asyncio.sleep(0, result=0)
        try:
            state = FSMContext(storage=MemoryStorage(),
                               key=StorageKey(bot_id=1, chat_id=1, user_id=1))
            await state.set_state(u.Submit.photo)
            msg = FakeMsg()

            # 1-fayl: joriy ish bo'lib qoladi
            await u.handle_document(msg, state, None)
            data = await state.get_data()
            assert data["file_id"] == "F1", "1-fayl joriy ish bo'lishi kerak"
            assert await state.get_state() == u.Submit.title.state, "nom so'ralishi kerak"
            assert not data.get("queue"), "navbat bo'sh bo'lishi kerak"

            # 2- va 3-fayllar (albomning qolgani): navbatga tushadi
            await u.handle_document(msg, state, None)
            await u.handle_document(msg, state, None)
            data = await state.get_data()
            assert len(data["queue"]) == 2, f"navbatda 2 ta kutilgan, {len(data['queue'])} ta"
            assert data["file_id"] == "F1", "joriy ish almashib ketmasligi kerak"
            assert [i["file_id"] for i in data["queue"]] == ["F2", "F3"], "tartib buzilgan"

            # 4-fayl: limitdan oshadi - rad etilishi kerak
            before = counter["n"]
            await u.handle_document(msg, state, None)
            data = await state.get_data()
            assert len(data["queue"]) == 2, "limitdan oshgan fayl navbatga tushmasligi kerak"
            assert counter["n"] == before, "limitdan oshgan fayl yuklab olinmasligi kerak"
            assert any("eng ko‘p miqdor" in s for s in msg.sent), "ogohlantirish yo'q"

            # tozalash barcha vaqtinchalik fayllarni qamrab olishi kerak
            u._cleanup_files(await state.get_data())
        finally:
            u.process_document, u.db.count_active_photos = real_process, real_count

    check("Albom: 1 ta joriy + navbat + limit", lambda: asyncio.run(queue_flow()))

    print("\n=== 7. Moderatsiya navbati ===")

    async def moderation_flow():
        from types import SimpleNamespace
        import handlers.admin as adm

        class FakeMsg:
            def __init__(self):
                self.texts: list[str] = []
                self.docs: list[str] = []
                self.markups: list = []

            async def answer(self, text="", **kw):
                self.texts.append(text)
                self.markups.append(kw.get("reply_markup"))
                return self

            async def answer_document(self, file_id, **kw):
                self.docs.append(file_id)
                self.markups.append(kw.get("reply_markup"))
                return self

        db_backup = cfg.db_path
        object.__setattr__(cfg, "db_path", Path(tempfile.mkdtemp()) / "mod.db")
        try:
            await db.init_db()
            await db.upsert_user(777, "moderator_test")
            await db.save_profile(777, "Testov Test", "+998901112233")
            ids = []
            for n in (1, 2):
                ids.append(await db.add_photo({
                    "user_id": 777, "file_id": f"FID{n}", "file_unique": f"U{n}",
                    "file_hash": str(n) * 64, "file_name": f"{n}.jpg", "file_path": "",
                    "width": 4000, "height": 3000, "file_size": 1000, "has_exif": 1,
                    "exif_info": "", "title": f"Surat {n}", "place": "Toshkent",
                    "shot_date": "01.01.2025", "description": "Izoh " * 12, "status": "pending",
                }))

            msg = FakeMsg()
            await adm.show_queue(msg, 0)
            assert msg.docs == ["FID1"], f"birinchi ariza kutilgan, {msg.docs}"
            nav = [b.text for r in msg.markups[-1].inline_keyboard for b in r]
            assert "➡️ Keyingi" in nav, "2 ta ariza bo‘lsa navigatsiya bo‘lishi kerak"

            # 1-arizani qabul qilamiz -> o'sha indeks endi 2-arizani ko'rsatishi kerak
            await db.set_status(ids[0], "approved", 1)
            msg = FakeMsg()
            await adm.show_queue(msg, 0, "✅ qabul qilindi")
            assert msg.docs == ["FID2"], f"keyingi arizaga o‘tmadi: {msg.docs}"
            nav = [b.text for r in msg.markups[-1].inline_keyboard for b in r]
            assert "➡️ Keyingi" not in nav and "⬅️ Oldingi" not in nav, \
                "oxirgi arizada navigatsiya ko‘rsatilmasligi kerak"

            # 2-arizani ham yopamiz -> admin panelga qaytishi kerak
            await db.set_status(ids[1], "rejected", 1, "sabab")
            msg = FakeMsg()
            await adm.show_queue(msg, 0, "❌ rad etildi")
            assert not msg.docs, "navbat bo‘sh bo‘lsa surat yuborilmasligi kerak"
            assert "qolmadi" in msg.texts[-1], "yakunlanish xabari yo‘q"
            assert "Administrator paneli" in msg.texts[-1], "admin panelga qaytmadi"
            btns = [b.text for r in msg.markups[-1].inline_keyboard for b in r]
            assert "📊 Statistika" in btns, "admin panel tugmalari yo‘q"
        finally:
            object.__setattr__(cfg, "db_path", db_backup)

    check("Qabul/rad etgach keyingisi, tugagach panel", lambda: asyncio.run(moderation_flow()))

    print("\n=== 8. Qayta /start bosilganda ===")

    async def restart_flow():
        from types import SimpleNamespace
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.base import StorageKey
        from aiogram.fsm.storage.memory import MemoryStorage
        import handlers.user as u
        import keyboards as kb

        class FakeMsg:
            def __init__(self, uid):
                self.from_user = SimpleNamespace(id=uid, username="qaytgan")
                self.chat = SimpleNamespace(id=uid)
                self.markups: list = []

            async def answer(self, text="", **kw):
                self.markups.append(kw.get("reply_markup"))
                return self

        db_backup, tm_backup = cfg.db_path, cfg.test_mode
        object.__setattr__(cfg, "db_path", Path(tempfile.mkdtemp()) / "restart.db")
        # Test tanlov muddatiga bog'liq bo'lmasligi kerak: TEST_MODE=0 va muddat
        # boshlanmagan bo'lsa route_join surat qabulini to'xtatadi - bu to'g'ri
        # xatti-harakat, lekin bu yerda tekshirilayotgan narsa emas.
        object.__setattr__(cfg, "test_mode", True)
        try:
            await db.init_db()
            uid = 999
            await db.upsert_user(uid, "qaytgan")
            await db.set_agreement(uid)
            await db.save_profile(uid, "Aliyev Sardor Baxtiyorovich", "+998901234567")

            state = FSMContext(storage=MemoryStorage(),
                               key=StorageKey(bot_id=1, chat_id=uid, user_id=uid))

            # Qayta /start - bitta xabar, asosiy menyu bilan
            msg = FakeMsg(uid)
            await u.cmd_start(msg, state)
            user = await db.get_user(uid)
            assert user["fio"] == "Aliyev Sardor Baxtiyorovich", "F.I.Sh. o‘chib ketdi"
            assert user["phone"] == "+998901234567", "telefon o‘chib ketdi"
            assert user["agreed_at"], "rozilik o‘chib ketdi"

            assert len(msg.markups) == 1, f"ortiqcha xabar yuborildi ({len(msg.markups)} ta)"
            markup = msg.markups[-1]
            assert hasattr(markup, "keyboard"), "qaytgan foydalanuvchi asosiy menyuni olishi kerak"
            btns = [b.text for r in markup.keyboard for b in r]
            assert kb.BTN_SEND in btns and kb.BTN_MY in btns, f"asosiy menyu to‘liq emas: {btns}"

            # Yangi foydalanuvchi esa pastki menyusiz, inline tugmalar bilan
            new_msg = FakeMsg(1000)
            await u.cmd_start(new_msg, state)
            assert len(new_msg.markups) == 1, "yangi foydalanuvchiga ham bitta xabar"
            assert hasattr(new_msg.markups[-1], "inline_keyboard"), \
                "yangi foydalanuvchida pastki menyu ko‘rinmasligi kerak"
            new_btns = [b.text for r in new_msg.markups[-1].inline_keyboard for b in r]
            assert "✅ Ishtirok etaman" in new_btns, f"inline menyu noto‘g‘ri: {new_btns}"

            # «Fotosurat yuborish» bosilganda darrov surat kutilishi kerak
            msg2 = FakeMsg(uid)
            await u.route_join(msg2, state, None, uid, "qaytgan")
            got = await state.get_state()
            assert got == u.Submit.photo.state, \
                f"surat kutilishi kerak edi, holat: {got}"
        finally:
            object.__setattr__(cfg, "db_path", db_backup)
            object.__setattr__(cfg, "test_mode", tm_backup)

    check("Ma’lumotlar saqlanadi, qayta so‘ralmaydi", lambda: asyncio.run(restart_flow()))

    print("\n=== 9. Yuklab olishda uzilish ===")

    async def download_retry():
        import handlers.user as u

        class FakeStatus:
            def __init__(self):
                self.texts: list[str] = []

            async def edit_text(self, text="", **kw):
                self.texts.append(text)
                return self

        class FakeBot:
            def __init__(self, fail_times: int):
                self.fail_times = fail_times
                self.calls = 0
                self.timeouts: list[int] = []

            async def download(self, doc, destination=None, timeout=None, **kw):
                self.calls += 1
                self.timeouts.append(timeout)
                Path(destination).write_bytes(b"yarim")  # yarim yuklangan fayl
                if self.calls <= self.fail_times:
                    raise asyncio.TimeoutError()
                Path(destination).write_bytes(b"toliq")

        tmp = Path(tempfile.mkdtemp()) / "x.jpg"
        sleep_real = asyncio.sleep

        async def no_sleep(*a, **kw):
            return None

        asyncio.sleep = no_sleep
        try:
            # 2 marta uzilib, 3-urinishda muvaffaqiyat
            bot = FakeBot(fail_times=2)
            st = FakeStatus()
            assert await u.download_with_retry(bot, object(), tmp, st) is True, \
                "3-urinishda muvaffaqiyat kutilgan edi"
            assert bot.calls == 3, f"{bot.calls} marta urinildi, 3 kutilgan"
            assert bot.timeouts[0] == cfg.download_timeout, \
                f"timeout uzatilmadi: {bot.timeouts[0]}"
            assert tmp.read_bytes() == b"toliq", "fayl to‘liq yozilmadi"

            # Hamma urinish uzilsa - False va yarim fayl qolmasligi kerak
            bot = FakeBot(fail_times=99)
            st = FakeStatus()
            assert await u.download_with_retry(bot, object(), tmp, st) is False, \
                "uzluksiz xatoda False qaytishi kerak"
            assert bot.calls == cfg.download_retries, \
                f"{bot.calls} marta urinildi, {cfg.download_retries} kutilgan"
            assert not tmp.exists(), "yarim yuklangan fayl o‘chirilmadi"
            assert "internet aloqasi" in st.texts[-1], "foydalanuvchiga tushunarli xabar yo‘q"
        finally:
            asyncio.sleep = sleep_real

    check("Qayta urinish + yarim faylni tozalash", lambda: asyncio.run(download_retry()))

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
