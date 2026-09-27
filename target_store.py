import csv
import os


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TARGET_CSV_PATH = os.path.join(DIRECTORY, "target.csv")
FIELDNAMES = [
    "telegram_id",
    "first_name",
    "username",
    "welcome_message",
    "status",
    "sent_at",
    "last_error",
]


def ensure_target_csv():
    if os.path.exists(TARGET_CSV_PATH):
        return TARGET_CSV_PATH

    with open(TARGET_CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
    return TARGET_CSV_PATH
