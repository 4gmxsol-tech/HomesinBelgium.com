# Partner Import

The importer converts an **authorized** JSON, CSV or XML partner feed into the normalized inventory used by Homes in Belgium.

## Commands

From the repository root:

```bash
python3 scripts/import_listings.py data/partner-feed.example.json \
  --partner-id example-partner \
  --source-name "Example Partner" \
  --source-type api \
  --source-url https://example.com \
  --referral-mode commission \
  --referral-url https://example.com/listings/example-001 \
  --campaign-id hib-demo
```

The example feed is fictional and must never be presented as real inventory.

## Supported formats

- JSON: an array, or an object containing `listings` / `properties`
- CSV: first row is the header
- XML: `<listing>` elements containing simple child fields

Common field aliases are normalized automatically for IDs, title, city, type, status, price, currency, beds, baths, area, image and listing URL.

## Freshness and removals

Every imported live listing receives `lastVerifiedAt`. Use `--stale-hours` to mark old partner records unavailable.

Use `--full-feed` only when the partner confirms the feed is a complete active-inventory snapshot. Listings absent from such a feed are then marked unavailable.

## Safety

Only import inventory covered by a partner agreement, API authorization, feed permission or explicit commercial arrangement. The importer does not scrape websites.

Referral destinations are stored with the listing and are resolved by `/go.html`; arbitrary query-string URLs are not accepted.
