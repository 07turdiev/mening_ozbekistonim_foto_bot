"""Klaviaturalar."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import cfg

BTN_SEND = "📸 Fotosurat yuborish"
BTN_MY = "🖼 Mening ishlarim"
BTN_RULES = "📋 Tanlov shartlari"
BTN_PROFILE = "👤 Ma’lumotlarim"
BTN_CONTACT = "☎️ Bog‘lanish"
BTN_CANCEL = "❌ Bekor qilish"
BTN_ADMIN = "🛠 Admin panel"

REMOVE = ReplyKeyboardRemove()


def main_menu(is_admin: bool = False, can_submit: bool = True) -> ReplyKeyboardMarkup:
    """Qabul yopiq bo'lsa «Fotosurat yuborish» tugmasi ko'rsatilmaydi."""
    kb = ReplyKeyboardBuilder()
    if can_submit:
        kb.row(KeyboardButton(text=BTN_SEND))
    kb.row(KeyboardButton(text=BTN_MY), KeyboardButton(text=BTN_RULES))
    kb.row(KeyboardButton(text=BTN_PROFILE), KeyboardButton(text=BTN_CONTACT))
    if is_admin:
        kb.row(KeyboardButton(text=BTN_ADMIN))
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]], resize_keyboard=True
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamimni yuborish", request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def closed_kb() -> InlineKeyboardMarkup:
    """Qabul yopiq - faqat ma'lumot tugmasi qoladi."""
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📋 Tanlov shartlari", callback_data="rules"))
    return kb.as_markup()


def start_kb() -> InlineKeyboardMarkup:
    """Yangi foydalanuvchi uchun - ro'yxatdan o'tganlar asosiy menyuni oladi."""
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Ishtirok etaman", callback_data="join"))
    kb.row(InlineKeyboardButton(text="📋 Tanlov shartlari", callback_data="rules"))
    return kb.as_markup()


def agreement_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Roziman, davom etaman", callback_data="agree"))
    kb.row(InlineKeyboardButton(text="📋 Shartlarni o‘qish", callback_data="rules"))
    return kb.as_markup()


def subscribe_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if cfg.channel_url:
        kb.row(InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=cfg.channel_url))
    kb.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
    return kb.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="submit_ok"))
    kb.row(InlineKeyboardButton(text="✏️ Qaytadan to‘ldirish", callback_data="submit_redo"))
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="submit_cancel"))
    return kb.as_markup()


def after_submit_kb(can_more: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if can_more:
        kb.row(InlineKeyboardButton(text="📸 Yana fotosurat yuborish", callback_data="join"))
    kb.row(InlineKeyboardButton(text="🖼 Mening ishlarim", callback_data="my_works"))
    return kb.as_markup()


# ------------------------------------------------------------------------ admin

def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📊 Statistika", callback_data="a:stats"))
    kb.row(
        InlineKeyboardButton(text="🕓 Ko‘rib chiqish", callback_data="a:mod:0"),
        InlineKeyboardButton(text="🔍 Qidiruv", callback_data="a:search"),
    )
    kb.row(
        InlineKeyboardButton(text="📥 Excel", callback_data="a:excel:all"),
        InlineKeyboardButton(text="🗜 ZIP (suratlar)", callback_data="a:zip"),
    )
    kb.row(InlineKeyboardButton(text="📢 Ommaviy xabar", callback_data="a:broadcast"))
    kb.row(InlineKeyboardButton(text="🔁 Qabulni to‘xtatish/ochish", callback_data="a:toggle"))
    return kb.as_markup()


def moderation_kb(photo_id: int, index: int, total: int = 1) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"a:ok:{photo_id}:{index}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"a:no:{photo_id}:{index}"),
    )
    # Navigatsiya faqat navbatda bir nechta ariza bo‘lganda kerak
    if total > 1:
        nav = []
        if index > 0:
            nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"a:mod:{index - 1}"))
        if index < total - 1:
            nav.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"a:mod:{index + 1}"))
        if nav:
            kb.row(*nav)
    kb.row(InlineKeyboardButton(text=BTN_ADMIN, callback_data="a:menu"))
    return kb.as_markup()


def excel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Hammasi", callback_data="a:excel:all"),
        InlineKeyboardButton(text="Qabul qilingan", callback_data="a:excel:approved"),
        InlineKeyboardButton(text="Kutilmoqda", callback_data="a:excel:pending"),
    )
    kb.row(InlineKeyboardButton(text=BTN_ADMIN, callback_data="a:menu"))
    return kb.as_markup()


def back_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=BTN_ADMIN, callback_data="a:menu"))
    return kb.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📢 Yuborish", callback_data="a:bc_go"))
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="a:menu"))
    return kb.as_markup()
