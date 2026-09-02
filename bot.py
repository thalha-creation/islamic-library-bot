#!/usr/bin/env python3
"""
====================================================================
📚 Islamic Library Telegram Bot
Created by Thalha Creations
====================================================================
"""

import os
import sys
import logging
import asyncio
import html
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

import aiosqlite
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ------------------------------------------------------------------
# 1. Configuration & Logging
# ------------------------------------------------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "islamic_library.db").strip()

if not BOT_TOKEN:
    print("FATAL: BOT_TOKEN is missing in environment variables.")
    sys.exit(1)

ADMIN_IDS: set[int] = set()
if ADMIN_IDS_RAW:
    for item in ADMIN_IDS_RAW.split(","):
        clean_item = item.strip()
        if clean_item.isdigit():
            ADMIN_IDS.add(int(clean_item))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("IslamicLibraryBot")

# ------------------------------------------------------------------
# 2. Multilingual Translations
# ------------------------------------------------------------------
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "Welcome to <b>📚 Islamic Library</b>!\n\nAccess authentic Islamic educational resources, books, audio, and documents.",
        "brand_footer": "\n\n<i>Created by Thalha Creations</i>",
        "btn_library": "📚 Library",
        "btn_search": "🔎 Search",
        "btn_categories": "📂 Categories",
        "btn_popular": "⭐ Popular",
        "btn_latest": "🆕 Latest",
        "btn_lang": "🌐 Language",
        "btn_about": "ℹ️ About",
        "btn_help": "📞 Help",
        "btn_prev": "⬅️ Prev",
        "btn_next": "Next ➡️",
        "btn_home": "🏠 Home",
        "btn_back": "⬅️ Back",
        "btn_download": "📥 Download",
        "btn_share": "🔗 Share",
        "btn_cancel": "❌ Cancel",
        "btn_web_search": "🌐 Search on Google",
        "about_text": "<b>📚 Islamic Library</b>\n\nA digital library for accessing and organizing authentic Islamic educational resources.\n\n<b>Brand:</b> Islamic Library\n<b>Developer:</b> Thalha Creations",
        "help_text": "<b>📖 How to use this bot:</b>\n\n• <b>📚 Library:</b> Browse all Islamic literature by pages.\n• <b>📂 Categories:</b> Discover books under specific topics.\n• <b>🔎 Search:</b> Type any author, title, or topic to search.\n• <b>📥 Download:</b> Click download inside any book page.\n• <b>🌐 Language:</b> Switch language anytime.\n• <b>/start or /home:</b> Return to the main menu.",
        "select_lang": "🌐 <b>Select your preferred language:</b>",
        "lang_updated": "✅ Language preference saved successfully!",
        "no_books": "No books found in this section.",
        "search_prompt": "🔎 <b>Enter keywords to search:</b>\n(Book title, author, category, or reference)",
        "search_results_title": "🔎 <b>Search Results for:</b> <code>{query}</code>\nShowing {start}-{end} of {total} results:",
        "book_not_found": "⚠️ Book not found or removed.",
        "sending_file": "📥 Delivering your file, please wait...",
        "file_error": "⚠️ Failed to send file. File ID might be invalid or expired.",
        "categories_title": "📂 <b>Select a Category:</b>",
        "popular_title": "⭐ <b>Most Popular Resources</b>",
        "latest_title": "🆕 <b>Recently Added Resources</b>",
        "views": "Views",
        "downloads": "Downloads",
        "category": "Category",
        "author": "Author",
        "keywords": "Keywords",
        "reference": "Reference",
        "added": "Added",
    },
    "ta": {
        "welcome": "<b>📚 Islamic Library</b>-க்கு நல்வரவு!\n\nநம்பகமான இஸ்லாமிய புத்தகங்கள், ஆவணங்கள் மற்றும் பயனுள்ள ஆடியோக்களை எளிதாகப் பெறுங்கள்.",
        "brand_footer": "\n\n<i>Created by Thalha Creations</i>",
        "btn_library": "📚 நூலகம்",
        "btn_search": "🔎 தேடல்",
        "btn_categories": "📂 பிரிவுகள்",
        "btn_popular": "⭐ பிரபலம்",
        "btn_latest": "🆕 புதியவை",
        "btn_lang": "🌐 மொழி",
        "btn_about": "ℹ️ எங்களை பற்றி",
        "btn_help": "📞 உதவி",
        "btn_prev": "⬅️ முந்தைய",
        "btn_next": "அடுத்தது ➡️",
        "btn_home": "🏠 முகப்பு",
        "btn_back": "⬅️ பின்செல்",
        "btn_download": "📥 பதிவிறக்கு",
        "btn_share": "🔗 பகிர்",
        "btn_cancel": "❌ ரத்து",
        "btn_web_search": "🌐 கூகுளில் தேடுக",
        "about_text": "<b>📚 Islamic Library</b>\n\nஇஸ்லாமிய கல்வி வளங்களை முறைப்படுத்தி வழங்கும் மின்னணு நூலகம்.\n\n<b>உருவாக்கம்:</b> Thalha Creations",
        "help_text": "<b>📖 போட்டைப் பயன்படுத்தும் முறை:</b>\n\n• <b>📚 நூலகம்:</b> அனைத்து புத்தகங்களையும் பக்கங்கள் வாரியாக பார்வையிட.\n• <b>📂 பிரிவுகள்:</b> தலைப்புகள் வாரியாக நூல்களைத் தேர்ந்தெடுக்க.\n• <b>🔎 தேடல்:</b> ஆசிரியர், தலைப்பு அல்லது குறிச்சொற்கள் மூலம் தேட.\n• <b>📥 பதிவிறக்கம்:</b> புத்தகத்தின் பக்கத்தில் உள்ள பதிவிறக்க பொத்தானை அழுத்தவும்.\n• <b>/home:</b> எந்த நேரத்திலும் முதன்மைப் பக்கத்திற்குத் திரும்ப.",
        "select_lang": "🌐 <b>உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்:</b>",
        "lang_updated": "✅ மொழி வெற்றிகரமாக மாற்றப்பட்டது!",
        "no_books": "இப்பிரிவில் நூல்கள் எதுவும் இல்லை.",
        "search_prompt": "🔎 <b>தேட வேண்டிய சொல்லை உள்ளிடவும்:</b>\n(தலைப்பு, ஆசிரியர், அல்லது குறிப்பு)",
        "search_results_title": "🔎 <b>தேடல் முடிவுகள்:</b> <code>{query}</code>\nமுடிவுகள் {start}-{end} / மொத்தம் {total}:",
        "book_not_found": "⚠️ நூல் கிடைக்கவில்லை அல்லது நீக்கப்பட்டுள்ளது.",
        "sending_file": "📥 கோப்பு அனுப்பப்படுகிறது, காத்திருக்கவும்...",
        "file_error": "⚠️ கோப்பை அனுப்புவதில் பிழை ஏற்பட்டது.",
        "categories_title": "📂 <b>பிரிவைத் தேர்ந்தெடுக்கவும்:</b>",
        "popular_title": "⭐ <b>அதிகம் பார்வையிடப்பட்ட நூல்கள்</b>",
        "latest_title": "🆕 <b>சமீபத்தில் சேர்க்கப்பட்டவை</b>",
        "views": "பார்வைகள்",
        "downloads": "பதிவிறக்கங்கள்",
        "category": "பிரிவு",
        "author": "ஆசிரியர்",
        "keywords": "குறிச்சொற்கள்",
        "reference": "குறிப்பு",
        "added": "சேர்க்கப்பட்ட தேதி",
    },
    "ar": {
        "welcome": "مرحبًا بك في <b>📚 المكتبة الإسلامية</b>!\n\nمنصة رقمية للوصول إلى الكتب والوسائط التعليمية الإسلامية الموثوقة.",
        "brand_footer": "\n\n<i>Created by Thalha Creations</i>",
        "btn_library": "📚 المكتبة",
        "btn_search": "🔎 بحث",
        "btn_categories": "📂 الأقسام",
        "btn_popular": "⭐ الشائع",
        "btn_latest": "🆕 الأحدث",
        "btn_lang": "🌐 اللغة",
        "btn_about": "ℹ️ حول",
        "btn_help": "📞 مساعدة",
        "btn_prev": "⬅️ السابق",
        "btn_next": "التالي ➡️",
        "btn_home": "🏠 الرئيسية",
        "btn_back": "⬅️ رجوع",
        "btn_download": "📥 تحميل",
        "btn_share": "🔗 مشاركة",
        "btn_cancel": "❌ إلغاء",
        "btn_web_search": "🌐 البحث في جوجل",
        "about_text": "<b>📚 المكتبة الإسلامية</b>\n\nمكتبة رقمية لتنظيم وتوفير المواد التعليمية الإسلامية.\n\n<b>تم التطوير بواسطة:</b> Thalha Creations",
        "help_text": "<b>📖 دليل الاستخدام:</b>\n\n• <b>📚 المكتبة:</b> تصفح جميع الكتب والمواد.\n• <b>📂 الأقسام:</b> استعراض المواد حسب التصنيف.\n• <b>🔎 بحث:</b> ابحث بالعنوان أو اسم المؤلف.\n• <b>📥 تحميل:</b> اضغط على زر التحميل للحصول على الملف مباشرة.\n• <b>/home:</b> العودة إلى القائمة الرئيسية.",
        "select_lang": "🌐 <b>اختر لغتك المفضلة:</b>",
        "lang_updated": "✅ تم تحديث اللغة بنجاح!",
        "no_books": "لا توجد كتب متاحة في هذا القسم حاليًا.",
        "search_prompt": "🔎 <b>أدخل كلمة البحث:</b>\n(عنوان الكتاب، اسم المؤلف، أو التصنيف)",
        "search_results_title": "🔎 <b>نتائج البحث عن:</b> <code>{query}</code>\nعرض {start}-{end} من أصل {total}:",
        "book_not_found": "⚠️ لم يتم العثور على الكتاب.",
        "sending_file": "📥 جاري إرسال الملف، يرجى الانتظار...",
        "file_error": "⚠️ حدث خطأ أثناء إرسال الملف.",
        "categories_title": "📂 <b>اختر القسم:</b>",
        "popular_title": "⭐ <b>الكتب الأكثر شهرة</b>",
        "latest_title": "🆕 <b>أحدث المواد المضافة</b>",
        "views": "مشاهدات",
        "downloads": "تحميلات",
        "category": "القسم",
        "author": "المؤلف",
        "keywords": "الكلمات المفتاحية",
        "reference": "المرجع",
        "added": "تاريخ الإضافة",
    },
    "ur": {
        "welcome": "<b>📚 اسلامی لائبریری</b> میں خوش آمدید!\n\nمستند اسلامی کتب، تعلیمی مواد اور آڈیو تک رسائی حاصل کریں۔",
        "brand_footer": "\n\n<i>Created by Thalha Creations</i>",
        "btn_library": "📚 لائبریری",
        "btn_search": "🔎 تلاش",
        "btn_categories": "📂 زمرہ جات",
        "btn_popular": "⭐ مقبول",
        "btn_latest": "🆕 تازہ ترین",
        "btn_lang": "🌐 زبان",
        "btn_about": "ℹ️ تعارف",
        "btn_help": "📞 مدد",
        "btn_prev": "⬅️ پچھلا",
        "btn_next": "اگلا ➡️",
        "btn_home": "🏠 ہوم",
        "btn_back": "⬅️ واپس",
        "btn_download": "📥 ڈاؤن لوڈ",
        "btn_share": "🔗 شیئر",
        "btn_cancel": "❌ منسوخ",
        "btn_web_search": "🌐 گوگل پر تلاش کریں",
        "about_text": "<b>📚 اسلامی لائبریری</b>\n\nاسلامی تعلیمی مواد اور کتب کی فراہمی کے لیے ایک ڈیجیٹل پلیٹ فارم۔\n\n<b>تیار کردہ:</b> Thalha Creations",
        "help_text": "<b>📖 بوٹ استعمال کرنے کا طریقہ:</b>\n\n• <b>📚 لائبریری:</b> تمام کتب کی فہرست براؤز کریں۔\n• <b>📂 زمرہ جات:</b> مخصوص موضوع کے تحت کتب دیکھیں۔\n• <b>🔎 تلاش:</b> مصنف یا کتاب کے نام سے سرچ کریں۔\n• <b>📥 ڈاؤن لوڈ:</b> فائل حاصل کرنے کے لیے ڈاؤن لوڈ بٹن دبائیں۔\n• <b>/home:</b> مین مینو پر واپس جائیں۔",
        "select_lang": "🌐 <b>اپنی پسندیدہ زبان کا انتخاب کریں:</b>",
        "lang_updated": "✅ زبان کامیابی سے تبدیل ہو گئی ہے!",
        "no_books": "اس حصے میں کوئی کتاب موجود نہیں ہے۔",
        "search_prompt": "🔎 <b>تلاش کے لیے الفاظ درج کریں:</b>",
        "search_results_title": "🔎 <b>تلاش کے نتائج برائے:</b> <code>{query}</code>\nدکھائے جا رہے ہیں {start}-{end} کل {total} میں سے:",
        "book_not_found": "⚠️ کتاب دستیاب نہیں ہے۔",
        "sending_file": "📥 فائل بھیجی جا رہی ہے، برائے مہربانی انتظار کریں...",
        "file_error": "⚠️ فائل بھیجنے میں خرابی پیش آگئی ہے۔",
        "categories_title": "📂 <b>زمرہ منتخب کریں:</b>",
        "popular_title": "⭐ <b>سب سے زیادہ دیکھی گئی کتب</b>",
        "latest_title": "🆕 <b>حال ہی میں شامل کی گئی کتب</b>",
        "views": "مناظر",
        "downloads": "ڈاؤن لوڈز",
        "category": "زمرہ",
        "author": "مصنف",
        "keywords": "کلیدی الفاظ",
        "reference": "حوالہ",
        "added": "شامل کرنے کی تاریخ",
    },
}

def t(key: str, lang: str = "en", **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text

# ------------------------------------------------------------------
# 3. Database Layer
# ------------------------------------------------------------------
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'en',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    author TEXT,
                    keywords TEXT,
                    reference TEXT,
                    category_id INTEGER,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_name TEXT,
                    file_size INTEGER DEFAULT 0,
                    thumbnail_file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    downloads INTEGER DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
                );
            """)

            await db.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_books_keywords ON books(keywords);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_books_created ON books(created_at);")

            cursor = await db.execute("SELECT COUNT(*) FROM categories;")
            count = (await cursor.fetchone())[0]
            if count == 0:
                default_cats = [
                    "📖 Quran & Tafsir",
                    "📜 Hadith",
                    "🕌 Aqeedah",
                    "⚖️ Fiqh",
                    "🌙 Seerah",
                    "📚 Islamic History",
                    "🤲 Dua & Adhkar",
                    "🧑‍🏫 Islamic Education",
                    "👨‍👩‍👧 Family & Character",
                    "📕 Other",
                ]
                for cat in default_cats:
                    await db.execute("INSERT OR IGNORE INTO categories (name) VALUES (?);", (cat,))
            
            await db.commit()

    async def upsert_user(self, telegram_id: int, username: Optional[str], first_name: Optional[str]) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT language FROM users WHERE telegram_id = ?;", (telegram_id,))
            row = await cursor.fetchone()
            now = datetime.now(timezone.utc).isoformat()
            if row:
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ?, last_active = ? WHERE telegram_id = ?;",
                    (username, first_name, now, telegram_id)
                )
                await db.commit()
                return row[0] or "en"
            else:
                await db.execute(
                    "INSERT INTO users (telegram_id, username, first_name, language, joined_at, last_active) VALUES (?, ?, ?, 'en', ?, ?);",
                    (telegram_id, username, first_name, now, now)
                )
                await db.commit()
                return "en"

    async def get_user_lang(self, telegram_id: int) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT language FROM users WHERE telegram_id = ?;", (telegram_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else "en"

    async def set_user_lang(self, telegram_id: int, lang: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?;", (lang, telegram_id))
            await db.commit()

    async def get_categories(self) -> List[Tuple[int, str]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT id, name FROM categories ORDER BY name ASC;")
            return await cursor.fetchall()

    async def get_category(self, cat_id: int) -> Optional[Tuple[int, str]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT id, name FROM categories WHERE id = ?;", (cat_id,))
            return await cursor.fetchone()

    async def add_category(self, name: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO categories (name) VALUES (?);", (name,))
                await db.commit()
                return True
        except Exception:
            return False

    async def rename_category(self, cat_id: int, new_name: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE categories SET name = ? WHERE id = ?;", (new_name, cat_id))
                await db.commit()
                return True
        except Exception:
            return False

    async def delete_category(self, cat_id: int) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
                await db.commit()
                return True
        except Exception:
            return False

    async def add_book(self, data: Dict[str, Any]) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO books (
                    title, description, author, keywords, reference,
                    category_id, file_id, file_type, file_name, file_size,
                    thumbnail_file_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                data["title"], data.get("description"), data.get("author"),
                data.get("keywords"), data.get("reference"), data.get("category_id"),
                data["file_id"], data["file_type"], data.get("file_name"),
                data.get("file_size", 0), data.get("thumbnail_file_id")
            ))
            await db.commit()
            return cursor.lastrowid

    async def update_book_field(self, book_id: int, field: str, value: Any):
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(f"UPDATE books SET {field} = ?, updated_at = ? WHERE id = ?;", (value, now, book_id))
            await db.commit()

    async def delete_book(self, book_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM books WHERE id = ?;", (book_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT b.*, c.name as category_name 
                FROM books b 
                LEFT JOIN categories c ON b.category_id = c.id 
                WHERE b.id = ?;
            """, (book_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def increment_view(self, book_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE books SET views = views + 1 WHERE id = ?;", (book_id,))
            await db.commit()

    async def increment_download(self, book_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE books SET downloads = downloads + 1 WHERE id = ?;", (book_id,))
            await db.commit()

    async def get_books_paginated(self, page: int = 1, page_size: int = 10, category_id: Optional[int] = None) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if category_id:
                count_cur = await db.execute("SELECT COUNT(*) FROM books WHERE category_id = ?;", (category_id,))
                total = (await count_cur.fetchone())[0]
                cur = await db.execute(
                    "SELECT id, title, author FROM books WHERE category_id = ? ORDER BY id DESC LIMIT ? OFFSET ?;",
                    (category_id, page_size, offset)
                )
            else:
                count_cur = await db.execute("SELECT COUNT(*) FROM books;")
                total = (await count_cur.fetchone())[0]
                cur = await db.execute(
                    "SELECT id, title, author FROM books ORDER BY id DESC LIMIT ? OFFSET ?;",
                    (page_size, offset)
                )
            rows = await cur.fetchall()
            return [dict(r) for r in rows], total

    async def get_popular_books(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT id, title, views, downloads FROM books ORDER BY (views + downloads * 2) DESC LIMIT ?;", (limit,))
            return [dict(r) for r in await cur.fetchall()]

    async def get_latest_books(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT id, title, created_at FROM books ORDER BY id DESC LIMIT ?;", (limit,))
            return [dict(r) for r in await cur.fetchall()]

    async def search_books(self, query: str, page: int = 1, page_size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        pattern = f"%{query.strip()}%"
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            count_cur = await db.execute("""
                SELECT COUNT(*) FROM books b
                LEFT JOIN categories c ON b.category_id = c.id
                WHERE b.title LIKE ? OR b.author LIKE ? OR b.keywords LIKE ? OR b.description LIKE ? OR b.reference LIKE ? OR c.name LIKE ?;
            """, (pattern, pattern, pattern, pattern, pattern, pattern))
            total = (await count_cur.fetchone())[0]

            cur = await db.execute("""
                SELECT b.id, b.title, b.author,
                CASE 
                    WHEN b.title LIKE ? THEN 1
                    WHEN b.keywords LIKE ? THEN 2
                    WHEN b.author LIKE ? THEN 3
                    ELSE 4
                END as rank
                FROM books b
                LEFT JOIN categories c ON b.category_id = c.id
                WHERE b.title LIKE ? OR b.author LIKE ? OR b.keywords LIKE ? OR b.description LIKE ? OR b.reference LIKE ? OR c.name LIKE ?
                ORDER BY rank ASC, b.id DESC
                LIMIT ? OFFSET ?;
            """, (pattern, pattern, pattern, pattern, pattern, pattern, pattern, pattern, pattern, page_size, offset))
            return [dict(r) for r in await cur.fetchall()], total

    async def get_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            u_count = (await (await db.execute("SELECT COUNT(*) FROM users;")).fetchone())[0]
            b_count = (await (await db.execute("SELECT COUNT(*) FROM books;")).fetchone())[0]
            c_count = (await (await db.execute("SELECT COUNT(*) FROM categories;")).fetchone())[0]
            v_count = (await (await db.execute("SELECT SUM(views) FROM books;")).fetchone())[0] or 0
            d_count = (await (await db.execute("SELECT SUM(downloads) FROM books;")).fetchone())[0] or 0

            today_count = (await (await db.execute("SELECT COUNT(*) FROM books WHERE date(created_at) = date('now');")).fetchone())[0]
            week_count = (await (await db.execute("SELECT COUNT(*) FROM books WHERE created_at >= date('now', '-7 days');")).fetchone())[0]
            month_count = (await (await db.execute("SELECT COUNT(*) FROM books WHERE created_at >= date('now', '-30 days');")).fetchone())[0]

            return {
                "total_users": u_count,
                "total_books": b_count,
                "total_categories": c_count,
                "total_views": v_count,
                "total_downloads": d_count,
                "books_today": today_count,
                "books_week": week_count,
                "books_month": month_count,
            }

    async def get_all_user_ids(self) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT telegram_id FROM users;")
            rows = await cur.fetchall()
            return [r[0] for r in rows]

db = Database(DATABASE_PATH)

# ------------------------------------------------------------------
# 4. Keyboards & UI Helpers
# ------------------------------------------------------------------
def get_main_menu(lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(t("btn_library", lang), callback_data="user_lib:1"),
            InlineKeyboardButton(t("btn_categories", lang), callback_data="user_cats"),
        ],
        [
            InlineKeyboardButton(t("btn_search", lang), callback_data="user_search"),
            InlineKeyboardButton(t("btn_popular", lang), callback_data="user_popular"),
        ],
        [
            InlineKeyboardButton(t("btn_latest", lang), callback_data="user_latest"),
            InlineKeyboardButton(t("btn_lang", lang), callback_data="user_lang"),
        ],
        [
            InlineKeyboardButton(t("btn_about", lang), callback_data="user_about"),
            InlineKeyboardButton(t("btn_help", lang), callback_data="user_help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_row(current_page: int, total_items: int, page_size: int, prefix: str, lang: str) -> List[InlineKeyboardButton]:
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton(t("btn_prev", lang), callback_data=f"{prefix}:{current_page - 1}"))
    buttons.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(t("btn_next", lang), callback_data=f"{prefix}:{current_page + 1}"))
    return buttons

def format_book_details(book: Dict[str, Any], lang: str) -> str:
    lines = [f"📖 <b>{html.escape(book['title'])}</b>\n"]
    if book.get("description"):
        lines.append(f"📝 <i>{html.escape(book['description'])}</i>\n")
    if book.get("category_name"):
        lines.append(f"🏷 <b>{t('category', lang)}:</b> {html.escape(book['category_name'])}")
    if book.get("author"):
        lines.append(f"📚 <b>{t('author', lang)}:</b> {html.escape(book['author'])}")
    if book.get("keywords"):
        lines.append(f"🔑 <b>{t('keywords', lang)}:</b> <code>{html.escape(book['keywords'])}</code>")
    if book.get("reference"):
        lines.append(f"📌 <b>{t('reference', lang)}:</b> {html.escape(book['reference'])}")
    if book.get("created_at"):
        date_str = book["created_at"].split()[0] if " " in book["created_at"] else book["created_at"]
        lines.append(f"📅 <b>{t('added', lang)}:</b> {date_str}")
    
    lines.append(f"👁 <b>{t('views', lang)}:</b> {book.get('views', 0)} | ⬇️ <b>{t('downloads', lang)}:</b> {book.get('downloads', 0)}")
    lines.append(t("brand_footer", lang))
    return "\n".join(lines)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ------------------------------------------------------------------
# 5. User Handlers
# ------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    
    lang = await db.upsert_user(user.id, user.username, user.first_name)
    
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("book_"):
            raw_id = arg.replace("book_", "")
            if raw_id.isdigit():
                book_id = int(raw_id)
                await show_book_details(update, context, book_id, lang)
                return

    name = html.escape(user.first_name or "Friend")
    text = f"السلام عليكم {name}!\n\n{t('welcome', lang)}{t('brand_footer', lang)}"
    keyboard = get_main_menu(lang)
    
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def cmd_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)

async def show_book_details(update: Update, context: ContextTypes.DEFAULT_TYPE, book_id: int, lang: str):
    book = await db.get_book(book_id)
    if not book:
        msg = t("book_not_found", lang)
        if update.callback_query:
            await update.callback_query.answer(msg, show_alert=True)
        else:
            await update.message.reply_text(msg)
        return

    await db.increment_view(book_id)
    text = format_book_details(book, lang)
    
    bot_username = context.bot.username or "IslamicLibraryBot"
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=book_{book_id}&text={urllib.parse.quote(book['title'])}"
    
    keyboard = [
        [InlineKeyboardButton(t("btn_download", lang), callback_data=f"book_dl:{book_id}")],
        [
            InlineKeyboardButton(t("btn_share", lang), url=share_url),
            InlineKeyboardButton(t("btn_back", lang), callback_data="user_lib:1"),
        ],
        [InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if book.get("thumbnail_file_id"):
            await query.message.reply_photo(
                photo=book["thumbnail_file_id"],
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            try:
                await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        if book.get("thumbnail_file_id"):
            await update.message.reply_photo(
                photo=book["thumbnail_file_id"],
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def user_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data
    user_id = query.from_user.id
    lang = await db.get_user_lang(user_id)

    if data == "noop":
        await query.answer()
        return

    elif data == "user_home":
        await query.answer()
        name = html.escape(query.from_user.first_name or "Friend")
        text = f"السلام عليكم {name}!\n\n{t('welcome', lang)}{t('brand_footer', lang)}"
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu(lang))

    elif data == "user_about":
        await query.answer()
        text = f"{t('about_text', lang)}{t('brand_footer', lang)}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "user_help":
        await query.answer()
        text = f"{t('help_text', lang)}{t('brand_footer', lang)}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "user_lang":
        await query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 தமிழ்", callback_data="set_lang:ta"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang:en")],
            [InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang:ar"), InlineKeyboardButton("🇵🇰 اردو", callback_data="set_lang:ur")],
            [InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]
        ])
        await query.message.edit_text(t("select_lang", lang), parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("set_lang:"):
        new_lang = data.split(":")[1]
        await db.set_user_lang(user_id, new_lang)
        await query.answer(t("lang_updated", new_lang), show_alert=True)
        name = html.escape(query.from_user.first_name or "Friend")
        text = f"السلام عليكم {name}!\n\n{t('welcome', new_lang)}{t('brand_footer', new_lang)}"
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu(new_lang))

    elif data.startswith("user_lib:"):
        await query.answer()
        page = int(data.split(":")[1])
        books, total = await db.get_books_paginated(page=page, page_size=10)
        
        if not books:
            text = f"📚 <b>{t('btn_library', lang)}</b>\n\n{t('no_books', lang)}"
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]])
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            return

        keyboard = []
        for b in books:
            title_btn = f"📖 {b['title']}" + (f" - {b['author']}" if b.get('author') else "")
            keyboard.append([InlineKeyboardButton(title_btn, callback_data=f"book_view:{b['id']}")])
        
        nav_row = get_pagination_row(page, total, 10, "user_lib", lang)
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")])

        text = f"📚 <b>{t('btn_library', lang)}</b>\nShowing {len(books)} of {total} books:"
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("book_view:"):
        book_id = int(data.split(":")[1])
        await show_book_details(update, context, book_id, lang)

    elif data.startswith("book_dl:"):
        book_id = int(data.split(":")[1])
        book = await db.get_book(book_id)
        if not book:
            await query.answer(t("book_not_found", lang), show_alert=True)
            return
        
        await query.answer(t("sending_file", lang))
        file_id = book["file_id"]
        file_type = book["file_type"]
        caption = f"📖 <b>{html.escape(book['title'])}</b>{t('brand_footer', lang)}"

        try:
            if file_type == "document":
                await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif file_type == "audio":
                await context.bot.send_audio(chat_id=user_id, audio=file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif file_type == "video":
                await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif file_type == "photo":
                await context.bot.send_photo(chat_id=user_id, photo=file_id, caption=caption, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
            
            await db.increment_download(book_id)
        except Exception as e:
            logger.error(f"Error sending file {file_id}: {e}")
            await query.message.reply_text(t("file_error", lang))

    elif data == "user_cats":
        await query.answer()
        cats = await db.get_categories()
        keyboard = []
        for cat_id, cat_name in cats:
            keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"cat_view:{cat_id}:1")])
        keyboard.append([InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")])
        await query.message.edit_text(t("categories_title", lang), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("cat_view:"):
        await query.answer()
        parts = data.split(":")
        cat_id = int(parts[1])
        page = int(parts[2])
        cat = await db.get_category(cat_id)
        cat_name = cat[1] if cat else "Category"

        books, total = await db.get_books_paginated(page=page, page_size=10, category_id=cat_id)
        keyboard = []
        if not books:
            text = f"📂 <b>{html.escape(cat_name)}</b>\n\n{t('no_books', lang)}"
        else:
            for b in books:
                title_btn = f"📖 {b['title']}" + (f" - {b['author']}" if b.get('author') else "")
                keyboard.append([InlineKeyboardButton(title_btn, callback_data=f"book_view:{b['id']}")])
            text = f"📂 <b>{html.escape(cat_name)}</b>\nShowing {len(books)} of {total} books:"
            nav_row = get_pagination_row(page, total, 10, f"cat_view:{cat_id}", lang)
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton(t("btn_back", lang), callback_data="user_cats"), InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "user_popular":
        await query.answer()
        books = await db.get_popular_books(limit=10)
        keyboard = []
        if not books:
            text = f"{t('popular_title', lang)}\n\n{t('no_books', lang)}"
        else:
            text = f"{t('popular_title', lang)}:"
            for b in books:
                keyboard.append([InlineKeyboardButton(f"⭐ {b['title']} (👁 {b['views']} | ⬇️ {b['downloads']})", callback_data=f"book_view:{b['id']}")])
        keyboard.append([InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "user_latest":
        await query.answer()
        books = await db.get_latest_books(limit=10)
        keyboard = []
        if not books:
            text = f"{t('latest_title', lang)}\n\n{t('no_books', lang)}"
        else:
            text = f"{t('latest_title', lang)}:"
            for b in books:
                keyboard.append([InlineKeyboardButton(f"🆕 {b['title']}", callback_data=f"book_view:{b['id']}")])
        keyboard.append([InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "user_search":
        await query.answer()
        context.user_data["awaiting_search"] = True
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", lang), callback_data="user_home")]])
        await query.message.edit_text(t("search_prompt", lang), parse_mode=ParseMode.HTML, reply_markup=kb)

# ------------------------------------------------------------------
# 6. Search Engine Message Flow & Web Fallback
# ------------------------------------------------------------------
async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    if context.user_data.get("awaiting_search"):
        context.user_data["awaiting_search"] = False
        query_text = update.message.text.strip()
        context.user_data["last_search_query"] = query_text
        await run_search_and_display(update, context, query_text, page=1, lang=lang)

async def run_search_and_display(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str, page: int, lang: str):
    books, total = await db.search_books(query_text, page=page, page_size=10)
    
    # பிரவுசரில் நேரடியாக தேட Google URL
    encoded_query = urllib.parse.quote(query_text)
    google_search_url = f"https://www.google.com/search?q={encoded_query}+islamic+pdf"

    if total == 0:
        text = (
            f"🔎 <b>Search:</b> <code>{html.escape(query_text)}</code>\n\n"
            f"{t('no_books', lang)}\n\n"
            "🌐 <i>நீங்கள் தேடிய புத்தகம் போட்டில் இல்லை என்றால், கீழே உள்ள பட்டனை கிளிக் செய்து கூகுளில் நேரடியாக தேடி பதிவிறக்கலாம்:</i>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_web_search", lang), url=google_search_url)],
            [InlineKeyboardButton(t("btn_search", lang), callback_data="user_search")],
            [InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]
        ])
        if update.callback_query:
            await update.callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    start_idx = (page - 1) * 10 + 1
    end_idx = min(page * 10, total)
    header = t("search_results_title", lang, query=html.escape(query_text), start=start_idx, end=end_idx, total=total)

    keyboard = []
    for b in books:
        title_btn = f"📖 {b['title']}" + (f" - {b['author']}" if b.get('author') else "")
        keyboard.append([InlineKeyboardButton(title_btn, callback_data=f"book_view:{b['id']}")])
    
    nav_row = get_pagination_row(page, total, 10, "search_page", lang)
    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton(t("btn_web_search", lang), url=google_search_url),
    ])
    keyboard.append([
        InlineKeyboardButton(t("btn_search", lang), callback_data="user_search"),
        InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")
    ])

    if update.callback_query:
        await update.callback_query.message.edit_text(header, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(header, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def search_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    search_q = context.user_data.get("last_search_query", "")
    lang = await db.get_user_lang(query.from_user.id)
    if search_q:
        await run_search_and_display(update, context, search_q, page=page, lang=lang)
    else:
        await query.message.edit_text(t("search_prompt", lang), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", lang), callback_data="user_home")]]))

# ------------------------------------------------------------------
# 7. Admin Panel & Management System
# ------------------------------------------------------------------
def get_admin_panel_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Book", callback_data="admin_add_book"),
            InlineKeyboardButton("📚 Manage Books", callback_data="admin_books:1"),
        ],
        [
            InlineKeyboardButton("📂 Manage Categories", callback_data="admin_manage_cats"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_panel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Unauthorized. Admin access only.")
        return
    text = "⚙️ <b>Admin Control Panel</b>\n\nWelcome Administrator. Select an operation below:"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=get_admin_panel_kb())

async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    if os.path.exists(DATABASE_PATH):
        await update.message.reply_text("📦 Preparing database backup...")
        with open(DATABASE_PATH, "rb") as f:
            await update.message.reply_document(document=f, filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    else:
        await update.message.reply_text("⚠️ Database file not found.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.answer("⛔ Unauthorized access.", show_alert=True)
        return
    
    data = query.data

    if data == "admin_panel":
        await query.answer()
        text = "⚙️ <b>Admin Control Panel</b>\n\nSelect an operation below:"
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_admin_panel_kb())

    elif data == "admin_stats":
        await query.answer()
        s = await db.get_stats()
        text = (
            "📊 <b>Library Statistics</b>\n\n"
            f"👥 <b>Total Users:</b> {s['total_users']}\n"
            f"📚 <b>Total Books:</b> {s['total_books']}\n"
            f"📂 <b>Total Categories:</b> {s['total_categories']}\n"
            f"👁 <b>Total Views:</b> {s['total_views']}\n"
            f"📥 <b>Total Downloads:</b> {s['total_downloads']}\n\n"
            f"🗓 <b>Books Added Today:</b> {s['books_today']}\n"
            f"🗓 <b>Books Added This Week:</b> {s['books_week']}\n"
            f"🗓 <b>Books Added This Month:</b> {s['books_month']}"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")]])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("admin_books:"):
        await query.answer()
        page = int(data.split(":")[1])
        books, total = await db.get_books_paginated(page=page, page_size=10)
        keyboard = []
        if not books:
            text = "📚 <b>Manage Books</b>\n\nNo books in the library."
        else:
            text = f"📚 <b>Manage Books</b> (Page {page}):\nClick any book to Edit or Delete:"
            for b in books:
                keyboard.append([InlineKeyboardButton(f"📖 {b['title']}", callback_data=f"admin_bopt:{b['id']}")])
            nav = get_pagination_row(page, total, 10, "admin_books", "en")
            keyboard.append(nav)
        
        keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_bopt:"):
        await query.answer()
        book_id = int(data.split(":")[1])
        book = await db.get_book(book_id)
        if not book:
            await query.answer("Book not found.", show_alert=True)
            return
        
        text = (
            f"⚙️ <b>Managing:</b> {html.escape(book['title'])}\n"
            f"<b>Author:</b> {html.escape(book.get('author') or 'N/A')}\n"
            f"<b>Category:</b> {html.escape(book.get('category_name') or 'N/A')}\n"
            f"<b>Views:</b> {book['views']} | <b>Downloads:</b> {book['downloads']}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Fields", callback_data=f"admin_edit:{book_id}")],
            [InlineKeyboardButton("🗑 Delete Book", callback_data=f"admin_del_confirm:{book_id}")],
            [InlineKeyboardButton("⬅️ Back to List", callback_data="admin_books:1")],
        ])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("admin_del_confirm:"):
        await query.answer()
        book_id = int(data.split(":")[1])
        book = await db.get_book(book_id)
        text = f"⚠️ <b>Are you sure you want to permanently delete:</b>\n\n<i>{html.escape(book['title'] if book else '')}</i>?"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"admin_del_exec:{book_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"admin_bopt:{book_id}")],
        ])
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("admin_del_exec:"):
        book_id = int(data.split(":")[1])
        success = await db.delete_book(book_id)
        if success:
            await query.answer("✅ Book deleted permanently.", show_alert=True)
            logger.info(f"Admin {user_id} deleted book {book_id}")
        else:
            await query.answer("⚠️ Could not delete book.", show_alert=True)
        
        books, total = await db.get_books_paginated(page=1, page_size=10)
        keyboard = []
        for b in books:
            keyboard.append([InlineKeyboardButton(f"📖 {b['title']}", callback_data=f"admin_bopt:{b['id']}")])
        nav = get_pagination_row(1, total, 10, "admin_books", "en")
        keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")])
        await query.message.edit_text("📚 <b>Manage Books</b>:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_manage_cats":
        await query.answer()
        cats = await db.get_categories()
        keyboard = []
        for cid, cname in cats:
            keyboard.append([
                InlineKeyboardButton(f"📁 {cname}", callback_data="noop"),
                InlineKeyboardButton("✏️", callback_data=f"admin_cat_ren:{cid}"),
                InlineKeyboardButton("🗑", callback_data=f"admin_cat_del:{cid}"),
            ])
        keyboard.append([InlineKeyboardButton("➕ Add New Category", callback_data="admin_cat_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")])
        await query.message.edit_text("📂 <b>Manage Categories</b>:\nCreate, rename, or remove categories:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_cat_del:"):
        cid = int(data.split(":")[1])
        await db.delete_category(cid)
        await query.answer("Category deleted.", show_alert=True)
        cats = await db.get_categories()
        keyboard = []
        for c_id, cname in cats:
            keyboard.append([
                InlineKeyboardButton(f"📁 {cname}", callback_data="noop"),
                InlineKeyboardButton("✏️", callback_data=f"admin_cat_ren:{c_id}"),
                InlineKeyboardButton("🗑", callback_data=f"admin_cat_del:{c_id}"),
            ])
        keyboard.append([InlineKeyboardButton("➕ Add New Category", callback_data="admin_cat_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")])
        await query.message.edit_text("📂 <b>Manage Categories</b>:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

# ------------------------------------------------------------------
# 8. Add Book Conversation (Step-by-Step) [FIXED]
# ------------------------------------------------------------------
(
    ADD_CAT,
    ADD_TITLE,
    ADD_DESC,
    ADD_AUTHOR,
    ADD_KEYWORDS,
    ADD_REF,
    ADD_FILE,
    ADD_CONFIRM,
) = range(8)

async def start_add_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query or not is_admin(query.from_user.id):
        return ConversationHandler.END
    
    await query.answer()
    cats = await db.get_categories()
    if not cats:
        await query.message.reply_text("⚠️ No categories found. Please create a category first.")
        return ConversationHandler.END
    
    keyboard = []
    for cid, cname in cats:
        keyboard.append([InlineKeyboardButton(cname, callback_data=f"addbk_cat:{cid}")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")])

    context.user_data["new_book"] = {}
    await query.message.edit_text("➕ <b>Step 1: Select Category</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CAT

async def add_book_cat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split(":")[1])
    context.user_data["new_book"]["category_id"] = cat_id
    cat = await db.get_category(cat_id)
    context.user_data["new_book"]["category_name"] = cat[1] if cat else ""

    await query.message.edit_text(
        "📖 <b>Step 2: Enter Book Title</b>\n\nType and send the title of the book:\n(or /cancel to abort)",
        parse_mode=ParseMode.HTML
    )
    return ADD_TITLE

async def add_book_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_book"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 <b>Step 3: Enter Description</b>\n\nProvide a description, or send /skip to leave blank:",
        parse_mode=ParseMode.HTML
    )
    return ADD_DESC

async def add_book_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    context.user_data["new_book"]["description"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "✍️ <b>Step 4: Enter Author Name</b>\n\nSend author name, or /skip to leave blank:",
        parse_mode=ParseMode.HTML
    )
    return ADD_AUTHOR

async def add_book_author_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    context.user_data["new_book"]["author"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "🔑 <b>Step 5: Enter Keywords / Tags</b>\n\nSend keywords separated by commas, or /skip to leave blank:",
        parse_mode=ParseMode.HTML
    )
    return ADD_KEYWORDS

async def add_book_keywords_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    context.user_data["new_book"]["keywords"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "📚 <b>Step 6: Enter Reference / Source</b>\n\nSend publisher/reference info, or /skip to leave blank:",
        parse_mode=ParseMode.HTML
    )
    return ADD_REF

async def add_book_ref_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    context.user_data["new_book"]["reference"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "📤 <b>Step 7: Upload File</b>\n\nSend the Document, PDF, Audio, Video, or Photo file now:",
        parse_mode=ParseMode.HTML
    )
    return ADD_FILE

async def add_book_file_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    file_id = None
    file_type = "document"
    file_name = None
    file_size = 0
    thumb_id = None

    if msg.document:
        file_id = msg.document.file_id
        file_type = "document"
        file_name = msg.document.file_name
        file_size = msg.document.file_size or 0
        if msg.document.thumbnail:
            thumb_id = msg.document.thumbnail.file_id
    elif msg.audio:
        file_id = msg.audio.file_id
        file_type = "audio"
        file_name = msg.audio.file_name or msg.audio.title
        file_size = msg.audio.file_size or 0
    elif msg.video:
        file_id = msg.video.file_id
        file_type = "video"
        file_name = msg.video.file_name
        file_size = msg.video.file_size or 0
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "photo"
        file_size = msg.photo[-1].file_size or 0

    if not file_id:
        await update.message.reply_text("⚠️ Invalid file. Please upload a valid Document, PDF, Audio, Video, or Photo:")
        return ADD_FILE

    b = context.user_data.get("new_book", {})
    b["file_id"] = file_id
    b["file_type"] = file_type
    b["file_name"] = file_name
    b["file_size"] = file_size
    b["thumbnail_file_id"] = thumb_id

    preview = (
        "📋 <b>Step 8: Review & Confirm Details</b>\n\n"
        f"📖 <b>Title:</b> {html.escape(b.get('title', ''))}\n"
        f"📂 <b>Category:</b> {html.escape(b.get('category_name') or '')}\n"
        f"✍️ <b>Author:</b> {html.escape(b.get('author') or 'N/A')}\n"
        f"📝 <b>Description:</b> {html.escape(b.get('description') or 'N/A')}\n"
        f"🔑 <b>Keywords:</b> {html.escape(b.get('keywords') or 'N/A')}\n"
        f"📚 <b>Reference:</b> {html.escape(b.get('reference') or 'N/A')}\n"
        f"📎 <b>File Type:</b> {file_type} ({round(file_size / (1024*1024), 2)} MB)\n\n"
        "Save this book to the library?"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="addbk_save")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")],
    ])
    await update.message.reply_text(preview, parse_mode=ParseMode.HTML, reply_markup=kb)
    return ADD_CONFIRM

async def add_book_save_execution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    b = context.user_data.get("new_book")
    if not b or "title" not in b:
        await query.message.reply_text("⚠️ Session expired or invalid details.")
        return ConversationHandler.END

    book_id = await db.add_book(b)
    logger.info(f"Book added successfully with ID: {book_id} by admin {query.from_user.id}")
    context.user_data.pop("new_book", None)
    
    await query.message.edit_text(
        f"✅ <b>Book Saved Successfully!</b>\nBook ID: <code>{book_id}</code>\nDeep link: <code>/start book_{book_id}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel")]])
    )
    return ConversationHandler.END

# ------------------------------------------------------------------
# 9. Edit Book Conversation
# ------------------------------------------------------------------
EDIT_SELECT_FIELD, EDIT_INPUT_VAL = range(8, 10)

async def start_edit_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    book_id = int(query.data.split(":")[1])
    context.user_data["edit_book_id"] = book_id
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Title", callback_data="ed_f:title"), InlineKeyboardButton("📝 Description", callback_data="ed_f:description")],
        [InlineKeyboardButton("✍️ Author", callback_data="ed_f:author"), InlineKeyboardButton("🔑 Keywords", callback_data="ed_f:keywords")],
        [InlineKeyboardButton("📌 Reference", callback_data="ed_f:reference"), InlineKeyboardButton("📂 Category", callback_data="ed_f:category_id")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")]
    ])
    await query.message.edit_text("✏️ <b>Select field to edit:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)
    return EDIT_SELECT_FIELD

async def edit_field_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.split(":")[1]
    context.user_data["edit_field"] = field

    if field == "category_id":
        cats = await db.get_categories()
        kb = []
        for cid, cname in cats:
            kb.append([InlineKeyboardButton(cname, callback_data=f"ed_catval:{cid}")])
        kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")])
        await query.message.edit_text("📂 <b>Select new category:</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        return EDIT_INPUT_VAL
    else:
        await query.message.edit_text(f"Send new value for <b>{field}</b> (or /cancel):", parse_mode=ParseMode.HTML)
        return EDIT_INPUT_VAL

async def edit_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    book_id = context.user_data.get("edit_book_id")
    field = context.user_data.get("edit_field")

    if update.callback_query and update.callback_query.data.startswith("ed_catval:"):
        val = int(update.callback_query.data.split(":")[1])
        await update.callback_query.answer()
        msg_obj = update.callback_query.message
    else:
        val = update.message.text.strip()
        msg_obj = update.message

    await db.update_book_field(book_id, field, val)
    await msg_obj.reply_text(
        f"✅ <b>{field} updated successfully!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")]])
    )
    context.user_data.pop("edit_book_id", None)
    context.user_data.pop("edit_field", None)
    return ConversationHandler.END

# ------------------------------------------------------------------
# 10. Category Addition & Renaming Conversations
# ------------------------------------------------------------------
CAT_ADD_NAME, CAT_REN_NAME = range(10, 12)

async def start_cat_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("➕ <b>Enter New Category Name:</b>\n(or /cancel to abort)", parse_mode=ParseMode.HTML)
    return CAT_ADD_NAME

async def cat_add_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    success = await db.add_category(name)
    if success:
        text = f"✅ Category <b>{html.escape(name)}</b> created!"
    else:
        text = "⚠️ Failed to create category. It might already exist."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Categories", callback_data="admin_manage_cats")]]))
    return ConversationHandler.END

async def start_cat_ren(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cid = int(query.data.split(":")[1])
    context.user_data["ren_cat_id"] = cid
    await query.message.edit_text("✏️ <b>Enter New Name for this category:</b>", parse_mode=ParseMode.HTML)
    return CAT_REN_NAME

async def cat_ren_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cid = context.user_data.get("ren_cat_id")
    name = update.message.text.strip()
    await db.rename_category(cid, name)
    context.user_data.pop("ren_cat_id", None)
    await update.message.reply_text(f"✅ Category renamed to <b>{html.escape(name)}</b>!", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Categories", callback_data="admin_manage_cats")]]))
    return ConversationHandler.END

# ------------------------------------------------------------------
# 11. Broadcast System
# ------------------------------------------------------------------
BC_MSG, BC_CONFIRM = range(12, 14)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_ids = await db.get_all_user_ids()
    await query.message.edit_text(
        f"📢 <b>Broadcast Message</b>\n\nTarget Users: <b>{len(user_ids)}</b>\n\nSend the message you want to broadcast (Text, Photo, Document):",
        parse_mode=ParseMode.HTML
    )
    return BC_MSG

async def broadcast_msg_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["broadcast_msg_id"] = update.message.message_id
    context.user_data["broadcast_chat_id"] = update.message.chat_id
    user_ids = await db.get_all_user_ids()
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Send", callback_data="bc_send")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")]
    ])
    await update.message.reply_text(
        f"⚠️ <b>Confirm Broadcast?</b>\n\nTarget users: <b>{len(user_ids)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )
    return BC_CONFIRM

async def broadcast_send_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_ids = await db.get_all_user_ids()
    from_chat_id = context.user_data.get("broadcast_chat_id")
    msg_id = context.user_data.get("broadcast_msg_id")

    await query.message.edit_text(f"🚀 Broadcasting message to {len(user_ids)} users... please wait.")
    
    success, failed = 0, 0
    for uid in user_ids:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=from_chat_id, message_id=msg_id)
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    await query.message.reply_text(
        f"📢 <b>Broadcast Complete!</b>\n\n✅ Delivered: {success}\n❌ Blocked/Failed: {failed}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel")]])
    )
    context.user_data.pop("broadcast_msg_id", None)
    context.user_data.pop("broadcast_chat_id", None)
    return ConversationHandler.END

# ------------------------------------------------------------------
# 12. Cancel & Global Error Handling
# ------------------------------------------------------------------
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_book", None)
    context.user_data.pop("edit_book_id", None)
    context.user_data.pop("edit_field", None)
    context.user_data.pop("ren_cat_id", None)
    context.user_data.pop("broadcast_msg_id", None)
    context.user_data.pop("broadcast_chat_id", None)
    
    msg = "❌ Operation cancelled."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="user_home")]]))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="user_home")]]))
    return ConversationHandler.END

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An unexpected error occurred. Please try again later.")
        except Exception:
            pass

# ------------------------------------------------------------------
# 13. Application Initialization & Startup
# ------------------------------------------------------------------
async def async_main():
    await db.init()
    logger.info("📚 Database initialized successfully.")

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    # Conversation: Add Book (Fixed Filters and Fallbacks)
    add_book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_book, pattern="^admin_add_book$")],
        states={
            ADD_CAT: [CallbackQueryHandler(add_book_cat_selected, pattern="^addbk_cat:")],
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_title_received)],
            ADD_DESC: [MessageHandler(filters.TEXT | filters.COMMAND, add_book_desc_received)],
            ADD_AUTHOR: [MessageHandler(filters.TEXT | filters.COMMAND, add_book_author_received)],
            ADD_KEYWORDS: [MessageHandler(filters.TEXT | filters.COMMAND, add_book_keywords_received)],
            ADD_REF: [MessageHandler(filters.TEXT | filters.COMMAND, add_book_ref_received)],
            ADD_FILE: [
                MessageHandler(
                    filters.Document.ALL | filters.AUDIO | filters.VIDEO | filters.PHOTO,
                    add_book_file_received
                )
            ],
            ADD_CONFIRM: [CallbackQueryHandler(add_book_save_execution, pattern="^addbk_save$")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
        ],
        per_user=True,
        per_chat=True,
    )

    # Conversation: Edit Book
    edit_book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_book, pattern="^admin_edit:")],
        states={
            EDIT_SELECT_FIELD: [CallbackQueryHandler(edit_field_selected, pattern="^ed_f:")],
            EDIT_INPUT_VAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_received),
                CallbackQueryHandler(edit_value_received, pattern="^ed_catval:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
        ],
        per_user=True,
        per_chat=True,
    )

    # Conversation: Add Category
    add_cat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_cat_add, pattern="^admin_cat_add$")],
        states={
            CAT_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_add_name_received)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
        ],
        per_user=True,
        per_chat=True,
    )

    # Conversation: Rename Category
    ren_cat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_cat_ren, pattern="^admin_cat_ren:")],
        states={
            CAT_REN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_ren_name_received)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
        ],
        per_user=True,
        per_chat=True,
    )

    # Conversation: Broadcast
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^admin_broadcast$")],
        states={
            BC_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_msg_received)],
            BC_CONFIRM: [CallbackQueryHandler(broadcast_send_exec, pattern="^bc_send$")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
        ],
        per_user=True,
        per_chat=True,
    )

    # Register Handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("home", cmd_home))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CommandHandler("backup", cmd_backup))

    application.add_handler(add_book_conv)
    application.add_handler(edit_book_conv)
    application.add_handler(add_cat_conv)
    application.add_handler(ren_cat_conv)
    application.add_handler(broadcast_conv)

    application.add_handler(CallbackQueryHandler(search_pagination_callback, pattern="^search_page:"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(user_callback_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    application.add_error_handler(global_error_handler)

    logger.info("📚 Islamic Library Bot is starting...")
    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            await application.updater.stop()
            await application.stop()

if __name__ == "__main__":
    asyncio.run(async_main())
