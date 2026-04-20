from datetime import datetime
from pathlib import Path
import re

from fpdf import FPDF

from config import (
    BEHAVIORAL_CONTRACT_SIGNED_FOLDER,
    BEHAVIORAL_CONTRACT_TEMPLATE,
)


CONTRACT_TITLE = "Robotics Lab Behavioral Contract"
CONTRACT_RULES = [
    "Maintain a respectful, safe, and non-disruptive work environment.",
    "Respect personal space and do not bully, threaten, or harass others.",
    "Use tools, materials, computers, and lab equipment only as authorized.",
    "Do not remove, damage, or tamper with lab equipment or supplies.",
    "Do not work in the lab or use resources when authorized staff or approved student leadership are not present.",
    "Do not enter staff-only offices, storage areas, or equipment rooms without permission.",
    "Follow posted food, drink, cleanup, and safety expectations for the workspace.",
]
EQUAL_ACCESS_NOTICE = (
    "Miami Dade College is an equal access/equal opportunity institution and does not "
    "discriminate on the basis of sex, race, color, marital status, age, religion, national "
    "origin, disability, veteran status, sexual orientation, or genetic information."
)


def sanitize_filename_part(value):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "unknown"


def _build_contract_pdf(student_name, student_id, signed_name, contract_date):
    pdf = FPDF(unit="pt", format="letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(54, 54, 54)
    pdf.add_page()

    line_height = 16
    body_font_size = 11

    pdf.set_font("Helvetica", style="B", size=18)
    pdf.multi_cell(0, 24, CONTRACT_TITLE, align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", size=body_font_size)
    intro_paragraphs = [
        "I understand that participation in the Robotics Lab and use of its spaces, tools, "
        "and equipment is a privilege that depends on respectful and safe behavior.",
        "I agree to follow lab staff instructions, respect other students and staff, and use "
        "equipment and work areas only as authorized.",
        "The following conduct expectations apply while I am in the lab or participating in "
        "lab activities:",
    ]

    for paragraph in intro_paragraphs:
        pdf.multi_cell(0, line_height, paragraph)
        pdf.ln(4)

    for rule in CONTRACT_RULES:
        pdf.multi_cell(0, line_height, "- {0}".format(rule))
        pdf.ln(2)

    closing_paragraphs = [
        "For normal lab operations and safety, this kiosk and its related records may store "
        "information entered into the system, card-derived information used for check-in and "
        "identity handling, daily check-in records, signed contract PDFs, and photos taken "
        "during registration or check-in.",
        "If I violate lab or club expectations, staff may require me to leave the space and "
        "may suspend lab privileges for a period determined by staff.",
        "By signing below, I acknowledge these expectations and understand the kiosk records "
        "described above as part of normal lab administration.",
    ]

    for paragraph in closing_paragraphs:
        pdf.ln(4)
        pdf.multi_cell(0, line_height, paragraph)

    pdf.ln(10)
    pdf.set_font("Helvetica", style="I", size=9)
    pdf.multi_cell(0, 13, EQUAL_ACCESS_NOTICE)

    pdf.ln(20)
    pdf.set_font("Helvetica", size=body_font_size)
    pdf.multi_cell(0, line_height, "Printed Name: {0}".format(student_name))
    pdf.ln(6)
    pdf.multi_cell(0, line_height, "Signature: {0}".format(signed_name))
    pdf.ln(6)
    pdf.multi_cell(0, line_height, "Student ID: {0}".format(student_id))
    pdf.ln(6)
    pdf.multi_cell(0, line_height, "Date: {0}".format(contract_date))

    return bytes(pdf.output())


def get_signed_contract_path(student_name, student_id):
    output_dir = Path(BEHAVIORAL_CONTRACT_SIGNED_FOLDER)
    safe_name = sanitize_filename_part(student_name)
    safe_student_id = sanitize_filename_part(student_id)
    return output_dir / f"{safe_name}-{safe_student_id}-signed_contract.pdf"


def has_signed_contract(student_name, student_id):
    return get_signed_contract_path(student_name, student_id).exists()


def _files_have_same_bytes(left_path, right_path):
    try:
        return left_path.read_bytes() == right_path.read_bytes()
    except Exception:
        return False


def rename_signed_contract(student_id, old_name, new_name):
    old_path = get_signed_contract_path(old_name, student_id)
    new_path = get_signed_contract_path(new_name, student_id)

    if old_path == new_path:
        return {
            "current_path": new_path if new_path.exists() else None,
            "renamed": False,
            "deduplicated": False,
            "collision": False,
        }

    if not old_path.exists():
        return {
            "current_path": new_path if new_path.exists() else None,
            "renamed": False,
            "deduplicated": False,
            "collision": False,
        }

    if new_path.exists():
        if _files_have_same_bytes(old_path, new_path):
            old_path.unlink()
            return {
                "current_path": new_path,
                "renamed": False,
                "deduplicated": True,
                "collision": False,
            }

        return {
            "current_path": new_path,
            "renamed": False,
            "deduplicated": False,
            "collision": True,
        }

    old_path.replace(new_path)
    return {
        "current_path": new_path,
        "renamed": True,
        "deduplicated": False,
        "collision": False,
    }


def write_contract_template():
    template_path = Path(BEHAVIORAL_CONTRACT_TEMPLATE)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_bytes(
        _build_contract_pdf(
            "______________________________",
            "________________",
            "______________________________",
            "________________",
        )
    )
    return template_path


def generate_behavioral_contract(student_name, student_id, signed_name=None):
    output_dir = Path(BEHAVIORAL_CONTRACT_SIGNED_FOLDER)
    signed_name = signed_name or student_name
    contract_date = datetime.now().strftime("%m/%d/%Y")
    output_path = get_signed_contract_path(student_name, student_id)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            print("[Contract] Reusing existing signed contract:", output_path)
            return output_path

        output_path.write_bytes(
            _build_contract_pdf(student_name, student_id, signed_name, contract_date)
        )

        print("[Contract] Saved signed contract:", output_path)
        return output_path
    except Exception as exc:
        print("[Contract] Failed to generate signed contract:", exc)
        print("[Contract] Output directory:", output_dir)
        return None
