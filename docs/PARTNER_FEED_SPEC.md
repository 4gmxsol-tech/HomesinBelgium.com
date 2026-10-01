# Partner Listing Feed Specification

Homes in Belgium is designed to accept authorized property inventory from agencies, developers and listing partners.

## Required principle

Only inventory that Homes in Belgium is authorized to display should be imported as live listings. Do not scrape, mirror or republish third-party listings without permission or a contractual/API/feed arrangement.

## Minimum listing fields

- id — stable unique partner listing identifier
- title
- city / cityName
- type — apartment, house, land, commercial, other
- status — sale or rent
- price
- currency — ISO 4217, normally EUR
- image — licensed display image URL
- source.name
- source.url — canonical listing page on the partner's site
- source.listingId
- lastVerifiedAt — ISO 8601 timestamp
- availabilityStatus — active, unavailable, pending-review

## Recommended fields

- beds
- baths
- area / areaUnit
- description
- address or area label, subject to partner/privacy rules
- gallery
- energy information
- features
- partner.name
- partner.contactUrl
- attribution text
- tracking parameters / referral URL

## Commercial fields

Keep commercial attribution separate from public listing content:

- partnerId
- agreementId
- referralMode — lead, click, affiliate, commission, fixed-fee
- referralUrl
- commissionNotes — internal only
- campaignId

These fields should not be exposed publicly unless the agreement permits it.

## Freshness

Every live listing should carry a source identifier and a verification timestamp. Feeds should be refreshed according to the partner agreement. Listings that become unavailable should be removed or marked unavailable rather than left looking active.

## Integration paths

The importer can later support:

1. API / REST
2. XML feed
3. CSV feed
4. Manual partner upload

The public site should consume a normalized internal listing shape regardless of the upstream format.
