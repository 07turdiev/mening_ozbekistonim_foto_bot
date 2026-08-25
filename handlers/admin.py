"""Administrator paneli."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

import database as db
import keyboards as kb
import texts as t
from config import cfg
from utils.export import build_excel, build_zip

router = Router(name="admin")
log = logging.getLogger(__name__)

# Ushbu routerdagi barcha handlerlar faqat adminlar uchun
router.message.filter(F.from_user.id.in_(cfg.admin_ids))
router.callback_query.filter(F.from_user.id.in_(cfg.admin_ids))

TG_FILE_LIMIT = 48 * 1024 * 1024  # bot orqali yuborish chegarasi (50 MB dan biroz kam)


class AdminState(StatesGroup):
    reject_reason = State()
    broadcast = State()
    search = State()


def _panel_text() -> str:
    warn = (
        "⚠️ <b>SINOV REJIMI YOQILGAN</b> (TEST_MODE=1) — tanlov muddati tekshirilmayapti!\n\n"
        if cfg.test_mode else ""
    )
    return (
        warn + "\U0001F6E0 <b>Administrator paneli</b>\n\n"
        f"Tanlov muddati: <b>{cfg.start_date:%d.%m.%Y} — {cfg.end_date:%d.%m.%Y}</b>\n"
        f"Bugun: {cfg.today():%d.%m.%Y}\n"
        f"Moderatsiya: <b>{'yoqilgan' if cfg.moderation else 'o‘chirilgan'}</b>\n\n"
        "Kerakli bo‘limni tanlang:"
    )


@router.message(Command("admin"))
@router.message(F.text == kb.BTN_ADMIN)
async def admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_panel_text(), reply_markup=kb.admin_menu())


@router.callback_query(F.data == "a:menu")
async def cb_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    await call.message.answer(_panel_text(), reply_markup=kb.admin_menu())


# ------------------------------------------------------------------- statistika

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await message.answer(await _stats_text(), reply_markup=kb.back_admin_kb())


@router.callback_query(F.data == "a:stats")
async def cb_stats(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer(await _stats_text(), reply_markup=kb.back_admin_kb())


async def _stats_text() -> str:
    s = await db.stats()
    paused = await db.acceptance_paused()
    if paused:
        state_line = "\U0001F512 vaqtincha to‘xtatilgan"
    elif cfg.not_started():
        state_line = "⏳ hali boshlanmagan"
    elif cfg.is_open():
        state_line = "\U0001F513 ochiq"
    else:
        state_line = "\U0001F512 yakunlangan"
    return (
        "\U0001F4CA <b>Statistika</b>\n\n"
        f"Qabul holati: <b>{state_line}</b>\n\n"
        f"\U0001F465 Botga kirgan foydalanuvchilar: <b>{s.get('users_total', 0)}</b>\n"
        f"\U0001F4DD Ro‘yxatdan o‘tganlar: <b>{s.get('users_reg', 0)}</b>\n"
        f"\U0001F3AF Ishtirokchilar (ish yuborganlar): <b>{s.get('participants', 0)}</b>\n\n"
        f"\U0001F5BC Jami arizalar: <b>{s.get('photos_total', 0)}</b>\n"
        f"   \U0001F553 ko‘rib chiqilmoqda: <b>{s.get('pending', 0)}</b>\n"
        f"   ✅ qabul qilingan: <b>{s.get('approved', 0)}</b>\n"
        f"   ❌ rad etilgan: <b>{s.get('rejected', 0)}</b>\n\n"
        f"\U0001F4C5 Bugun kelgan arizalar: <b>{s.get('today', 0)}</b>"
    )


# ------------------------------------------------------------------ moderatsiya

async def show_queue(message: Message, index: int = 0, note: str = "") -> None:
    """Navbatdagi arizani ko'rsatadi. Navbat bo'sh bo'lsa - admin panelga qaytaradi."""
    total = await db.count_by_status("pending")
    if total == 0:
        await message.answer(
            (note + "\n\n" if note else "")
            + "✅ <b>Ko‘rib chiqilmagan arizalar qolmadi.</b>\n\n" + _panel_text(),
            reply_markup=kb.admin_menu(),
        )
        return

    index = min(max(index, 0), total - 1)
    rows = await db.photos_by_status("pending", 1, index)
    if not rows:
        await message.answer(_panel_text(), reply_markup=kb.admin_menu())
        return

    r = rows[0]
    caption = (
        (note + "\n\n" if note else "")
        + f"\U0001F553 <b>Ariza #{r['id']}</b>  ({index + 1}/{total})\n\n"
        f"\U0001F464 {r['fio']}\n☎️ {r['phone']}\n"
        f"\U0001F194 <code>{r['user_id']}</code>"
        + (f" | @{r['username']}" if r["username"] else "") + "\n\n"
        f"\U0001F3F7 <b>{r['title']}</b>\n"
        f"\U0001F4CD {r['place']}\n\U0001F5D3 {r['shot_date']}\n"
        f"\U0001F4D0 {r['width']}×{r['height']} px | "
        f"{(r['file_size'] or 0) / 1048576:.1f} MB | "
        f"EXIF: {'bor' if r['has_exif'] else 'yo‘q'}\n"
        + (f"\U0001F4F7 {r['exif_info']}\n" if r["exif_info"] else "")
        + f"\n✍️ {r['description']}"
    )
    await message.answer_document(
        r["file_id"], caption=t.clip(caption),
        reply_markup=kb.moderation_kb(r["id"], index, total),
    )


@router.callback_query(F.data.startswith("a:mod:"))
async def cb_moderate(call: CallbackQuery) -> None:
    await call.answer()
    await show_queue(call.message, int(call.data.split(":")[2]))


@router.callback_query(F.data.startswith("a:ok:"))
async def cb_approve(call: CallbackQuery, bot: Bot) -> None:
    _, _, photo_id, index = call.data.split(":")
    row = await db.get_photo(int(photo_id))
    if not row:
        await call.answer("Ariza topilmadi", show_alert=True)
        return
    if row["status"] != "pending":
        await call.answer("Bu ariza allaqachon ko‘rib chiqilgan.", show_alert=True)
        return

    await db.set_status(int(photo_id), "approved", call.from_user.id)
    await call.answer("Qabul qilindi ✅")
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    # Ariza navbatdan chiqdi - o'sha indeks endi keyingi arizani ko'rsatadi
    await show_queue(call.message, int(index), f"✅ Ariza #{photo_id} qabul qilindi.")
    try:
        await bot.send_message(
            row["user_id"],
            f"✅ <b>Xushxabar!</b>\n\n«{row['title']}» nomli fotosuratingiz tanlovga "
            "muvaffaqiyatli qabul qilindi va tanlov hay’ati ko‘rigiga taqdim etiladi.\n\n"
            "Omad tilaymiz! \U0001F1FA\U0001F1FF",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        log.warning("Foydalanuvchiga xabar yuborilmadi: %s", exc)


@router.callback_query(F.data.startswith("a:no:"))
async def cb_reject(call: CallbackQuery, state: FSMContext) -> None:
    _, _, photo_id, index = call.data.split(":")
    row = await db.get_photo(int(photo_id))
    if not row:
        await call.answer("Ariza topilmadi", show_alert=True)
        return
    if row["status"] != "pending":
        await call.answer("Bu ariza allaqachon ko‘rib chiqilgan.", show_alert=True)
        return

    await call.answer()
    await state.set_state(AdminState.reject_reason)
    await state.update_data(photo_id=int(photo_id), index=int(index))
    await call.message.answer(
        f"❌ <b>Ariza #{photo_id} rad etilmoqda.</b>\n\n"
        "Rad etish sababini yozing — u ishtirokchiga yuboriladi.\n"
        "<i>Masalan: Fotosurat talab qilingan o‘lchamga mos emas.</i>\n\n"
        "Bekor qilish uchun /cancel"
    )


@router.message(AdminState.reject_reason, Command("cancel"))
async def cancel_reject(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.back_admin_kb())


@router.message(AdminState.reject_reason, F.text)
async def save_reject(message: Message, state: FSMContext, bot: Bot) -> None:
    reason = " ".join(message.text.split())
    if len(reason) < 5:
        await message.answer("⚠️ Sabab juda qisqa. Aniqroq yozing.")
        return
    data = await state.get_data()
    photo_id, index = data["photo_id"], data["index"]
    row = await db.get_photo(photo_id)
    await db.set_status(photo_id, "rejected", message.from_user.id, reason)
    await state.clear()
    await show_queue(message, index, f"❌ Ariza #{photo_id} rad etildi.\nSabab: {reason}")
    if row:
        try:
            await bot.send_message(
                row["user_id"],
                f"❌ Afsuski, «{row['title']}» nomli fotosuratingiz tanlov talablariga mos "
                f"kelmagani sababli qabul qilinmadi.\n\n"
                f"<b>Sabab:</b> {reason}\n\n"
                "Siz talablarga mos boshqa ijodiy ishingizni yuborishingiz mumkin.",
            )
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            log.warning("Foydalanuvchiga xabar yuborilmadi: %s", exc)


# ----------------------------------------------------------------------- eksport

@router.message(Command("excel"))
async def cmd_excel(message: Message) -> None:
    await message.answer("Qaysi arizalarni eksport qilamiz?", reply_markup=kb.excel_kb())


@router.callback_query(F.data.startswith("a:excel:"))
async def cb_excel(call: CallbackQuery) -> None:
    await call.answer("Fayl tayyorlanmoqda...")
    kind = call.data.split(":")[2]
    if kind == "all":
        rows = await db.all_photos_full()
        label = None
    else:
        rows = await db.photos_by_status(kind, 100000, 0)
        label = kind
    if not rows:
        await call.message.answer("Eksport uchun ma’lumot yo‘q.", reply_markup=kb.back_admin_kb())
        return
    path = build_excel(rows, label)
    await call.message.answer_document(
        FSInputFile(path),
        caption=f"\U0001F4E5 Jami <b>{len(rows)}</b> ta yozuv.\n{cfg.now():%d.%m.%Y %H:%M}",
        reply_markup=kb.excel_kb(),
    )


@router.callback_query(F.data == "a:zip")
async def cb_zip(call: CallbackQuery) -> None:
    await call.answer("Arxiv tayyorlanmoqda, biroz kuting...")
    rows = await db.photos_by_status("approved", 100000, 0)
    if not rows:
        rows = await db.all_photos_full()
    if not rows:
        await call.message.answer("Arxivlash uchun surat yo‘q.", reply_markup=kb.back_admin_kb())
        return

    path, added, skipped = build_zip(rows)
    size = Path(path).stat().st_size
    if size > TG_FILE_LIMIT:
        await call.message.answer(
            f"⚠️ Arxiv hajmi juda katta ({size / 1048576:.0f} MB) — Telegram orqali yuborib bo‘lmaydi.\n"
            f"Fayl serverda saqlandi:\n<code>{path}</code>",
            reply_markup=kb.back_admin_kb(),
        )
        return
    note = f"\n⚠️ {skipped} ta fayl arxivga sig‘madi yoki topilmadi." if skipped else ""
    await call.message.answer_document(
        FSInputFile(path),
        caption=f"\U0001F5DC Arxivda <b>{added}</b> ta fotosurat.{note}",
        reply_markup=kb.back_admin_kb(),
    )


# ------------------------------------------------------------------------ qidiruv

@router.callback_query(F.data == "a:search")
async def cb_search(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(AdminState.search)
    await call.message.answer(
        "\U0001F50D Ishtirokchining <b>F.I.Sh.</b>, <b>telefon raqami</b> yoki "
        "<b>Telegram ID</b> sini yozing.\n\nBekor qilish uchun /cancel"
    )


@router.message(AdminState.search, Command("cancel"))
async def cancel_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.back_admin_kb())


@router.message(AdminState.search, F.text)
async def do_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    users = await db.search_users(message.text.strip())
    if not users:
        await message.answer("Hech narsa topilmadi.", reply_markup=kb.back_admin_kb())
        return
    for u in users:
        photos = await db.user_photos(u["user_id"])
        lines = [
            f"\U0001F464 <b>{u['fio'] or '—'}</b>\n"
            f"☎️ {u['phone'] or '—'}\n"
            f"\U0001F194 <code>{u['user_id']}</code>"
            + (f" | @{u['username']}" if u["username"] else "")
            + f"\n\U0001F5BC Ishlar: {len(photos)}"
        ]
        for p in photos:
            lines.append(f"   • #{p['id']} «{p['title']}» — {p['status']}")
        await message.answer("\n".join(lines))
    await message.answer("Qidiruv yakunlandi.", reply_markup=kb.back_admin_kb())


# ------------------------------------------------------------------ ommaviy xabar

@router.callback_query(F.data == "a:broadcast")
async def cb_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(AdminState.broadcast)
    await call.message.answer(
        "\U0001F4E2 Barcha foydalanuvchilarga yuboriladigan xabar matnini yuboring.\n"
        "HTML formatlash qo‘llab-quvvatlanadi.\n\nBekor qilish uchun /cancel"
    )


@router.message(AdminState.broadcast, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.back_admin_kb())


@router.message(AdminState.broadcast, F.text)
async def preview_broadcast(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.html_text)
    total = len(await db.all_user_ids())
    await message.answer(
        f"Xabar <b>{total}</b> ta foydalanuvchiga yuboriladi. Ko‘rinishi:"
    )
    await message.answer(message.html_text, reply_markup=kb.broadcast_confirm_kb())


@router.callback_query(F.data == "a:bc_go")
async def cb_broadcast_go(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    text = data.get("text")
    await state.clear()
    if not text:
        await call.answer("Xabar topilmadi", show_alert=True)
        return
    await call.answer("Yuborish boshlandi")
    user_ids = await db.all_user_ids()
    sent = failed = 0
    progress = await call.message.answer(f"\U0001F4E4 Yuborilmoqda... 0/{len(user_ids)}")

    for i, uid in enumerate(user_ids, start=1):
        try:
            await bot.send_message(uid, text)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.send_message(uid, text)
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            failed += 1
            await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (uid,))
        except Exception as exc:
            failed += 1
            log.warning("Broadcast xatosi (%s): %s", uid, exc)
        await asyncio.sleep(0.05)
        if i % 25 == 0:
            try:
                await progress.edit_text(f"\U0001F4E4 Yuborilmoqda... {i}/{len(user_ids)}")
            except TelegramBadRequest:
                pass

    await progress.edit_text(
        f"✅ <b>Yakunlandi.</b>\nYuborildi: <b>{sent}</b>\nYuborilmadi: <b>{failed}</b>"
    )
    await call.message.answer(_panel_text(), reply_markup=kb.admin_menu())


# --------------------------------------------------------------- qabulni boshqarish

@router.callback_query(F.data == "a:toggle")
async def cb_toggle(call: CallbackQuery) -> None:
    paused = await db.acceptance_paused()
    await db.set_setting("paused", "0" if paused else "1")
    state_text = "ochildi \U0001F513" if paused else "vaqtincha to‘xtatildi \U0001F512"
    await call.answer(f"Qabul {state_text}", show_alert=True)
    await call.message.answer(
        f"Fotosurat qabul qilish <b>{state_text}</b>.", reply_markup=kb.admin_menu()
    )
