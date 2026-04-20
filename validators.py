import re


TRACK1_PATTERN = re.compile(r"%B(?P<card_id>[^^;?]+)\^(?P<name>[^^]+)\^")
UPPERCASE_TOKENS = {"II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "JR", "SR"}


def _normalize_name_token(token):
    token = token.strip()
    if not token:
        return ""

    suffix = ""
    if token.endswith("."):
        suffix = "."
        token = token[:-1]

    upper_token = token.upper()
    if len(token) == 1 or upper_token in UPPERCASE_TOKENS:
        normalized = upper_token
    else:
        parts = re.split(r"([\-'])", token.lower())
        normalized = "".join(
            part.capitalize() if part not in ("-", "'") else part
            for part in parts
        )

    if suffix and len(normalized) == 1:
        return normalized + suffix

    return normalized


def _normalize_name_component(value):
    cleaned = re.sub(r"[^A-Za-z .'-]+", " ", str(value).strip())
    tokens = [_normalize_name_token(token) for token in cleaned.split()]
    tokens = [token for token in tokens if token]
    return " ".join(tokens)


def normalize_cardholder_name(track1_name):
    name_value = str(track1_name).strip()
    if "/" not in name_value:
        raise ValueError("Name format invalid")

    last_raw, first_raw = name_value.split("/", 1)
    first_middle = _normalize_name_component(first_raw)
    last = _normalize_name_component(last_raw)

    if not first_middle or not last:
        raise ValueError("Name format incomplete")

    return "{0} {1}".format(first_middle, last)


def parse_swipe(swipe):
    swipe_value = str(swipe).strip()
    match = TRACK1_PATTERN.search(swipe_value)
    if not match:
        raise ValueError("Swipe data missing complete Track 1")

    card_id = match.group("card_id").strip()
    raw_name = match.group("name").strip()
    formatted_name = normalize_cardholder_name(raw_name)
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
