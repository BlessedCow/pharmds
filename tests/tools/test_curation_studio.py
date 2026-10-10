from __future__ import annotations

from tools.curation_gui import PharmDSCurationGui
from tools.curation_studio import CurationStudio, product_detail


def test_studio_keeps_the_original_editor_and_product_basis_visible() -> None:
    assert issubclass(CurationStudio, PharmDSCurationGui)
    detail = product_detail(
        {
            "product_name": "ARISTADA",
            "strength_value": 441,
            "strength_unit": "mg aripiprazole lauroxil",
            "composition": (
                "Aripiprazole lauroxil ester per syringe, "
                "not aripiprazole base equivalent"
            ),
        }
    )
    assert "ARISTADA" in detail
    assert "441 mg aripiprazole lauroxil" in detail
    assert "not aripiprazole base equivalent" in detail
