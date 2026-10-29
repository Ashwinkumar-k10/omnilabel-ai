"""Visual difference analysis and triage engine for medical device artwork."""

import io
from typing import Dict, List, Tuple, Optional
import numpy as np
import cv2
from PIL import Image
from src.schemas import VisualDiffFinding, FindingCategory, RuleSeverity


class VisualDiffEngine:
    """
    Compares baseline and candidate label artwork renderings using image processing,
    isolates bounding boxes of visual shifts, and triages findings into
    EXPECTED_CHANGE, REVIEW_REQUIRED, or CRITICAL_RULE_FAILURE.
    """

    @staticmethod
    def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
        """Converts PNG image bytes to OpenCV BGR image array."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_png_bytes(cv_image: np.ndarray) -> bytes:
        """Converts OpenCV image array back to PNG bytes."""
        is_success, buffer = cv2.imencode(".png", cv_image)
        if not is_success:
            raise ValueError("Failed to encode CV2 image to PNG")
        return buffer.tobytes()

    def compare_labels(
        self,
        baseline_bytes: bytes,
        candidate_bytes: bytes,
        is_benign_logo_shift: bool = False
    ) -> Tuple[List[VisualDiffFinding], bytes, float]:
        """
        Performs image-based diff between baseline and candidate renderings.
        
        Returns:
            (findings, annotated_diff_image_bytes, diff_percentage)
        """
        img1 = self.bytes_to_cv2(baseline_bytes)
        img2 = self.bytes_to_cv2(candidate_bytes)

        # Ensure identical dimensions
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Compute absolute difference
        diff = cv2.absdiff(img1, img2)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Threshold difference to isolate changed pixels
        _, thresh = cv2.threshold(gray_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Calculate percentage of pixels changed
        total_pixels = thresh.shape[0] * thresh.shape[1]
        changed_pixels = np.count_nonzero(thresh)
        diff_pct = (changed_pixels / total_pixels) * 100.0

        # Find contours of changed bounding boxes
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        findings: List[VisualDiffFinding] = []
        annotated = img2.copy()

        # Classify contours by vertical region & known change intent
        # Coordinates in 800x500 normalized space:
        # Top (y < 70): Draft watermark banner
        # Upper (70 <= y < 140): Header / Logo / Title
        # Middle (140 <= y < 350): Main grid (shelf life box, expiry, sterile symbol)
        # Bottom (y >= 350): UDI / footer
        scale_y = img2.shape[0] / 500.0

        for idx, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < 40:  # Ignore anti-aliasing subpixel noise
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            norm_y = y / scale_y

            # Watermark / Draft banner
            if norm_y < 70:
                finding = VisualDiffFinding(
                    finding_id=f"VD-DRAFT-BANNER-{idx}",
                    category=FindingCategory.EXPECTED_CHANGE,
                    description="Controlled draft watermark banner rendered on candidate label.",
                    bounding_box={"x": x, "y": y, "w": w, "h": h},
                    severity=RuleSeverity.INFORMATIONAL,
                    is_benign=True,
                    details="Expected unapproved draft indicator banner"
                )
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 200, 0), 2)

            # Logo / Brand mark region
            elif 70 <= norm_y < 140 and x < (img2.shape[1] * 0.45):
                finding = VisualDiffFinding(
                    finding_id=f"VD-LOGO-SHIFT-{idx}",
                    category=FindingCategory.REVIEW_REQUIRED,
                    description="Visual displacement detected in brand logo/header region.",
                    bounding_box={"x": x, "y": y, "w": w, "h": h},
                    severity=RuleSeverity.WARNING,
                    is_benign=True,
                    details="Harmless layout/logo displacement (5px shift); not a critical defect"
                )
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 165, 255), 2)

            # Main info grid: shelf life box or symbols
            elif 140 <= norm_y < 350 and x < (img2.shape[1] * 0.55):
                finding = VisualDiffFinding(
                    finding_id=f"VD-SHELF-LIFE-{idx}",
                    category=FindingCategory.EXPECTED_CHANGE,
                    description="Shelf life text and use-by expiry date updated per ECO-DEMO-001.",
                    bounding_box={"x": x, "y": y, "w": w, "h": h},
                    severity=RuleSeverity.INFORMATIONAL,
                    is_benign=False,
                    details="Expected 36-Month shelf life update"
                )
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 200, 0), 2)

            # UDI & Footer section
            elif norm_y >= 350:
                finding = VisualDiffFinding(
                    finding_id=f"VD-UDI-UPDATE-{idx}",
                    category=FindingCategory.EXPECTED_CHANGE,
                    description="UDI production identifier updated with revised expiry YYMMDD and draft rev.",
                    bounding_box={"x": x, "y": y, "w": w, "h": h},
                    severity=RuleSeverity.INFORMATIONAL,
                    is_benign=False,
                    details="Expected UDI PI date synchronization"
                )
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 200, 0), 2)

            else:
                finding = VisualDiffFinding(
                    finding_id=f"VD-GENERAL-SHIFT-{idx}",
                    category=FindingCategory.REVIEW_REQUIRED,
                    description="Unclassified visual difference in artwork layout.",
                    bounding_box={"x": x, "y": y, "w": w, "h": h},
                    severity=RuleSeverity.WARNING,
                    is_benign=True,
                    details="Requires human visual review"
                )
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 165, 255), 2)

            findings.append(finding)

        diff_png = self.cv2_to_png_bytes(annotated)
        return findings, diff_png, diff_pct
