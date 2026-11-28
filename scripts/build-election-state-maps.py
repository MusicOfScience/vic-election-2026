#!/usr/bin/env python3
"""Build small, topology-preserving paths from the public VEC boundary ZIP."""
import argparse
import csv
from hashlib import sha256
import json
from math import cos, radians
from pathlib import Path
import re
from zipfile import ZipFile

import shapely
from shapely.affinity import affine_transform
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://vec.vic.gov.au/-/media/f67f3c2562c9439c880150ede051991f.zip"
CENTRES = (
    ("Geelong", 144.36, -38.15),
    ("Ballarat", 143.85, -37.56),
    ("Bendigo", 144.28, -36.76),
    ("Shepparton", 145.40, -36.38),
    ("Mildura", 142.16, -34.19),
    ("Warrnambool", 142.48, -38.38),
    ("Wodonga", 146.89, -36.12),
    ("Latrobe Valley", 146.53, -38.20),
)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def to_path(geometry):
    def coord(x, y):
        return f"{x:.2f}".rstrip("0").rstrip(".") + "," + f"{y:.2f}".rstrip("0").rstrip(".")

    parts = geometry.geoms if geometry.geom_type == "MultiPolygon" else [geometry]
    return "".join(
        "M" + " ".join(coord(x, y) for x, y in list(ring.coords)[:-1]) + "Z"
        for part in parts for ring in (part.exterior, *part.interiors)
    )


def map_frame(geometry):
    left, bottom, right, top = shapely.total_bounds(geometry)
    x_scale = 880 / (right - left)
    y_scale = x_scale / cos(radians((top + bottom) / 2))
    return ([x_scale, 0, 0, -y_scale, 10 - left * x_scale, 10 + top * y_scale],
            [900, round((top - bottom) * y_scale + 20, 1)])


def build(archive_path):
    with (ROOT / "model/data/processed/district_region_membership_2026.csv").open() as file:
        membership = list(csv.DictReader(file))
    districts = {slug(row["district_name"]): row["district_name"] for row in membership}
    regions = {slug(row["region_name"]): row["region_name"] for row in membership}
    if (len(districts), len(regions)) != (88, 8):
        raise ValueError("The 2026 contest universe does not contain 88 districts and eight regions")
    outputs = {}
    with ZipFile(archive_path) as archive:
        for house, key, roster in (("assembly", "district", districts), ("council", "region", regions)):
            data = json.loads(archive.read(f"state_{house}_2022.geojson"))
            features = sorted(data["features"], key=lambda row: slug(row["properties"][key]))
            geometries = [shape(row["geometry"]) for row in features]
            labels = [slug(row["properties"][key]) for row in features]
            if set(labels) != roster.keys() or len(labels) != len(roster):
                raise ValueError(f"{house} geography does not match the 2026 contest universe")
            if not all(shapely.is_valid(geometries)) or not shapely.coverage_is_valid(geometries):
                raise ValueError(f"{house} source geometry has overlaps or mismatched edges")
            transform, view_box = map_frame(geometries)
            reduced = shapely.coverage_simplify(geometries, 0.004)
            projected = [shapely.set_precision(affine_transform(item, transform), 0.01) for item in reduced]
            if (any(shapely.is_empty(projected)) or not all(shapely.is_valid(projected))
                    or not shapely.coverage_is_valid(projected)):
                raise ValueError(f"{house} simplified geometry failed topology checks")
            entries = []
            for label, row, geometry in zip(labels, features, projected, strict=True):
                props = row["properties"]
                entries.append({"id": label, "name": roster[label], "boundaryCode": props[f"{key}_code"],
                                "path": to_path(geometry)})
            if len({row["boundaryCode"] for row in entries}) != len(entries):
                raise ValueError(f"{house} source boundary codes are not unique")
            outputs[house] = {"viewBox": "0 0 " + " ".join(map(str, view_box)), "areas": entries}
            if house == "assembly":
                centres = []
                for name, lon, lat in CENTRES:
                    location = Point(lon, lat)
                    if not any(item.covers(location) for item in geometries):
                        raise ValueError(f"{name} map centre is outside Assembly boundaries")
                    point = affine_transform(location, transform)
                    centres.append({"name": name, "x": round(point.x, 2), "y": round(point.y, 2)})
                outputs[house]["centres"] = centres
    return {"schemaVersion": 1, "source": SOURCE,
            "sourceSha256": sha256(archive_path.read_bytes()).hexdigest(), **outputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "app/election-state-maps.generated.json"
    result = json.dumps(build(args.archive), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.check:
        if target.read_text() != result:
            parser.exit(1, "Generated map asset differs\n")
    else:
        target.write_text(result)
    print(f"Verified 88 Assembly districts and eight Council regions ({len(result):,} characters)")


if __name__ == "__main__":
    main()
