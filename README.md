# “MENING O‘ZBEKISTONIM” fototanlovi — Telegram bot

O‘zbekiston Respublikasi Madaniyat vazirligi tomonidan e’lon qilingan “Mening O‘zbekistonim”
fototanloviga arizalarni qabul qilish, tekshirish va yig‘ish uchun mo‘ljallangan bot.

---

## 1. Tez ishga tushirish (Windows)

1. **Bot yarating** — Telegramda [@BotFather](https://t.me/BotFather) ga `/newbot` yozing va tokenni oling.
2. **Telegram ID** ni aniqlang — [@userinfobot](https://t.me/userinfobot) ga `/start` yozing.
3. `.env` faylini oching va to‘ldiring:

   ```env
   BOT_TOKEN=8123456789:AAF...            # BotFather bergan token
   ADMIN_IDS=123456789,987654321          # administratorlar Telegram ID si
   CONTACT_INFO=+998 71 000 00 00 | @admin
   ```

4. `test.bat` ni ishga tushiring — barcha tekshiruvlar `[OK]` bo‘lishi kerak.
5. `run.bat` ni ishga tushiring. Bot ishlay boshlaydi.

> Bot ishlab turgan vaqtda oyna yopilmasligi kerak. Doimiy ishlashi uchun 3-bo‘limga qarang.

---

## 2. Bot nima qiladi

### Ishtirokchi uchun

| Bosqich | Tavsif |
|---|---|
| `/start` (yangi) | Tanlov e’loni + inline tugmalar. Pastki menyu ko‘rsatilmaydi |
| `/start` (qaytgan) | Tanlov e’loni + **asosiy menyu**. Ma’lumotlar qayta so‘ralmaydi |
| Rozilik | Mualliflik va ma’lumotlardan foydalanishga rozilik tasdiqlanadi |
| Ro‘yxatdan o‘tish | F.I.Sh. + telefon raqami (tugma orqali yoki qo‘lda) |
| Fotosurat | **Fayl (hujjat)** ko‘rinishida yuboriladi — siqilgan rasm rad etiladi |
| Ma’lumotlar | Nomi → suratga olingan joy → sana → 2–3 jumlalik izoh |
| Tasdiqlash | Yakuniy ko‘rinish ko‘rsatiladi, ishtirokchi tasdiqlaydi |

### Bir nechta surat yuborish

- Ishtirokchi **bir yo‘la bir nechta faylni** (albom qilib) tanlab yuborishi mumkin.
  Birinchisi darhol ishlov beriladi, qolganlari **navbatga** qo‘yiladi va joriy ish
  yakunlangach avtomatik ravishda keyingisiga o‘tiladi — qayta tugma bosish shart emas.
- Bitta surat tasdiqlangach bot darrov keyingisini kutadi; ishtirokchi yakunlamoqchi
  bo‘lsa «❌ Bekor qilish» tugmasini bosadi (yuborilgan ishlar saqlanib qoladi).
- Limitdan (`MAX_PHOTOS`, standart 3) oshgan fayllar qabul qilinmaydi va yuklab
  olinmaydi ham — trafik behuda sarflanmaydi.
- Albomdagi fayllar parallel kelgani uchun foydalanuvchi bo‘yicha `asyncio.Lock`
  qo‘yilgan — suratlar bir-birining ustiga yozilib qolmaydi.

**Menyu:** Fotosurat yuborish · Mening ishlarim · Tanlov shartlari · Ma’lumotlarim · Bog‘lanish

### Avtomatik tekshiruvlar

- format **JPG/JPEG** (haqiqiy fayl mazmuni bo‘yicha, kengaytma bo‘yicha emas);
- o‘lchami kamida **3000 × 2000** piksel;
- hajmi **20 MB** dan oshmasligi;
- bitta ishtirokchidan ko‘pi bilan **3 ta** ish;
- **takroriy surat** SHA-256 hash bo‘yicha aniqlanadi (o‘zi yoki boshqa ishtirokchi yuborgan bo‘lsa);
- **EXIF** ma’lumoti o‘qiladi (kamera, suratga olingan sana) — hay’at uchun qo‘shimcha ma’lumot,
  EXIF yo‘qligi Excelda alohida ustunda ko‘rsatiladi;
- tanlov muddati (`START_DATE` … `END_DATE`) tashqarisida qabul avtomatik yopiladi.

### Administrator uchun (`/admin`)

- 📊 **Statistika** — foydalanuvchilar, ishtirokchilar, arizalar holati bo‘yicha
- 🕓 **Ko‘rib chiqish** — arizalar ketma-ket ko‘riladi: ✅ qabul qilish / ❌ rad etish
  (rad etilganda sabab yoziladi va ishtirokchiga avtomatik yuboriladi).
  Har bir qarordan keyin **keyingi ariza avtomatik ochiladi**, navbat tugagach
  **admin panelga qaytadi** — tugma bosib yurish shart emas.
- 🔍 **Qidiruv** — F.I.Sh., telefon yoki Telegram ID bo‘yicha
- 📥 **Excel** — barcha ma’lumotlar bilan `.xlsx` jadval (filtr, ranglar, avtofiltr)
- 🗜 **ZIP** — qabul qilingan suratlarni arxiv qilib olish
- 📢 **Ommaviy xabar** — barcha foydalanuvchilarga
- 🔁 **Qabulni to‘xtatish/ochish** — muddatdan qat’i nazar qo‘lda boshqarish

---

## 3. Sozlamalar (`.env`)

| Kalit | Vazifasi | Standart |
|---|---|---|
| `BOT_TOKEN` | BotFather tokeni | — (majburiy) |
| `ADMIN_IDS` | Adminlar ID si, vergul bilan | — (majburiy) |
| `START_DATE` / `END_DATE` | Qabul muddati (`YYYY-MM-DD`) | 2026-08-27 / 2026-09-05 |
| `MAX_PHOTOS` | Bir ishtirokchidan ishlar soni | 3 |
| `MIN_WIDTH` / `MIN_HEIGHT` | Eng kichik o‘lcham, piksel | 3000 / 2000 |
| `MAX_FILE_MB` | Fayl hajmi chegarasi | 20 |
| `DOWNLOAD_TIMEOUT` | Fayl yuklab olish uchun vaqt, soniya | 300 |
| `DOWNLOAD_RETRIES` | Aloqa uzilganda qayta urinishlar soni | 3 |
| `MODERATION` | `1` — adminlar tasdiqlaydi, `0` — avtomatik qabul | 1 |
| `CHANNEL_ID`, `CHANNEL_URL` | Majburiy obuna kanali (ixtiyoriy) | bo‘sh |
| `ARCHIVE_CHAT_ID` | Har bir ariza nusxasi yuboriladigan yopiq kanal | bo‘sh |
| `CONTACT_INFO` | «Bog‘lanish» bo‘limidagi matn | — |
| `TIMEZONE_OFFSET` | Vaqt mintaqasi (Toshkent = 5) | 5 |

> **Majburiy obuna** kerak bo‘lsa: botni kanalga administrator qilib qo‘shing va
> `CHANNEL_ID=@kanal_nomi`, `CHANNEL_URL=https://t.me/kanal_nomi` deb yozing.

> **Sekin internet.** aiogram'ning standart yuklab olish chegarasi atigi 30 soniya —
> 20 MB fayl ulgurmay `TimeoutError` beradi. Shuning uchun `DOWNLOAD_TIMEOUT=300` qilingan
> va aloqa uzilsa bot `DOWNLOAD_RETRIES` marta qayta urinadi (yarim yuklangan fayl o‘chiriladi).

> **20 MB chegarasi** Telegram Bot API ning fayl yuklab olish chegarasi bilan mos.
> Undan kattaroq fayllar kerak bo‘lsa, lokal Bot API server o‘rnatish talab qilinadi.

---

## 4. Ma’lumotlar qayerda saqlanadi

```
contest.db                  SQLite baza (foydalanuvchilar, arizalar)
uploads/<user_id>/          Asl fotosuratlar (00012_Registon_tongi.jpg)
exports/                    Yaratilgan Excel va ZIP fayllar
bot.log                     Ish jurnali
```

**Zaxira nusxa:** `contest.db` va `uploads/` papkasini har kuni nusxalab turing —
tanlov yakunida hay’atga aynan shu ikkisi kerak bo‘ladi.

---

## 5. Doimiy ishlashi uchun

**Windows Server — vazifalar rejalashtiruvchisi (Task Scheduler):**
`run.bat` ni «tizim ishga tushganda» (At startup) ishga tushadigan vazifa sifatida qo‘shing,
«Restart if the task fails» bandini yoqing.

**Linux server — systemd:**

```ini
# /etc/systemd/system/fotobot.service
[Unit]
Description=Mening Ozbekistonim foto bot
After=network.target

[Service]
WorkingDirectory=/opt/fotobot
ExecStart=/opt/fotobot/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now fotobot
```

---

## 6. Fayllar tuzilishi

```
bot.py                 Ishga tushirish nuqtasi, routerlar ulanishi
config.py              .env dan sozlamalar
texts.py               Barcha matnlar (e’lon, shartlar, rozilik, savollar)
keyboards.py           Tugmalar
database.py            SQLite bilan ishlash
handlers/user.py       Ishtirokchi ssenariysi (FSM)
handlers/admin.py      Admin paneli, moderatsiya, eksport
utils/validators.py    F.I.Sh., telefon, sana va fotosurat tekshiruvi
utils/export.py        Excel va ZIP shakllantirish
selftest.py            Ishga tushirishdan oldingi tekshiruv
```

## 7. Matnni o‘zgartirish

E’lon, tanlov shartlari, rozilik matni va savollar — barchasi [texts.py](texts.py) faylida.
O‘zgartirgandan so‘ng botni qayta ishga tushiring.

Yuborish manzili va murojaat ma’lumotlari e’londa bo‘sh qoldirilgan edi —
ular `.env` dagi `CONTACT_INFO` orqali to‘ldiriladi (fotosuratlar shu botning o‘ziga yuboriladi).
