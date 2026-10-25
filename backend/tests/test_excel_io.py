"""Uji modul Excel: workbook register baru & penambahan baris ke workbook register yang sudah ada."""
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import excel_io  # noqa: E402

H = ["Kode Poligon GC", "Volume As-mined (BCM)", "GC Au (g/t)", "Pit", "Shift"]


def _register_like_user(p: Path):
    """Tiru format register user: judul di baris 1-2, header di baris 4, tabel Excel, 2 baris data."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Register"
    ws["A1"] = "REGISTER POLIGON GC - AS-MINED"
    ws["A2"] = "Input oranye: ..."
    for j, h in enumerate(["Kode Poligon GC", "Volume As-mined (BCM)", "Densitas Override", "GC Au (g/t)", "Pit", "Shift"], 1):
        ws.cell(4, j, h)
    ws.append(["P2_240_15_0101DS_LGSF_SPL", 383, None, 0.70, "P2", "Siang"])
    ws.append(["P2_240_13_0101DS_HGSF_ROM", 213, None, 1.17, "P2", "Siang"])
    ws.add_table(Table(displayName="tblRegister", ref="A4:F6"))
    wb.save(p)


def test_build_register_roundtrip(tmp_path):
    data = excel_io.build_register(H, [["A_1", 10.5, 0.7, "P2", "Siang"]])
    f = tmp_path / "r.xlsx"
    f.write_bytes(data)
    ws = load_workbook(f).active
    assert [c.value for c in ws[1]] == H
    assert ws["A2"].value == "A_1" and ws["B2"].value == 10.5


def test_append_matches_by_header_and_extends_table(tmp_path):
    f = tmp_path / "reg.xlsx"
    _register_like_user(f)
    rows = [["P1_255_11_0101DS_LGOX_SPO", 461, 0.75, "P1", "Siang"],
            ["P2_240_15_0101DS_LGSF_SPL", 999, 9.9, "P2", "Siang"]]  # sudah ada -> dilewati
    r = excel_io.append_rows(f, None, H, rows, key_header="Kode Poligon GC")
    assert r["header_row"] == 4 and r["added"] == 1
    assert r["skipped_existing"] == ["P2_240_15_0101DS_LGSF_SPL"]
    assert r["backup"] and Path(r["backup"]).exists()
    ws = load_workbook(f)["Register"]
    assert ws["A7"].value == "P1_255_11_0101DS_LGOX_SPO"
    assert ws["B7"].value == 461 and ws["C7"].value is None and ws["D7"].value == 0.75  # kolom dicocokkan nama
    assert ws.tables["tblRegister"].ref == "A4:F7"


def test_missing_column_reported(tmp_path):
    f = tmp_path / "reg.xlsx"
    _register_like_user(f)
    r = excel_io.append_rows(f, "Register", H + ["Kolom Tidak Ada"], [["X_1", 1, 0.1, "P2", "Malam", "?"]], backup=False)
    assert r["missing_columns"] == ["Kolom Tidak Ada"] and r["added"] == 1


def _register_with_formulas(p: Path):
    """Seperti sheet GC_Polygon user: baris data sudah berisi rumus (L = Pit dari kode), baris 7-10 kosong."""
    wb = Workbook()
    ws = wb.active
    ws.title = "GC_Polygon"
    for j, h in enumerate(["Kode Poligon GC", "Volume As-mined (BCM)", "GC Au (g/t)", "Pit"], 1):
        ws.cell(4, j, h)
    ws["A5"], ws["B5"], ws["C5"] = "P2_240_15_0101DS_LGSF_SPL", 383, 0.7
    ws["A6"], ws["B6"], ws["C6"] = "P2_240_13_0101DS_HGSF_ROM", 213, 1.17
    for r in range(5, 11):
        ws.cell(r, 4, f'=IF($A{r}="","",LEFT($A{r},2))')
    ws.add_chart(__import__("openpyxl.chart", fromlist=["BarChart"]).BarChart(), "F2")  # grafik harus tetap ada
    wb.save(p)


def test_patch_writes_inputs_only_and_keeps_formulas(tmp_path):
    import zipfile
    from gcex_backend import xlsx_patch
    f = tmp_path / "om.xlsx"
    _register_with_formulas(f)
    with zipfile.ZipFile(f) as z0:
        parts_before = {i.filename: z0.read(i.filename) for i in z0.infolist()}
    H = ["Kode Poligon GC", "Volume As-mined (BCM)", "GC Au (g/t)", "Pit", "Kolom Lain"]
    rows = [["P1_274_05_0101DS_HGSF_ROM", 412.5, 1.43, "P1", "x"], ["P2_240_15_0101DS_LGSF_SPL", 1, 1, "P2", "x"]]
    plan = xlsx_patch.write_register(f, H, rows, dry_run=True)
    assert plan["rows"] == [{"code": "P1_274_05_0101DS_HGSF_ROM", "row": 7, "action": "baru"}]
    assert plan["formula_columns_kept"] == ["Pit"] and plan["missing_columns"] == ["Kolom Lain"]
    with zipfile.ZipFile(f) as z0:
        assert z0.read("xl/worksheets/sheet1.xml") == parts_before["xl/worksheets/sheet1.xml"]  # dry run tidak mengubah
    r = xlsx_patch.write_register(f, H, rows)
    assert r["added"] == 1 and r["first_row"] == 7 and Path(r["backup"]).exists()
    ws = load_workbook(f)["GC_Polygon"]
    assert ws["A7"].value == "P1_274_05_0101DS_HGSF_ROM" and ws["B7"].value == 412.5 and ws["C7"].value == 1.43
    assert ws["D7"].value == '=IF($A7="","",LEFT($A7,2))'  # rumus tidak ditimpa
    with zipfile.ZipFile(f) as z:
        for name, data in parts_before.items():  # semua bagian lain (grafik dll) tetap identik
            if name not in ("xl/worksheets/sheet1.xml", "xl/workbook.xml"):
                assert z.read(name) == data, name
    upd = xlsx_patch.write_register(f, H, [["P1_274_05_0101DS_HGSF_ROM", 420, 1.5, "P1", ""]], mode="update")
    assert upd["updated"] == 1 and load_workbook(f)["GC_Polygon"]["B7"].value == 420
