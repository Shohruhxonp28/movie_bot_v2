# 🎬 KinoBot — Telegram Kino Bot

Professional, kengaytiriladigan va real foydalanishga tayyor Telegram kino bot.

## 📋 Xususiyatlar

- 🎬 Kino, serial, anime va multfilmlarni kod yoki nomi orqali qidirish
- 🔍 Fuzzy search — xato yozilgan nomlarni ham topadi (pg_trgm)
- 💎 VIP obuna tizimi
- 📢 Majburiy kanal obuna
- 🔗 Deep link tizimi (har kino uchun alohida havola)
- 📊 Admin statistika
- 📨 Broadcast xabar yuborish
- 💬 Inline mode

---

## 🏗️ Loyiha Strukturasi

```
project/
  bot/
    main.py              # Entry point
    config.py            # Settings (pydantic)
    loader.py            # Bot, Dispatcher, Storage

    handlers/
      user/              # Foydalanuvchi handlerlari
        start.py         # /start, deep link, subscription check
        search.py        # Kino qidiruv (FSM)
        vip.py           # VIP ko'rish
        settings.py      # Sozlamalar
        callbacks.py     # Kino yuborish

      admin/             # Admin handlerlari (IsAdmin filter)
        admin.py         # Admin panel, statistika
        movies.py        # Kino qo'shish (AI + qo'lda)
        channels.py      # Majburiy kanallar boshqarish
        vip.py           # VIP berish/bekor qilish
        ads.py           # Reklama boshqarish
        broadcast.py     # Broadcast

      inline/
        inline.py        # Inline qidiruv

    keyboards/
      user.py            # Foydalanuvchi klaviaturalari
      admin.py           # Admin klaviaturalari

    middlewares/
      __init__.py        # DatabaseMiddleware
      throttling.py      # Rate limiting
      subscription.py    # Majburiy obuna tekshirish

    services/
      movie_service.py        # Kino CRUD + smart search
      user_service.py         # Foydalanuvchi CRUD
      subscription_service.py # Obuna tekshirish
      vip_service.py          # VIP boshqarish
      search_service.py       # Qidiruv log
      ad_service.py           # Reklama
      stats_service.py        # Statistika

    database/
      models.py          # SQLAlchemy ORM modellari
      session.py         # Async engine va session
      migrations/        # Alembic migratsiyalar
        env.py
        001_initial.py

    utils/
      i18n.py            # Tarjimalar va movie caption
      logger.py          # Logging sozlash
      helpers.py         # Yordamchi funksiyalar + IsAdmin filter

  requirements.txt
  .env.example
  alembic.ini
  README.md
```

---

## ⚙️ O'rnatish

### 1. Talablar

- Python 3.11+
- PostgreSQL 14+ (pg_trgm extension bilan)
- Redis (ixtiyoriy, FSM uchun)

### 2. O'rnatish

```bash
git clone <repo>
cd project
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 3. Sozlash

```bash
cp .env.example .env
# .env faylini to'ldiring
```

`.env` fayli:

```env
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kinobot
BOT_USERNAME=your_bot_username

MAIN_CHANNEL_ID=-1001234567891
MAIN_CHANNEL_USERNAME=your_main_channel

REDIS_URL=redis://localhost:6379/0
```

### 4. Ma'lumotlar bazasi

```bash
# PostgreSQL da database yarating
createdb kinobot

# Migratsiya ishga tushiring
alembic upgrade head

# Yoki avtomatik (bot ishga tushganda create_tables() chaqiriladi)
```

### 5. Botni ishga tushirish

```bash
python -m bot.main
# yoki
cd project && python bot/main.py
```

---

## 📊 Database Modellari

| Model           | Tavsif                            |
|-----------------|-----------------------------------|
| `User`          | Foydalanuvchilar                  |
| `Channel`       | Majburiy obuna kanallar           |
| `Movie`         | Kinolar (poster, trailer, info)   |
| `VIPPlan`       | VIP rejalari                      |
| `VIPSubscription`| VIP obunalar                     |
| `SearchLog`     | Qidiruv loglari                   |
| `DownloadLog`   | Yuklab olish loglari              |
| `Ad`            | Reklama bloki                     |

---

## 🔗 Deep Link Tizimi

| Link                              | Tavsif                    |
|-----------------------------------|---------------------------|
| `?start=movie_CODE`               | Kino ochish               |

**Muhim:** Bot ichida ulashish tugmalari yo'q. Deep link faqat:
- Admin panelda ko'rinadi
- Publik kanalga post inline button sifatida yuboriladi

---



## 📢 Admin Buyruqlari

`/admin` — Admin panel ochish

Admin panel bo'limlari:
- 🎬 Kinolar ro'yxati + qo'shish
- 📺 Kanallar boshqarish
- 💎 VIP berish/bekor qilish + yangi plan
- 📢 Reklama qo'shish
- 📊 Statistika
- 📨 Broadcast (barcha foydalanuvchilarga)

---

## 🔒 Xavfsizlik

- Admin filter: `IsAdmin` — faqat `.env` dagi ID lar
- Foydalanuvchi kino havolasini ko'ra olmaydi
- VIP tekshiruvi kino yuklanganda
- Majburiy obuna tekshiruvi har so'rovda
- Rate limiting: 0.5s oralig'ida bir so'rov

---

## 🚀 Production Deployment

```bash
# systemd service
[Unit]
Description=KinoBot
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python bot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

