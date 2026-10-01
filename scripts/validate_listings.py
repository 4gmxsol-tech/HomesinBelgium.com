#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"data/listings.json").read_text(encoding="utf-8"))
errors=[]
for i,item in enumerate(data.get("listings",[]),1):
    for key in ["id","title","city","type","status","price","currency","source","isIllustrative","availabilityStatus"]:
        if key not in item: errors.append(f"listing {i}: missing {key}")
    if not isinstance(item.get("price"),(int,float)) or item.get("price",0)<0: errors.append(f"listing {i}: invalid price")
    if len(str(item.get("currency","")))!=3: errors.append(f"listing {i}: invalid currency")
    if not isinstance(item.get("source"),dict) or not item.get("source",{}).get("listingId"): errors.append(f"listing {i}: missing source.listingId")
    if item.get("isIllustrative") is False and not item.get("lastVerifiedAt"): errors.append(f"listing {i}: live listing missing lastVerifiedAt")
    stamp=item.get("lastVerifiedAt")
    if stamp:
        try: datetime.fromisoformat(stamp.replace("Z","+00:00"))
        except ValueError: errors.append(f"listing {i}: invalid lastVerifiedAt")
if errors:
    print("\n".join(errors), file=sys.stderr); sys.exit(1)
print(f"Validated {len(data.get('listings',[]))} listings.")
