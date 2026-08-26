# TRD-2026 — build 2026-08-26 (v1.98 → v1.99)

Files in this zip: `index.html`, `data.js`, `manifest.webmanifest`,
`gpx/gpx-etappe5.gpx`, `climbs/segment-gardena.png`.

Drop all 5 into the repo at their listed paths, overwriting what's there.
Same file works for both `TRD-2026` (production) and `TRD-2026-TEST` — see
item 1, this is what makes that true.

---

## 1. Cover/gate — restored, switched by URL

- `index.html` — restored the original pre-v1.81 `#cover` splash (real
  `<img>` of `cover-photo.jpg`, black gradient overlay, logo + "DOLOMITES
  2026" + tap prompt clustered at the bottom, title styled like the header's
  own skewed logotype) verbatim from the old build Jacco supplied, and
  restored `#gate` (password screen) exactly as it already was.
- Switched by the existing `IS_TEST_URL` mechanism (`/TRD-2026-TEST/i.test
  (location.href)`, built 2026-08-22): `#cover` shows on `TRD-2026`, no
  password step at all; `#gate` shows on `TRD-2026-TEST`, unchanged
  behaviour. Only one of the two ever renders.
- `cover-photo.jpg` is referenced by filename only — same convention as
  `logo-transparent.png`. It's already in the repo per Jacco; nothing else
  needed for it to show.
- `APP_VERSION`: `1.98` → `1.99`.

## 2. Zoom cap + rotation lock

- `index.html` viewport meta: added `maximum-scale=1.0`. Caps pinch-zoom on
  the page itself without fully disabling it (`user-scalable=no` was
  deliberately avoided — real accessibility regression for pinch-to-zoom
  text-size users). Climb-profile/segment charts, the camping map, and the
  route map all run their own separate zoom handling, unaffected.
- `manifest.webmanifest`: added `"orientation": "portrait-primary"`.
  Android honors this when installed to the home screen; iOS Safari does
  not expose orientation lock to web content at all (no manifest key fixes
  that) — worth knowing before an iPhone-landscape test reads as a bug.

## 3. Etappe 5 GPX / VP2

- `gpx/gpx-etappe5.gpx` replaced with the new file (real VP2 waypoint,
  accommodating the actual verzorgingspost location).
- `data.js`, stage 5 (Etappe 5):
  - `dist`: `115` → `116`
  - `loss`: `3380` → `3390` (`gain` unchanged, `2420`, already matched)
  - `wxPoints[VP2]`: lat/lon `46.075359/11.474861` → `46.070150/11.471764`,
    `km` `87.6` → `88.4`, `ele` `610` → `636`, `tbd:true` removed
  - `wxPoints[Finish]`: `km` `115.2` → `115.6` (this stage's own real
    GPX-parsed total — same convention every other stage's Finish point
    already uses, independent of the Komoot-sourced headline `dist`)
  - `warnings`: `"km 90,1 — Drinkwaterpunt"` → `"km 90,5 — Drinkwaterpunt"`
    (found during the check: the new GPX's real water-fountain waypoint
    sits at km 90.529, shifted downstream by the VP2 detour)
  - `mapCoords` (401-point map polyline) regenerated from the new GPX —
    distance-resampled at the same ~288m average spacing as the original,
    snapped to real trackpoints, so the map now draws the actual ~0.55km
    detour into VP2 instead of the old alignment.
  - `gpxFile` path unchanged (`gpx/gpx-etappe5.gpx`) — same filename, new
    content.

## 4. Three stale col map pins + Gardena chart (2026-08-24 audit)

- `data.js` `lat`/`lon`, data-only:
  - Passo Brocon (Etappe 1): `46.118614, 11.688537` → `46.109120, 11.648785`
  - Passo di Pramadiccio (Etappe 5): `46.317449, 11.490387` →
    `46.322204, 11.486115`
  - Passo Giau (Etappe 4): `46.482649, 12.053127` → `46.482504, 12.054644`
- `climbs/segment-gardena.png` regenerated at `km_top=25.82` (was 25.70,
  120m short of the segment's own already-corrected 5.58km length). Same
  house style (`climb_chart.py`, `ORANGE_STOPS`, `bin_km=0.25,
  label_bin_km=0.5`), boundaries only.

## 5. SOS two-choice screen

- Noodnummer button in the header no longer dials directly — opens a
  full-screen choice: **Bel 112** (top, solid red, "Bij levensgevaar of
  spoedeisende hulp") or **Bel The Ride noodnummer** (below, white/rose
  border, "Voor hulp van de organisatie (geen 112-spoed)"). Reuses the
  existing map-zoom overlay's structure (dark background, circular
  top-right close button).
- The real emergency number (`RIDE.event.emergency`) now lands on the
  choice screen's own link, not the header button.

## 6. Campingschema card

- New card at the top of the Camping tab, above the 4 camp cards: one row
  per night (date → which camp), derived live from `campSchedule`'s own
  `camp`/`pm`/`iso` fields — not a hand-maintained list. Today's row bold +
  rose; nights before today struck through (reuses the Prep tab's own
  done-item styling, `.pitem.done .lbl`).

---

## Verified

- Headless (Playwright): `IS_TEST_URL=false` → cover shows, no password
  input anywhere, tap dismisses into the real app. `IS_TEST_URL=true`
  (real `/TRD-2026-TEST/` path) → gate shows, password check works
  unchanged. SOS overlay opens/closes, correct `tel:` link. Campingschema
  renders all 7 nights with correct past/active/future styling against a
  simulated live date. Quick-link rose border intact. Viewport meta
  correct. Full 6-stage × 5-tab render sweep: zero `undefined`/`NaN`, zero
  new console errors (the only errors seen are this offline sandbox's
  known network-blocked noise — fonts/Leaflet/weather.json — not
  regressions).
- `data.js` diff: exactly the fields listed above changed, nothing else
  moved (confirmed by full recursive before/after diff, mapCoords excluded
  from the diff listing since it's a wholesale regenerated array by
  design).
- Not independently verified in this session: `shift_dates.py`
  (TEST's date-shifting script) isn't available here to run directly —
  nothing above touches a date/`iso` field, so no interaction is expected,
  but worth a real check on TEST once this is live there.
