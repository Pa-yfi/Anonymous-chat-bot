import csv
import os
import time
import uuid

import csv_storage
from csv_runtime import get_admin_ids


USERS_CSV_PATH = os.path.join(csv_storage.CSV_DATA_DIR, "users.csv")
FIELDNAMES = [
    "id",
    "user_id",
    "username",
    "first_name",
    "language",
    "chat_count",
    "is_banned",
    "status",
    "step",
    "created_at",
    "uniq_id",
]


def _read_rows():
    csv_storage.ensure_storage_layout()
    with open(USERS_CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            clean_row = {}
            for field in FIELDNAMES:
                clean_row[field] = (row.get(field) or "").strip()
            rows.append(clean_row)
        return rows


def _write_rows(rows):
    csv_storage.ensure_storage_layout()
    with open(USERS_CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def register_user(user_id, username="", first_name="", language=""):
    user_id = str(user_id).strip()
    username = str(username or "").strip()
    first_name = str(first_name or "").strip()
    language = str(language or "").strip().lower()
    rows = _read_rows()
    for row in rows:
        if row["user_id"] == user_id:
            row["username"] = username
            row["first_name"] = first_name
            if language in ("en", "fa"):
                row["language"] = language
            elif not row.get("language", "").strip():
                row["language"] = "en"
            if not row.get("chat_count", "").strip():
                row["chat_count"] = "0"
            if not row.get("is_banned", "").strip():
                row["is_banned"] = "0"
            _write_rows(rows)
            return row

    next_id = 1
    for row in rows:
        try:
            next_id = max(next_id, int(row["id"]) + 1)
        except:
            pass

    row = {
        "id": str(next_id),
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "language": language if language in ("en", "fa") else "en",
        "chat_count": "0",
        "is_banned": "0",
        "status": "1",
        "step": "start",
        "created_at": str(int(time.time())),
        "uniq_id": uuid.uuid4().hex,
    }
    rows.append(row)
    _write_rows(rows)
    return row


def get_user_list_text(limit=50, language="en"):
    rows = _read_rows()
    if not rows:
        if language == "fa":
            return "هنوز کاربری در ربات ثبت نشده است."
        return "No bot users yet."

    output = ["لیست کاربران:" if language == "fa" else "User Lists:"]
    for index, row in enumerate(rows[:limit], start=1):
        username = row.get("username", "").strip()
        first_name = row.get("first_name", "").strip()
        if username:
            label = f"@{username}"
        elif first_name:
            label = first_name
        else:
            label = "ناشناس" if language == "fa" else "Unknown"
        if language == "fa":
            output.append(f"{index}. {label} | شناسه: {row['user_id']}")
        else:
            output.append(f"{index}. {label} | id: {row['user_id']}")

    if len(rows) > limit:
        if language == "fa":
            output.append(f"... و {len(rows) - limit} کاربر دیگر")
        else:
            output.append(f"... and {len(rows) - limit} more")
    return "\n".join(output)


def get_active_users(admin_ids=None):
    admin_ids = {str(value) for value in (admin_ids or [])}
    rows = _read_rows()
    result = []
    for row in rows:
        user_id = row.get("user_id", "").strip()
        if not user_id or user_id in admin_ids:
            continue
        result.append(row)
    return result


def get_all_users(limit=None):
    rows = _read_rows()
    if limit is None:
        return rows
    return rows[: int(limit)]


def get_user_language(user_id, default="en"):
    user_id = str(user_id).strip()
    rows = _read_rows()
    for row in rows:
        if row.get("user_id", "").strip() == user_id:
            language = row.get("language", "").strip().lower()
            if language in ("en", "fa"):
                return language
            return default
    return default


def set_user_language(user_id, language):
    user_id = str(user_id).strip()
    language = str(language or "").strip().lower()
    if language not in ("en", "fa"):
        language = "en"

    rows = _read_rows()
    for row in rows:
        if row.get("user_id", "").strip() == user_id:
            row["language"] = language
            _write_rows(rows)
            return row

    return register_user(user_id, language=language)


def get_users_by_ids(user_ids):
    wanted = {str(value).strip() for value in user_ids}
    rows = _read_rows()
    return [row for row in rows if row.get("user_id", "").strip() in wanted]


def get_user_by_id(user_id):
    user_id = str(user_id).strip()
    for row in _read_rows():
        if row.get("user_id", "").strip() == user_id:
            return row
    return None


def get_display_name(row, include_id=False):
    username = row.get("username", "").strip()
    first_name = row.get("first_name", "").strip()
    if username:
        label = f"@{username}"
    elif first_name:
        label = first_name
    else:
        label = "Unknown"
    if include_id:
        return f"{label} | id: {row.get('user_id', '').strip()}"
    return label


def is_user_banned(user_id):
    row = get_user_by_id(user_id)
    if not row:
        return False
    return row.get("is_banned", "").strip() == "1"


def set_user_banned(user_id, banned):
    user_id = str(user_id).strip()
    rows = _read_rows()
    for row in rows:
        if row.get("user_id", "").strip() == user_id:
            row["is_banned"] = "1" if banned else "0"
            _write_rows(rows)
            return row
    return None


def increment_chat_count(user_id):
    user_id = str(user_id).strip()
    rows = _read_rows()
    for row in rows:
        if row.get("user_id", "").strip() != user_id:
            continue
        try:
            current_count = int(row.get("chat_count", "0") or "0")
        except:
            current_count = 0
        row["chat_count"] = str(current_count + 1)
        _write_rows(rows)
        return row
    return None


def get_chat_status_text(language="en"):
    rows = _read_rows()
    admin_ids = {str(admin_id) for admin_id in get_admin_ids()}
    total_users = len(rows)
    admin_count = 0
    banned_count = 0
    total_chats = 0

    for row in rows:
        user_id = row.get("user_id", "").strip()
        if user_id in admin_ids:
            admin_count += 1
        if row.get("is_banned", "").strip() == "1":
            banned_count += 1
        try:
            total_chats += int(row.get("chat_count", "0") or "0")
        except:
            pass

    if language == "fa":
        return "\n".join(
            [
                "وضعیت ربات:",
                f"همه کاربران: {total_users}",
                f"ادمین ها: {admin_count}",
                f"کاربران بن شده: {banned_count}",
                f"جمع گفتگوها: {total_chats}",
            ]
        )

    return "\n".join(
        [
            "Bot Status:",
            f"All users: {total_users}",
            f"Admins: {admin_count}",
            f"Banned users: {banned_count}",
            f"Total chats: {total_chats}",
        ]
    )
