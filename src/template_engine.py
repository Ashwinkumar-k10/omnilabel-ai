"""Controlled label drafting engine using Jinja2 and SVG templates with PyMuPDF rendering."""

import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import pymupdf


def calculate_expiry_date(mfg_date_str: str, shelf_life_months: int) -> Tuple[str, str]:
    """
    Given an ISO mfg date (YYYY-MM-DD) and shelf life in months,
    calculates expiry date (YYYY-MM-DD) and GS1 format YYMMDD.
    """
    mfg_dt = datetime.strptime(mfg_date_str, "%Y-%m-%d")
    
    # Calculate target year and month
    total_months = mfg_dt.month + shelf_life_months
    exp_year = mfg_dt.year + (total_months - 1) // 12
    exp_month = ((total_months - 1) % 12) + 1
    
    # Clamp to last day of month if needed, but for first of month stay on first
    exp_day = min(mfg_dt.day, 28) if exp_month == 2 else min(mfg_dt.day, 30) if exp_month in [4, 6, 9, 11] else mfg_dt.day
    
    exp_dt = datetime(exp_year, exp_month, exp_day)
    iso_str = exp_dt.strftime("%Y-%m-%d")
    gs1_str = exp_dt.strftime("%y%m%d")
    return iso_str, gs1_str


class ControlledTemplateEngine:
    """Renders controlled candidate labels and manages visual rendering."""

    def __init__(self, templates_dir: Optional[str] = None):
        if not templates_dir:
            templates_dir = str(Path(__file__).parent.parent / "templates")
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

    def generate_candidate_data(
        self,
        baseline_data: Dict[str, Any],
        proposed_shelf_life_months: int,
        proposed_shelf_life_text: str,
        storage_condition: str,
        seeded_defect: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates the candidate label field values by applying the controlled ECO change
        while preserving all unrelated and immutable fields.
        """
        data = dict(baseline_data)
        mfg_date = data.get("mfg_date", "2026-11-01")
        
        # Calculate new expiry
        new_iso_exp, new_gs1_exp = calculate_expiry_date(mfg_date, proposed_shelf_life_months)

        # Apply ECO changes to controlled fields
        data["shelf_life_months"] = proposed_shelf_life_months
        data["shelf_life_text"] = proposed_shelf_life_text
        data["expiry_date"] = new_iso_exp
        data["storage_conditions"] = storage_condition
        data["is_draft"] = True
        data["revision"] = "C (DRAFT)"
        data["template_version"] = "TMPL-STERILE-V2.0-DRAFT"

        # Update UDI PI with new expiry YYMMDD
        lot_clean = re.sub(r"[^A-Za-z0-9]", "", data.get("lot_number", "LOT20261101"))
        data["udi_pi"] = f"(17){new_gs1_exp}(10){lot_clean}"
        data["full_udi"] = f"(01){data['udi_di']}{data['udi_pi']}"

        # Inject seeded defects if requested for acceptance testing
        if seeded_defect == "DEFECT-EXPIRY-MATH":
            # Seed error: wrong expiry calculation (kept at 2028-11-01 instead of 2029-11-01)
            data["expiry_date"] = "2028-11-01"
            data["udi_pi"] = f"(17)281101(10){lot_clean}"
            data["full_udi"] = f"(01){data['udi_di']}{data['udi_pi']}"
        elif seeded_defect == "DEFECT-UDI-CHECKSUM":
            # Seed error: corrupted check digit in UDI-DI
            corrupted_di = data["udi_di"][:-1] + "9"  # invalid check digit
            data["udi_di"] = corrupted_di
            data["full_udi"] = f"(01){corrupted_di}{data['udi_pi']}"
        elif seeded_defect == "DEFECT-STERILE-SYMBOL":
            # Seed error: stripped sterilization symbol
            data["sterilization_symbol"] = None
        elif seeded_defect == "DEFECT-PROPAGATION-MISMATCH":
            # Seed error: shelf life field was not updated
            data["shelf_life_text"] = "24 Months"
            data["shelf_life_months"] = 24

        return data

    def render_svg(
        self,
        template_name: str,
        data: Dict[str, Any],
        benign_shift: bool = False
    ) -> str:
        """Renders the SVG string using Jinja2."""
        actual_template = template_name
        if benign_shift:
            actual_template = "approved_label_benign.svg"
            
        tmpl = self.env.get_template(actual_template)
        return tmpl.render(**data)

    def render_to_pixmap(self, svg_content: str, dpi: int = 150) -> pymupdf.Pixmap:
        """Renders SVG content string into a PyMuPDF Pixmap."""
        doc = pymupdf.open(stream=svg_content.encode("utf-8"), filetype="svg")
        # PyMuPDF zoom matrix for DPI: 72 dpi is 1.0
        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        return doc[0].get_pixmap(matrix=mat, alpha=False)

    def render_to_png_bytes(self, svg_content: str, dpi: int = 150) -> bytes:
        """Converts SVG content to PNG image bytes."""
        pixmap = self.render_to_pixmap(svg_content, dpi)
        return pixmap.tobytes(output="png")

    def render_to_pdf_bytes(self, svg_content: str) -> bytes:
        """Converts SVG content to PDF bytes."""
        doc = pymupdf.open(stream=svg_content.encode("utf-8"), filetype="svg")
        return doc.convert_to_pdf()
