from datetime import datetime
from io import BytesIO
from pathlib import Path
import re

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

from config import (
    BEHAVIORAL_CONTRACT_TEMPLATE,
    BEHAVIORAL_CONTRACT_SIGNED_FOLDER
)


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
DEFAULT_FONT_SIZE = 12
MIN_FONT_SIZE = 8

FIELD_LAYOUT = {
    "printed_name": {
        "x": 115.8,
        "y": 608.6,
        "max_width": 125.4
    },
    "signature_name": {
        "x": 126.4,
        "y": 183.4,
        "max_width": 101.64
    },
    "student_id": {
        "x": 445.0,
        "y": 183.6,
        "max_width": 74.52
    },
    "date": {
        "x": 103.2,
        "y": 159.6,
        "max_width": 71.64
    }
}


def sanitize_filename_part(value):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "unknown"


def _bottom_to_top_y(y_value):
    return PAGE_HEIGHT - y_value


def _draw_fitted_text(pdf, text, x_pos, y_pos, max_width):
    font_size = DEFAULT_FONT_SIZE

    while font_size > MIN_FONT_SIZE:
        pdf.set_font("Helvetica", size=font_size)
        if pdf.get_string_width(text) <= max_width:
            break
        font_size -= 1

    pdf.text(x=x_pos, y=_bottom_to_top_y(y_pos), text=text)


def _build_overlay(student_name, student_id, signed_name, contract_date):
    pdf = FPDF(unit="pt", format=(PAGE_WIDTH, PAGE_HEIGHT))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    _draw_fitted_text(
        pdf,
        student_name,
        FIELD_LAYOUT["printed_name"]["x"],
        FIELD_LAYOUT["printed_name"]["y"],
        FIELD_LAYOUT["printed_name"]["max_width"]
    )
    _draw_fitted_text(
        pdf,
        signed_name,
        FIELD_LAYOUT["signature_name"]["x"],
        FIELD_LAYOUT["signature_name"]["y"],
        FIELD_LAYOUT["signature_name"]["max_width"]
    )
    _draw_fitted_text(
        pdf,
        student_id,
        FIELD_LAYOUT["student_id"]["x"],
        FIELD_LAYOUT["student_id"]["y"],
        FIELD_LAYOUT["student_id"]["max_width"]
    )
    _draw_fitted_text(
        pdf,
        contract_date,
        FIELD_LAYOUT["date"]["x"],
        FIELD_LAYOUT["date"]["y"],
        FIELD_LAYOUT["date"]["max_width"]
    )

    return bytes(pdf.output())


def generate_behavioral_contract(student_name, student_id, signed_name=None):
    template_path = Path(BEHAVIORAL_CONTRACT_TEMPLATE)
    output_dir = Path(BEHAVIORAL_CONTRACT_SIGNED_FOLDER)
    signed_name = signed_name or student_name
    contract_date = datetime.now().strftime("%m/%d/%Y")

    safe_name = sanitize_filename_part(student_name)
    safe_student_id = sanitize_filename_part(student_id)
    output_path = output_dir / f"{safe_name}-{safe_student_id}-signed_contract.pdf"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        if not template_path.exists():
            raise FileNotFoundError("Contract template not found: {0}".format(template_path))

        reader = PdfReader(str(template_path))
        overlay_pdf = BytesIO(
            _build_overlay(student_name, student_id, signed_name, contract_date)
        )
        overlay_reader = PdfReader(overlay_pdf)

        writer = PdfWriter()
        page = reader.pages[0]
        page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

        with output_path.open("wb") as output_file:
            writer.write(output_file)

        print("[Contract] Saved signed contract:", output_path)
        return output_path
    except Exception as exc:
        print("[Contract] Failed to generate signed contract:", exc)
        print("[Contract] Template path:", template_path)
        print("[Contract] Output directory:", output_dir)
        return None
