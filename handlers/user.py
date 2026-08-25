"""Ishtirokchi uchun handlerlar."""
from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import texts as t
from config import cfg
from utils.validators import (
    ALLOWED_EXT, ALLOWED_MIME, check_photo_file, safe_name, validate_description,
    validate_fio, validate_phone, validate_place, validate_shot_date, validate_title,
)

router = Router(name="user")
log = logging.getLogger(__name__)

STATUS_UZ = {
    "pending": "\U0001F553 Ko‘rib chiqilmoqda",
    "approved": "✅ Qabul qilindi",
    "rejected": "❌ Rad etildi",
}


class Reg(StatesGroup):
    fio = State()
    phone = State()


class Submit(StatesGroup):
    photo = State()
    title = State()
    place = State()
    shot_date = State()
    description = State()
    confirm = State()


# ----------------------------------------------------------------- yordamchilar

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    if not cfg.channel_id:
        return True
    try:
        member = await bot.get_chat_member(cfg.channel_id, user_id)
        return member.status in {"creator", "administrator", "member"}
    except Exception as exc:  # kanal topilmasa - tekshiruvni o'tkazib yuboramiz
        log.warning("Obuna tekshiruvi muvaffaqiyatsiz: %s", exc)
        return True


async def acceptance_blocked() -> str | None:
    """Qabul yopiq bo'lsa sabab matnini qaytaradi, aks holda None."""
    if await db.acceptance_paused():
        return t.CLOSED_MANUAL
    if cfg.not_started():
        return t.CLOSED_BEFORE
    if not cfg.is_open():
        return t.CLOSED_AFTER
    return None


def photo_card(data: dict, fio: str, phone: str) -> str:
    return (
        "\U0001F50E <b>Ma’lumotlarni tekshiring</b>\n\n"
        f"\U0001F464 <b>Muallif:</b> {fio}\n"
        f"☎️ <b>Telefon:</b> {phone}\n"
        f"\U0001F3F7 <b>Nomi:</b> {data['title']}\n"
        f"\U0001F4CD <b>Joy:</b> {data['place']}\n"
        f"\U0001F5D3 <b>Sana:</b> {data['shot_date']}\n"
        f"\U0001F4D0 <b>O‘lcham:</b> {data['width']} × {data['height']} px "
        f"({data['file_size'] / 1048576:.1f} MB)\n\n"
        f"✍️ <b>Izoh:</b>\n{data['description']}\n\n"
        "Hammasi to‘g‘rimi?"
    )


async def notify_admins(bot: Bot, photo_id: int) -> None:
    row = await db.get_photo(photo_id)
    if not row:
        return
    caption = (
        f"\U0001F195 <b>Yangi ariza #{row['id']}</b>\n\n"
        f"\U0001F464 {row['fio']}\n☎️ {row['phone']}\n"
        f"\U0001F3F7 {row['title']}\n\U0001F4CD {row['place']}\n\U0001F5D3 {row['shot_date']}\n"
        f"\U0001F4D0 {row['width']}×{row['height']} px | "
        f"{(row['file_size'] or 0) / 1048576:.1f} MB | "
        f"EXIF: {'bor' if row['has_exif'] else 'yo‘q'}\n\n"
        f"✍️ {row['description']}"
    )
    for admin_id in cfg.admin_ids:
        try:
            await bot.send_document(
                admin_id, row["file_id"], caption=t.clip(caption),
                reply_markup=kb.moderation_kb(row["id"], 0),
            )
        except Exception as exc:
            log.warning("Adminni (%s) xabardor qilib bo‘lmadi: %s", admin_id, exc)

    if cfg.archive_chat_id:
        try:
            await bot.send_document(cfg.archive_chat_id, row["file_id"], caption=t.clip(caption))
        except Exception as exc:
            log.warning("Arxiv kanaliga yuborib bo‘lmadi: %s", exc)


async def start_submission(message: Message, state: FSMContext) -> None:
    """Foydalanuvchini fotosurat yuborish bosqichiga o'tkazadi."""
    user_id = message.chat.id
    used = await db.count_active_photos(user_id)
    if used >= cfg.max_photos:
        await state.clear()
        await message.answer(t.LIMIT_REACHED, reply_markup=kb.main_menu(cfg.is_admin(user_id)))
        return
    await state.set_state(Submit.photo)
    await message.answer(
        f"{t.HOW_TO_SEND}\n\n<i>Yuborilgan ishlar: {used}/{cfg.max_photos}</i>",
        reply_markup=kb.cancel_kb(),
    )


# --------------------------------------------------------------- /start va menyu

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(t.WELCOME, reply_markup=kb.main_menu(cfg.is_admin(message.from_user.id)))
    await message.answer("Quyidagi amallardan birini tanlang:", reply_markup=kb.start_kb())


@router.message(Command("help"))
@router.message(F.text == kb.BTN_RULES)
async def show_rules(message: Message) -> None:
    await message.answer(t.RULES, reply_markup=kb.main_menu(cfg.is_admin(message.from_user.id)))


@router.callback_query(F.data == "rules")
async def cb_rules(call: CallbackQuery) -> None:
    await call.message.answer(t.RULES)
    await call.answer()


@router.message(Command("cancel"))
@router.message(F.text == kb.BTN_CANCEL)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    tmp = data.get("tmp_path")
    if tmp:
        Path(tmp).unlink(missing_ok=True)
    await state.clear()
    await message.answer(t.CANCELLED, reply_markup=kb.main_menu(cfg.is_admin(message.from_user.id)))


@router.message(F.text == kb.BTN_CONTACT)
async def show_contact(message: Message) -> None:
    await message.answer(
        f"☎️ <b>Murojaat uchun</b>\n\n{cfg.contact_info}\n\n"
        "Savollaringizni ushbu manzilga yo‘llashingiz mumkin."
    )


@router.message(F.text == kb.BTN_PROFILE)
async def show_profile(message: Message) -> None:
    user = await db.get_user(message.from_user.id)
    if not user or not user["fio"]:
        await message.answer(
            "Siz hali ro‘yxatdan o‘tmagansiz. «Fotosurat yuborish» tugmasini bosing."
        )
        return
    used = await db.count_active_photos(message.from_user.id)
    await message.answer(
        f"\U0001F464 <b>Ma’lumotlaringiz</b>\n\n"
        f"F.I.Sh.: <b>{user['fio']}</b>\n"
        f"Telefon: <b>{user['phone']}</b>\n"
        f"Yuborilgan ishlar: <b>{used}/{cfg.max_photos}</b>\n\n"
        "Ma’lumotni o‘zgartirish uchun /profil buyrug‘ini yuboring."
    )


@router.message(Command("profil"))
async def edit_profile(message: Message, state: FSMContext) -> None:
    await state.set_state(Reg.fio)
    await state.update_data(after="menu")
    await message.answer(t.ASK_FIO, reply_markup=kb.cancel_kb())


@router.message(F.text == kb.BTN_MY)
async def my_works_msg(message: Message) -> None:
    await send_my_works(message, message.from_user.id)


@router.callback_query(F.data == "my_works")
async def my_works_cb(call: CallbackQuery) -> None:
    await send_my_works(call.message, call.from_user.id)
    await call.answer()


async def send_my_works(message: Message, user_id: int) -> None:
    rows = await db.user_photos(user_id)
    if not rows:
        await message.answer(
            "Siz hali fotosurat yubormagansiz.\n\n"
            "«\U0001F4F8 Fotosurat yuborish» tugmasini bosing."
        )
        return
    used = await db.count_active_photos(user_id)
    lines = [f"\U0001F5BC <b>Sizning ishlaringiz</b> ({used}/{cfg.max_photos})\n"]
    for i, r in enumerate(rows, start=1):
        block = (
            f"<b>{i}. {r['title']}</b>\n"
            f"   \U0001F4CD {r['place']} | \U0001F5D3 {r['shot_date']}\n"
            f"   Holati: {STATUS_UZ.get(r['status'], r['status'])}"
        )
        if r["status"] == "rejected" and r["reject_reason"]:
            block += f"\n   \U0001F4AC Sabab: {r['reject_reason']}"
        lines.append(block)
    await message.answer("\n".join(lines))


# --------------------------------------------------------------- ishtirok etish

@router.message(F.text == kb.BTN_SEND)
async def btn_send(message: Message, state: FSMContext, bot: Bot) -> None:
    await route_join(message, state, bot, message.from_user.id, message.from_user.username)


@router.callback_query(F.data == "join")
async def cb_join(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await call.answer()
    await route_join(call.message, state, bot, call.from_user.id, call.from_user.username)


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not await is_subscribed(bot, call.from_user.id):
        await call.answer("Siz hali obuna bo‘lmagansiz.", show_alert=True)
        return
    await call.answer("Rahmat!")
    await route_join(call.message, state, bot, call.from_user.id, call.from_user.username)


async def route_join(message: Message, state: FSMContext, bot: Bot,
                     user_id: int, username: str | None) -> None:
    await db.upsert_user(user_id, username)

    blocked = await acceptance_blocked()
    if blocked:
        await message.answer(blocked, reply_markup=kb.main_menu(cfg.is_admin(user_id)))
        return

    if not await is_subscribed(bot, user_id):
        await message.answer(
            "\U0001F4E2 Tanlovda ishtirok etish uchun avval rasmiy kanalimizga obuna bo‘ling:",
            reply_markup=kb.subscribe_kb(),
        )
        return

    user = await db.get_user(user_id)
    if not user or not user["agreed_at"]:
        await message.answer(t.AGREEMENT, reply_markup=kb.agreement_kb())
        return

    if not user["fio"] or not user["phone"]:
        await state.set_state(Reg.fio)
        await state.update_data(after="photo")
        await message.answer(t.ASK_FIO, reply_markup=kb.cancel_kb())
        return

    await start_submission(message, state)


@router.callback_query(F.data == "agree")
async def cb_agree(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await db.set_agreement(call.from_user.id)
    await call.answer("Rozilik qabul qilindi")
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await route_join(call.message, state, bot, call.from_user.id, call.from_user.username)


# ----------------------------------------------------------- ro'yxatdan o'tish

@router.message(Reg.fio, F.text)
async def reg_fio(message: Message, state: FSMContext) -> None:
    ok, value = validate_fio(message.text)
    if not ok:
        await message.answer(f"⚠️ {value}")
        return
    await state.update_data(fio=value)
    await state.set_state(Reg.phone)
    await message.answer(t.ASK_PHONE, reply_markup=kb.phone_kb())


@router.message(Reg.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext) -> None:
    if message.contact.user_id != message.from_user.id:
        await message.answer("⚠️ Iltimos, o‘zingizning raqamingizni yuboring.")
        return
    await finish_registration(message, state, message.contact.phone_number)


@router.message(Reg.phone, F.text)
async def reg_phone_text(message: Message, state: FSMContext) -> None:
    await finish_registration(message, state, message.text)


async def finish_registration(message: Message, state: FSMContext, raw_phone: str) -> None:
    ok, phone = validate_phone(raw_phone)
    if not ok:
        await message.answer(f"⚠️ {phone}")
        return
    data = await state.get_data()
    after = data.get("after")
    await db.save_profile(message.from_user.id, data["fio"], phone)
    await state.clear()
    await message.answer(
        f"✅ Ma’lumotlaringiz saqlandi.\n\n\U0001F464 {data['fio']}\n☎️ {phone}",
        reply_markup=kb.main_menu(cfg.is_admin(message.from_user.id)),
    )
    if after == "menu":
        return
    blocked = await acceptance_blocked()
    if blocked:
        await message.answer(blocked)
        return
    await start_submission(message, state)


# -------------------------------------------------------------------- fotosurat

@router.message(Submit.photo, F.photo)
async def reject_compressed(message: Message) -> None:
    await message.answer(
        "⚠️ <b>Fotosurat siqilgan holda yuborildi.</b>\n\n"
        "Telegram oddiy rasmlarni siqib, sifatini keskin pasaytiradi. Tanlov talablariga ko‘ra "
        "surat asl sifatida bo‘lishi shart.\n\n"
        "Iltimos, rasmni <b>FAYL</b> ko‘rinishida qayta yuboring:\n"
        "\U0001F4CE → <i>Fayl / File</i> → galereyadan tanlang."
    )


@router.message(Submit.photo, F.document)
async def receive_document(message: Message, state: FSMContext, bot: Bot) -> None:
    doc = message.document
    ext = Path(doc.file_name or "").suffix.lower()

    if ext not in ALLOWED_EXT and (doc.mime_type or "") not in ALLOWED_MIME:
        await message.answer(
            f"⚠️ Fayl formati mos emas "
            f"(<code>{ext or doc.mime_type or 'noma’lum'}</code>).\n\n"
            "Tanlovga faqat <b>JPG / JPEG</b> formatidagi fotosuratlar qabul qilinadi."
        )
        return

    if (doc.file_size or 0) > cfg.max_file_bytes:
        await message.answer(
            f"⚠️ Fayl hajmi <b>{doc.file_size / 1048576:.1f} MB</b> — "
            f"ruxsat etilgan chegara <b>{cfg.max_file_mb} MB</b>.\n\n"
            "Suratni biroz siqib (o‘lchamini kamaytirmasdan) qayta yuboring."
        )
        return

    tmp_dir = cfg.uploads_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{message.from_user.id}_{doc.file_unique_id}.jpg"

    status = await message.answer("⏳ Fotosurat yuklanmoqda va tekshirilmoqda...")
    try:
        await bot.download(doc, destination=tmp_path)
    except TelegramBadRequest as exc:
        log.warning("Yuklab olishda xato: %s", exc)
        await status.edit_text(
            "⚠️ Faylni yuklab bo‘lmadi — hajmi juda katta bo‘lishi mumkin.\n"
            f"Iltimos, {cfg.max_file_mb} MB dan kichik fayl yuboring."
        )
        return
    except Exception as exc:
        log.exception("Yuklab olishda kutilmagan xato: %s", exc)
        await status.edit_text(
            "⚠️ Texnik xatolik yuz berdi. Iltimos, qaytadan urinib ko‘ring."
        )
        return

    file_size = doc.file_size or tmp_path.stat().st_size
    check = check_photo_file(tmp_path, file_size)
    if not check.ok:
        tmp_path.unlink(missing_ok=True)
        await status.edit_text(
            f"⚠️ {check.error}\n\nBoshqa fotosurat yuboring yoki bekor qiling."
        )
        return

    dup = await db.find_duplicate(check.file_hash)
    if dup:
        tmp_path.unlink(missing_ok=True)
        owner = "siz" if dup["user_id"] == message.from_user.id else "boshqa ishtirokchi"
        await status.edit_text(
            f"⚠️ Ushbu fotosurat allaqachon tanlovga taqdim etilgan ({owner} tomonidan).\n\n"
            "Iltimos, boshqa ijodiy ishingizni yuboring."
        )
        return

    await state.update_data(
        file_id=doc.file_id, file_unique=doc.file_unique_id,
        file_name=doc.file_name or tmp_path.name, tmp_path=str(tmp_path),
        width=check.width, height=check.height, file_size=file_size,
        has_exif=int(check.has_exif), exif_info=check.exif_info,
        file_hash=check.file_hash,
    )
    await status.edit_text(
        f"✅ Fotosurat qabul qilindi.\n"
        f"\U0001F4D0 O‘lcham: <b>{check.width} × {check.height}</b> px | "
        f"{file_size / 1048576:.1f} MB"
    )
    await state.set_state(Submit.title)
    await message.answer(t.ASK_TITLE, reply_markup=kb.cancel_kb())


@router.message(Submit.photo)
async def submit_photo_other(message: Message) -> None:
    await message.answer(t.HOW_TO_SEND)


@router.message(Submit.title, F.text)
async def submit_title(message: Message, state: FSMContext) -> None:
    ok, value = validate_title(message.text)
    if not ok:
        await message.answer(f"⚠️ {value}")
        return
    await state.update_data(title=value)
    await state.set_state(Submit.place)
    await message.answer(t.ASK_PLACE, reply_markup=kb.cancel_kb())


@router.message(Submit.place, F.text)
async def submit_place(message: Message, state: FSMContext) -> None:
    ok, value = validate_place(message.text)
    if not ok:
        await message.answer(f"⚠️ {value}")
        return
    await state.update_data(place=value)
    await state.set_state(Submit.shot_date)
    await message.answer(t.ASK_DATE, reply_markup=kb.cancel_kb())


@router.message(Submit.shot_date, F.text)
async def submit_date(message: Message, state: FSMContext) -> None:
    ok, value = validate_shot_date(message.text)
    if not ok:
        await message.answer(f"⚠️ {value}")
        return
    await state.update_data(shot_date=value)
    await state.set_state(Submit.description)
    await message.answer(t.ASK_DESC, reply_markup=kb.cancel_kb())


@router.message(Submit.description, F.text)
async def submit_description(message: Message, state: FSMContext) -> None:
    ok, value = validate_description(message.text)
    if not ok:
        await message.answer(f"⚠️ {value}")
        return
    await state.update_data(description=value)
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    await state.set_state(Submit.confirm)
    await message.answer("\U0001F50E Yakuniy tekshiruv:", reply_markup=kb.REMOVE)
    await message.answer_document(
        data["file_id"],
        caption=t.clip(photo_card(data, user["fio"], user["phone"])),
        reply_markup=kb.confirm_kb(),
    )


@router.message(Submit.description)
async def submit_description_other(message: Message) -> None:
    await message.answer("⚠️ Izohni matn ko‘rinishida yuboring.")


@router.callback_query(Submit.confirm, F.data == "submit_redo")
async def cb_redo(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(Submit.title)
    await call.message.answer(t.ASK_TITLE, reply_markup=kb.cancel_kb())


@router.callback_query(Submit.confirm, F.data == "submit_cancel")
async def cb_submit_cancel(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("tmp_path"):
        Path(data["tmp_path"]).unlink(missing_ok=True)
    await state.clear()
    await call.answer("Bekor qilindi")
    await call.message.answer(t.CANCELLED, reply_markup=kb.main_menu(cfg.is_admin(call.from_user.id)))


@router.callback_query(Submit.confirm, F.data == "submit_ok")
async def cb_submit_ok(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await call.answer()
    user_id = call.from_user.id
    data = await state.get_data()
    if not data.get("file_id"):
        await state.clear()
        await call.message.answer(t.CANCELLED, reply_markup=kb.main_menu(cfg.is_admin(user_id)))
        return

    blocked = await acceptance_blocked()
    if blocked:
        await state.clear()
        await call.message.answer(blocked, reply_markup=kb.main_menu(cfg.is_admin(user_id)))
        return

    if await db.count_active_photos(user_id) >= cfg.max_photos:
        await state.clear()
        await call.message.answer(t.LIMIT_REACHED, reply_markup=kb.main_menu(cfg.is_admin(user_id)))
        return

    status = "pending" if cfg.moderation else "approved"
    photo_id = await db.add_photo({
        "user_id": user_id,
        "file_id": data["file_id"],
        "file_unique": data["file_unique"],
        "file_hash": data["file_hash"],
        "file_name": data["file_name"],
        "file_path": "",
        "width": data["width"],
        "height": data["height"],
        "file_size": data["file_size"],
        "has_exif": data["has_exif"],
        "exif_info": data["exif_info"],
        "title": data["title"],
        "place": data["place"],
        "shot_date": data["shot_date"],
        "description": data["description"],
        "status": status,
    })

    user_dir = cfg.uploads_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    final_path = user_dir / f"{photo_id:05d}_{safe_name(data['title'])}.jpg"
    try:
        Path(data["tmp_path"]).replace(final_path)
    except OSError as exc:
        log.error("Faylni ko‘chirishda xato: %s", exc)
        final_path = Path(data["tmp_path"])
    await db.execute("UPDATE photos SET file_path = ? WHERE id = ?", (str(final_path), photo_id))

    await state.clear()
    used = await db.count_active_photos(user_id)
    left = cfg.max_photos - used
    tail = (
        f"Siz yana <b>{left} ta</b> fotosurat yuborishingiz mumkin."
        if left > 0 else "Siz tanlov uchun barcha ishlaringizni yubordingiz."
    )
    await call.message.answer(
        f"\U0001F389 <b>Rahmat! Ishingiz qabul qilindi.</b>\n\n"
        f"Ariza raqami: <b>#{photo_id}</b>\n"
        f"\U0001F3F7 {data['title']}\n"
        f"Holati: {STATUS_UZ[status]}\n\n{tail}\n\nOmad tilaymiz! \U0001F1FA\U0001F1FF",
        reply_markup=kb.main_menu(cfg.is_admin(user_id)),
    )
    await call.message.answer("Keyingi amal:", reply_markup=kb.after_submit_kb(left > 0))
    await notify_admins(bot, photo_id)


# ------------------------------------------------------------------- qolgan holat

@router.message(StateFilter(None))
async def fallback(message: Message) -> None:
    await message.answer(t.UNKNOWN, reply_markup=kb.main_menu(cfg.is_admin(message.from_user.id)))
