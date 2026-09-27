import csv
import os


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CSV_DATA_DIR = os.path.join(DIRECTORY, "csv_data")

TABLE_SCHEMAS = {
    "admin": [
        "id", "cache", "change_pass", "exit_session", "is_change_profile",
        "is_set_username", "api_per_number", "limit_per_h", "send_per_h",
        "account_password"
    ],
    "analyze": [
        "id", "order_id", "user_id", "username", "group_id", "is_real",
        "is_fake", "is_phone", "is_online", "reserved_by", "created_at"
    ],
    "apis": ["id", "api_id", "api_hash"],
    "cats": ["id", "name"],
    "egroup": [
        "id", "type", "user_id", "chat_id", "link", "status", "users_all",
        "users_real", "users_fake", "users_has_phone", "users_online",
        "participants_count", "participants_online_count",
        "participants_bot_count", "created_at", "updated_at", "uniq_id"
    ],
    "files": ["id", "order_id", "type_message", "message_id", "created_at", "uniq_id"],
    "mbots": [
        "id", "creator_user_id", "cat_id", "phone", "user_id", "status",
        "end_restrict", "last_order_at", "last_leave_at", "last_delete_chats_at",
        "api_id", "api_hash", "code", "password", "is_change_pass",
        "change_pass_at", "is_exit_session", "exit_session_at",
        "is_change_profile", "is_set_username", "created_at", "uniq_id"
    ],
    "orders": [
        "id", "user_id", "cats", "group_link", "group_id", "count", "max_users",
        "count_request", "count_done", "type_users", "type_send", "status",
        "status_analyze", "count_acc", "count_restrict", "count_restrict_error",
        "count_report", "count_accout", "count_usrspam", "count_userincorrect",
        "count_other_errors", "send_per_h", "created_at", "updated_at", "uniq_id"
    ],
    "reports": ["id", "order_id", "bot_id", "user_id", "username", "group_id", "status", "created_at"],
    "usedaccs": ["id", "order_id", "bot_id", "created_at"],
    "users": ["id", "user_id", "status", "step", "created_at", "uniq_id"],
}


def ensure_storage_layout():
    os.makedirs(CSV_DATA_DIR, exist_ok=True)
    for table_name, headers in TABLE_SCHEMAS.items():
        file_path = os.path.join(CSV_DATA_DIR, f"{table_name}.csv")
        if os.path.exists(file_path):
            continue
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

