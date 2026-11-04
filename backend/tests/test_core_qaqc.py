"""Uji ruang kerja QAQC DB-Ex: rumus CRM / Blank / Duplikat sama dengan makro workbook QAQC, impor workbook (upsert per
Sample_ID, ID ganda), panel kontrol, ringkasan per kelas kadar / zona / batch, lampiran, QAQC data bor, ekspor Excel, grafik,
laporan. Semua data fiktif."""
import io
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "backend"))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))
from gcex_backend import core_dh, core_io, core_qaqc as q  # noqa: E402


@pytest.fixture()
def prj(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "foto"
    (d / "XX-1").mkdir(parents=True)
    Image.new("RGB", (200, 150)).save(d / "XX-1" / "XX-1_Box1_0.00-3.00.jpg")
    core_io._PROJECTS.clear()
    q._STORES.clear()
    return d, tmp_path


def _rows(head, body):
    return [head] + [list(r) for r in body]


def test_formulas_match_workbook_macros(prj):
    d, _ = prj
    s = q.store(str(d))
    q.upsert(s, "master_crm", _rows(["Standard_Name", "Certified_Mean", "Certified_SD"], [("CRM-A", 0.556, 0.017)]), 0, "uji")
    q.upsert(s, "assay_import", _rows(["Batch_ID", "Hole_ID", "Sample_ID", "Sample_Type", "Lab_Au_ppm"],
                                      [("B1", "Z9_100_01", "QA_001_Z9", "Standard", 0.55), ("B2", "Z9_100_02", "QA_003_Z9", "Standard", 0.48),
                                       ("B2", "Z9_100_02", "QA_010_Z9", "Blank", 0.02)]), 0, "uji")
    q.upsert(s, "crm_data", _rows(["Sample_ID", "Standard_Name", "Lab_Grade"],
                                  [("QA_001_Z9", "CRM-A", 0.55), ("QA_002_Z9", "CRM-A", 0.51), ("QA_003_Z9", "CRM-A", 0.48),
                                   ("QA_004_Z9", "CRM-X", 0.5)]), 0, "uji")
    q.upsert(s, "blank_data", _rows(["Sample_ID", "Standard_Name", "Lab_Grade"],
                                    [("QA_010_Z9", "Blank", 0.02), ("QA_011_Z9", "Blank", 0.01), ("QA_012_Z9", "Blank", "<0.01")]), 0, "uji")
    q.upsert(s, "dup_data", _rows(["Original_ID", "Duplicate_ID", "Original", "Duplicate", "Zona"],
                                  [("QA_020_Z9", "QA_021_Z9", 0.05, 0.04, "Z9"), ("QA_022_Z9", "QA_023_Z9", 0.01, 0.01, ""),
                                   ("QA_024_Z9", "QA_025_Z9", 0.2, 0.9, "Z9"), ("QA_026_Z9", "QA_027_Z9", 0, 0.3, "Z9")]), 0, "uji")
    r = q.analyze(s)
    crm = {x["sample_id"]: x for x in r["crm"]}
    # Z = (Lab - Mean) / SD dibulatkan 2 desimal (RoundJS) -> status seperti makro CRM_Run
    assert (crm["QA_001_Z9"]["z"], crm["QA_001_Z9"]["status"]) == (-0.35, "PASS")
    assert (crm["QA_002_Z9"]["z"], crm["QA_002_Z9"]["status"]) == (-2.71, "WARNING (>2SD)")
    assert (crm["QA_003_Z9"]["z"], crm["QA_003_Z9"]["status"], crm["QA_003_Z9"]["batch"]) == (-4.47, "FAIL (>3SD)", "B2")
    assert crm["QA_004_Z9"]["status"] == "" and "CRM-X (1)" in r["warnings"][0]
    cs = r["crm_summary"][0]
    assert (cs["n"], cs["mean_lab"], cs["pwf"]) == (3, 0.5133, "1 / 1 / 1 (33.3% PASS)")
    assert abs(cs["sd_lab"] - 0.035119) < 1e-5 and cs["sd_text"] == "0.0351 vs 0.017"
    # Blank: PASS bila <= cut-off 0.01 ('<0.01' dibaca 0.005)
    bl = {x["sample_id"]: x for x in r["blank"]}
    assert [bl[k]["status"] for k in ("QA_010_Z9", "QA_011_Z9", "QA_012_Z9")] == ["FAIL (>Cut-Off)", "PASS", "PASS"]
    assert bl["QA_012_Z9"]["grade"] == 0.005 and bl["QA_010_Z9"]["ratio"] == 2
    # Duplikat: HARD = |O-D|/(O+D), RPD = (O-D)/rata-rata, ARD = HARD; O atau D <= 0 tidak dinilai
    dp = {x["dup_id"]: x for x in r["dup"]}
    a = dp["QA_021_Z9"]
    assert abs(a["hard"] - 1 / 9) < 1e-12 and abs(a["rpd"] - 2 / 9) < 1e-12 and a["status"] == "FAIL (>10%)" and a["mean"] == 0.045
    assert dp["QA_023_Z9"]["status"] == "PASS" and dp["QA_023_Z9"]["zona"] == "Z9" and dp["QA_027_Z9"]["status"] == ""
    assert r["dup_valid"] == 3 and "1 pasangan duplikat tidak dinilai" in r["warnings"][1]
    ds = {x["kelas"]: x for x in r["dup_summary"]}
    assert ds["≤ 0.10 g/t"]["n"] == 2 and ds["≤ 0.10 g/t"]["pass"] == 1 and ds["> 0.30 g/t"]["n"] == 1
    assert ds["Total Semua Pair"]["n"] == 3
    # Lampiran C: rasio maks/min >= 3 dan maks >= 0.2
    assert [x["orig_id"] for x in r["app_c"]] == ["QA_024_Z9"] and abs(r["app_c"][0]["ratio"] - 4.5) < 1e-9
    assert len(r["app_a"]) == 2 and len(r["app_b"]) == 1
    # dashboard per zona
    z = r["dashboard"][0]
    assert z["zona"] == "Z9" and z["crm"].startswith("Tidak memuaskan — 33.3% PASS (1/3)") and z["dup"].startswith("Tidak memuaskan")
    assert z["blank"] == "Memuaskan — 66.7% PASS (2/3)" or z["blank"].startswith("Tidak memuaskan")
    assert z["overall"] == "Perlu tindakan korektif"
    b = {x["batch"]: x for x in r["batches"]}
    assert b["B2"]["status"] == "FAIL" and b["B1"]["status"] == "PASS"
    assert q.assess("blank", 10, 0, 0, q.SETTINGS_DEFAULT) == ("Bersih, namun hanya 10 blank", 2)
    assert q.assess("dup", 9, 0, 1, q.SETTINGS_DEFAULT)[0] == "Memuaskan — 90.0% PASS (9/10)"
    assert q.r2_label(0.9554) == "Sangat Baik (Korelasi Kuat / Presisi Tinggi)" and q.extract_zone("dp_145703_z4") == "Z4"


def test_import_workbook_upsert_settings_exports(prj):
    from buat_data_dummy import qaqc_data
    d, tmp = prj
    wbp = qaqc_data(tmp / "dummy")
    s = q.store(str(d))
    reps = {r["table"]: r for r in q.import_file(s, str(wbp), "auto", "Rina")}
    assert set(reps) == {"master_crm", "assay_import", "crm_data", "blank_data", "dup_data"}
    assert reps["blank_data"]["dup_keys"] == 1 and reps["crm_data"]["new"] == 48 and reps["dup_data"]["new"] == 48
    reps2 = {r["table"]: r for r in q.import_file(s, str(wbp), "auto", "Rina")}
    assert reps2["crm_data"]["new"] == 0 and reps2["crm_data"]["updated"] == 48 and reps2["blank_data"]["updated"] == 48
    r = q.analyze(s)
    assert r["zones"] == ["Z7", "Z8"] and r["totals"]["crm"] == {"PASS": 42, "WARN": 3, "FAIL": 3}
    assert {g["tipe"] for g in r["dup_groups"]} == {"Lapangan", "Coarse", "Pulp"}
    assert [x["overall"] for x in r["dashboard"]] == ["Perlu tindakan korektif", "Perlu tindakan korektif"]
    # panel kontrol: zona & cut-off & tipe duplikat
    q.save_settings(s, {"zone": "z8", "blank_cutoff": "0,04", "dup_type": "Pulp"}, "Rina")
    r = q.analyze(s)
    assert r["zones"] == ["Z8"] and r["totals"]["blank"]["FAIL"] == 0 and {g["tipe"] for g in r["dup_groups"]} == {"Pulp"}
    with pytest.raises(ValueError):
        q.save_settings(s, {"hard_max": "sepuluh"}, "Rina")
    q.save_settings(s, dict(q.SETTINGS_DEFAULT), "Rina")
    # satu tabel dari CSV (upsert) + Master_CRM disimpan dari layar
    f = tmp / "crm_baru.csv"
    f.write_text("Sample_ID;Standard_Name;Lab_Grade\nLT_09999_Z7;CRM-A;0,51\nLT_00110_Z7;CRM-A;0,512\n", encoding="utf-8")
    rep = q.import_file(s, str(f), "crm_data", "Rina")[0]
    assert (rep["new"], rep["updated"]) == (1, 1)
    q.save_master(s, [{"name": "CRM-A", "mean": "0,512", "sd": "0.015"}, {"name": "CRM-B", "mean": 1.48, "sd": 0.042},
                      {"name": "CRM-C", "mean": 0.195, "sd": 0.009}], "Rina")
    with pytest.raises(ValueError):
        q.save_master(s, [{"name": "CRM-A", "mean": 1, "sd": 0}], "Rina")
    # ekspor Excel: struktur sheet sama dengan workbook QAQC
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(q.to_xlsx(s, str(d))))
    for name in ("QAQC_Dashboard", "CRM_Data", "Duplicate_Data", "Blank_Data", "CRM_Summary", "Duplicate Summary", "Report_Appendix",
                 "Batch_Summary", "Master_CRM", "Assay_Import", "Control_Panel"):
        assert name in wb.sheetnames, name
    ws = wb["CRM_Data"]
    assert [c.value for c in ws[1]][:8] == ["Sample_ID", "Standard_Name", "Lab_Grade", "Cert_Mean", "Cert_SD", "Zona", "Status", "Z_Score"]
    assert [c.value for c in wb["Duplicate_Data"][1]][:10] == ["Original_ID", "Duplicate_ID", "Original", "Duplicate", "HARD_Result", "Status",
                                                               "Zona", "Mean_Grade", "RPD (%)", "ARD (%)"]
    assert wb["Report_Appendix"]["A1"].value == "Lampiran A. CRM berstatus WARNING dan FAIL"
    pytest.importorskip("matplotlib")
    assert "CRM_Charts" in wb.sheetnames and "Duplicate_Charts" in wb.sheetnames
    r = q.analyze(s)
    z = zipfile.ZipFile(io.BytesIO(q.charts_zip(r)))
    names = z.namelist()
    assert len(names) == len(q.chart_list(r)) and all(n.endswith(".png") for n in names) and z.read(names[1])[:4] == b"\x89PNG"
    rep = q.report(s, str(d), "Laporan uji", "Rina", "Latihan")
    h = rep["html"]
    for part in ("Ringkasan Eksekutif", "Akurasi CRM", "Kontaminasi Blank", "Presisi Duplikat", "Ringkasan per Batch Lab", "Dashboard per Zona",
                 "Lampiran A", "MERAH — PERLU TINDAKAN KOREKTIF"):
        assert part in h, part
    assert len(rep["images"]) == len(q.chart_list(r)) and all(f'img:{k}' in h for k in rep["images"])


def test_dh_checks(prj):
    d, tmp = prj
    p = core_io.get_project(str(d))
    col = [["Hole", "E", "N", "RL", "EOH"], ["XX-1", 1000, 2000, 300, 30], ["XX-2", 1010, 2000, 300, None], ["XX-3", 0, 2005, 300, 20]]
    core_dh.do_import(p, "collar", col, 0, {"hole": 0, "x": 1, "y": 2, "z": 3, "depth": 4}, [], "replace")
    sv = [["Hole", "Depth", "Dip", "Azi"], ["XX-1", 0, -60, 90], ["XX-1", 15, -58, 92], ["XX-1", 30, 55, 95], ["XX-1", 33, -40, 140],
          ["XX-9", 0, -90, 0]]
    core_dh.do_import(p, "survey", sv, 0, {"hole": 0, "at": 1, "dip": 2, "azi": 3}, [], "replace")
    asy = [["Hole", "From", "To", "Sample", "Au"], ["XX-1", 0, 2, "S1", 0.1], ["XX-1", 1.5, 3, "S2", 0.2], ["XX-1", 5, 6, "S3", -0.01],
           ["XX-1", 29, 31, "S1", 0.3], ["XX-7", 0, 1, "S9", 0.1]]
    core_dh.do_import(p, "assay", asy, 0, {"hole": 0, "from": 1, "to": 2},
                      [{"i": 3, "src": "Sample", "name": "Sample", "type": "s", "use": True}, {"i": 4, "src": "Au", "name": "Au", "type": "n", "use": True}],
                      "replace")
    r = q.dh_checks(str(d))
    codes = {x["code"] for x in r["issues"]}
    assert {"C1", "C2", "S1", "S2", "S3", "S5", "A1", "A2", "A3", "A4", "A5", "A6", "C3"} <= codes
    s2 = [x for x in r["issues"] if x["code"] == "S2"]
    assert s2[0]["hole"] == "XX-1" and s2[0]["item"] == "30 m" and r["light"] == "MERAH" and not r["empty"]
    assert next(x for x in r["issues"] if x["code"] == "A6")["item"] == "S1"
    assert r["summary"][0]["severity"] == "MERAH" and r["counts"]["holes"] == 5
    assert q.dh_checks(str(d), dict(q.SETTINGS_DEFAULT, dh_dip_jump=200, dh_azi_jump=200))["red"] == r["red"]


def test_manual_edit_save_table(prj):
    """Input manual / tempel dari Excel: simpan seluruh tabel, validasi kunci ganda & angka, urutan = seq, peringatan silang."""
    d, _ = prj
    s = q.store(str(d))
    q.save_master(s, [{"name": "CRM-X", "mean": 1.0, "sd": 0.05}], "uji")
    rows = [{"sample_id": f"QX_{i:03d}_Z9", "std": "CRM-X", "grade": f"{1 + (i % 3 - 1) * 0.02:.2f}".replace(".", ","), "zona": ""}
            for i in range(1, 6)]
    j = q.save_table(s, "crm_data", rows + [{"sample_id": "", "std": "", "grade": "", "zona": ""}], "uji")
    assert j["ok"] and j["n"] == 5 and j["new"] == 5 and j["warnings"] == []
    # galat: ID ganda (beda huruf besar/kecil), angka tidak valid, kolom wajib kosong -> tidak ada yang disimpan
    bad = rows + [{"sample_id": "qx_002_z9", "std": "CRM-X", "grade": "1.0"}, {"sample_id": "QX_009_Z9", "std": "CRM-X", "grade": "satu"},
                  {"sample_id": "QX_010_Z9", "std": "", "grade": "1"}]
    j = q.save_table(s, "crm_data", bad, "uji")
    assert not j["ok"] and {(e["row"], e["col"]) for e in j["errors"]} == {(5, "sample_id"), (6, "grade"), (7, "std")}
    assert q.counts(s)["crm_data"] == 5
    # ubah satu nilai, hapus satu baris, tambah satu CRM tanpa master + Sample_ID yang juga ada di Blank_Data
    q.upsert(s, "blank_data", [["Sample_ID", "Lab_Grade"], ["QX_100_Z9", 0.005]], 0, "uji")
    rows2 = [dict(r) for r in rows[1:]]
    rows2[0]["grade"] = "1.20"
    rows2.append({"sample_id": "QX_100_Z9", "std": "CRM-Y", "grade": "<0.01"})
    j = q.save_table(s, "crm_data", rows2, "uji")
    assert j["ok"] and (j["new"], j["updated"], j["deleted"]) == (1, 1, 1)
    assert any("Blank_Data" in w for w in j["warnings"]) and any("CRM-Y" in w for w in j["warnings"])
    tr = q.table_rows(s, "crm_data")
    assert [r["sample_id"] for r in tr][:2] == ["QX_002_Z9", "QX_003_Z9"] and tr[0]["grade"] == 1.2 and tr[-1]["grade"] == 0.005
    res = q.analyze(s)
    assert any(r["status"].startswith("FAIL") for r in res["crm"])  # 1.20 = Z 4,0
    # duplikat: Duplicate_ID kosong -> Original_ID|DUP, tipe dinormalkan
    j = q.save_table(s, "dup_data", [{"orig_id": "QX_200_Z9", "dup_id": "", "orig": "0.5", "dup": "0.52", "tipe": "pulp"}], "uji")
    assert j["ok"] and q.table_rows(s, "dup_data")[0]["dup_id"] == "QX_200_Z9|DUP" and q.table_rows(s, "dup_data")[0]["tipe"] == "Pulp"
    with pytest.raises(ValueError):
        q.save_table(s, "master_crm", [], "uji")
