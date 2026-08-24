# 2026-08-24 — Source link in event descriptions

## What

`generate_ics.to_ics_event` now appends `Źródło: <url>` to each VEVENT
`DESCRIPTION` (after the existing description text, if any).

## Why

The iCal `URL` property is hidden by many calendar clients (e.g. Google
Calendar), so from the event alone it was unclear where it came from. Putting the
link in the description makes it visible and clickable.

## Notes

- The `URL` property is still set as well. Events without a scraped description
  get a description that is just the source link.
