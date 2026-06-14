#!/usr/bin/env python3
"""
ربات معرفی کتاب روز - هر ۲۴ ساعت یک کتاب رندوم از طاقچه
"""

import asyncio
import logging
import random
import requests
import sys
import os
from telegram import Bot

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

FALLBACK_BOOKS = [
    {
        "title": "بوف کور",
        "author": "صادق هدایت",
        "summary": "بوف کور رمانی است از صادق هدایت که در سال ۱۳۱۵ نوشته شد. این کتاب یکی از مهم‌ترین آثار ادبیات فارسی معاصر است که دنیای درونی یک نقاش منزوی و دردمند را به شکلی سوررئالیستی به تصویر می‌کشد.",
        "genre": "رمان",
        "rating": "4.5",
        "cover_url": "",
    },
    {
        "title": "کلیدر",
        "author": "محمود دولت‌آبادی",
        "summary": "کلیدر حماسه‌ای است از زندگی مردم خراسان در دهه ۱۳۲۰. این رمان چند جلدی یکی از بزرگ‌ترین آثار ادبیات داستانی فارسی است که سرگذشت خانواده‌ای روستایی را با زبانی شاعرانه روایت می‌کند.",
        "genre": "رمان تاریخی",
        "rating": "4.7",
        "cover_url": "",
    },
]


def fetch_random_book():
    try:
        urls = [
            "https://api.taaghche.com/v8/books?offset=0&limit=50&order=1&filter-target=0",
            "https://api.taaghche.com/v8/books?offset=50&limit=50&order=1&filter-target=0",
            "https://api.taaghche.com/v8/books?offset=0&limit=50&order=3&filter-target=0",
        ]
        url = random.choice(urls)
        log.info(f"دریافت کتاب از: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)

        if resp.status_code == 200:
            data  = resp.json()
            books = data.get("books", []) or data.get("data", [])

            if books:
                valid = [b for b in books if b.get("description") and len(b.get("description", "")) > 80]
                if not valid:
                    valid = books
                book = random.choice(valid)

                title = book.get("title", "نامشخص")
                desc  = book.get("description", "") or book.get("summary", "")

                author = "نامشخص"
                if book.get("authors"):
                    a = book["authors"][0]
                    author = a.get("name", "نامشخص") if isinstance(a, dict) else str(a)

                genre = "ادبیات"
                if book.get("categories"):
                    c = book["categories"][0]
                    genre = c.get("name", "ادبیات") if isinstance(c, dict) else str(c)

                rating = ""
                r = book.get("rating", {})
                if isinstance(r, dict):
                    rating = str(r.get("score", ""))
                elif r:
                    rating = str(r)

                cover = book.get("coverUri", "") or book.get("cover", "")

                log.info(f"✅ کتاب: {title} - {author}")
                return {
                    "title": title,
                    "author": author,
                    "summary": desc[:900],
                    "genre": genre,
                    "rating": rating,
                    "cover_url": cover,
                }

    except Exception as e:
        log.warning(f"خطا در دریافت کتاب: {e}")

    log.info("کتاب پشتیبان انتخاب شد")
    return random.choice(FALLBACK_BOOKS)


def build_caption(book):
    try:
        score = float(book.get("rating", 0))
        stars = "⭐" * min(int(score), 5)
    except:
        stars = "⭐⭐⭐⭐"

    lines = [
        "📚 *کتاب روز*",
        "",
        f"✨ *{book['title']}*",
        f"🖊 نویسنده: _{book['author']}_",
        f"🏷 ژانر: {book.get('genre', '—')}",
    ]
    if book.get("rating"):
        lines.append(f"⭐ امتیاز: {book['rating']} {stars}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━",
        "📖 *خلاصه:*",
        "",
        book["summary"],
        "",
        "━━━━━━━━━━━━━━━",
        f"📚 {CHANNEL_ID}",
    ]
    return "\n".join(lines)


async def send_post():
    if not BOT_TOKEN or not CHANNEL_ID:
        log.error("❌ BOT_TOKEN یا CHANNEL_ID تنظیم نشده!")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    me  = await bot.get_me()
    log.info(f"🤖 ربات: @{me.username}")

    book    = fetch_random_book()
    caption = build_caption(book)
    cover   = book.get("cover_url", "")

    if cover and cover.startswith("http"):
        try:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=cover,
                caption=caption,
                parse_mode="Markdown"
            )
            log.info("✅ پست با جلد کتاب ارسال شد")
            return
        except Exception as e:
            log.warning(f"خطا در ارسال عکس جلد: {e}")

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=caption,
        parse_mode="Markdown"
    )
    log.info("✅ پست متنی ارسال شد")


if __name__ == "__main__":
    asyncio.run(send_post())
