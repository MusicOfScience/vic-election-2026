import importlib.util
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "model/scripts/extract_vec_enrolment.py"
spec = importlib.util.spec_from_file_location("extract_vec_enrolment", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _write_workbook(path: Path, area_type: str, rows: int) -> None:
    strings = [
        "Area Type Name:", area_type.title(), "Date Extracted:", "Area No", "Area Name",
        "Elector Count", "Variance to Average (%)", "Property Count",
        *[f"Area {number}" for number in range(1, rows + 1)],
    ]
    shared = "".join(f"<si><t>{value}</t></si>" for value in strings)
    cells = [
        '<row r="5"><c r="A5" t="s"><v>0</v></c><c r="B5" t="s"><v>1</v></c></row>',
        '<row r="7"><c r="A7" t="s"><v>2</v></c><c r="B7"><v>46269</v></c></row>',
        '<row r="10"><c r="A10" t="s"><v>3</v></c><c r="B10" t="s"><v>4</v></c><c r="F10" t="s"><v>5</v></c><c r="G10" t="s"><v>6</v></c><c r="I10" t="s"><v>7</v></c></row>',
    ]
    for number in range(1, rows + 1):
        sheet_row = number + 12
        cells.append(
            f'<row r="{sheet_row}"><c r="A{sheet_row}"><v>{number}</v></c>'
            f'<c r="B{sheet_row}" t="s"><v>{number + 7}</v></c>'
            f'<c r="F{sheet_row}"><v>{50000 + number}</v></c>'
            f'<c r="G{sheet_row}"><v>{number / 10}</v></c>'
            f'<c r="I{sheet_row}"><v>{30000 + number}</v></c></row>'
        )
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", f'<sst xmlns="{namespace}">{shared}</sst>')
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{namespace}"><sheetData>{"".join(cells)}</sheetData></worksheet>')


def test_reads_valid_vec_workbook_without_excel_dependency(tmp_path):
    workbook = tmp_path / "district.xlsx"
    _write_workbook(workbook, "district", 88)

    result = module.read_workbook(workbook, "district")

    assert result.effective_date == "2026-09-04"
    assert len(result.records) == 88
    assert result.records[0]["geography_name"] == "Area 1"
    assert result.records[-1]["enrolled_electors"] == 50088


def test_rejects_wrong_area_type(tmp_path):
    workbook = tmp_path / "region.xlsx"
    _write_workbook(workbook, "region", 8)

    with pytest.raises(ValueError, match="expected District workbook"):
        module.read_workbook(workbook, "district")
