# validates the data read from card

def parse_swipe(swipe):
    swipe = swipe.strip()

    if "^" not in swipe:
        raise ValueError("Swipe data missing '^' separators")

    parts = swipe.split("^")

    if len(parts) < 2:
        raise ValueError("Swipe data incomplete")

    card_part = parts[0].strip()

    if not card_part.startswith("%B"):
        raise ValueError("Swipe data missing Track 1 start")

    card_id = card_part.replace("%B", "").strip()

    name_raw = parts[1].strip()

    if "/" not in name_raw:
        raise ValueError("Name format invalid")

    name_parts = name_raw.split("/")

    if len(name_parts) < 2:
        raise ValueError("Name format incomplete")

    last = name_parts[0].strip()
    first = name_parts[1].strip()

    first = " ".join(first.split())
    last = " ".join(last.split())

    formatted_name = "{0} {1}".format(first, last)
    return formatted_name, card_id

def valid_student_id(student_id):
    return student_id.isdigit() and len(student_id) == 10

def valid_phone_number(phone):
    digits_only = "".join(ch for ch in phone if ch.isdigit())
    return len(digits_only) == 10

def normalize_phone_number(phone):
    return "".join(ch for ch in phone if ch.isdigit())

def valid_mymdc_username(username):
    username = username.strip().lower()
    if username == "":
        return False
    if "@" in username:
        return False
    return True

def build_mymdc_email(username):
    username = username.strip().lower()

    if username.endswith("@mymdc.net"):
        username = username.replace("@mymdc.net", "")

    return username, "{0}@mymdc.net".format(username)
