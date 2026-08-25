"""Kiritilgan ma'lumotlar va fotosuratni tekshirish."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ExifTags

from config import cfg

# Fotosuratning yuqori o'lchami CHEKLANMAGAN - qancha katta bo'lsa, shuncha yaxshi.
# Pillow standart holatda ~178 megapiksellik rasmni "decompression bomb" deb
# rad etadi; bu yerda faqat sarlavha va EXIF o'qiladi (piksellar dekodlanmaydi),
# shuning uchun chegarani olib tashlaymiz - aks holda haqiqiy yirik kadrlar
# "fayl buzilgan" degan noto'g'ri xabar bilan qaytarilardi.
Image.MAX_IMAGE_PIXELS = None

ALLOWED_EXT = {".jpg", ".jpeg"}
ALLOWED_MIME = {"image/jpeg", "image/jpg"}

_FIO_RE = re.compile(r"^[A-Za-zʼ'‘’\u0400-\u04FF\s\.\-]{5,120}$")
_PHONE_CLEAN = re.compile(r"[^\d+]")


def validate_fio(text: str) -> tuple[bool, str]:
    value = " ".join((text or "").split())
    if len(value) < 5:
        return False, "F.I.Sh. juda qisqa. To‘liq yozing: Familiya Ism Otasining ismi."
    if len(value) > 120:
        return False, "F.I.Sh. juda uzun (120 belgidan oshmasin)."
    if len(value.split()) < 2:
        return False, "Kamida familiya va ismni yozing.\n<i>Masalan: Aliyev Sardor Baxtiyorovich</i>"
    if not _FIO_RE.match(value):
        return False, "F.I.Sh. faqat harflardan iborat bo‘lishi kerak (raqam va belgilarsiz)."
    return True, value


def validate_phone(text: str) -> tuple[bool, str]:
    raw = _PHONE_CLEAN.sub("", text or "")
    digits = raw.lstrip("+")
    if digits.startswith("998") and len(digits) == 12:
        return True, "+" + digits
    if len(digits) == 9 and digits[0] in "3456789":
        return True, "+998" + digits
    if 10 <= len(digits) <= 15:
        return True, "+" + digits
    return False, "Telefon raqami noto‘g‘ri.\n<i>Masalan: +998901234567</i>"


def validate_title(text: str) -> tuple[bool, str]:
    value = " ".join((text or "").split())
    if len(value) < 2:
        return False, "Nom juda qisqa."
    if len(value) > 100:
        return False, "Nom 100 belgidan oshmasligi kerak."
    return True, value


def validate_place(text: str) -> tuple[bool, str]:
    value = " ".join((text or "").split())
    if len(value) < 3:
        return False, "Joy nomini aniqroq yozing.\n<i>Masalan: Samarqand shahri, Registon maydoni</i>"
    if len(value) > 150:
        return False, "Joy nomi 150 belgidan oshmasligi kerak."
    return True, value


def validate_shot_date(text: str) -> tuple[bool, str]:
    value = (text or "").strip().replace("/", ".").replace("-", ".")
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y.%m.%d"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            break
        except ValueError:
            continue
    else:
        return False, "Sana formati noto‘g‘ri.\n<i>Kun.Oy.Yil ko‘rinishida yozing, masalan: 15.06.2025</i>"

    if parsed > cfg.today():
        return False, "Suratga olingan sana kelajakda bo‘lishi mumkin emas."
    if parsed < date(1900, 1, 1):
        return False, "Sana juda eski ko‘rinadi. Iltimos, tekshirib qayta kiriting."
    return True, parsed.strftime("%d.%m.%Y")


def validate_description(text: str) -> tuple[bool, str]:
    value = " ".join((text or "").split())
    if len(value) < 40:
        return False, f"Izoh juda qisqa ({len(value)} belgi). Kamida 40 ta belgi — 2–3 jumla yozing."
    if len(value) > 700:
        return False, "Izoh 700 belgidan oshmasligi kerak."
    return True, value


# --------------------------------------------------------------------- fotosurat

@dataclass
class PhotoCheck:
    ok: bool
    error: str = ""
    width: int = 0
    height: int = 0
    has_exif: bool = False
    exif_info: str = ""
    file_hash: str = ""


def _read_exif(img: Image.Image) -> tuple[bool, str]:
    try:
        exif = img.getexif()
    except Exception:
        return False, ""
    if not exif:
        return False, ""
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    parts = []
    for key in ("Make", "Model", "DateTimeOriginal", "DateTime", "LensModel"):
        val = tags.get(key)
        if val:
            parts.append(f"{key}: {str(val).strip()}")
    return True, "; ".join(parts)


def oversize_hint(file_size: int) -> str:
    """Hajm chegarasidan oshganda - piksel o'lchamini saqlab qolish maslahati bilan."""
    return (
        f"Fayl hajmi <b>{file_size / 1048576:.1f} MB</b> — ruxsat etilgan chegara "
        f"<b>{cfg.max_file_mb} MB</b>.\n\n"
        "<i>Piksel o‘lchamiga yuqori chegara yo‘q — surat qancha yirik bo‘lsa, shuncha yaxshi. "
        "Faqat fayl hajmini kamaytirish kerak: rasmni tahrirlash dasturida "
        "«Save as JPEG» qilib, sifatni 90–95% ga qo‘ying. O‘lcham o‘zgarmaydi, "
        "hajm esa 2–3 barobar kichrayadi.</i>"
    )


def check_photo_file(path: Path, file_size: int) -> PhotoCheck:
    """Yuklab olingan faylni format, o'lcham va hajm bo'yicha tekshiradi."""
    if file_size > cfg.max_file_bytes:
        return PhotoCheck(False, oversize_hint(file_size))
    try:
        with Image.open(path) as img:
            fmt = (img.format or "").upper()
            width, height = img.size
            has_exif, exif_info = _read_exif(img)
    except Exception:
        return PhotoCheck(False, "Faylni o‘qib bo‘lmadi. U buzilgan yoki rasm emas.")

    if fmt not in {"JPEG", "MPO"}:
        return PhotoCheck(False, f"Fayl formati — {fmt or 'noma’lum'}. "
                                 "Tanlovga faqat <b>JPG / JPEG</b> qabul qilinadi.")
    # O'lcham talabi kadr yo'nalishiga bog'liq emas: vertikal (portret) surat uchun
    # 3000x2000 emas, 2000x3000 bo'ladi. Shuning uchun uzun va qisqa tomonlar
    # alohida solishtiriladi.
    long_side, short_side = max(width, height), min(width, height)
    need_long, need_short = max(cfg.min_width, cfg.min_height), min(cfg.min_width, cfg.min_height)
    if long_side < need_long or short_side < need_short:
        return PhotoCheck(
            False,
            f"Fotosurat o‘lchami — <b>{width} × {height}</b> piksel.\n\n"
            f"Talab: uzun tomoni kamida <b>{need_long}</b>, qisqa tomoni kamida "
            f"<b>{need_short}</b> piksel bo‘lishi kerak "
            f"(gorizontal kadr — {need_long} × {need_short}, "
            f"vertikal kadr — {need_short} × {need_long}).\n\n"
            "<i>Eslatma: rasmni «Fayl» ko‘rinishida yuborganingizga ishonch hosil qiling — "
            "oddiy rasm sifatida yuborilganda Telegram uni siqib yuboradi.</i>",
            width, height,
        )

    return PhotoCheck(True, "", width, height, has_exif, exif_info, sha256_file(path))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(text: str, limit: int = 40) -> str:
    value = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE).strip().replace(" ", "_")
    return (value[:limit] or "foto")
