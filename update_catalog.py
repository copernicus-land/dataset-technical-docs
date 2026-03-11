"""
Scan the docs/ folder and generate (or update) catalog.json.

Usage:
    python update_catalog.py            # uses ./docs as default
    python update_catalog.py /path/to/docs
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Document-type classification
# ---------------------------------------------------------------------------
DOC_TYPES = {
    "atbd": "Algorithm Theoretical Basis Document",
    "pum": "Product User Manual",
    "qar": "Quality Assessment Report",
    "pmm": "Product Management Manual",
    "pqad": "Product Quality Assurance Document",
    "sqad": "Service Quality Assurance Document",
    "review_report": "Review Report",
}

# Patterns to match document types from file names (case-insensitive)
DOC_TYPE_PATTERNS = [
    (re.compile(r"_ATBD_", re.IGNORECASE), "atbd"),
    (re.compile(r"_PUM_", re.IGNORECASE), "pum"),
    (re.compile(r"_QAR_", re.IGNORECASE), "qar"),
    (re.compile(r"_PMM_", re.IGNORECASE), "pmm"),
    (re.compile(r"_PQAD", re.IGNORECASE), "pqad"),
    (re.compile(r"_SQAD", re.IGNORECASE), "sqad"),
    (re.compile(r"ReviewReport", re.IGNORECASE), "review_report"),
]

# ---------------------------------------------------------------------------
# Variable full names
# ---------------------------------------------------------------------------
VARIABLE_NAMES = {
    "ba": "Burnt Area",
    "dmp": "Dry Matter Productivity",
    "eta": "Evapotranspiration",
    "fapar": "Fraction of Absorbed Photosynthetically Active Radiation",
    "fcover": "Fraction of Vegetation Cover",
    "gdmp": "Gross Dry Matter Productivity",
    "gpp": "Gross Primary Production",
    "hf": "Heat Flux",
    "lai": "Leaf Area Index",
    "lc": "Land Cover",
    "lcfm-lcm": "Land Cover Fine Map - Land Cover Map",
    "lcfm-tcd": "Land Cover Fine Map - Tree Cover Density",
    "lcm": "Land Cover Map",
    "lie": "Lake Ice Extent",
    "lsp": "Land Surface Phenology",
    "lst": "Land Surface Temperature",
    "lst-daily-cycle": "Land Surface Temperature Daily Cycle",
    "lst-tci": "Land Surface Temperature - Temperature Condition Index",
    "lswt-nrt": "Lake Surface Water Temperature (Near Real Time)",
    "lswt-offline": "Lake Surface Water Temperature (Offline)",
    "lwq-nrt": "Lake Water Quality (Near Real Time)",
    "lwq-reproc": "Lake Water Quality (Reprocessed)",
    "lwq": "Lake Water Quality",
    "ndvi": "Normalized Difference Vegetation Index",
    "ndvi-lts": "NDVI Long Term Statistics",
    "ndvi-sts": "NDVI Short Term Statistics",
    "npp": "Net Primary Production",
    "sce": "Snow Cover Extent",
    "ssm": "Surface Soil Moisture",
    "swe": "Snow Water Equivalent",
    "swi": "Soil Water Index",
    "swi-static": "Soil Water Index (Static Layers)",
    "swi-timeseries": "Soil Water Index (Time Series)",
    "tcd": "Tree Cover Density",
    "toc": "Top-of-Canopy Reflectance",
    "wb": "Water Bodies",
    "wl-lakes": "Water Level - Lakes",
    "wl-rivers": "Water Level - Rivers",
}

# ---------------------------------------------------------------------------
# CLMS product categories (consistent with https://land.copernicus.eu/en/products)
# ---------------------------------------------------------------------------
VARIABLE_CATEGORIES = {
    "ba": "Vegetation",
    "dmp": "Vegetation",
    "fapar": "Vegetation",
    "fcover": "Vegetation",
    "gdmp": "Vegetation",
    "gpp": "Vegetation",
    "lai": "Vegetation",
    "lsp": "Vegetation",
    "ndvi": "Vegetation",
    "ndvi-lts": "Vegetation",
    "ndvi-sts": "Vegetation",
    "npp": "Vegetation",
    "lst": "Temperature and Reflectance",
    "lst-daily-cycle": "Temperature and Reflectance",
    "lst-tci": "Temperature and Reflectance",
    "toc": "Temperature and Reflectance",
    "wb": "Water Bodies",
    "lwq": "Water Bodies",
    "lwq-nrt": "Water Bodies",
    "lwq-reproc": "Water Bodies",
    "lswt-nrt": "Water Bodies",
    "lswt-offline": "Water Bodies",
    "wl-lakes": "Water Bodies",
    "wl-rivers": "Water Bodies",
    "lie": "Water Bodies",
    "sce": "Snow",
    "swe": "Snow",
    "ssm": "Soil Moisture",
    "swi": "Soil Moisture",
    "swi-static": "Soil Moisture",
    "swi-timeseries": "Soil Moisture",
    "eta": "Evapotranspiration",
    "hf": "Evapotranspiration",
    "lc": "Land Cover",
    "lcm": "Land Cover",
    "lcfm-lcm": "Land Cover",
    "lcfm-tcd": "Land Cover",
    "tcd": "Land Cover",
}


def classify_document(filename: str) -> str:
    """Return the document type key, or 'other'."""
    for pattern, doc_type in DOC_TYPE_PATTERNS:
        if pattern.search(filename):
            return doc_type
    return "other"


def parse_product_id(folder_name: str) -> dict | None:
    """
    Parse a product folder name like 'ndvi_global_300m_10daily_v2'
    into its component fields.  Returns None for special folders
    (those starting with '_').
    """
    if folder_name.startswith("_"):
        return None

    # Pattern: <variable>_<coverage>_<resolution>_<frequency>_<version>
    # variable may contain hyphens (e.g. lst-daily-cycle, lwq-nrt)
    pattern = re.compile(
        r"^(?P<variable>[a-z][a-z0-9\-]*)"
        r"_(?P<coverage>[a-z]+)"
        r"_(?P<resolution>[a-z0-9.]+)"
        r"_(?P<frequency>[a-z0-9]+)"
        r"_(?P<version>v[0-9.]+)$",
        re.IGNORECASE,
    )
    match = pattern.match(folder_name)
    if not match:
        return {"variable": folder_name}

    return match.groupdict()


def scan_product_folder(docs_dir: Path, folder_name: str) -> dict:
    """Build a catalog entry for a single product folder."""
    folder_path = docs_dir / folder_name
    files = sorted(f for f in os.listdir(folder_path) if os.path.isfile(folder_path / f))

    # Classify documents
    documents = {}
    for f in files:
        doc_type = classify_document(f)
        documents.setdefault(doc_type, []).append(f"docs/{folder_name}/{f}")

    entry = {"id": folder_name, "documents": documents, "file_count": len(files)}

    # Parse structured fields from folder name
    parsed = parse_product_id(folder_name)
    if parsed:
        for key in ("variable", "coverage", "resolution", "frequency", "version"):
            if key in parsed:
                entry[key] = parsed[key]
        # Add full variable name and CLMS category
        var_key = parsed.get("variable", "").lower()
        if var_key in VARIABLE_NAMES:
            entry["variable_full_name"] = VARIABLE_NAMES[var_key]
        if var_key in VARIABLE_CATEGORIES:
            entry["category"] = VARIABLE_CATEGORIES[var_key]

    return entry


def build_catalog(docs_dir: Path) -> dict:
    """Scan docs_dir and build the full catalog."""
    folders = sorted(
        f
        for f in os.listdir(docs_dir)
        if os.path.isdir(docs_dir / f)
    )

    products = []
    special = []

    for folder in folders:
        entry = scan_product_folder(docs_dir, folder)
        if folder.startswith("_"):
            special.append(entry)
        else:
            products.append(entry)

    catalog = {
        "title": "Copernicus Global Land Service - Product Documentation Catalog",
        "description": "Machine-readable index of all product documentation.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_products": len(products),
        "document_types": DOC_TYPES,
        "special_collections": special,
        "products": products,
    }
    return catalog


def main():
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "docs"
    docs_dir = docs_dir.resolve()

    if not docs_dir.is_dir():
        print(f"Error: {docs_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    catalog = build_catalog(docs_dir)
    output_path = docs_dir.parent / "catalog.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Catalog written to {output_path}")
    print(f"  - {catalog['total_products']} products")
    print(f"  - {len(catalog['special_collections'])} special collections")


if __name__ == "__main__":
    main()
