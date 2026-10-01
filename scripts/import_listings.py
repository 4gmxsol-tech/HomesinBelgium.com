#!/usr/bin/env python3
"""Import authorized partner property feeds into Homes in Belgium's normalized inventory.

Supported input formats: JSON, CSV and XML (standard library only).
This tool never discovers or scrapes third-party listings. It expects an authorized feed.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "listings.json"

ALIASES = {
    "id": ["id", "listingId", "listing_id", "propertyId", "property_id"],
    "title": ["title", "name", "propertyTitle", "property_title"],
    "city": ["city", "town", "municipality"],
    "type": ["type", "propertyType", "property_type"],
    "status": ["status", "listingStatus", "listing_status", "transaction"],
    "price": ["price", "amount", "listingPrice", "listing_price"],
    "currency": ["currency", "currencyCode", "currency_code"],
    "beds": ["beds", "bedrooms", "bedroomCount", "bedroom_count"],
    "baths": ["baths", "bathrooms", "bathroomCount", "bathroom_count"],
    "area": ["area", "surface", "surfaceArea", "surface_area", "sqm"],
    "areaUnit": ["areaUnit", "area_unit", "surfaceUnit", "surface_unit"],
    "image": ["image", "imageUrl", "image_url", "photo", "photoUrl", "photo_url"],
    "url": ["url", "listingUrl", "listing_url", "propertyUrl", "property_url"],
    "description": ["description", "summary"],
    "availabilityStatus": ["availabilityStatus", "availability_status", "availability"],
    "lastVerifiedAt": ["lastVerifiedAt", "last_verified_at", "verifiedAt", "verified_at"],
    "referralUrl": ["referralUrl", "referral_url", "affiliateUrl", "affiliate_url"],
    "campaignId": ["campaignId", "campaign_id"],
}

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None

def pick(row, key):
    for alias in ALIASES[key]:
        if alias in row and clean(row[alias]) is not None:
            return clean(row[alias])
    return None

def slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return value or "unknown"

def number(value, integer=False):
    value = clean(value)
    if value is None:
        return None
    value = value.replace("€", "").replace("$", "").replace("£", "").replace(",", "").replace(" ", "")
    try:
        n = float(value)
        return int(n) if integer else n
    except ValueError:
        raise ValueError(f"Invalid numeric value: {value}")

def normalize_type(value):
    v = slug(value)
    if v in {"flat", "condo", "condominium"}:
        return "apartment"
    if v in {"villa", "townhouse", "town-home", "single-family", "single-family-home"}:
        return "house"
    if v in {"plot", "building-land"}:
        return "land"
    if v in {"business", "office", "retail"}:
        return "commercial"
    return v if v in {"apartment", "house", "land", "commercial", "other"} else "other"

def normalize_status(value):
    v = slug(value)
    if v in {"for-rent", "rental", "lease", "leased"}:
        return "rent"
    if v in {"for-sale", "sale", "sold"}:
        return "sale"
    return v if v in {"sale", "rent"} else "sale"

def xml_to_rows(path):
    root = ET.parse(path).getroot()
    nodes = root.findall(".//listing")
    if not nodes and root.tag.lower().endswith("listing"):
        nodes = [root]
    rows = []
    for node in nodes:
        row = {}
        for child in node.iter():
            if child is node:
                continue
            if len(child) == 0:
                row[child.tag.split("}")[-1]] = clean(child.text)
        rows.append(row)
    return rows

def load_rows(path, fmt):
    if fmt == "auto":
        fmt = path.suffix.lower().lstrip(".")
        if fmt == "": fmt = "json"
    if fmt == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("listings", data.get("properties", data))
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError("JSON feed must be an array or an object containing listings/properties.")
        return [dict(x) for x in data]
    if fmt == "csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            return [dict(x) for x in csv.DictReader(f)]
    if fmt == "xml":
        return xml_to_rows(path)
    raise ValueError("Unsupported format. Use json, csv, xml or auto.")

def normalize(row, args, verified_at):
    listing_id = pick(row, "id")
    title = pick(row, "title")
    city = pick(row, "city")
    if not listing_id or not title or not city:
        raise ValueError("Every listing needs id, title and city.")
    price = number(pick(row, "price"))
    if price is None or price < 0:
        raise ValueError(f"Listing {listing_id}: price must be a non-negative number.")
    currency = (pick(row, "currency") or args.currency).upper()
    if len(currency) != 3:
        raise ValueError(f"Listing {listing_id}: currency must be a 3-letter code.")
    typ = normalize_type(pick(row, "type"))
    status = normalize_status(pick(row, "status"))
    source_id = listing_id
    image = pick(row, "image")
    url = pick(row, "url")
    if not url or not urlparse(url).scheme in {"http", "https"}:
        raise ValueError(f"Listing {listing_id}: url must be an absolute http(s) URL.")
    if image and urlparse(image).scheme not in {"http", "https"}:
        raise ValueError(f"Listing {listing_id}: image must be an absolute http(s) URL.")
    referral_url = pick(row, "referralUrl") or args.referral_url
    if referral_url and urlparse(referral_url).scheme not in {"http", "https"}:
        raise ValueError(f"Listing {listing_id}: referralUrl must be an absolute http(s) URL.")
    item = {
        "id": f"{slug(args.partner_id)}-{source_id}",
        "title": title,
        "city": slug(city),
        "cityName": city,
        "type": typ,
        "typeName": typ.title(),
        "status": status,
        "statusName": "For rent" if status == "rent" else "For sale",
        "price": price,
        "currency": currency,
        "priceLabel": f"{currency} {price:,.0f}" + (" / month" if status == "rent" else ""),
        "beds": number(pick(row, "beds"), integer=True),
        "baths": number(pick(row, "baths")),
        "area": number(pick(row, "area")),
        "areaUnit": pick(row, "areaUnit") or "m²",
        "areaLabel": None,
        "image": image,
        "url": url,
        "description": pick(row, "description"),
        "isIllustrative": False,
        "source": {
            "type": args.source_type,
            "name": args.source_name,
            "url": args.source_url,
            "listingId": source_id
        },
        "partner": {"id": args.partner_id, "name": args.source_name},
        "lastVerifiedAt": verified_at,
        "availabilityStatus": pick(row, "availabilityStatus") or "active",
        "referral": {
            "mode": args.referral_mode,
            "url": referral_url,
            "campaignId": pick(row, "campaignId") or args.campaign_id
        },
        "attribution": args.attribution
    }
    if item["area"] is not None:
        item["areaLabel"] = f'{item["area"]:g} {item["areaUnit"]}'
    return item

def validate_listing(item):
    required = ["id","title","city","type","status","price","currency","source","isIllustrative","availabilityStatus"]
    missing = [k for k in required if k not in item]
    if missing:
        return [f"missing {', '.join(missing)}"]
    errors = []
    if not isinstance(item["price"], (int,float)) or item["price"] < 0:
        errors.append("price must be a non-negative number")
    if len(str(item["currency"])) != 3:
        errors.append("currency must be a 3-letter code")
    if not isinstance(item["source"], dict) or not item["source"].get("listingId"):
        errors.append("source.listingId is required")
    if item["isIllustrative"] is False and not item.get("lastVerifiedAt"):
        errors.append("live partner listings require lastVerifiedAt")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--format", default="auto", choices=["auto","json","csv","xml"])
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--partner-id", required=True)
    p.add_argument("--source-name", required=True)
    p.add_argument("--source-type", default="partner-feed")
    p.add_argument("--source-url", default=None)
    p.add_argument("--currency", default="EUR")
    p.add_argument("--referral-mode", default="none", choices=["none","lead","click","affiliate","commission","fixed-fee"])
    p.add_argument("--referral-url", default=None)
    p.add_argument("--campaign-id", default=None)
    p.add_argument("--attribution", default="Partner listing")
    p.add_argument("--full-feed", action="store_true", help="Mark existing listings from this partner that are missing from the feed as unavailable.")
    p.add_argument("--stale-hours", type=float, default=48, help="Mark older live partner listings unavailable.")
    args = p.parse_args()

    input_path = Path(args.input)
    rows = load_rows(input_path, args.format)
    verified_at = now_iso()
    imported = [normalize(r, args, verified_at) for r in rows]
    for item in imported:
        errors = validate_listing(item)
        if errors:
            raise ValueError(f'{item["id"]}: ' + "; ".join(errors))

    output_path = Path(args.output)
    existing = {"version":"1.0","generatedAt":verified_at[:10],"environment":"partner","listings":[],"schemaVersion":"1.1"}
    if output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
    current = existing.get("listings", [])
    source_ids = {x["source"]["listingId"] for x in imported}
    partner_items = [x for x in current if x.get("partner",{}).get("id") == args.partner_id]
    other_items = [x for x in current if x.get("partner",{}).get("id") != args.partner_id]

    if args.full_feed:
        for old in partner_items:
            if old.get("source",{}).get("listingId") not in source_ids:
                old["availabilityStatus"] = "unavailable"
                old["lastVerifiedAt"] = verified_at
        partner_items = [x for x in partner_items if x.get("source",{}).get("listingId") not in source_ids]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.stale_hours)
    for old in partner_items:
        stamp = old.get("lastVerifiedAt")
        if stamp:
            try:
                dt = datetime.fromisoformat(stamp.replace("Z","+00:00"))
                if dt < cutoff:
                    old["availabilityStatus"] = "unavailable"
            except ValueError:
                old["availabilityStatus"] = "unavailable"

    merged = other_items + partner_items + imported
    # Keep demo/illustrative listings that are not partner-owned.
    merged = [x for x in merged if x.get("availabilityStatus") != "unavailable" or x.get("isIllustrative") is False]
    result = {
        "version": existing.get("version","1.0"),
        "generatedAt": verified_at[:10],
        "environment": "partner" if imported else existing.get("environment","demo"),
        "schemaVersion": "1.1",
        "listings": merged
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(imported)} listings from {args.source_name}.")
    print(f"Wrote {len(merged)} normalized listings to {output_path}.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
