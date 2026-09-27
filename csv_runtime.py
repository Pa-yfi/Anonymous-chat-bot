import csv
import os

from dotenv import load_dotenv


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(DIRECTORY, ".env"))

PROFILE_CSV_PATH = os.path.join(DIRECTORY, "profile.csv")
REQUIREMENTS_PATH = os.path.join(DIRECTORY, "requirements.txt")


def _read_profile_settings():
    result = {}
    if not os.path.exists(PROFILE_CSV_PATH):
        return result
    try:
        with open(PROFILE_CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = (row.get("key") or "").strip().upper()
                value = (row.get("value") or "").strip()
                if key:
                    result[key] = value
    except:
        pass
    return result


def _read_requirements_settings():
    result = {}
    if not os.path.exists(REQUIREMENTS_PATH):
        return result
    try:
        with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()
                if key:
                    result[key] = value
    except:
        pass
    return result


def get_setting(name, default=None):
    name = name.upper()
    env_value = os.getenv(name)
    if env_value:
        return env_value

    profile_value = _read_profile_settings().get(name)
    if profile_value:
        return profile_value

    requirements_value = _read_requirements_settings().get(name)
    if requirements_value:
        return requirements_value
    return default


def get_required_setting(name):
    value = get_setting(name)
    if value is None:
        raise ValueError(f"Missing required setting: {name}")
    return value


def _parse_ids(raw_value):
    ids = []
    for value in str(raw_value).split(","):
        value = value.strip()
        if value.isdigit():
            ids.append(int(value))
    return ids


def get_owner_ids():
    return _parse_ids(get_setting("OWNER_ID", ""))


def get_admin_ids():
    admin_ids = _parse_ids(get_setting("ADMINS", ""))
    for owner_id in get_owner_ids():
        if owner_id not in admin_ids:
            admin_ids.append(owner_id)
    return admin_ids


def is_bootstrap_admin_mode():
    raw_value = str(get_setting("ADMINS", "")).strip()
    return raw_value in ("", "1234") and not get_owner_ids()


def set_profile_setting(name, value):
    name = str(name).strip().upper()
    value = str(value).strip()
    rows = []
    seen = False

    if os.path.exists(PROFILE_CSV_PATH):
        try:
            with open(PROFILE_CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    key = (row.get("key") or "").strip().upper()
                    current_value = (row.get("value") or "").strip()
                    if key == name:
                        rows.append({"key": name, "value": value})
                        seen = True
                    elif key:
                        rows.append({"key": key, "value": current_value})
        except:
            rows = []

    if not seen:
        rows.append({"key": name, "value": value})

    with open(PROFILE_CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["key", "value"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def get_storage_mode():
    return str(get_setting("STORAGE_MODE", "csv")).strip().lower()
