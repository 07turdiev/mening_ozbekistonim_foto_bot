"""Botning barcha matnlari (o'zbek tilida)."""
from __future__ import annotations

from config import cfg

MONTHS = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel", 5: "may", 6: "iyun",
    7: "iyul", 8: "avgust", 9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr",
}


def uz_date(d) -> str:
    return f"{d.day}-{MONTHS[d.month]} {d.year}-yil"


PERIOD = f"{cfg.start_date.day}-{MONTHS[cfg.start_date.month]}dan {cfg.end_date.day}-{MONTHS[cfg.end_date.month]}ga qadar"

WELCOME = (
    "🇺🇿 <b>“MENING O‘ZBEKISTONIM” FOTOTANLOVI</b>\n"
    "<i>Vatanni o‘z nigohingiz bilan kashf eting!</i>\n\n"
    "O‘zbekiston Respublikasi davlat mustaqilligining <b>35 yilligi</b> munosabati bilan "
    "O‘zbekiston Respublikasi Madaniyat vazirligi “Mening O‘zbekistonim” fototanlovini e’lon qiladi.\n\n"
    f"🗓 <b>Tanlov muddati:</b> {PERIOD}\n"
    f"🏆 <b>Umumiy mukofot jamg‘armasi:</b> 15 000 000 so‘m\n\n"
    "Ishtirok etish uchun quyidagi tugmani bosing 👇"
)

RULES = (
    "📋 <b>TANLOV SHARTLARI</b>\n\n"
    "<b>Maqsad</b>\nO‘zbekistonning betakror tabiati, tarixiy va zamonaviy qiyofasi, milliy qadriyatlari, "
    "madaniy merosi, bunyodkorlik jarayonlari, xalqimizning hayoti va Vatanga muhabbat tuyg‘usini "
    "fotosan’at vositasida keng namoyon etish.\n\n"
    f"🗓 <b>Tanlov muddati:</b> {PERIOD}\n\n"
    "🏆 <b>G‘oliblar va mukofotlar</b>\n"
    "• “O‘zbekiston — mening nigohimda” — <b>7 000 000</b> so‘m\n"
    "• “Vatan ranglari” — <b>5 000 000</b> so‘m\n"
    "• “Eng yaxshi ijodiy kadr” — <b>3 000 000</b> so‘m\n"
    "Umumiy mukofot jamg‘armasi — <b>15 000 000</b> so‘m.\n\n"
    "G‘oliblar tanlov hay’ati tomonidan fotosuratning mazmuni, badiiy saviyasi, kompozitsiyasi, "
    "o‘ziga xosligi va mavzuni ochib berish darajasi asosida aniqlanadi.\n\n"
    "🖼 <b>Mavzular</b>\n"
    "• Yangi O‘zbekistonning zamonaviy qiyofasi va bunyodkorlik jarayonlari\n"
    "• Tarixiy obidalar va madaniy meros maskanlari\n"
    "• O‘zbekistonning tabiati va betakror manzaralari\n"
    "• Milliy urf-odatlar, an’analar va qadriyatlar\n"
    "• Madaniyat va san’at jarayonlari\n"
    "• Xalqimizning kundalik hayoti va samimiy lahzalari\n"
    "• Vatanga muhabbat, daxldorlik va faxr tuyg‘usini ifodalovchi ijodiy kadrlar\n\n"
    "📸 <b>Fotosuratlarga qo‘yiladigan talablar</b>\n"
    "• JPG yoki JPEG formatida, yuqori sifatli bo‘lishi\n"
    f"• kamida <b>{cfg.min_width} × {cfg.min_height}</b> piksel o‘lchamda bo‘lishi\n"
    f"• fayl hajmi <b>{cfg.max_file_mb} MB</b>dan oshmasligi\n"
    "• ishtirokchining o‘zi tomonidan suratga olingan original ijodiy ish bo‘lishi\n"
    "• mualliflik belgisi, logotip, sana yoki boshqa yozuvlar bo‘lmasligi\n"
    "• mazmunni o‘zgartiradigan sun’iy montaj va manipulyatsiyalardan xoli bo‘lishi\n"
    "• sun’iy intellekt vositalari yordamida yaratilmagan bo‘lishi\n"
    "• ilgari boshqa tanlovlarda g‘olib deb topilmagan bo‘lishi lozim\n\n"
    "Rang, yorqinlik, kontrast, ekspozitsiya va kadrni kesish kabi oddiy fotografik ishlovlarga ruxsat beriladi.\n"
    f"Har bir ishtirokchi tanlovga <b>{cfg.max_photos} tagacha</b> fotosurat taqdim etishi mumkin.\n\n"
    "📝 <b>Har bir fotosurat bilan birga taqdim etiladi</b>\n"
    "• muallifning F.I.Sh.\n• telefon raqami\n• fotosurat nomi\n"
    "• suratga olingan joy va sana\n• fotosurat haqida 2–3 jumladan iborat qisqa izoh\n\n"
    "🖼 <b>Eng yaxshi fotosuratlar — ko‘rgazmada!</b>\n"
    "Tanlov hay’ati tomonidan saralangan eng yaxshi ijodiy ishlar asosida "
    "“Mening O‘zbekistonim” fotoko‘rgazmasi tashkil etiladi.\n\n"
    f"☎️ <b>Murojaat uchun:</b> {cfg.contact_info}"
)

AGREEMENT = (
    "📄 <b>ROZILIK</b>\n\n"
    "Tanlovga fotosurat yuborish orqali ishtirokchi taqdim etilgan ijodiy ishning <b>muallifi</b> "
    "ekanligini tasdiqlaydi hamda tanlov doirasida ushbu fotosuratdan <b>ko‘rgazma</b>, vazirlikning "
    "<b>rasmiy veb-sayti</b> va <b>ijtimoiy tarmoqlarida</b> muallifini ko‘rsatgan holda foydalanishga "
    "rozilik bildiradi.\n\n"
    "Shuningdek, ishtirokchi shaxsiy ma’lumotlari (F.I.Sh., telefon raqami) tanlovni tashkil etish "
    "maqsadida qayta ishlanishiga rozilik bildiradi.\n\n"
    "Davom etish uchun rozilikni tasdiqlang 👇"
)

ASK_FIO = (
    "👤 <b>1/2. F.I.Sh.</b>\n\n"
    "Familiya, ism va otangizning ismini to‘liq yozing.\n"
    "<i>Masalan: Aliyev Sardor Baxtiyorovich</i>"
)
ASK_PHONE = (
    "☎️ <b>2/2. Telefon raqami</b>\n\n"
    "Pastdagi tugma orqali raqamingizni yuboring yoki qo‘lda kiriting.\n"
    "<i>Masalan: +998901234567</i>"
)

HOW_TO_SEND = (
    "📸 <b>Fotosuratni yuborish</b>\n\n"
    "⚠️ <b>Diqqat!</b> Fotosuratni albatta <b>FAYL</b> (hujjat) ko‘rinishida yuboring — "
    "aks holda Telegram uni siqib, sifatini pasaytiradi va ish qabul qilinmaydi.\n\n"
    "<b>Telefonda:</b> 📎 → <i>Fayl</i> / <i>File</i> → galereyadan rasmni tanlang\n"
    "<b>Kompyuterda:</b> faylni sudrab tashlang va <i>“Siqmasdan yuborish / Send as file”</i> ni belgilang\n\n"
    "<b>Talablar:</b>\n"
    "• format — JPG / JPEG\n"
    f"• o‘lcham — kamida {cfg.min_width} × {cfg.min_height} piksel\n"
    f"• hajmi — {cfg.max_file_mb} MB dan oshmasligi\n\n"
    f"💡 Bir vaqtning o‘zida <b>{cfg.max_photos} tagacha</b> faylni birdan belgilab yuborishingiz "
    "mumkin — bot ularni navbat bilan qabul qiladi va har biri uchun ma’lumot so‘raydi.\n\n"
    "Endi fotosuratni yuboring 👇"
)

NEXT_PHOTO = (
    "📸 <b>Keyingi fotosurat</b>\n\n"
    "Yana ish yubormoqchi bo‘lsangiz, suratni <b>fayl</b> ko‘rinishida yuboring "
    "(bir nechtasini birdan belgilash mumkin).\n\n"
    "Yakunlash uchun «❌ Bekor qilish» tugmasini bosing — yuborilgan ishlaringiz saqlanib qoladi."
)

ASK_TITLE = "🏷 <b>1/4. Fotosurat nomi</b>\n\nAsaringizga nom bering.\n<i>Masalan: “Registon tongi”</i>"
ASK_PLACE = "📍 <b>2/4. Suratga olingan joy</b>\n\n<i>Masalan: Samarqand shahri, Registon maydoni</i>"
ASK_DATE = "🗓 <b>3/4. Suratga olingan sana</b>\n\nKun.Oy.Yil ko‘rinishida yozing.\n<i>Masalan: 15.06.2025</i>"
ASK_DESC = (
    "✍️ <b>4/4. Qisqa izoh</b>\n\n"
    "Fotosurat haqida <b>2–3 jumladan</b> iborat izoh yozing: nima aks etgan, qanday lahza, "
    "nima uchun siz uchun qadrli.\n\n<i>Kamida 40 ta belgi.</i>"
)

CLOSED_BEFORE = (
    "⏳ Tanlovga fotosurat qabul qilish hali boshlanmadi.\n\n"
    f"Qabul <b>{uz_date(cfg.start_date)}</b> kuni boshlanadi. "
    "Shu paytgacha tanlov shartlari bilan tanishib turing."
)
CLOSED_AFTER = (
    "🔒 Tanlovga fotosurat qabul qilish yakunlandi.\n\n"
    f"Qabul muddati {uz_date(cfg.end_date)} kuni tugadi. "
    "Natijalar tanlov hay’ati tomonidan e’lon qilinadi. E’tiboringiz uchun rahmat!"
)
CLOSED_MANUAL = "🔒 Hozircha fotosurat qabul qilish vaqtincha to‘xtatilgan. Iltimos, keyinroq urinib ko‘ring."

LIMIT_REACHED = (
    f"ℹ️ Siz allaqachon <b>{cfg.max_photos} ta</b> fotosurat yubordingiz — bu tanlovdagi eng ko‘p miqdor.\n\n"
    "Ishlaringizni «🖼 Mening ishlarim» bo‘limida ko‘rishingiz mumkin."
)

CANCELLED = "❌ Bekor qilindi."
FINISHED = "✅ Yakunlandi. Yuborilgan ishlaringiz «🖼 Mening ishlarim» bo‘limida saqlanib qoldi."
UNKNOWN = "Iltimos, pastdagi menyu tugmalaridan foydalaning 👇"


CAPTION_LIMIT = 1024


def clip(text: str, limit: int = CAPTION_LIMIT) -> str:
    """Telegram caption chegarasiga (1024 belgi) sig'diradi."""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
