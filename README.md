# The Ride Dolomites 2026 — Tour Companion (dummy v0.1)

Mobile-first PWA companion for The Ride Dolomites 2026. Static site, no build step.

## Files
- `index.html` — the app (HTML/CSS/JS in one file)
- `data.js` — all content: stages, event/camp/meal info, standings, sponsors, packing list
- `weather.json` — generated hourly by GitHub Actions (do not edit by hand)
- `fetch_weather.py` — Open-Meteo fetch (best_match + per-point elevation, wttr fallback)
- `.github/workflows/fetch_weather.yml` — hourly cron + manual trigger
- `manifest.webmanifest`, `sw.js`, `icon*.png`, `icon.svg` — PWA install assets

## What is dummy vs real
- **Real (from the official page):** event name, dates, stage names, towns, official km/HM, 3 camps, 3 round-trips.
- **From your GPX:** profile shapes + map lines (knowingly partial — Proloog 42 km vs 60, E2 not yet a loop, E5 not yet returning to Levico).
- **Placeholder:** cols/segments (named after real Dolomite passes but positioned on GPX peaks), feed-station positions, meal times, notices, standings, sponsors.

## Deploy (GitHub Pages)
1. New repo `the-ride-dolomites-2026`, push these files.
2. Settings → Pages → deploy from `main` / root.
3. (Optional) custom subdomain: add a `CNAME` file with e.g. `dolomites.the-ride.cc` and a DNS CNAME record `dolomites → <user>.github.io`.
4. Actions tab → run "Fetch weather" once to seed `weather.json`.

## Editing content
Everything lives in `data.js`. Stage figures (`dist`/`gain`/`loss`) are the Komoot/official override values shown everywhere. Replace `profile`/`mapCoords` when real GPX lands. Evening updates (meal times, next start, notices) are in `event.days`.

## Demo
Use the "Demo dag" stepper in the header to preview any day (today/tomorrow focus, weather suppression, KM-to-finish). "nu" returns to the real date..
