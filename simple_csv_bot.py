import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

import csv_storage
from csv_runtime import (
    get_admin_ids,
    get_owner_ids,
    get_required_setting,
    get_setting,
    is_bootstrap_admin_mode,
    set_profile_setting,
)
from target_store import ensure_target_csv
from user_store import (
    get_all_users,
    get_active_users,
    get_chat_status_text,
    get_display_name,
    get_user_by_id,
    get_user_language,
    get_user_list_text,
    get_users_by_ids,
    increment_chat_count,
    is_user_banned,
    register_user,
    set_user_banned,
    set_user_language,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

ADMIN_IDS = get_admin_ids()
OWNER_IDS = get_owner_ids()
TOKEN = get_required_setting("TOKEN")
DOT_ANIMATION_FRAMES = [".", "..", "...", ".", ".."]
ANON_SENDER_FRAMES = ["📡", "🛰️", "📶", "🛰️"]
ANON_RECEIVER_FRAMES = ["🌙", "⭐", "✨", "⭐"]
ROOT_ADMIN_USERNAMES = {
    name.strip().lower().lstrip("@")
    for name in get_setting("ROOT_ADMINS", "lucifitas,lucifias").split(",")
    if name.strip()
}
PENDING_REQUESTS = {}
ANONYMOUS_REQUESTS = {}
ACTIVE_CHATS = {}
CHAT_MONITORS = {}
ACTIVE_INTERFERING_ADMINS = {}
BOT_JOB_QUEUE = None
RESPONSE_FRAME_INDEX = 0
RESPONSE_FRAME_SETS = {
    "admin": ["👑", "⚡", "🛠", "✨"],
    "chat": ["💬", "🗨️", "📨", "✨"],
    "warning": ["⚠️", "🚨", "🔥", "⚡"],
    "status": ["📊", "📈", "✨", "📉"],
    "welcome": ["🌈", "✨", "🌟", "🫧"],
    "default": ["✨", "💫", "🌟", "✦"],
}
RESPONSE_ANIMATION_FRAMES = DOT_ANIMATION_FRAMES
TEXT = {
    "en": {
        "button_my_id": "🆔 My ID",
        "button_claim_admin": "👑 Claim Admin",
        "button_status": "📊 Status",
        "button_connect_user": "🔗 Connect to User",
        "button_contact_admin": "💬 Contact with Admin",
        "button_start_anonymous_talk": "🎭 Start Anonymous Talk",
        "button_add_target": "➕ Add Target",
        "button_user_lists": "👥 User Lists",
        "button_interfere_chat": "🛠 Interfere In Chat",
        "button_help": "❓ Help",
        "button_cancel": "↩️ Cancel",
        "button_yes": "✅ Yes",
        "button_no": "❌ No",
        "button_end_chat": "🔚 End Chat",
        "button_connect_chat_user": "➕ Connect A User To This Chat",
        "button_language": "🇮🇷 Farsi",
        "title_admin_console": "👑 Admin Console",
        "title_welcome": "✨ Welcome",
        "title_identity": "🆔 Your Identity",
        "title_admin_connected": "🎉 Admin Connected",
        "title_queue_status": "📊 Queue Status",
        "title_connect_user": "🔗 Connect To User",
        "title_contact_admin": "💬 Contact With Admin",
        "title_request_closed": "⌛ Request Closed",
        "title_no_response": "😴 No Response",
        "title_request_expired": "⌛ Request Expired",
        "title_private_request": "💌 Private Request",
        "title_request_failed": "⚠️ Request Failed",
        "title_target_added": "✅ Target Added",
        "title_add_target": "➕ Add Target",
        "title_manage_user": "🛠 User Manager",
        "title_warning": "⚠️ Warning Center",
        "title_root_only": "👑 Root Only",
        "title_anonymous_talk": "🎭 Anonymous Talk",
        "title_anonymous_request": "🎭 Anonymous Request",
        "title_interfere_chat": "🛠 Interfere In Chat",
        "title_conversation_ended": "🔚 Conversation Ended",
        "title_connected": "🎉 Connected",
        "title_chat_started": "💬 Chat Started",
        "title_declined": "❌ Declined",
        "title_request_declined": "❌ Request Declined",
        "title_invalid_format": "⚠️ Invalid Format",
        "title_menu": "🙂 Friendly Reminder",
        "title_language_changed": "🗣🗣 Language Changed",
        "title_start_welcome": "Welcome to Jamal Bot 🗣",
        "admin_ready": "Everything is ready and running smoothly.",
        "user_ready": "You are connected to the private support bot.",
        "you_can_use": "You can use:",
        "use_buttons": "👇 Use the buttons below.",
        "telegram_id": "Your Telegram ID: {user_id}",
        "admin_already_configured": "⚠️ Admin is already configured.",
        "admin_mode_active": "Admin mode is now active for this account.",
        "saved_admin_id": "Saved admin ID: {user_id}",
        "access_denied": "🚫 Access denied.",
        "all_users": "All users: {count}",
        "pending": "Pending: {count}",
        "sent": "Sent: {count}",
        "failed": "Failed: {count}",
        "no_active_users": "😕 No active users found right now.",
        "no_admins": "😕 No admins found right now.",
        "no_manageable_users": "😕 No users are available to manage right now.",
        "choose_active_user": "Choose an active user from the popup buttons below.",
        "choose_admin": "Choose an admin from the popup buttons below.",
        "choose_manage_user": "Choose a user from the popup buttons below to manage them.",
        "manage_user_selected": "Selected user: {target_name}",
        "manage_user_status": "Admin: {admin_status} | Ban: {ban_status}",
        "status_on": "On",
        "status_off": "Off",
        "ban_enabled": "🚫 {target_name} is now banned and cannot start private connections.",
        "ban_removed": "✅ Ban removed for {target_name}.",
        "admin_added": "👑 {target_name} is now an admin.",
        "admin_removed": "➖ {target_name} is no longer an admin.",
        "warning_prompt": "Type the warning message you want the bot to send to {target_name}.",
        "warning_sent": "✅ Your warning was sent to {target_name}.",
        "warning_received": "⚠️ Warning from Jamal Bot:",
        "warning_delivery_failed": "⚠️ Could not send the warning to {target_name}.",
        "warning_canceled": "↩️ Warning message canceled.",
        "warning_empty": "⚠️ Warning message cannot be empty.",
        "banned_cannot_connect": "🚫 You are banned and cannot connect to users right now.",
        "target_is_banned": "🚫 {target_name} is banned and cannot be connected right now.",
        "root_admin_only": "👑 Only root admin can change admin roles.",
        "cannot_ban_root_admin": "👑 Root admin cannot be banned by another admin.",
        "no_active_conversations": "😕 No active user conversations were found.",
        "choose_conversation": "Choose one live conversation from the popup buttons below.",
        "selected_conversation": "Selected conversation: {user_one} <-> {user_two}",
        "chat_closed_by_admin": "🛠 Admin closed this conversation.",
        "admin_joined_chat": "🛠 Admin entered this conversation.",
        "admin_monitoring_started": "You are now inside this conversation. Your messages go to both users.",
        "choose_user_to_keep": "Choose which user should stay connected with you. The other user will be disconnected.",
        "choose_user_for_chat": "Choose a user from the popup buttons below to connect into your current admin chat.",
        "user_kept_with_admin": "🛠 Admin kept {target_name} in chat and disconnected the other user.",
        "chat_user_connected": "➕ {target_name} is now connected to your current chat.",
        "no_users_for_chat_connect": "😕 No users are available to connect into this chat right now.",
        "other_user_disconnected": "🛠 The other user was disconnected by admin.",
        "stop_interfering": "🛠 Stop Interfering",
        "admin_stopped_interfering": "You left the interfered conversation.",
        "no_anonymous_users": "😕 No users were found for anonymous talk right now.",
        "anonymous_sender_pending": "Looking for an anonymous chat\nYour request was sent to {count} users.\nWaiting for the first person to accept.",
        "anonymous_receiver_pending": "Someone wants an anonymous chat.\nAccept or reject below before this request expires.",
        "anonymous_started_sender": "Anonymous chat started successfully.",
        "anonymous_started_receiver": "You accepted and joined the anonymous chat.",
        "anonymous_no_accept": "Nobody accepted your anonymous request.",
        "anonymous_request_rejected": "You rejected the anonymous request.",
        "anonymous_taken_by_other": "Another user accepted this anonymous request first.",
        "anonymous_request_expired_receiver": "This anonymous request has expired.",
        "anonymous_pending_exists": "⚠️ You already have a pending request. Please wait for it to finish.",
        "admins_cannot_anonymous": "👑 Admins cannot use anonymous talk. Use Connect to User instead.",
        "admins_use_connect": "👑 Admins can use Connect to User.",
        "pending_text": "{hourglass} Pending {hourglass}\nWaiting for {target_name} to answer your request.\nThis request closes automatically in 45 seconds.",
        "request_closed_line_1": "{target_name} did not answer in time.",
        "request_closed_line_2": "The target session is now closed.",
        "no_response_line_1": "{target_name} did not respond.",
        "no_response_line_2": "The private request has expired.",
        "request_expired_line": "This private chat request has expired.",
        "admin_private_request": "An admin wants to talk to you privately. Do you want to join?",
        "user_private_request": "{requester_name} wants to contact you privately. Do you want to join?",
        "choose_yes_no": "Please choose Yes or No below.",
        "request_failed_line_1": "Could not deliver the request to {target_name}.",
        "request_failed_self": "You cannot connect to yourself.",
        "request_failed_busy_you": "You are already in an active conversation.",
        "request_failed_busy_target": "That user is already in an active conversation.",
        "request_already_pending_you": "You already have a pending request.",
        "request_already_pending_target": "That user already has a pending request.",
        "usage_addtarget": "ℹ️ Use: /addtarget <telegram_id> <message>",
        "telegram_id_must_be_numeric": "⚠️ telegram_id must be numeric.",
        "message_cannot_be_empty": "⚠️ Message cannot be empty.",
        "target_added_id": "Telegram ID: {telegram_id}",
        "target_added_message": "Message: {message}",
        "add_target_format": "Send the target in this format:",
        "example": "Example:",
        "tap_cancel": "↩️ Tap Cancel to stop.",
        "forward_failed": "⚠️ Failed to forward message: {error}",
        "request_not_active": "⚠️ This request is no longer active.",
        "conversation_started_with": "Conversation started with {target_name}.",
        "chat_started_admin_1": "You are now connected with {target_name}.",
        "chat_started_target_1": "You are now connected privately.",
        "chat_started_2": "Send any message to continue.",
        "declined_line": "{target_name} declined your request.",
        "target_declined": "Target declined the private request.",
        "you_declined": "You declined the private request.",
        "add_target_canceled": "↩️ Add target canceled.",
        "invalid_format_line_1": "Please use:",
        "menu_reminder": "Please use the Telegram buttons below.",
        "language_changed_1": "English mode is now active.",
        "language_changed_2": "All buttons and messages are now in English.",
        "start_subtitle_user": "Choose a button below.",
        "start_subtitle_admin": "Choose a button below. Your admin tools are ready.",
        "button_back_users": "⬅️ Back to Users",
    },
    "fa": {
        "button_my_id": "🆔 شناسه من",
        "button_claim_admin": "👑 فعال سازی ادمین",
        "button_status": "📊 وضعیت",
        "button_connect_user": "🔗 اتصال به کاربر",
        "button_contact_admin": "💬 ارتباط با ادمین",
        "button_start_anonymous_talk": "🎭 شروع گفتگوی ناشناس",
        "button_add_target": "➕ افزودن کاربر",
        "button_user_lists": "👥 لیست کاربران",
        "button_interfere_chat": "🛠 دخالت در گفتگو",
        "button_help": "❓ راهنما",
        "button_cancel": "↩️ انصراف",
        "button_yes": "✅ بله",
        "button_no": "❌ خیر",
        "button_end_chat": "🔚 پایان گفتگو",
        "button_connect_chat_user": "➕ اتصال کاربر به این گفتگو",
        "button_language": "🇬🇧 English",
        "title_admin_console": "👑 پنل ادمین",
        "title_welcome": "✨ خوش آمدید",
        "title_identity": "🆔 شناسه شما",
        "title_admin_connected": "🎉 ادمین فعال شد",
        "title_queue_status": "📊 وضعیت صف",
        "title_connect_user": "🔗 اتصال به کاربر",
        "title_contact_admin": "💬 ارتباط با ادمین",
        "title_request_closed": "⌛ درخواست بسته شد",
        "title_no_response": "😴 بدون پاسخ",
        "title_request_expired": "⌛ درخواست منقضی شد",
        "title_private_request": "💌 درخواست خصوصی",
        "title_request_failed": "⚠️ خطا در درخواست",
        "title_target_added": "✅ کاربر اضافه شد",
        "title_add_target": "➕ افزودن کاربر",
        "title_manage_user": "🛠 مدیریت کاربر",
        "title_warning": "⚠️ مرکز هشدار",
        "title_root_only": "👑 فقط روت",
        "title_anonymous_talk": "🎭 گفتگوی ناشناس",
        "title_anonymous_request": "🎭 درخواست ناشناس",
        "title_interfere_chat": "🛠 دخالت در گفتگو",
        "title_conversation_ended": "🔚 گفتگو پایان یافت",
        "title_connected": "🎉 اتصال برقرار شد",
        "title_chat_started": "💬 گفتگو شروع شد",
        "title_declined": "❌ رد شد",
        "title_request_declined": "❌ درخواست رد شد",
        "title_invalid_format": "⚠️ فرمت نامعتبر",
        "title_menu": "🙂 یادآوری",
        "title_language_changed": "🗣🗣 زبان تغییر کرد",
        "title_start_welcome": "به ربات Jamal خوش آمدید 🗣",
        "admin_ready": "همه چیز آماده است و ربات به خوبی کار می کند.",
        "user_ready": "شما به ربات پشتیبانی خصوصی متصل هستید.",
        "you_can_use": "امکانات شما:",
        "use_buttons": "👇 از دکمه های زیر استفاده کنید.",
        "telegram_id": "شناسه تلگرام شما: {user_id}",
        "admin_already_configured": "⚠️ ادمین قبلا تنظیم شده است.",
        "admin_mode_active": "حالت ادمین برای این حساب فعال شد.",
        "saved_admin_id": "شناسه ذخیره شده ادمین: {user_id}",
        "access_denied": "🚫 دسترسی ندارید.",
        "all_users": "همه کاربران: {count}",
        "pending": "در انتظار: {count}",
        "sent": "ارسال شده: {count}",
        "failed": "ناموفق: {count}",
        "no_active_users": "😕 فعلا کاربر فعالی پیدا نشد.",
        "no_admins": "😕 فعلا ادمینی پیدا نشد.",
        "no_manageable_users": "😕 فعلا کاربری برای مدیریت پیدا نشد.",
        "choose_active_user": "یک کاربر فعال را از دکمه های پاپ آپ زیر انتخاب کنید.",
        "choose_admin": "یک ادمین را از دکمه های پاپ آپ زیر انتخاب کنید.",
        "choose_manage_user": "یک کاربر را از دکمه های پاپ آپ زیر انتخاب کنید تا مدیریت شود.",
        "manage_user_selected": "کاربر انتخاب شده: {target_name}",
        "manage_user_status": "ادمین: {admin_status} | بن: {ban_status}",
        "status_on": "فعال",
        "status_off": "غیرفعال",
        "ban_enabled": "🚫 {target_name} اکنون بن شد و نمی تواند گفتگوی خصوصی را شروع کند.",
        "ban_removed": "✅ بن {target_name} برداشته شد.",
        "admin_added": "👑 {target_name} اکنون ادمین است.",
        "admin_removed": "➖ {target_name} دیگر ادمین نیست.",
        "warning_prompt": "پیام هشداری را که می خواهید ربات برای {target_name} بفرستد تایپ کنید.",
        "warning_sent": "✅ هشدار شما برای {target_name} ارسال شد.",
        "warning_received": "⚠️ هشدار از طرف ربات Jamal:",
        "warning_delivery_failed": "⚠️ ارسال هشدار به {target_name} ممکن نشد.",
        "warning_canceled": "↩️ پیام هشدار لغو شد.",
        "warning_empty": "⚠️ متن هشدار نمی تواند خالی باشد.",
        "banned_cannot_connect": "🚫 شما بن شده اید و فعلا نمی توانید به کاربران متصل شوید.",
        "target_is_banned": "🚫 {target_name} بن شده است و فعلا قابل اتصال نیست.",
        "root_admin_only": "👑 فقط ادمین روت می تواند نقش ادمین را تغییر دهد.",
        "cannot_ban_root_admin": "👑 هیچ ادمینی نمی تواند ادمین روت را بن کند.",
        "no_active_conversations": "😕 فعلا گفتگوی فعالی بین کاربران پیدا نشد.",
        "choose_conversation": "یکی از گفتگوهای فعال را از دکمه های پاپ آپ زیر انتخاب کنید.",
        "selected_conversation": "گفتگوی انتخاب شده: {user_one} <-> {user_two}",
        "chat_closed_by_admin": "🛠 ادمین این گفتگو را بست.",
        "admin_joined_chat": "🛠 ادمین وارد این گفتگو شد.",
        "admin_monitoring_started": "اکنون داخل این گفتگو هستید. پیام های شما برای هر دو کاربر ارسال می شود.",
        "choose_user_to_keep": "انتخاب کنید کدام کاربر با شما بماند. کاربر دیگر قطع می شود.",
        "choose_user_for_chat": "یک کاربر را از دکمه های پاپ آپ زیر انتخاب کنید تا به گفتگوی فعلی شما وصل شود.",
        "user_kept_with_admin": "🛠 ادمین {target_name} را نگه داشت و کاربر دیگر را قطع کرد.",
        "chat_user_connected": "➕ {target_name} اکنون به گفتگوی فعلی شما وصل شد.",
        "no_users_for_chat_connect": "😕 فعلا کاربری برای اتصال به این گفتگو پیدا نشد.",
        "other_user_disconnected": "🛠 کاربر دیگر توسط ادمین قطع شد.",
        "stop_interfering": "🛠 توقف دخالت",
        "admin_stopped_interfering": "شما از گفتگوی دخالتی خارج شدید.",
        "no_anonymous_users": "😕 فعلا کاربری برای گفتگوی ناشناس پیدا نشد.",
        "anonymous_sender_pending": "در حال پیدا کردن گفتگوی ناشناس\nدرخواست شما برای {count} کاربر ارسال شد.\nمنتظر اولین پذیرش هستیم.",
        "anonymous_receiver_pending": "یک نفر گفتگوی ناشناس می خواهد.\nپایین همین پیام قبول یا رد را بزنید.",
        "anonymous_started_sender": "گفتگوی ناشناس با موفقیت شروع شد.",
        "anonymous_started_receiver": "شما درخواست گفتگوی ناشناس را پذیرفتید.",
        "anonymous_no_accept": "هیچکس درخواست ناشناس شما را نپذیرفت.",
        "anonymous_request_rejected": "شما درخواست ناشناس را رد کردید.",
        "anonymous_taken_by_other": "یک کاربر دیگر زودتر این درخواست ناشناس را پذیرفت.",
        "anonymous_request_expired_receiver": "این درخواست گفتگوی ناشناس منقضی شد.",
        "anonymous_pending_exists": "⚠️ شما از قبل یک درخواست در انتظار دارید. لطفا صبر کنید.",
        "admins_cannot_anonymous": "👑 ادمین ها نمی توانند از گفتگوی ناشناس استفاده کنند. از اتصال به کاربر استفاده کنید.",
        "admins_use_connect": "👑 ادمین ها باید از دکمه اتصال به کاربر استفاده کنند.",
        "pending_text": "{hourglass} در انتظار {hourglass}\nمنتظر پاسخ {target_name} هستیم.\nاین درخواست بعد از 45 ثانیه خودکار بسته می شود.",
        "request_closed_line_1": "{target_name} در زمان مشخص پاسخ نداد.",
        "request_closed_line_2": "جلسه هدف بسته شد.",
        "no_response_line_1": "{target_name} پاسخی نداد.",
        "no_response_line_2": "درخواست گفتگوی خصوصی منقضی شد.",
        "request_expired_line": "این درخواست گفتگوی خصوصی منقضی شده است.",
        "admin_private_request": "یک ادمین می خواهد خصوصی با شما صحبت کند. مایل هستید وارد شوید؟",
        "user_private_request": "{requester_name} می خواهد خصوصی با شما صحبت کند. مایل هستید وارد شوید؟",
        "choose_yes_no": "لطفا از پایین بله یا خیر را انتخاب کنید.",
        "request_failed_line_1": "ارسال درخواست برای {target_name} ممکن نشد.",
        "request_failed_self": "شما نمی توانید خودتان را انتخاب کنید.",
        "request_failed_busy_you": "شما هم اکنون در یک گفتگوی فعال هستید.",
        "request_failed_busy_target": "این کاربر هم اکنون در یک گفتگوی فعال است.",
        "request_already_pending_you": "شما از قبل یک درخواست در انتظار دارید.",
        "request_already_pending_target": "برای این کاربر از قبل یک درخواست در انتظار وجود دارد.",
        "usage_addtarget": "ℹ️ استفاده: /addtarget <telegram_id> <message>",
        "telegram_id_must_be_numeric": "⚠️ شناسه تلگرام باید عددی باشد.",
        "message_cannot_be_empty": "⚠️ متن پیام نمی تواند خالی باشد.",
        "target_added_id": "شناسه تلگرام: {telegram_id}",
        "target_added_message": "پیام: {message}",
        "add_target_format": "کاربر را با این فرمت ارسال کنید:",
        "example": "نمونه:",
        "tap_cancel": "↩️ برای توقف روی انصراف بزنید.",
        "forward_failed": "⚠️ ارسال پیام انجام نشد: {error}",
        "request_not_active": "⚠️ این درخواست دیگر فعال نیست.",
        "conversation_started_with": "گفتگو با {target_name} شروع شد.",
        "chat_started_admin_1": "اکنون به {target_name} متصل شدید.",
        "chat_started_target_1": "اکنون گفتگوی خصوصی شما شروع شد.",
        "chat_started_2": "برای ادامه هر پیامی ارسال کنید.",
        "declined_line": "{target_name} درخواست شما را رد کرد.",
        "target_declined": "کاربر درخواست گفتگوی خصوصی را رد کرد.",
        "you_declined": "شما درخواست گفتگوی خصوصی را رد کردید.",
        "add_target_canceled": "↩️ افزودن کاربر لغو شد.",
        "invalid_format_line_1": "لطفا از این فرمت استفاده کنید:",
        "menu_reminder": "لطفا از دکمه های تلگرام در پایین استفاده کنید.",
        "language_changed_1": "حالت فارسی فعال شد.",
        "language_changed_2": "همه دکمه ها و پیام ها اکنون فارسی هستند.",
        "start_subtitle_user": "یکی از دکمه های زیر را انتخاب کنید.",
        "start_subtitle_admin": "یکی از دکمه های زیر را انتخاب کنید. ابزارهای ادمین شما آماده هستند.",
        "button_back_users": "⬅️ بازگشت به کاربران",
    },
}


def t(lang, key, **kwargs):
    language = lang if lang in TEXT else "en"
    return TEXT[language][key].format(**kwargs)


def button(lang, key):
    return t(lang, f"button_{key}")


def get_lang(user_id):
    return get_user_language(user_id, default="en")


def is_button_text(text, key):
    return text in {button("en", key), button("fa", key)}


def is_admin(user_id):
    return user_id in ADMIN_IDS


def refresh_admin_ids():
    global ADMIN_IDS
    ADMIN_IDS = get_admin_ids()


def save_admin_ids(admin_ids):
    normalized_ids = []
    seen = set()
    for value in admin_ids:
        try:
            user_id = int(value)
        except:
            continue
        if user_id in seen:
            continue
        seen.add(user_id)
        normalized_ids.append(user_id)
    set_profile_setting("ADMINS", ",".join(str(user_id) for user_id in normalized_ids))
    refresh_admin_ids()


def set_admin_status(user_id, make_admin):
    admin_ids = list(ADMIN_IDS)
    if make_admin:
        if user_id not in admin_ids:
            admin_ids.append(user_id)
    else:
        admin_ids = [admin_id for admin_id in admin_ids if admin_id != user_id]
    save_admin_ids(admin_ids)


def normalize_username(username):
    return str(username or "").strip().lower().lstrip("@")


def is_owner(user_id):
    return str(user_id).strip() in {str(owner_id) for owner_id in OWNER_IDS}


def is_root_admin(user_id=None, telegram_user=None):
    if (user_id is not None and is_owner(user_id)) or (telegram_user is not None and is_owner(telegram_user.id)):
        return True
    usernames = set()
    if telegram_user is not None:
        usernames.add(normalize_username(getattr(telegram_user, "username", "")))
    if user_id is not None:
        row = get_user_by_id(user_id)
        if row:
            usernames.add(normalize_username(row.get("username", "")))
    return any(username in ROOT_ADMIN_USERNAMES for username in usernames if username)


def ensure_root_admin_unbanned():
    for row in get_all_users():
        if normalize_username(row.get("username", "")) in ROOT_ADMIN_USERNAMES:
            if row.get("is_banned", "").strip() == "1":
                set_user_banned(row.get("user_id", "").strip(), False)


def is_effectively_banned(user_id):
    return (not is_root_admin(user_id)) and is_user_banned(user_id)


def has_direct_pending_request(user_id):
    for request in PENDING_REQUESTS.values():
        if request.get("status") != "pending":
            continue
        if request.get("admin_id") == user_id or request.get("target_id") == user_id:
            return True
    return False


def has_anonymous_pending_request(user_id):
    for request in ANONYMOUS_REQUESTS.values():
        if request.get("status") != "pending":
            continue
        if request.get("requester_id") == user_id:
            return True
        if user_id in request.get("receiver_messages", {}):
            return True
    return False


def get_available_anonymous_users(requester_id):
    result = []
    for row in get_all_users():
        user_id_text = row.get("user_id", "").strip()
        if not user_id_text or not user_id_text.isdigit():
            continue
        user_id = int(user_id_text)
        if user_id == requester_id or is_admin(user_id):
            continue
        if is_effectively_banned(user_id):
            continue
        result.append(row)
    return result


def get_chat_pair_key(user_one_id, user_two_id):
    return tuple(sorted((int(user_one_id), int(user_two_id))))


def get_interferable_chat_pairs():
    pairs = []
    seen = set()
    for user_id, partner_id in ACTIVE_CHATS.items():
        if is_admin(user_id) or is_admin(partner_id):
            continue
        pair_key = get_chat_pair_key(user_id, partner_id)
        if pair_key in seen:
            continue
        seen.add(pair_key)
        pairs.append(pair_key)
    return sorted(pairs)


def get_monitors_for_pair(user_one_id, user_two_id):
    return CHAT_MONITORS.get(get_chat_pair_key(user_one_id, user_two_id), set())


def clear_admin_interference(admin_id):
    pair_key = ACTIVE_INTERFERING_ADMINS.pop(admin_id, None)
    if not pair_key:
        return
    monitors = CHAT_MONITORS.get(pair_key, set())
    if admin_id in monitors:
        monitors.discard(admin_id)
    if monitors:
        CHAT_MONITORS[pair_key] = monitors
    else:
        CHAT_MONITORS.pop(pair_key, None)


def clear_chat_monitors(user_one_id, user_two_id):
    pair_key = get_chat_pair_key(user_one_id, user_two_id)
    monitors = CHAT_MONITORS.pop(pair_key, set())
    for admin_id in list(monitors):
        ACTIVE_INTERFERING_ADMINS.pop(admin_id, None)
    return monitors


def build_interfere_chat_keyboard(lang):
    return ReplyKeyboardMarkup([[t(lang, "stop_interfering")]], resize_keyboard=True)


def get_main_keyboard(user_id=None):
    lang = get_lang(user_id) if user_id is not None else "en"
    rows = [[button(lang, "my_id"), button(lang, "claim_admin")]]
    if user_id is not None and is_admin(user_id):
        rows.append([button(lang, "status"), button(lang, "connect_user")])
        rows.append([button(lang, "add_target"), button(lang, "user_lists")])
        rows.append([button(lang, "interfere_chat")])
    else:
        rows.append([button(lang, "contact_admin"), button(lang, "start_anonymous_talk")])
    rows.append([button(lang, "help"), button(lang, "language")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def get_target_decision_keyboard(lang):
    return ReplyKeyboardMarkup([[button(lang, "yes"), button(lang, "no")]], resize_keyboard=True)


def get_chat_keyboard(lang, user_id=None):
    if user_id is not None and is_admin(user_id):
        return ReplyKeyboardMarkup(
            [
                [button(lang, "connect_chat_user")],
                [button(lang, "end_chat")],
            ],
            resize_keyboard=True,
        )
    return ReplyKeyboardMarkup([[button(lang, "end_chat")]], resize_keyboard=True)


def get_warning_keyboard(lang):
    return ReplyKeyboardMarkup([[button(lang, "cancel")]], resize_keyboard=True)


def get_connectable_chat_users(current_admin_id, current_partner_id):
    users = []
    for row in get_all_users(limit=50):
        user_id_text = row.get("user_id", "").strip()
        if not user_id_text or not user_id_text.isdigit():
            continue
        user_id = int(user_id_text)
        if user_id in {int(current_admin_id), int(current_partner_id)}:
            continue
        if is_admin(user_id) or is_effectively_banned(user_id):
            continue
        if user_id in ACTIVE_CHATS or has_direct_pending_request(user_id) or has_anonymous_pending_request(user_id):
            continue
        users.append(row)
    return users


def build_connect_chat_user_markup(admin_id, current_partner_id, lang):
    buttons = []
    for row in get_connectable_chat_users(admin_id, current_partner_id):
        user_id = row.get("user_id", "").strip()
        label = get_display_name(row, include_id=True)
        buttons.append([InlineKeyboardButton(f"👤 {label}", callback_data=f"admin_chat:swap:{current_partner_id}:{user_id}")])
    if not buttons:
        return None
    return InlineKeyboardMarkup(buttons)


def get_conversation_label(user_one_id, user_two_id):
    rows = get_users_by_ids([user_one_id, user_two_id])
    by_id = {int(row.get("user_id", "0")): row for row in rows if row.get("user_id", "").isdigit()}
    user_one_name = get_display_name(by_id.get(int(user_one_id), {"user_id": str(user_one_id)}))
    user_two_name = get_display_name(by_id.get(int(user_two_id), {"user_id": str(user_two_id)}))
    return user_one_name, user_two_name


def build_interfere_actions_markup(user_one_id, user_two_id, lang):
    enter_label = "🛠 Enter Conversation" if lang == "en" else "🛠 ورود به گفتگو"
    close_label = "🔚 Close Conversation" if lang == "en" else "🔚 بستن گفتگو"
    keep_label = "👤 Keep One User" if lang == "en" else "👤 نگه داشتن یک کاربر"
    back_label = t(lang, "button_back_users")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(enter_label, callback_data=f"interfere_chat:join:{user_one_id}:{user_two_id}")],
        [InlineKeyboardButton(close_label, callback_data=f"interfere_chat:close:{user_one_id}:{user_two_id}")],
        [InlineKeyboardButton(keep_label, callback_data=f"interfere_chat:keep_menu:{user_one_id}:{user_two_id}")],
        [InlineKeyboardButton(back_label, callback_data="interfere_chat:list")],
    ])


def build_keep_user_markup(user_one_id, user_two_id, lang):
    user_one_name, user_two_name = get_conversation_label(user_one_id, user_two_id)
    back_label = t(lang, "button_back_users")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👤 {user_one_name}", callback_data=f"interfere_chat:keep:{user_one_id}:{user_two_id}:{user_one_id}")],
        [InlineKeyboardButton(f"👤 {user_two_name}", callback_data=f"interfere_chat:keep:{user_one_id}:{user_two_id}:{user_two_id}")],
        [InlineKeyboardButton(back_label, callback_data=f"interfere_chat:select:{user_one_id}:{user_two_id}")],
    ])


def render_interfere_chat_list(update, context):
    ensure_registered(update)
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    if not is_admin(user_id):
        if update.callback_query:
            return update.callback_query.edit_message_text(t(lang, "access_denied"))
        return reply_with_menu(update.message, t(lang, "access_denied"))
    pairs = get_interferable_chat_pairs()
    if not pairs:
        if update.callback_query:
            return update.callback_query.edit_message_text(t(lang, "no_active_conversations"))
        return reply_with_menu(update.message, t(lang, "no_active_conversations"))
    keyboard_rows = []
    for user_one_id, user_two_id in pairs[:20]:
        user_one_name, user_two_name = get_conversation_label(user_one_id, user_two_id)
        keyboard_rows.append([
            InlineKeyboardButton(
                f"💬 {user_one_name} <-> {user_two_name}",
                callback_data=f"interfere_chat:select:{user_one_id}:{user_two_id}",
            )
        ])
    text = format_panel(
        t(lang, "title_interfere_chat"),
        [
            t(lang, "choose_conversation"),
        ],
    )
    if update.callback_query:
        return edit_animated_text(
            context.bot,
            update.callback_query.message.chat_id,
            update.callback_query.message.message_id,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard_rows),
        )
    return reply_animated_text(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard_rows))


def render_interfere_actions(query, user_one_id, user_two_id):
    lang = get_lang(query.from_user.id)
    if ACTIVE_CHATS.get(int(user_one_id)) != int(user_two_id) or ACTIVE_CHATS.get(int(user_two_id)) != int(user_one_id):
        return query.edit_message_text(t(lang, "no_active_conversations"))
    user_one_name, user_two_name = get_conversation_label(user_one_id, user_two_id)
    return edit_animated_text(
        query.bot,
        query.message.chat_id,
        query.message.message_id,
        format_panel(
            t(lang, "title_interfere_chat"),
            [
                t(lang, "selected_conversation", user_one=user_one_name, user_two=user_two_name),
            ],
        ),
        reply_markup=build_interfere_actions_markup(user_one_id, user_two_id, lang),
    )


def get_response_frame_set(title):
    lower_title = str(title or "").lower()
    if "admin" in lower_title or "ادمین" in lower_title or "👑" in lower_title or "🛠" in lower_title:
        return RESPONSE_FRAME_SETS["admin"]
    if "warning" in lower_title or "هشدار" in lower_title or "⚠️" in lower_title:
        return RESPONSE_FRAME_SETS["warning"]
    if "chat" in lower_title or "conversation" in lower_title or "گفتگو" in lower_title or "💬" in lower_title:
        return RESPONSE_FRAME_SETS["chat"]
    if "status" in lower_title or "وضعیت" in lower_title or "📊" in lower_title:
        return RESPONSE_FRAME_SETS["status"]
    if "welcome" in lower_title or "خوش آمد" in lower_title:
        return RESPONSE_FRAME_SETS["welcome"]
    return RESPONSE_FRAME_SETS["default"]


def decorate_title(title):
    global RESPONSE_FRAME_INDEX
    frame_set = get_response_frame_set(title)
    frame = frame_set[RESPONSE_FRAME_INDEX % len(frame_set)]
    RESPONSE_FRAME_INDEX += 1
    return f"{frame} {title} {frame}"


def format_panel(title, lines, hint=None):
    output = [decorate_title(title)]
    if lines:
        output.append("")
        output.extend(lines)
    if hint:
        output.extend(["", hint])
    return "\n".join(output)


def ensure_panel_text(user_id, text):
    if text is None:
        return text
    lines = str(text).splitlines()
    if len(lines) >= 2 and lines[1] == "":
        return text
    lang = get_lang(user_id) if user_id is not None else "en"
    return format_panel(t(lang, "title_menu"), [str(text)])


def append_animation_suffix(text, step):
    lines = str(text).splitlines()
    suffix = RESPONSE_ANIMATION_FRAMES[step % len(RESPONSE_ANIMATION_FRAMES)]
    if not lines:
        return suffix

    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip():
            lines[index] = f"{lines[index]} {suffix}"
            return "\n".join(lines)

    lines[-1] = suffix
    return "\n".join(lines)


def build_response_animation_text(final_text, step):
    return append_animation_suffix(final_text, step)


def animate_response_job(context):
    data = context.job.context
    final_text = data["final_text"]
    reply_markup = data.get("reply_markup")
    chat_id = data["chat_id"]
    message_id = data["message_id"]
    step = data["step"]
    try:
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=build_response_animation_text(final_text, step),
            reply_markup=reply_markup,
        )
    except:
        pass


def schedule_response_animation(bot, chat_id, message_id, final_text, reply_markup=None):
    if BOT_JOB_QUEUE is None or message_id is None:
        return
    for step in range(1, len(RESPONSE_ANIMATION_FRAMES)):
        BOT_JOB_QUEUE.run_once(
            animate_response_job,
            when=0.18 * step,
            context={
                "chat_id": chat_id,
                "message_id": message_id,
                "final_text": final_text,
                "reply_markup": reply_markup,
                "step": step,
            },
            name=f"response-anim-{chat_id}-{message_id}-{step}",
        )
    BOT_JOB_QUEUE.run_once(
        animate_response_job,
        when=0.18 * len(RESPONSE_ANIMATION_FRAMES),
        context={
            "chat_id": chat_id,
            "message_id": message_id,
            "final_text": final_text,
            "reply_markup": reply_markup,
            "step": len(RESPONSE_ANIMATION_FRAMES) - 1,
        },
        name=f"response-anim-{chat_id}-{message_id}-final",
    )


def reply_animated_text(message, text, reply_markup=None):
    user_id = message.from_user.id if message and message.from_user else None
    final_text = ensure_panel_text(user_id, text)
    response = message.reply_text(
        build_response_animation_text(final_text, 0),
        reply_markup=reply_markup,
    )
    schedule_response_animation(message.bot, message.chat_id, response.message_id, final_text, reply_markup)
    return response


def send_animated_text(bot, chat_id, text, reply_markup=None):
    final_text = ensure_panel_text(chat_id, text)
    response = bot.send_message(
        chat_id=chat_id,
        text=build_response_animation_text(final_text, 0),
        reply_markup=reply_markup,
    )
    schedule_response_animation(bot, chat_id, response.message_id, final_text, reply_markup)
    return response


def edit_animated_text(bot, chat_id, message_id, text, reply_markup=None):
    final_text = ensure_panel_text(chat_id, text)
    response = bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=build_response_animation_text(final_text, 0),
        reply_markup=reply_markup,
    )
    schedule_response_animation(bot, chat_id, message_id, final_text, reply_markup)
    return response


def reply_with_menu(message, text):
    user_id = message.from_user.id if message and message.from_user else None
    return reply_animated_text(message, text, reply_markup=get_main_keyboard(user_id))


def send_menu_message(bot, chat_id, text):
    return send_animated_text(bot, chat_id, text, reply_markup=get_main_keyboard(chat_id))


def ensure_registered(update):
    if update and update.effective_user:
        register_user(
            update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )


def build_manage_users_keyboard(current_user_id):
    keyboard_rows = []
    for row in get_all_users(limit=30):
        user_id = row.get("user_id", "").strip()
        if not user_id or user_id == str(current_user_id):
            continue
        label = get_display_name(row, include_id=True)
        keyboard_rows.append([InlineKeyboardButton(f"👤 {label}", callback_data=f"manage_user:select:{user_id}")])
    return keyboard_rows


def build_manage_actions_keyboard(lang, target_user_id, current_user_id):
    target_user_id = int(target_user_id)
    buttons = []
    ban_label = "🚫 Ban User" if lang == "en" else "🚫 بن کاربر"
    unban_label = "✅ Remove From Ban" if lang == "en" else "✅ حذف از بن"
    add_admin_label = "👑 Add As Admin" if lang == "en" else "👑 افزودن ادمین"
    remove_admin_label = "➖ Remove As Admin" if lang == "en" else "➖ حذف ادمین"
    if not is_root_admin(target_user_id):
        if is_effectively_banned(target_user_id):
            buttons.append([InlineKeyboardButton(unban_label, callback_data=f"manage_user:action:unban:{target_user_id}")])
        else:
            buttons.append([InlineKeyboardButton(ban_label, callback_data=f"manage_user:action:ban:{target_user_id}")])
    if is_root_admin(current_user_id) and not is_owner(target_user_id):
        if is_admin(target_user_id):
            buttons.append([InlineKeyboardButton(remove_admin_label, callback_data=f"manage_user:action:remove_admin:{target_user_id}")])
        else:
            buttons.append([InlineKeyboardButton(add_admin_label, callback_data=f"manage_user:action:add_admin:{target_user_id}")])
    warning_label = "⚠️ Send Warning" if lang == "en" else "⚠️ ارسال هشدار"
    buttons.append([InlineKeyboardButton(warning_label, callback_data=f"manage_user:action:warn:{target_user_id}")])
    buttons.append([InlineKeyboardButton(t(lang, "button_back_users"), callback_data="manage_user:list")])
    return InlineKeyboardMarkup(buttons)


def render_manage_users(update, context):
    ensure_registered(update)
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    if not is_admin(user_id):
        if update.callback_query:
            return update.callback_query.edit_message_text(t(lang, "access_denied"))
        return reply_with_menu(update.message, t(lang, "access_denied"))
    keyboard_rows = build_manage_users_keyboard(user_id)
    if not keyboard_rows:
        if update.callback_query:
            return update.callback_query.edit_message_text(t(lang, "no_manageable_users"))
        return reply_with_menu(update.message, t(lang, "no_manageable_users"))
    text = format_panel(
        t(lang, "title_add_target"),
        [
            t(lang, "choose_manage_user"),
        ],
    )
    if update.callback_query:
        return edit_animated_text(
            context.bot,
            update.callback_query.message.chat_id,
            update.callback_query.message.message_id,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard_rows),
        )
    return reply_animated_text(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard_rows))


def render_manage_actions(query, user_id):
    lang = get_lang(query.from_user.id)
    row = get_user_by_id(user_id)
    if not row:
        return query.edit_message_text(t(lang, "no_manageable_users"))
    target_name = get_display_name(row)
    admin_status = t(lang, "status_on") if is_admin(int(user_id)) else t(lang, "status_off")
    ban_status = t(lang, "status_off") if is_root_admin(user_id) else (
        t(lang, "status_on") if is_effectively_banned(user_id) else t(lang, "status_off")
    )
    return edit_animated_text(
        query.bot,
        query.message.chat_id,
        query.message.message_id,
        format_panel(
            t(lang, "title_manage_user"),
            [
                t(lang, "manage_user_selected", target_name=target_name),
                t(lang, "manage_user_status", admin_status=admin_status, ban_status=ban_status),
            ],
        ),
        reply_markup=build_manage_actions_keyboard(lang, user_id, query.from_user.id),
    )


def switch_language(update, context):
    ensure_registered(update)
    current_lang = get_lang(update.effective_user.id)
    next_lang = "fa" if current_lang == "en" else "en"
    set_user_language(update.effective_user.id, next_lang)
    reply_with_menu(
        update.message,
        format_panel(
            t(next_lang, "title_language_changed"),
            [
                t(next_lang, "language_changed_1"),
                t(next_lang, "language_changed_2"),
            ],
        ),
    )


def start(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if is_admin(update.effective_user.id):
        message = format_panel(
            t(lang, "title_start_welcome"),
            [
                t(lang, "start_subtitle_admin"),
            ],
        )
    else:
        message = format_panel(
            t(lang, "title_start_welcome"),
            [
                t(lang, "start_subtitle_user"),
            ],
        )
    reply_with_menu(update.message, message)


def help_command(update, context):
    return start(update, context)


def myid_command(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    reply_with_menu(
        update.message,
        format_panel(
            t(lang, "title_identity"),
            [
                t(lang, "telegram_id", user_id=update.effective_user.id),
            ],
        ),
    )


def claimadmin_command(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if not is_bootstrap_admin_mode() and not is_admin(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "admin_already_configured"))

    set_admin_status(update.effective_user.id, True)
    reply_with_menu(
        update.message,
        format_panel(
            t(lang, "title_admin_connected"),
            [
                t(lang, "admin_mode_active"),
                t(lang, "saved_admin_id", user_id=update.effective_user.id),
            ],
        )
    )


def status(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if not is_admin(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "access_denied"))
    reply_with_menu(update.message, get_chat_status_text(language=lang))


def start_interfere_chat(update, context):
    return render_interfere_chat_list(update, context)


def start_connect_user(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if not is_admin(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "access_denied"))
    if is_effectively_banned(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "banned_cannot_connect"))
    if has_anonymous_pending_request(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "anonymous_pending_exists"))
    users = get_active_users(ADMIN_IDS)
    if not users:
        return reply_with_menu(update.message, t(lang, "no_active_users"))

    keyboard_rows = []
    for row in users[:20]:
        label = get_display_name(row)
        keyboard_rows.append(
            [InlineKeyboardButton(f"{label} | {row['user_id']}", callback_data=f"request_chat:user:{row['user_id']}")]
        )

    return reply_animated_text(
        update.message,
        format_panel(
            t(lang, "title_connect_user"),
            [
                t(lang, "choose_active_user"),
            ],
        ),
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )


def start_contact_admin(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if is_admin(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "admins_use_connect"))
    if is_effectively_banned(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "banned_cannot_connect"))
    if has_anonymous_pending_request(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "anonymous_pending_exists"))
    admin_rows = get_users_by_ids(ADMIN_IDS)
    if not admin_rows:
        return reply_with_menu(update.message, t(lang, "no_admins"))

    keyboard_rows = []
    for row in admin_rows[:20]:
        keyboard_rows.append(
            [InlineKeyboardButton(get_display_name(row), callback_data=f"request_chat:admin:{row['user_id']}")]
        )

    return reply_animated_text(
        update.message,
        format_panel(
            t(lang, "title_contact_admin"),
            [
                t(lang, "choose_admin"),
            ],
        ),
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )


def start_anonymous_talk(update, context):
    ensure_registered(update)
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    if is_admin(user_id):
        return reply_with_menu(update.message, t(lang, "admins_cannot_anonymous"))
    if is_effectively_banned(user_id):
        return reply_with_menu(update.message, t(lang, "banned_cannot_connect"))
    if user_id in ACTIVE_CHATS or has_direct_pending_request(user_id) or has_anonymous_pending_request(user_id):
        return reply_with_menu(update.message, t(lang, "anonymous_pending_exists"))

    targets = get_available_anonymous_users(user_id)
    if not targets:
        return reply_with_menu(update.message, t(lang, "no_anonymous_users"))

    request_id = f"anon_{user_id}"
    request = {
        "request_id": request_id,
        "requester_id": user_id,
        "requester_lang": lang,
        "status": "pending",
        "sender_step": 0,
        "receiver_step": 0,
        "receiver_messages": {},
        "receiver_languages": {},
    }
    sender_message = update.message.reply_text(
        build_anonymous_sender_text(request),
        reply_markup=get_main_keyboard(user_id),
    )
    request["sender_message_id"] = sender_message.message_id

    delivered_count = 0
    for row in targets:
        target_id = int(row["user_id"])
        target_lang = get_lang(target_id)
        try:
            receiver_message = context.bot.send_message(
                chat_id=target_id,
                text=format_panel(
                    t(target_lang, "title_anonymous_request"),
                    [
                        t(target_lang, "anonymous_receiver_pending", animation=ANON_RECEIVER_FRAMES[0]),
                    ],
                ),
                reply_markup=get_anonymous_response_keyboard(target_lang, request_id),
            )
        except:
            continue
        request["receiver_messages"][target_id] = receiver_message.message_id
        request["receiver_languages"][target_id] = target_lang
        delivered_count += 1

    if delivered_count == 0:
        try:
            context.bot.edit_message_text(
                chat_id=user_id,
                message_id=request["sender_message_id"],
                text=format_panel(
                    t(lang, "title_anonymous_talk"),
                    [
                        t(lang, "no_anonymous_users"),
                    ],
                ),
            )
        except:
            pass
        return reply_with_menu(update.message, t(lang, "no_anonymous_users"))

    ANONYMOUS_REQUESTS[request_id] = request
    context.job_queue.run_repeating(
        anonymous_pending_animation_job,
        interval=0.6,
        first=0.6,
        context={"request_id": request_id},
        name=f"anonymous-pending-{request_id}",
    )
    context.job_queue.run_once(
        anonymous_timeout_job,
        when=45,
        context={"request_id": request_id},
        name=f"anonymous-timeout-{request_id}",
    )
    return sender_message


def get_anonymous_response_keyboard(lang, request_id):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(button(lang, "yes"), callback_data=f"anonymous_reply:accept:{request_id}"),
            InlineKeyboardButton(button(lang, "no"), callback_data=f"anonymous_reply:reject:{request_id}"),
        ]]
    )


def build_anonymous_sender_text(request):
    lang = request.get("requester_lang", "en")
    text = format_panel(
        t(lang, "title_anonymous_talk"),
        [
            t(lang, "anonymous_sender_pending", count=len(request.get("receiver_messages", {}))),
        ],
    )
    return append_animation_suffix(text, request.get("sender_step", 0))


def build_anonymous_receiver_text(request, receiver_id):
    lang = request.get("receiver_languages", {}).get(receiver_id, "en")
    text = format_panel(
        t(lang, "title_anonymous_request"),
        [
            t(lang, "anonymous_receiver_pending"),
        ],
    )
    return append_animation_suffix(text, request.get("receiver_step", 0))


def finish_anonymous_request(request_id):
    request = ANONYMOUS_REQUESTS.pop(request_id, None)
    if not request:
        return None
    request["status"] = "closed"
    return request


def anonymous_pending_animation_job(context):
    request_id = context.job.context["request_id"]
    request = ANONYMOUS_REQUESTS.get(request_id)
    if not request or request.get("status") != "pending":
        context.job.schedule_removal()
        return
    request["sender_step"] = request.get("sender_step", 0) + 1
    request["receiver_step"] = request.get("receiver_step", 0) + 1
    try:
        context.bot.edit_message_text(
            chat_id=request["requester_id"],
            message_id=request["sender_message_id"],
            text=build_anonymous_sender_text(request),
        )
    except:
        pass
    for receiver_id, message_id in list(request.get("receiver_messages", {}).items()):
        try:
            receiver_lang = request.get("receiver_languages", {}).get(receiver_id, "en")
            context.bot.edit_message_text(
                chat_id=receiver_id,
                message_id=message_id,
                text=build_anonymous_receiver_text(request, receiver_id),
                reply_markup=get_anonymous_response_keyboard(receiver_lang, request_id),
            )
        except:
            pass


def anonymous_timeout_job(context):
    request_id = context.job.context["request_id"]
    request = finish_anonymous_request(request_id)
    if not request or request.get("status") == "accepted":
        return
    try:
        context.bot.edit_message_text(
            chat_id=request["requester_id"],
            message_id=request["sender_message_id"],
            text=format_panel(
                t(request.get("requester_lang", "en"), "title_no_response"),
                [
                    t(request.get("requester_lang", "en"), "anonymous_no_accept"),
                ],
            ),
        )
    except:
        pass
    for receiver_id, message_id in request.get("receiver_messages", {}).items():
        try:
            receiver_lang = request.get("receiver_languages", {}).get(receiver_id, "en")
            context.bot.edit_message_text(
                chat_id=receiver_id,
                message_id=message_id,
                text=format_panel(
                    t(receiver_lang, "title_request_expired"),
                    [
                        t(receiver_lang, "anonymous_request_expired_receiver"),
                    ],
                ),
            )
        except:
            pass


def build_pending_text(request):
    lang = request.get("requester_lang", "en")
    hourglass = "⏳" if request.get("pending_step", 0) % 2 == 0 else "⌛️"
    text = t(
        lang,
        "pending_text",
        hourglass=hourglass,
        target_name=request["target_name"],
    )
    return append_animation_suffix(text, request.get("pending_step", 0))


def finish_request(request_id):
    request = PENDING_REQUESTS.pop(request_id, None)
    if not request:
        return None
    request["status"] = "closed"
    return request


def end_chat(bot, user_id, reason):
    partner_id = ACTIVE_CHATS.pop(user_id, None)
    if partner_id is None:
        return
    ACTIVE_CHATS.pop(partner_id, None)
    monitor_ids = clear_chat_monitors(user_id, partner_id)
    send_menu_message(bot, user_id, reason)
    send_menu_message(bot, partner_id, reason)
    for admin_id in monitor_ids:
        send_menu_message(
            bot,
            admin_id,
            format_panel(
                t(get_lang(admin_id), "title_conversation_ended"),
                [
                    t(get_lang(admin_id), "request_closed_line_2"),
                ],
            ),
        )


def close_chat_silently(user_id, partner_id):
    ACTIVE_CHATS.pop(user_id, None)
    ACTIVE_CHATS.pop(partner_id, None)
    clear_chat_monitors(user_id, partner_id)


def pending_animation_job(context):
    request_id = context.job.context["request_id"]
    request = PENDING_REQUESTS.get(request_id)
    if not request or request.get("status") != "pending":
        context.job.schedule_removal()
        return
    request["pending_step"] = request.get("pending_step", 0) + 1
    try:
        context.bot.edit_message_text(
            chat_id=request["admin_id"],
            message_id=request["pending_message_id"],
            text=build_pending_text(request),
        )
    except:
        pass


def pending_timeout_job(context):
    request_id = context.job.context["request_id"]
    request = finish_request(request_id)
    if not request or request.get("status") == "accepted":
        return
    try:
        context.bot.edit_message_text(
            chat_id=request["admin_id"],
            message_id=request["pending_message_id"],
            text=format_panel(
                t(request.get("requester_lang", "en"), "title_request_closed"),
                [
                    t(request.get("requester_lang", "en"), "request_closed_line_1", target_name=request["target_name"]),
                    t(request.get("requester_lang", "en"), "request_closed_line_2"),
                ],
            ),
        )
    except:
        pass
    send_menu_message(
        context.bot,
        request["admin_id"],
        format_panel(
            t(request.get("requester_lang", "en"), "title_no_response"),
            [
                t(request.get("requester_lang", "en"), "no_response_line_1", target_name=request["target_name"]),
                t(request.get("requester_lang", "en"), "no_response_line_2"),
            ],
        ),
    )
    send_menu_message(
        context.bot,
        request["target_id"],
        format_panel(
            t(request.get("target_lang", "en"), "title_request_expired"),
            [
                t(request.get("target_lang", "en"), "request_expired_line"),
            ],
        ),
    )


def connect_user_callback(update, context):
    query = update.callback_query
    query.answer()
    ensure_registered(update)
    requester_lang = get_lang(query.from_user.id)
    parts = query.data.split(":")
    _, request_type, target_id = parts
    requester_is_admin = request_type == "user"
    if requester_is_admin and not is_admin(query.from_user.id):
        return query.edit_message_text(t(requester_lang, "access_denied"))
    if (not requester_is_admin) and is_admin(query.from_user.id):
        return query.edit_message_text(t(requester_lang, "admins_use_connect"))
    if is_effectively_banned(query.from_user.id):
        return query.edit_message_text(t(requester_lang, "banned_cannot_connect"))
    if has_anonymous_pending_request(query.from_user.id):
        return query.edit_message_text(t(requester_lang, "anonymous_pending_exists"))

    if str(query.from_user.id) == target_id:
        return query.edit_message_text(t(requester_lang, "request_failed_self"))
    target_row_list = get_users_by_ids([target_id])
    target_name = get_display_name(target_row_list[0]) if target_row_list else str(target_id)
    if is_effectively_banned(target_id):
        return query.edit_message_text(t(requester_lang, "target_is_banned", target_name=target_name))
    if has_anonymous_pending_request(int(target_id)):
        return query.edit_message_text(t(requester_lang, "request_already_pending_target"))
    if query.from_user.id in ACTIVE_CHATS:
        return query.edit_message_text(t(requester_lang, "request_failed_busy_you"))
    if int(target_id) in ACTIVE_CHATS:
        return query.edit_message_text(t(requester_lang, "request_failed_busy_target"))
    for pending_request in PENDING_REQUESTS.values():
        if pending_request["admin_id"] == query.from_user.id and pending_request["status"] == "pending":
            return query.edit_message_text(t(requester_lang, "request_already_pending_you"))
        if pending_request["target_id"] == int(target_id) and pending_request["status"] == "pending":
            return query.edit_message_text(t(requester_lang, "request_already_pending_target"))

    request_id = f"{query.from_user.id}:{target_id}"
    requester_name = query.from_user.username or query.from_user.first_name or str(query.from_user.id)
    target_lang = get_lang(int(target_id))
    request = {
        "request_id": request_id,
        "admin_id": query.from_user.id,
        "target_id": int(target_id),
        "status": "pending",
        "pending_step": 0,
        "target_name": target_name,
        "requester_name": requester_name,
        "requester_is_admin": requester_is_admin,
        "requester_lang": requester_lang,
        "target_lang": target_lang,
    }
    pending_message = query.edit_message_text(build_pending_text(request))
    request["pending_message_id"] = pending_message.message_id
    PENDING_REQUESTS[request_id] = request

    if requester_is_admin:
        request_text = t(target_lang, "admin_private_request")
    else:
        request_text = t(target_lang, "user_private_request", requester_name=requester_name)
    try:
        context.bot.send_message(
            chat_id=int(target_id),
            text=format_panel(
                t(target_lang, "title_private_request"),
                [
                    request_text,
                    "",
                    t(target_lang, "choose_yes_no"),
                ],
            ),
            reply_markup=get_target_decision_keyboard(target_lang),
        )
    except Exception as e:
        finish_request(request_id)
        return query.edit_message_text(
            format_panel(
                t(requester_lang, "title_request_failed"),
                [
                    t(requester_lang, "request_failed_line_1", target_name=target_name),
                    str(e)[:180],
                ],
            )
        )
    context.job_queue.run_repeating(
        pending_animation_job,
        interval=0.4,
        first=0.4,
        context={"request_id": request_id},
        name=f"pending-animation-{request_id}",
    )
    context.job_queue.run_once(
        pending_timeout_job,
        when=45,
        context={"request_id": request_id},
        name=f"pending-timeout-{request_id}",
    )


def interfere_chat_callback(update, context):
    query = update.callback_query
    query.answer()
    ensure_registered(update)
    admin_id = query.from_user.id
    lang = get_lang(admin_id)
    if not is_admin(admin_id):
        return query.edit_message_text(t(lang, "access_denied"))

    parts = query.data.split(":")
    if len(parts) < 2:
        return query.edit_message_text(t(lang, "no_active_conversations"))
    action = parts[1]

    if action == "list":
        return render_interfere_chat_list(update, context)

    if len(parts) < 4:
        return query.edit_message_text(t(lang, "no_active_conversations"))

    user_one_id = int(parts[2])
    user_two_id = int(parts[3])
    if ACTIVE_CHATS.get(user_one_id) != user_two_id or ACTIVE_CHATS.get(user_two_id) != user_one_id:
        return query.edit_message_text(t(lang, "no_active_conversations"))

    if action == "select":
        return render_interfere_actions(query, user_one_id, user_two_id)

    if action == "keep_menu":
        return query.edit_message_text(
            text=format_panel(
                t(lang, "title_interfere_chat"),
                [
                    t(lang, "choose_user_to_keep"),
                ],
            ),
            reply_markup=build_keep_user_markup(user_one_id, user_two_id, lang),
        )

    if action == "close":
        close_chat_silently(user_one_id, user_two_id)
        return query.edit_message_text(
            format_panel(
                t(lang, "title_conversation_ended"),
                [
                    t(lang, "chat_closed_by_admin"),
                ],
            )
        )

    if action == "join":
        if admin_id in ACTIVE_CHATS:
            return query.edit_message_text(t(lang, "request_failed_busy_you"))
        clear_admin_interference(admin_id)
        pair_key = get_chat_pair_key(user_one_id, user_two_id)
        CHAT_MONITORS.setdefault(pair_key, set()).add(admin_id)
        ACTIVE_INTERFERING_ADMINS[admin_id] = pair_key
        query.edit_message_text(
            text=format_panel(
                t(lang, "title_interfere_chat"),
                [
                    t(lang, "admin_monitoring_started"),
                ],
            ),
        )
        return context.bot.send_message(
            chat_id=admin_id,
            text=format_panel(
                t(lang, "title_interfere_chat"),
                [
                    t(lang, "admin_monitoring_started"),
                ],
            ),
            reply_markup=build_interfere_chat_keyboard(lang),
        )

    if action == "keep" and len(parts) == 5:
        if admin_id in ACTIVE_CHATS:
            return query.edit_message_text(t(lang, "request_failed_busy_you"))
        clear_admin_interference(admin_id)
        kept_user_id = int(parts[4])
        other_user_id = user_two_id if kept_user_id == user_one_id else user_one_id
        kept_user_row = get_user_by_id(kept_user_id)
        kept_user_name = get_display_name(kept_user_row) if kept_user_row else str(kept_user_id)
        close_chat_silently(user_one_id, user_two_id)
        ACTIVE_CHATS[admin_id] = kept_user_id
        ACTIVE_CHATS[kept_user_id] = admin_id
        increment_chat_count(admin_id)
        increment_chat_count(kept_user_id)
        query.edit_message_text(
            format_panel(
                t(lang, "title_interfere_chat"),
                [
                    t(lang, "user_kept_with_admin", target_name=kept_user_name),
                ],
            )
        )
        return context.bot.send_message(
            chat_id=admin_id,
            text=format_panel(
                t(lang, "title_chat_started"),
                [
                    t(lang, "user_kept_with_admin", target_name=kept_user_name),
                    t(lang, "chat_started_2"),
                ],
            ),
            reply_markup=get_chat_keyboard(lang, admin_id),
        )

    return query.edit_message_text(t(lang, "no_active_conversations"))


def anonymous_reply_callback(update, context):
    query = update.callback_query
    query.answer()
    ensure_registered(update)
    user_id = query.from_user.id
    lang = get_lang(user_id)
    parts = query.data.split(":")
    if len(parts) != 3:
        return query.edit_message_text(t(lang, "request_not_active"))

    action = parts[1]
    request_id = parts[2]
    request = ANONYMOUS_REQUESTS.get(request_id)
    if not request or request.get("status") != "pending":
        return query.edit_message_text(t(lang, "request_not_active"))
    if user_id not in request.get("receiver_messages", {}):
        return query.edit_message_text(t(lang, "request_not_active"))

    requester_id = request["requester_id"]
    requester_lang = request.get("requester_lang", "en")
    requester_row = get_user_by_id(requester_id)
    requester_name = get_display_name(requester_row) if requester_row else str(requester_id)

    if action == "reject":
        request["receiver_messages"].pop(user_id, None)
        try:
            query.edit_message_text(
                format_panel(
                    t(lang, "title_request_declined"),
                    [
                        t(lang, "anonymous_request_rejected"),
                    ],
                )
            )
        except:
            pass
        if not request["receiver_messages"]:
            finish_anonymous_request(request_id)
            try:
                context.bot.edit_message_text(
                    chat_id=requester_id,
                    message_id=request["sender_message_id"],
                    text=format_panel(
                        t(requester_lang, "title_no_response"),
                        [
                            t(requester_lang, "anonymous_no_accept"),
                        ],
                    ),
                )
            except:
                pass
        return

    if action != "accept":
        return query.edit_message_text(t(lang, "request_not_active"))
    if requester_id in ACTIVE_CHATS or user_id in ACTIVE_CHATS:
        return query.edit_message_text(t(lang, "request_failed_busy_you"))

    request["status"] = "accepted"
    ANONYMOUS_REQUESTS.pop(request_id, None)
    increment_chat_count(requester_id)
    increment_chat_count(user_id)
    ACTIVE_CHATS[requester_id] = user_id
    ACTIVE_CHATS[user_id] = requester_id

    try:
        context.bot.edit_message_text(
            chat_id=requester_id,
            message_id=request["sender_message_id"],
            text=format_panel(
                t(requester_lang, "title_connected"),
                [
                    t(requester_lang, "anonymous_started_sender"),
                ],
            ),
        )
    except:
        pass
    try:
        query.edit_message_text(
            format_panel(
                t(lang, "title_connected"),
                [
                    t(lang, "anonymous_started_receiver"),
                ],
            )
        )
    except:
        pass
    for other_user_id, message_id in request.get("receiver_messages", {}).items():
        if other_user_id == user_id:
            continue
        try:
            context.bot.edit_message_text(
                chat_id=other_user_id,
                message_id=message_id,
                text=format_panel(
                    t(get_lang(other_user_id), "title_request_closed"),
                    [
                        t(get_lang(other_user_id), "anonymous_taken_by_other"),
                    ],
                ),
            )
        except:
            pass

    context.bot.send_message(
        chat_id=requester_id,
        text=format_panel(
            t(requester_lang, "title_chat_started"),
            [
                t(requester_lang, "anonymous_started_sender"),
                t(requester_lang, "chat_started_2"),
            ],
        ),
        reply_markup=get_chat_keyboard(requester_lang, requester_id),
    )
    context.bot.send_message(
        chat_id=user_id,
        text=format_panel(
            t(lang, "title_chat_started"),
            [
                t(lang, "anonymous_started_receiver"),
                t(lang, "chat_started_2"),
            ],
        ),
        reply_markup=get_chat_keyboard(lang, user_id),
    )


def admin_chat_callback(update, context):
    query = update.callback_query
    query.answer()
    ensure_registered(update)
    admin_id = query.from_user.id
    lang = get_lang(admin_id)
    if not is_admin(admin_id):
        return query.edit_message_text(t(lang, "access_denied"))
    if admin_id not in ACTIVE_CHATS:
        return query.edit_message_text(t(lang, "request_failed_busy_you"))

    parts = query.data.split(":")
    if len(parts) != 4 or parts[1] != "swap":
        return query.edit_message_text(t(lang, "title_menu"))

    current_partner_id = int(parts[2])
    target_user_id = int(parts[3])
    if ACTIVE_CHATS.get(admin_id) != current_partner_id:
        return query.edit_message_text(t(lang, "request_failed_busy_you"))
    if target_user_id in ACTIVE_CHATS or has_direct_pending_request(target_user_id) or has_anonymous_pending_request(target_user_id):
        return query.edit_message_text(t(lang, "request_failed_busy_target"))
    if is_admin(target_user_id) or is_effectively_banned(target_user_id):
        return query.edit_message_text(t(lang, "request_failed_busy_target"))

    target_row = get_user_by_id(target_user_id)
    target_name = get_display_name(target_row) if target_row else str(target_user_id)
    close_chat_silently(admin_id, current_partner_id)
    ACTIVE_CHATS[admin_id] = target_user_id
    ACTIVE_CHATS[target_user_id] = admin_id
    increment_chat_count(admin_id)
    increment_chat_count(target_user_id)
    query.edit_message_text(
        format_panel(
            t(lang, "title_chat_started"),
            [
                t(lang, "chat_user_connected", target_name=target_name),
            ],
        )
    )
    context.bot.send_message(
        chat_id=target_user_id,
        text=format_panel(
            t(get_lang(target_user_id), "title_chat_started"),
            [
                t(get_lang(target_user_id), "chat_started_target_1"),
                t(get_lang(target_user_id), "chat_started_2"),
            ],
        ),
        reply_markup=get_chat_keyboard(get_lang(target_user_id), target_user_id),
    )
    return context.bot.send_message(
        chat_id=admin_id,
        text=format_panel(
            t(lang, "title_chat_started"),
            [
                t(lang, "chat_user_connected", target_name=target_name),
                t(lang, "chat_started_2"),
            ],
        ),
        reply_markup=get_chat_keyboard(lang, admin_id),
    )


def addtarget_command(update, context):
    return render_manage_users(update, context)


def user_lists_command(update, context):
    ensure_registered(update)
    lang = get_lang(update.effective_user.id)
    if not is_admin(update.effective_user.id):
        return reply_with_menu(update.message, t(lang, "access_denied"))
    reply_with_menu(update.message, get_user_list_text(language=lang))


def prompt_add_target(update, context):
    return render_manage_users(update, context)


def manage_user_callback(update, context):
    query = update.callback_query
    query.answer()
    ensure_registered(update)
    lang = get_lang(query.from_user.id)
    if not is_admin(query.from_user.id):
        return query.edit_message_text(t(lang, "access_denied"))

    parts = query.data.split(":")
    if len(parts) < 2:
        return query.edit_message_text(t(lang, "title_menu"))

    action_type = parts[1]
    if action_type == "list":
        return render_manage_users(update, context)
    if action_type == "select" and len(parts) == 3:
        return render_manage_actions(query, parts[2])
    if action_type != "action" or len(parts) != 4:
        return query.edit_message_text(t(lang, "title_menu"))

    action_name = parts[2]
    target_user_id = parts[3]
    row = get_user_by_id(target_user_id)
    if not row:
        return query.edit_message_text(t(lang, "no_manageable_users"))

    target_name = get_display_name(row)
    if action_name == "ban":
        if is_root_admin(target_user_id):
            return query.edit_message_text(
                format_panel(
                    t(lang, "title_root_only"),
                    [
                        t(lang, "cannot_ban_root_admin"),
                    ],
                )
            )
        set_user_banned(target_user_id, True)
        return query.edit_message_text(
            text=format_panel(
                t(lang, "title_manage_user"),
                [
                    t(lang, "ban_enabled", target_name=target_name),
                ],
            ),
            reply_markup=build_manage_actions_keyboard(lang, target_user_id, query.from_user.id),
        )
    if action_name == "unban":
        set_user_banned(target_user_id, False)
        return query.edit_message_text(
            text=format_panel(
                t(lang, "title_manage_user"),
                [
                    t(lang, "ban_removed", target_name=target_name),
                ],
            ),
            reply_markup=build_manage_actions_keyboard(lang, target_user_id, query.from_user.id),
        )
    if action_name == "add_admin":
        if not is_root_admin(query.from_user.id, query.from_user):
            return query.edit_message_text(
                format_panel(
                    t(lang, "title_root_only"),
                    [
                        t(lang, "root_admin_only"),
                    ],
                )
            )
        set_admin_status(int(target_user_id), True)
        return query.edit_message_text(
            text=format_panel(
                t(lang, "title_manage_user"),
                [
                    t(lang, "admin_added", target_name=target_name),
                ],
            ),
            reply_markup=build_manage_actions_keyboard(lang, target_user_id, query.from_user.id),
        )
    if action_name == "remove_admin":
        if not is_root_admin(query.from_user.id, query.from_user):
            return query.edit_message_text(
                format_panel(
                    t(lang, "title_root_only"),
                    [
                        t(lang, "root_admin_only"),
                    ],
                )
            )
        set_admin_status(int(target_user_id), False)
        return query.edit_message_text(
            text=format_panel(
                t(lang, "title_manage_user"),
                [
                    t(lang, "admin_removed", target_name=target_name),
                ],
            ),
            reply_markup=build_manage_actions_keyboard(lang, target_user_id, query.from_user.id),
        )
    if action_name == "warn":
        context.user_data["awaiting_warning_target_id"] = str(target_user_id)
        context.user_data["awaiting_warning_target_name"] = target_name
        return send_animated_text(
            context.bot,
            query.from_user.id,
            format_panel(
                t(lang, "title_warning"),
                [
                    t(lang, "warning_prompt", target_name=target_name),
                ],
                t(lang, "tap_cancel"),
            ),
            reply_markup=get_warning_keyboard(lang),
        )

    return render_manage_actions(query, target_user_id)


def handle_text(update, context):
    ensure_registered(update)
    text = (update.message.text or "").strip()
    user_id = update.effective_user.id
    lang = get_lang(user_id)

    if user_id in ACTIVE_INTERFERING_ADMINS:
        pair_key = ACTIVE_INTERFERING_ADMINS.get(user_id)
        if is_button_text(text, "end_chat") or text == t(lang, "stop_interfering"):
            clear_admin_interference(user_id)
            return reply_with_menu(update.message, t(lang, "admin_stopped_interfering"))
        if pair_key:
            user_one_id, user_two_id = pair_key
            if ACTIVE_CHATS.get(user_one_id) == user_two_id and ACTIVE_CHATS.get(user_two_id) == user_one_id:
                for target_id in (user_one_id, user_two_id):
                    try:
                        context.bot.copy_message(
                            chat_id=target_id,
                            from_chat_id=update.effective_chat.id,
                            message_id=update.effective_message.message_id,
                        )
                    except Exception as e:
                        return reply_with_menu(update.message, t(lang, "forward_failed", error=e))
                return
        clear_admin_interference(user_id)
        return reply_with_menu(update.message, t(lang, "admin_stopped_interfering"))

    if user_id in ACTIVE_CHATS:
        partner_id = ACTIVE_CHATS[user_id]
        if is_admin(user_id) and is_button_text(text, "connect_chat_user"):
            markup = build_connect_chat_user_markup(user_id, partner_id, lang)
            if not markup:
                return reply_animated_text(update.message, t(lang, "no_users_for_chat_connect"))
            return reply_animated_text(
                update.message,
                format_panel(
                    t(lang, "title_chat_started"),
                    [
                        t(lang, "choose_user_for_chat"),
                    ],
                ),
                reply_markup=markup,
            )
        if is_button_text(text, "end_chat"):
            return end_chat(
                context.bot,
                user_id,
                format_panel(
                    t(lang, "title_conversation_ended"),
                    [
                        t(lang, "request_closed_line_2"),
                    ],
                ),
            )
        try:
            context.bot.copy_message(
                chat_id=partner_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id,
            )
            for admin_id in get_monitors_for_pair(user_id, partner_id):
                context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=update.effective_chat.id,
                    message_id=update.effective_message.message_id,
                )
        except Exception as e:
            return reply_with_menu(update.message, t(lang, "forward_failed", error=e))
        return

    target_request = None
    for request in list(PENDING_REQUESTS.values()):
        if request["target_id"] == user_id and request["status"] == "pending":
            target_request = request
            break

    if target_request:
        if is_button_text(text, "yes"):
            request = finish_request(target_request["request_id"])
            if not request:
                return send_menu_message(context.bot, user_id, t(lang, "request_not_active"))
            request["status"] = "accepted"
            increment_chat_count(request["admin_id"])
            increment_chat_count(request["target_id"])
            ACTIVE_CHATS[request["admin_id"]] = request["target_id"]
            ACTIVE_CHATS[request["target_id"]] = request["admin_id"]
            try:
                context.bot.edit_message_text(
                    chat_id=request["admin_id"],
                    message_id=request["pending_message_id"],
                    text=format_panel(
                        t(request["requester_lang"], "title_connected"),
                        [
                            t(request["requester_lang"], "conversation_started_with", target_name=request["target_name"]),
                        ],
                    ),
                )
            except:
                pass
            send_animated_text(
                context.bot,
                request["admin_id"],
                format_panel(
                    t(request["requester_lang"], "title_chat_started"),
                    [
                        t(request["requester_lang"], "chat_started_admin_1", target_name=request["target_name"]),
                        t(request["requester_lang"], "chat_started_2"),
                    ],
                ),
                reply_markup=get_chat_keyboard(request["requester_lang"], request["admin_id"]),
            )
            send_animated_text(
                context.bot,
                request["target_id"],
                format_panel(
                    t(request["target_lang"], "title_chat_started"),
                    [
                        t(request["target_lang"], "chat_started_target_1"),
                        t(request["target_lang"], "chat_started_2"),
                    ],
                ),
                reply_markup=get_chat_keyboard(request["target_lang"], request["target_id"]),
            )
            return
        if is_button_text(text, "no"):
            request = finish_request(target_request["request_id"])
            if not request:
                return send_menu_message(context.bot, user_id, t(lang, "request_not_active"))
            try:
                context.bot.edit_message_text(
                    chat_id=request["admin_id"],
                    message_id=request["pending_message_id"],
                    text=format_panel(
                        t(request["requester_lang"], "title_declined"),
                        [
                            t(request["requester_lang"], "declined_line", target_name=request["target_name"]),
                        ],
                    ),
                )
            except:
                pass
            send_menu_message(
                context.bot,
                request["admin_id"],
                format_panel(
                    t(request["requester_lang"], "title_request_declined"),
                    [
                        t(request["requester_lang"], "target_declined"),
                    ],
                ),
            )
            return send_menu_message(
                context.bot,
                request["target_id"],
                format_panel(
                    t(request["target_lang"], "title_request_declined"),
                    [
                        t(request["target_lang"], "you_declined"),
                    ],
                ),
            )

    warning_target_id = context.user_data.get("awaiting_warning_target_id")
    if warning_target_id:
        if is_button_text(text, "cancel"):
            context.user_data.pop("awaiting_warning_target_id", None)
            context.user_data.pop("awaiting_warning_target_name", None)
            return reply_with_menu(update.message, t(lang, "warning_canceled"))

        warning_message = text.strip()
        if not warning_message:
            return reply_animated_text(update.message, t(lang, "warning_empty"), reply_markup=get_warning_keyboard(lang))

        target_row = get_user_by_id(warning_target_id)
        target_name = context.user_data.get("awaiting_warning_target_name") or (
            get_display_name(target_row) if target_row else warning_target_id
        )
        target_lang = get_lang(int(warning_target_id)) if str(warning_target_id).isdigit() else "en"
        try:
            context.bot.send_message(
                chat_id=int(warning_target_id),
                text=format_panel(
                    t(target_lang, "title_warning"),
                    [
                        t(target_lang, "warning_received"),
                        warning_message,
                    ],
                ),
            )
        except Exception:
            context.user_data.pop("awaiting_warning_target_id", None)
            context.user_data.pop("awaiting_warning_target_name", None)
            return reply_with_menu(
                update.message,
                t(lang, "warning_delivery_failed", target_name=target_name),
            )

        context.user_data.pop("awaiting_warning_target_id", None)
        context.user_data.pop("awaiting_warning_target_name", None)
        return reply_with_menu(
            update.message,
            t(lang, "warning_sent", target_name=target_name),
        )

    for key, action in (
        ("my_id", myid_command),
        ("claim_admin", claimadmin_command),
        ("status", status),
        ("connect_user", start_connect_user),
        ("interfere_chat", start_interfere_chat),
        ("contact_admin", start_contact_admin),
        ("start_anonymous_talk", start_anonymous_talk),
        ("add_target", prompt_add_target),
        ("user_lists", user_lists_command),
        ("help", help_command),
        ("language", switch_language),
    ):
        if is_button_text(text, key):
            return action(update, context)

    return reply_with_menu(
        update.message,
        format_panel(
            t(lang, "title_menu"),
            [
                t(lang, "menu_reminder"),
            ],
        ),
    )


def unknown(update, context):
    lang = get_lang(update.effective_user.id)
    reply_with_menu(
        update.message,
        format_panel(
            t(lang, "title_menu"),
            [
                t(lang, "menu_reminder"),
            ],
        ),
    )


def main():
    global BOT_JOB_QUEUE
    csv_storage.ensure_storage_layout()
    ensure_target_csv()
    ensure_root_admin_unbanned()

    updater = Updater(TOKEN, use_context=True)
    BOT_JOB_QUEUE = updater.job_queue
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("myid", myid_command))
    dispatcher.add_handler(CommandHandler("claimadmin", claimadmin_command))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("connectuser", start_connect_user))
    dispatcher.add_handler(CommandHandler("contactadmin", start_contact_admin))
    dispatcher.add_handler(CommandHandler("addtarget", addtarget_command))
    dispatcher.add_handler(CommandHandler("userlists", user_lists_command))
    dispatcher.add_handler(CallbackQueryHandler(admin_chat_callback, pattern=r"^admin_chat:"))
    dispatcher.add_handler(CallbackQueryHandler(anonymous_reply_callback, pattern=r"^anonymous_reply:"))
    dispatcher.add_handler(CallbackQueryHandler(interfere_chat_callback, pattern=r"^interfere_chat:"))
    dispatcher.add_handler(CallbackQueryHandler(manage_user_callback, pattern=r"^manage_user:"))
    dispatcher.add_handler(CallbackQueryHandler(connect_user_callback, pattern=r"^request_chat:(user|admin):"))
    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_text))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
