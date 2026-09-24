"""Build the prediction-safe 2014 multi-party geography translation surface.

The bridge uses only the restored 2011 ABS/VIC geographic and census payloads
and the final 2013 Victorian Assembly boundary shapefile.  It deliberately
does not read any Victorian 2014 election result or transition artefact.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import pyproj
import shapefile
from shapely.geometry import Polygon, shape as make_shape
from shapely.ops import transform
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/historical-2014-sources"
OUT = ROOT / "model/data/processed/historical_2014_crosswalk_core_features_long.csv"
MANIFEST = ROOT / "metadata/historical-replay-2014-crosswalk-build-manifest.json"

SOURCES = {
    "bcp_sa1_2011_vic": ("2011_BCP_SA1_for_VIC_short-header.zip", 52198605,
                           "0d94aaf6ee3f8db0e770ba5f384e3594ef87cff4930200d8fe521c7113678fe6"),
    "mesh_block_shape_2011_vic": ("1270055001_mb_2011_vic_shape.zip", 39426176,
                                   "6d8cdb31efd4852d826218b8ebc241ff07f9f927602976941ddb92ff3defd6a9"),
    "census_counts_mesh_block_2011": ("censuscounts_mb_2011_aust.csv", 6478814,
                                       "62a24f1705e98bf847c016d00d44dd99cbb5f70439945563417861cb44477239"),
    "state_assembly_2013_shape": ("STATEASSEMBLY2013 SHP.zip", 7590829,
                                   "d9a97e8f35f8403656a454bb6c00e986d2721e6a12ad13d9ef0d327d451aef69"),
}
FEATURES = ("mortgage_share", "renter_share", "owned_outright_share",
            "separate_house_share", "apartment_share", "age_18_34_share",
            "age_65_plus_share")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def number(value: str | None) -> float:
    if value is None:
        return 0.0
    value = value.strip()
    if not value or value in {"..", "-", "np", "NP"}:
        return 0.0
    return float(value.replace(",", ""))


def unzip_member(z: zipfile.ZipFile, suffix: str, directory: Path) -> Path:
    names = [n for n in z.namelist() if n.lower().endswith(suffix.lower())]
    if len(names) != 1:
        raise ValueError(f"expected one {suffix} member, found {names}")
    target = directory / Path(names[0]).name
    with z.open(names[0]) as source, target.open("wb") as dest:
        shutil.copyfileobj(source, dest)
    return target


def read_bcp() -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    path = SOURCE / SOURCES["bcp_sa1_2011_vic"][0]
    with zipfile.ZipFile(path) as z:
        b01_name = next(n for n in z.namelist() if n.endswith("2011Census_B01_VIC_SA1_short.csv"))
        b32_name = next(n for n in z.namelist() if n.endswith("2011Census_B32_VIC_SA1_short.csv"))
        def load(name: str) -> dict[str, dict[str, float]]:
            with z.open(name) as handle:
                rows = csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig"))
                return {row["region_id"]: row for row in rows}
        return load(b01_name), load(b32_name)


def feature_values(b01: dict[str, float], b32: dict[str, float]) -> dict[str, float] | None:
    total_dwellings = number(b32.get("Total_Total"))
    total_people = number(b01.get("Tot_P_P"))
    if total_dwellings <= 0 or total_people <= 0:
        return None
    rental_fields = ("R_RE_Agt_Total", "R_ST_h_auth_Total", "R_Psn_not_in_s_hh_Total",
                     "R_Hs_cop_cty_ch_gp_Total", "R_Ot_landld_typ_Total", "R_Landld_typ_NS_Total")
    values = {
        "mortgage_share": number(b32.get("O_MTG_Total")) / total_dwellings,
        "renter_share": sum(number(b32.get(k)) for k in rental_fields) / total_dwellings,
        "owned_outright_share": number(b32.get("O_OR_Total")) / total_dwellings,
        "separate_house_share": number(b32.get("Total_DS_Sep_house")) / total_dwellings,
        "apartment_share": number(b32.get("Total_DS_Flat_unit_apart")) / total_dwellings,
        # The 2011 BCP has 20-24 and 25-34 bands, but no 18-19 split.  We
        # retain only directly observed ages rather than inventing 18/19.
        "age_18_34_share": (number(b01.get("Age_20_24_yr_P")) + number(b01.get("Age_25_34_yr_P"))) / total_people,
        "age_65_plus_share": (number(b01.get("Age_65_74_yr_P")) + number(b01.get("Age_75_84_yr_P")) + number(b01.get("Age_85ov_P"))) / total_people,
    }
    return {k: min(1.0, max(0.0, v)) for k, v in values.items()}


def main() -> None:
    for key, (name, size, digest) in SOURCES.items():
        path = SOURCE / name
        if not path.exists() or path.stat().st_size != size or sha256(path) != digest:
            raise RuntimeError(f"source verification failed: {key}")
    b01, b32 = read_bcp()
    with tempfile.TemporaryDirectory(prefix="vic2014-crosswalk-") as temp:
        temp_path = Path(temp)
        with zipfile.ZipFile(SOURCE / SOURCES["mesh_block_shape_2011_vic"][0]) as z:
            mb_shp = unzip_member(z, "MB_2011_VIC.shp", temp_path)
            for ext in (".shx", ".dbf", ".prj", ".cpg"):
                unzip_member(z, f"MB_2011_VIC{ext}", temp_path)
        with zipfile.ZipFile(SOURCE / SOURCES["state_assembly_2013_shape"][0]) as z:
            asm_shp = unzip_member(z, "STATE_ASSEMBLY_2013.shp", temp_path)
            for ext in (".shx", ".dbf", ".prj", ".cpg"):
                unzip_member(z, f"STATE_ASSEMBLY_2013{ext}", temp_path)
        mb_reader = shapefile.Reader(str(mb_shp))
        asm_reader = shapefile.Reader(str(asm_shp))
        mb_fields = [f[0] for f in mb_reader.fields[1:]]
        asm_fields = [f[0] for f in asm_reader.fields[1:]]
        mb_records = [dict(zip(mb_fields, row)) for row in mb_reader.records()]
        asm_records = [dict(zip(asm_fields, row)) for row in asm_reader.records()]
        if len(mb_records) != 81377 or len(asm_records) != 88:
            raise RuntimeError("unexpected geometry record count")
        mb_geoms = [Polygon() if s.shapeType == shapefile.NULL else make_shape(s.__geo_interface__) for s in mb_reader.shapes()]
        asm_geoms = [make_shape(s.__geo_interface__) for s in asm_reader.shapes()]
        project = pyproj.Transformer.from_crs("EPSG:4283", "EPSG:3111", always_xy=True).transform
        mb_geoms = [transform(project, g) if not g.is_empty else g for g in mb_geoms]
        asm_geoms = [transform(project, g) for g in asm_geoms]
        tree = STRtree(asm_geoms)
        census = {}
        with (SOURCE / SOURCES["census_counts_mesh_block_2011"][0]).open(newline="", encoding="cp1252") as handle:
            for row in csv.DictReader(handle):
                census[row["Mesh_Block_ID"]] = (number(row.get("Dwellings")), number(row.get("Persons_Usually_Resident")))
        accum = defaultdict(lambda: {f: [0.0, 0.0] for f in FEATURES})
        matched = 0
        fractions_checked = 0
        special = 0
        uncovered = 0
        max_uncovered_fraction = 0.0
        min_intersection_coverage = 1.0
        for record, geom in zip(mb_records, mb_geoms):
            if geom.is_empty or not geom.is_valid:
                special += 1
                continue
            candidates = tree.query(geom)
            area = geom.area
            if area <= 0:
                special += 1
                continue
            intersections = []
            for idx in candidates:
                district_geom = asm_geoms[int(idx)]
                inter_area = geom.intersection(district_geom).area
                if inter_area > 0:
                    intersections.append((int(idx), inter_area / area))
            fraction_total = sum(f for _, f in intersections)
            if not intersections:
                uncovered += 1
                max_uncovered_fraction = max(max_uncovered_fraction, 1.0)
                continue
            min_intersection_coverage = min(min_intersection_coverage, fraction_total)
            max_uncovered_fraction = max(max_uncovered_fraction, 1.0 - fraction_total)
            # The two official boundary datasets have small edge slivers and
            # occasional water/outside-jurisdiction fragments.  Renormalise
            # the intersecting district fractions, never inventing a district
            # for an entirely uncovered mesh block.
            intersections = [(idx, fraction / fraction_total) for idx, fraction in intersections]
            fractions_checked += 1
            # The short BCP extracts are keyed by the seven-digit SA1 code;
            # the mesh-block shapefile carries both the 11-digit main code
            # and this 7-digit join key.
            sa1 = str(record.get("SA1_7DIG11", ""))
            vals = feature_values(b01.get(sa1, {}), b32.get(sa1, {}))
            if vals is None:
                continue
            dwellings, persons = census.get(str(record["MB_CODE11"]), (0.0, 0.0))
            weight = persons if persons > 0 else dwellings
            if weight <= 0:
                continue
            matched += 1
            for idx, fraction in intersections:
                district = asm_records[idx]
                district_id = str(district["DISTRICTC"]).strip()
                district_name = str(district["DISTRICT"]).strip()
                w = weight * fraction
                for feature, value in vals.items():
                    accum[(district_id, district_name)][feature][0] += value * w
                    accum[(district_id, district_name)][feature][1] += w
        rows = []
        for (district_id, district_name), features in sorted(accum.items(), key=lambda x: (x[0][0], x[0][1])):
            if any(den <= 0 for _, den in features.values()):
                raise RuntimeError(f"missing feature mass for {district_id} {district_name}")
            for feature in FEATURES:
                num, den = features[feature]
                rows.append({"district_id": district_id, "district_name": district_name,
                             "feature_id": feature, "value": f"{num / den:.12f}",
                             "cutoff": "2014-11-28", "source_role": "prediction-safe-prior-geographic-translation"})
        if len({r["district_id"] for r in rows}) != 88 or len(rows) != 616:
            raise RuntimeError(f"expected 88 districts x 7 features, got {len(rows)} rows")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    manifest = {
        "schemaVersion": 1, "status": "pass", "algorithmVersion": "historical_2014_mesh_area_fraction_sa1_bcp_v1",
        "cycleId": "vic_la_2014", "informationCutoff": "2014-11-28", "targetElectionOutcomesUsed": False,
        "sources": {k: {"path": f"work/historical-2014-sources/{v[0]}", "sizeBytes": v[1], "sha256": v[2]} for k, v in SOURCES.items()},
        "geometry": {"meshRecords": 81377, "meshSpatialRecords": fractions_checked, "meshSpecialPurposeRecords": special,
                     "meshUncoveredRecords": uncovered, "maxUncoveredFraction": max_uncovered_fraction,
                     "minimumRawIntersectionCoverage": min_intersection_coverage,
                     "assemblyDistricts": 88, "projectedCrs": "EPSG:3111", "sourceCrs": "EPSG:4283", "intersectionCoverageTolerance": 1e-5},
        "features": list(FEATURES), "featureCells": len(rows), "weighting": "census persons usually resident, dwelling fallback; mesh-district area fraction",
        "featureDefinitions": {"age_18_34_share": "directly observed BCP 20-24 + 25-34 bands (18-19 unavailable in source)",
                              "tenureAndDwellingShares": "BCP B32 totals over Total_Total"},
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT), "rows": len(rows)},
        "forbiddenInputs": ["model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv", "2014 Victorian election outcomes"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
