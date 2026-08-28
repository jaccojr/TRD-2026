# TRD-2026 — build 2026-08-27 (v1.99 → v2.06)

Files in this zip: `index.html`, `data.js`, `manifest.webmanifest`,
`gpx/gpx-etappe5.gpx`, `climbs/segment-gardena.png`, `_points_data.json`,
`partners/*.png` (7 files — new folder).

Drop everything into the repo at their listed paths (`_points_data.json`
goes in the repo root, alongside `gen_points.py`; `partners/` is a new
top-level folder next to `climbs/`), overwriting what's there. Same file
works for both `TRD-2026` (production) and `TRD-2026-TEST` — the
`IS_TEST_URL` switch is unchanged.

This changelog covers everything new since `CHANGELOG-2026-08-26.md`
(carried the prior 8 items — CartoDB key, partner rose border, VP2
weather, cover/gate, campingschema, etc., all still in this build).

---

## 1. Partner rotation — built

7 real partners now rotate across whichever tabs are visible, instead of
sitting in one static footer grid. SiS is out entirely (was a partner in
the old footer grid; not carried forward as an 8th or a placeholder).

- **The 7 partners**: fi'zi:k, JOIN, Kwaremont (existing links, unchanged),
  plus 4 new — Rogelli (`https://rogelli.com/`), Coca-Cola
  (`https://www.coca-cola.com/nl/nl`), Sockeloen (`https://sockeloen.com/nl`),
  U Sport (`https://www.u-sport.com/`).
- **Rotation**: every visible tab always shows 4 blocks. Each partner gets
  one guaranteed slot, round-robin'd across the tabs currently visible
  (`TAB_ORDER[eventPhase()]` — today/route/event/prep while in preview,
  today/route/event once live). Remaining slots on each tab are filled by
  a weighted-random draw from the other partners (never repeating one
  already on that tab) — fi'zi:k and U Sport are weighted 2x, everyone
  else 1x. Preview phase (4 tabs): 16 blocks total (7 guaranteed + 9
  bonus). Live phase (3 tabs, Prep drops out): 12 blocks total (7
  guaranteed + 5 bonus).
- **Computed once per real page load**, cached — doesn't reshuffle on
  every `renderAll()` call (simulator/soft-refresh reuse the same
  assignment), so a partner's placement stays put under a rider mid-
  session.
- **Tile styling rebuilt** per `TRD2026-partners-build-spec.md`: `.pgrid`
  2-column grid, `.plogo` cards now a `247/140` aspect-ratio box (was a
  fixed 70px-tall card) with 7 named per-partner `max-height`/`max-width`
  size classes so each logo can be tuned independently. Neutral `1px
  var(--line)` border (see item 2).
- Old single global footer partner grid (`.foot-logos`/`#footLogos`) is
  gone, replaced by `partnerGridHtml(tabKey)` calls at the bottom of each
  of the 4 tab renderers.
- `data.js`'s `sponsors` array rebuilt: added `cls` (per-partner CSS
  class) and `weight`, dropped `logoH`, `logo` paths now
  `partners/<name>.png`.
- 7 real partner PNGs added in a new `partners/` folder.

## 2. Border — reverted to neutral

The rose border added 2026-08-26/27 (`.link-btn`, `.spotify-btn`,
`.plogo`) is reverted back to the original `1px solid var(--line)`
hairline, applied consistently across all 7 blocks a tab can show at once
(MIJN, WhatsApp, Spotify, and the 4 partner tiles) — Jacco: "if we go for
a neutral line that would be for all 7 blocks... start with neutral."

## 3. WhatsApp channel link — live

- `WA_COMMUNITY_URL` set to the real channel:
  `https://whatsapp.com/channel/0029Vb8K51oLNSa0pwHwWv3k`.
- Button simplified: dropped the "COMMUNITY" text and the icon-left-of-
  stacked-logo layout — now just the WhatsApp icon + The Ride logo side
  by side, same `.lb-row` layout the MIJN button already uses. Dead CSS
  (`.lb-row-alt`, `.lb-stack`) removed.

## 4. Spotify playlist — updated

`RIDE.event.playlistUrl` (`data.js`) and the HTML's static fallback href
both now point to the new playlist:
`https://open.spotify.com/playlist/1dOhnSWWgLyStp3DNXXWw5`.

## 5. Campingschema card — sizing fixed

`campSchedCard()`'s inline `style="margin:0 0 14px;"` override removed —
the card now inherits `.today-card`'s standard `margin:0 16px 14px`,
matching the width of every other today-card (including the "avondprogramma"
evening-menu card).

## 6. Version

`APP_VERSION`: `1.99` → `2.00`.

## 7. Partner tile overflow — bug found and fixed same day

Jacco caught this in a live screenshot right after the first v2.00
delivery: partner tiles were overflowing off the right edge of the
screen instead of sitting in a clean 2-column grid, and it was affecting
the rest of the tab's layout too.

Root cause: `.plogo` is a CSS grid item with the new `aspect-ratio:
247/140` box, but grid items default to `min-width:auto`, which sizes
the item to fit its content's *intrinsic* width when not otherwise
constrained. The logo `<img>` inside only had a percentage `max-width:
70%` — percentages don't count for this intrinsic-sizing calculation —
so the browser fell back to each PNG's real, undecoded pixel width
(the partner logos are ~800px wide on the long side) as the tile's
effective minimum width, blowing every tile out to roughly that size
regardless of the `1fr` grid track.

Fix: added `min-width:0;overflow:hidden;` to `.plogo`, the standard
fix for this exact CSS grid behavior. Re-verified headlessly at a real
390px phone viewport: `document.body.scrollWidth` now equals
`window.innerWidth` (no horizontal overflow), all 4 tiles land at 176px
wide, cleanly 2-per-row. Re-screenshotted the Route tab's partner grid
to confirm visually. Nothing else in this build changed as part of this
fix — same partner rotation logic, same borders, same everything else.

**Follow-up, same day**: Jacco reported the fix only held on the Today
tab — Route/Event/Prep were still overflowing on his real device
(iPhone). The `min-width:0`/`overflow:hidden` fix is plain CSS on a
class shared identically by all 4 tabs, so headless Chromium testing
(160 checks: 5 device widths × 8 randomized partner draws × all 4 tabs)
came back completely clean and couldn't reproduce a per-tab difference
— pointing at a WebKit/Safari-specific edge case in how `aspect-ratio`
interacts with grid-item intrinsic sizing that Chromium doesn't share.
Hardened `.plogo` further: added `width:100%;max-width:100%;
box-sizing:border-box;` alongside the existing `min-width:0`, so the
box's width is always pinned to its grid track directly rather than
ever being inferred from `aspect-ratio` + content — this closes the
loophole regardless of which browser's intrinsic-sizing quirks are in
play. Re-verified: same 160-check sweep still clean, plus fresh
screenshots of all 4 tabs' partner grids individually (Route, Event,
Prep) confirming 2-clean-columns in each.

**To be clear about what's confirmed vs. a working theory**: the first
overflow bug (item 1 below) was diagnosed with a concrete, verified
root cause. This second report — "fine on Today, still broken on
Route/Event/Prep" — could not be reproduced in headless testing at all
(one shared CSS rule can't behave differently per tab), so the
`width:100%` hardening above is a plausible, defensive patch based on a
theory (a WebKit/Safari `aspect-ratio` quirk this sandbox can't test
directly), not a confirmed diagnosis. If it's still off after this,
the likelier explanation is a cached/stale copy being served for some
views (browser cache or a PWA service worker) rather than a remaining
CSS bug — worth ruling out with a hard refresh / clear site data before
assuming the CSS itself is still wrong.

## 8. Partner tile box — rebuilt again, dropped `aspect-ratio` entirely

Jacco confirmed the `width:100%` hardening (item 7) did not fix it —
still oversized/inconsistent partner tiles on his real iPhone. Since a
real WebKit engine isn't installable in this sandbox (network-blocked)
to test against directly, guessing at another `aspect-ratio`-based patch
wasn't a responsible next move. Instead, dropped `aspect-ratio` from
`.plogo` entirely and rebuilt the box with the old padding-top-percentage
technique, which has zero dependency on `aspect-ratio` support or any
grid/flex intrinsic-sizing edge case, in any browser, going back to the
IE era:

- `.plogo` is now a plain block-level grid item (`position:relative`,
  no `display:flex`) — CSS Grid's own default stretch behavior already
  fills a block-level item to 100% of its column track, no special
  properties needed for that part.
- Its height comes entirely from a `.plogo::before{padding-top:56.68%}`
  pseudo-element — `padding-top` as a percentage is *always* resolved
  against the box's own width, a rule with no cross-browser ambiguity.
  `56.68%` = `140/247`, the spec's box ratio.
- The logo now sits in a `.pl-inner` wrapper (`position:absolute;
  inset:0`), fully decoupled from `.plogo`'s own sizing — HTML changed
  from `<a class="plogo"><img></a>` to `<a class="plogo"><div
  class="pl-inner"><img></div></a>`.

Re-verified: same 160-case sweep (5 widths × 8 randomized partner draws
× 4 tabs) still completely clean, full functional suite re-passed
(partner counts/dupes, WhatsApp, Spotify, borders, campingschema),
fresh screenshots of Route/Prep tabs. `APP_VERSION` bumped `2.01` →
`2.02`.

**Still can't rule out a caching issue on Jacco's side as a contributing
factor** — but this rebuild removes the one CSS feature (`aspect-ratio`
on a grid item) every prior patch was pinned on, so if it's still wrong
after this on a hard-refreshed page, the next step is a real-device
screenshot with the browser's dev tools/inspector open on the `.plogo`
element to see its actual computed box model, rather than another blind
CSS iteration.

## 9. Map on the Route tab — root cause found and fixed, `APP_VERSION` 2.02→2.03

Jacco reported the "Bekijk route op kaart" map panel opens (chevron
flips, the section expands) but shows a completely blank area — no
tiles, no route line, no markers, nothing. And critically: **it happens
on every stage, not just one** — that detail ruled out a per-stage data
bug and pointed at something shared by the whole map feature.

**Diagnosed, not guessed, this time**: `index.html` was loading Leaflet
itself from an external CDN (`unpkg.com`) via a blocking `<script>` tag
in `<head>`. Reproduced the exact failure in a network-blocked test
environment — Leaflet's script fails to load, the global `L` never gets
defined, and `toggleMap()` throws a `ReferenceError` the instant it
tries to call `L.map(...)`. Because the expand/collapse toggle
(`w.classList.toggle("open")`) runs *before* that line, the section
still visually opens — chevron flips, area expands to its full height —
and then the function silently dies with nothing drawn inside it,
producing exactly the blank box Jacco described, on every stage,
completely silently (no visible error to a user, browser console only).

This app runs through Dolomites mountain roads for six days — exactly
the kind of place a rider's phone has flaky or dead cell signal — so a
hard runtime dependency on a third-party CDN just to load the mapping
*library itself* (before a single tile is even requested) was a real
robustness gap independent of whatever specifically triggered it on
Jacco's phone.

**Fix**: Leaflet 1.9.4's JS (~148KB) and CSS (~15KB) are now inlined
directly into `index.html` — no external request for the map library
at all. Verified by blocking *every* outbound network request in a
test browser (strictly harsher than real spotty cell coverage) and
confirming: `typeof L` is still `"object"`, `toggleMap()` no longer
throws, the route polyline/markers render correctly (19 layers), and
zero page errors. Map *tiles* (CARTO) still require a live connection
to actually show imagery — that part is inherent to online maps and
unchanged — but the map failing to draw its own vector overlay (route
line, start/finish, cols, VPs) should no longer be possible regardless
of network conditions.

Also folded in while touching this code: `m.attributionControl.
setPrefix(false)` removes Leaflet's own default "Leaflet | 🇺🇦" branding
line from the attribution control (a real, intentional feature of
Leaflet itself since v1.9.1 — the maintainer's solidarity statement,
not a bug — but Jacco asked for it removed). The required CARTO/OSM
attribution stays, unaffected.

`APP_VERSION`: `2.02` → `2.03`.

## 10. Sluggishness / "doesn't open a tab on the first touch" — diagnosed and fixed, `APP_VERSION` 2.03→2.04

Jacco reported the app feeling "a bit more sluggish" and not always responding to the first tap on a tab. Confirmed the production repo was up to date first (byte-identical `index.html`/`data.js` fetched fresh from `raw.githubusercontent.com/jaccojr/TRD-2026/main/`, both at `2.03`) before testing anything, so this was diagnosed against the real shipped build, not a stale local copy.

**Diagnosed, not guessed**: `renderAll()` was unconditionally rebuilding all five tab views on *every* call — `renderToday();renderRoute();renderKlass();renderEvent();renderPrep();` — even though only one tab is ever visible at a time, and even though `renderKlass()` builds a tab (Klassement) that's been unreachable dead code since `TAB_ORDER` dropped it — the in-app tab is gone, that link now goes straight to `challenges.the-ride.cc`. Measured with `performance.now()` marks around the real boot call, under 4x CPU throttle: **105.4ms** of synchronous main-thread blocking on every page load, every day-stepper move, and every tab-away-and-back soft refresh.

**Fix, and what got ruled out along the way**: only the tab actually on screen (`curTab`) now renders synchronously in `renderAll()` — measured drop to **~7ms**, a 93% cut. The other tabs are then prewarmed one at a time via chained `setTimeout(fn,0)` calls (each tick short enough to let the browser paint and handle input in between), and `showTab()` falls back to rendering a tab on the spot, exactly once, if a tap ever beats the prewarm to it — so nothing is ever shown blank or stale. `renderKlass()` is no longer called by anything.

Two more aggressive shapes were tried first and *rejected* by direct measurement rather than assumed better: a `requestIdleCallback`-based background prewarm measured *worse* under throttling (idle callbacks landed on top of the test tap: tap-to-paint went from ~134ms to ~203ms); pure on-demand rendering with zero prewarm was also worse for a tab's first-ever visit (~166ms/~203ms), since the tab's render cost — previously already finished during boot — now landed inside the tap itself. The chained-`setTimeout` version above is the one that actually measured back to baseline-or-better (median of 5 runs, real in-page click dispatch, 4x throttle, tap ~700ms after boot): click-handler 133.9ms→125.5ms, tap-to-paint 135.5ms→125.7ms — on top of the much larger, unambiguous 105ms→7ms boot-time win.

Full regression suite re-run and clean: partner rotation (16/12 blocks, zero dupes, both preview and live phase), WhatsApp/Spotify links, neutral borders, campingschema width, map still opens and draws correctly, and a worst-case rapid-tap test (all tabs clicked back-to-back with zero delay right after boot, no waiting for any prewarm) — every tab still renders complete, correct content with zero console errors.

`APP_VERSION`: `2.03` → `2.04`.

## 11. Route maps failing progressively ("first one, eventually all") — root cause found and fixed, `APP_VERSION` 2.04→2.05

Jacco reported that on `2.03`, maps on the Route tab fail "at some point" — the first one, then eventually all of them — and was explicit that it's **not** a network issue (1000up/1000down). That detail mattered: it ruled out the CDN/connectivity theory behind the item-9 fix above and pointed somewhere else entirely.

**Diagnosed, not guessed**: `renderRoute()` rebuilds every stage card's HTML (`v.innerHTML=...`) on every call — which destroys and recreates each stage's `map-N` container div. `toggleMap()` caches the Leaflet map object it creates in a `maps[num]` object and, on a second open, just calls `.invalidateSize()` on whatever's cached there rather than creating a new one. Once `renderRoute()` wipes the DOM, that cached object still exists but is now bound to a container that's no longer attached to the page — a dangling reference. The panel still opens visually (the chevron flips, the section expands), `.invalidateSize()` on the dead object silently does nothing, and no new map ever gets created on the fresh container: permanently blank, for that stage, forever.

The trigger is `renderRoute()` running while the user is on the Route tab — and that happens constantly on a phone: the app's own `visibilitychange` listener calls `softRefresh()` → `renderAll()` on **every** lock/unlock and every app-switch away and back, which is unavoidable during 6 days of actual riding. Confirmed with a headless repro: open a stage's map, call `renderAll()` (simulating exactly that lock/unlock refresh), reopen the same stage — 0 Leaflet panes, 0 tiles, completely blank. Repeated across 3 stages over 3 simulated refresh cycles: same result for every stage that had been opened before its refresh — matching "first one, eventually all" exactly, and confirming it has nothing to do with the network.

**Fix**: `renderRoute()` now tears down every live map properly before replacing the DOM — `Object.keys(maps).forEach(k => {maps[k].remove(); delete maps[k];})` — the same cleanup `setAlt()` (the A/B route toggle) already did correctly for its own single-stage case, just applied to the full-view rebuild too. Re-ran the same repro after the fix: reopening a previously-touched stage after a rebuild now renders correctly (7 panes, 6 tiles) every time, across repeated refresh cycles, with no leaked map objects left behind (`maps` only ever holds entries for maps actually still open). Full regression suite re-passed clean.

`APP_VERSION`: `2.04` → `2.05`.

## 12. Full audit against v1.99, requested by Jacco — map-over-header/footer bug found, dead code removed, `APP_VERSION` 2.05→2.06

Jacco reported the app "going backwards" since v1.99: tile sizing needing multiple patches, the map disappearing needing multiple patches, and now — screenshots attached — the expanded map rendering **over** the sticky header and the fixed footer nav, plus tab switches (especially Vandaag→Route) feeling sluggish and sometimes needing a second tap. He asked for a full audit against v1.99 with real root causes, not more patching, and for any leftover dead code/patches to be cleaned out.

**Did the audit for real**: cloned the actual production repo and diffed the real `a8d923a` commit (the last commit at `APP_VERSION="1.99"`) against the current `index.html`, line by line, rather than relying on memory of what changed. Confirmed: outside the Leaflet CSS/JS block and the final `.plogo` partner-tile rules, **nothing else touches `position`, `z-index`, `overflow`, or `transform` anywhere in the whole diff** — `.hd-top` (header) and `.tabs` (footer nav) are byte-identical to v1.99. That rules out the partner-rotation work as the cause of the header/footer bug.

**Root cause, found by structural CSS audit**: Leaflet's own stylesheet gives its corner control box (`.leaflet-top`/`.leaflet-bottom` — the box the zoom +/− buttons live in) `z-index:1000`. `.map-c` only gets `position:relative` from Leaflet's own init code, with no `z-index` of its own, so it never forms a real stacking context — meaning that `z-index:1000` box is compared directly against the app's own chrome (header `z-index:50`, footer nav `z-index:60`) in the same global stack. Confirmed via computed-style inspection in headless testing. Chromium's own `overflow:hidden` clipping on `.map-wrap` still contains it correctly there (couldn't get it to visually escape in this sandbox), but Leaflet drives its pan/zoom with CSS transforms, and iOS Safari has a well-documented bug where a transformed/GPU-composited descendant can escape an `overflow:hidden` ancestor that isn't itself promoted to a compositing layer — which matches Jacco's screenshots (a Leaflet zoom control rendered where the header should be) far better than a plain layout mistake would.

**This was dormant, not new**: the map was blank (CDN load failure) from before v1.99 until the 2026-08-27 CDN-inlining fix made it render for the first time — so this stacking conflict has been sitting in the CSS the whole time, just never triggered because there was never any real map content to escape. It surfaced today because the map got fixed today, not because of the partner-tile work. **Being straight about the limits here**: this sandbox has no real WebKit/Safari to test against (confirmed unavailable in an earlier attempt), so the exact Safari compositing mechanism isn't independently verified the way the other fixes in this build were — the diagnosis is a structural CSS finding plus a well-known, well-documented bug category that matches the visual evidence closely.

**Fix**: `.map-wrap` now gets `isolation:isolate` (gives it a real stacking context — nothing inside can ever compete against page-level `z-index` again, regardless of what Leaflet sets internally), `contain:paint` (the modern, spec-guaranteed version of "nothing paints outside this box," stronger than `overflow:hidden` alone), and `transform:translateZ(0)` (the standard, specifically-documented fix for the Safari bug — promotes the *clipping* element itself to its own compositing layer, which is what closes the gap when composited content escapes a non-composited clipper). All three are defense-in-depth for the same failure mode, applied together since none of them can be independently verified against real Safari here.

**Tab-switching sluggishness / double-tap**: plausibly the same underlying issue — a misplaced Leaflet layer sitting over the footer nav could absorb the first tap on a tab button (second tap then lands correctly once things settle). Flagged as a working theory, not confirmed; the header/footer fix above should be re-tested for this too rather than assuming it's a separate problem.

**Dead code removed** (not just left uncalled) per Jacco's explicit ask: `renderKlass()`, `#v-klassement`, `setCat()`, `setMode()`, `curCat`/`curMode`, and the `TAB_DEF.klassement` entry are gone entirely — this was the Klassement tab, unreachable via any in-app navigation since `TAB_ORDER` dropped it (that link goes straight to `challenges.the-ride.cc`). Also audited the `.plogo` partner-tile CSS specifically for leftover patches from the earlier back-and-forth (the `min-width:0`/`overflow:hidden` patch, then the `width:100%`/`box-sizing:border-box` hardening) — confirmed clean: only the one final, complete rule set from the padding-top-percentage rebuild exists; each patch fully replaced the last rather than stacking.

Full regression suite re-passed: partner rotation (16/12 blocks, zero dupes), WhatsApp/Spotify, borders, campingschema, the map-staleness-after-refresh fix (item 11), the rapid-tap stress test, and the boot-render performance number (still ~7ms, unaffected by this CSS change).

`APP_VERSION`: `2.05` → `2.06`.

**What Jacco should check next**: retest on the real iPhone — both the header/footer overlap and the double-tap. If either persists, the most useful next diagnostic is Safari's own Web Inspector (Mac + iPhone via Settings → Safari → Advanced → Web Inspector), since that's real WebKit and this sandbox can't get there.

## 13. Rose brand colour realigned, 3 app icons rebuilt, "haal locatie op" replaced with a WhatsApp-noodnummer button — `APP_VERSION` 2.06→2.07

Jacco brought a longer pre-launch shortlist ("let's discuss all this first"), and asked to have the first three items — colour, icons, and the location button — built and commented, with the rest of the list held for a follow-up pass. This section covers only those three; see "Not in this build" below for what's still open.

**Rose colour realigned to the organisation's own brand colour.** Jacco shared a screenshot of the organisation's actual rose as the reference. `--rose` (`#EC96D3`) is sampled pixel-exact from that screenshot's background — not eyeballed. Only one shade was given, so the other three custom properties (`--rose-deep`, `--rose-soft`, `--rose-line`) are *derived*, not independently specified: measured the old palette's own internal HSL relationship between its four shades (hue held constant, lightness/saturation shifted proportionally) and applied that same relationship to the new reference colour. This is flagged in-code as a derivation for Jacco to confirm or override, not presented as an authoritative brand value — if the organisation has an official spec for the darker/lighter shades, those should replace the derived ones directly.

Everything that reads the CSS custom properties updated automatically. Three things don't read them and needed a manual pass, found by grepping for the old hex values rather than assuming the properties covered everything:
- `manifest.webmanifest`'s `theme_color` (`#F59BB0` → `#EC96D3` — this is what colours the OS status bar / task switcher when the PWA is installed, and it's a separate file, not CSS).
- The loading bar's gradient companion shade (a hardcoded second colour stop that was never a variable, kept as a fixed RGB-offset from `--rose` to preserve its subtle two-tone look).
- The hidden TEST-only "Weer testen" debug button and its diagnostic panel — 6 occurrences of the old `#E51F4D` (`--rose-deep`'s old value) hardcoded instead of referencing the variable, all replaced with `var(--rose-deep)`.

**Flagged, not touched**: `climb_chart.py`'s `ROSE`/`ROSE_DEEP` constants, and the static `climbs/segment-gardena.png` image they produce, still use the *old* rose baked directly into pixels. Regenerating that PNG is a separate step (needs the Python chart pipeline re-run and the new file redeployed) — deliberately not bundled into this HTML/CSS change. Still an open inconsistency until that's done.

**3 app icons rebuilt from Jacco's reference mockup.** Jacco supplied a second image — a cleaner icon/tile design he wants used going forward — and asked for the 3 icon files the app actually needs, in the new rose. Confirmed the exact requirement first (manifest's `icons` array + the HTML's `<link rel="icon">`/`<link rel="apple-touch-icon">` tags) rather than guessing a count: 180×180, 192×192, 512×512.

Rebuilding required separating the mockup's navy logo mark from its background reliably — the source JPEG has genuine white lettering *and* an incidental white corner-cutout that a naive colour threshold would have treated the same way. Solved geometrically: found the mark's bounding box using only the unambiguous navy colour (which has no lookalike elsewhere in the image), padded it into a safe "protected region," and only trusted the white-vs-background classification inside that region — everywhere else is forced to pure new-rose background regardless of what colour the source pixel was. Within the protected region, a smooth colour-distance-based alpha blend (not a hard cutoff) preserves the mark's original anti-aliasing instead of leaving jagged edges.

Output: full-bleed new-rose (`#EC96D3`) square background, navy (`#2e3440`) wordmark, matching the mockup. While rebuilding, found and fixed two pre-existing bugs in the old icon files, unrelated to the colour change: `icon-192.png` was actually 180×180 despite its filename and the manifest's declared size, and `icon-512.png` didn't exist at all even though the manifest referenced it twice (192 and the maskable 512 entry) — meaning the PWA install icon and any maskable-icon platform were silently falling back to whatever the OS does for a missing image. Both are now correctly sized real files.

**"Deel mijn locatie" replaced with a WhatsApp-noodnummer button.** The old button used real `navigator.geolocation` to read out the rider's coordinates as a lat/lon + Google Maps link. Jacco went for a simpler approach instead: the organisation will publish their own "how to share your location via WhatsApp" instructions separately, so the app's job is just to open a WhatsApp chat with the org's noodnummer contact. `getLoc()` (and the `#locout`/`.hd-locout` output area it wrote into) is removed entirely, not just unused.

New `<a id="waNoodnummer">` link: `href` is set in `renderAll()` from `RIDE.event.emergency` (the same number "Bel The Ride noodnummer" already calls — flagged in-code in case a separate, dedicated WhatsApp number should be used instead), `target="_blank"` so it hands off to the WhatsApp app/web client. Per Jacco's confirmation ("badge green background with phone indeed"), the icon is the classic WhatsApp app-icon treatment — solid `#25D366` green rounded-square badge with a white phone-handset glyph — deliberately a different, bolder style from the thin outline-on-white WhatsApp icon the "whatsapp theride" community-link button already uses elsewhere; that's an intentional pair of treatments per Jacco's ask, not leftover inconsistency. Button border also switched to WhatsApp green (`#25D366`) to match.

**Verified** (`verify_new_button_and_color.js` + a targeted `.hd-actions` screenshot with `SIM_DATE` pinned to the Proloog day, since this button only shows during the live event phase): `APP_VERSION` reads `2.07`; `waHref` resolves to `https://wa.me/31618418240`; `waTarget` is `_blank`; the button's computed border colour is WhatsApp green; the header/nav bar's computed background and `--rose` both read the new `#EC96D3`; `#locout` and `window.getLoc` are both confirmed gone from the DOM/global scope; zero console errors. Screenshot confirms the button renders correctly next to the existing red "Noodnummer" button — solid green badge, white phone glyph, green border, black text label. Full regression suite (partner rotation, WhatsApp/Spotify links, campingschema, map staleness fix, rapid-tap stress test) re-passed clean.

`APP_VERSION`: `2.06` → `2.07`.

## 14. WhatsApp-noodnummer button label simplified — `APP_VERSION` 2.07→2.08

Jacco: "it doesnt need a separate whatsapp text on the button, that is what the logo is for. like the other whatsapp button." The "whatsapp theride" community-link button never spells out "WhatsApp" in its own text either — it relies on its icon alone — so the new noodnummer button now follows the same convention. Label changed from "WhatsApp noodnummer" to just "Noodnummer", the same word the neighboring bel-112 button already uses; the two stay visually distinct by icon (solid WhatsApp badge vs. phone glyph) and border colour (WhatsApp green vs. red), not by wording.

Re-verified: `APP_VERSION` reads `2.08`, href/target/border colour/header colour all unchanged from item 13, zero console errors. Screenshot confirms both header buttons now read "Noodnummer" with their icons doing the differentiation.

`APP_VERSION`: `2.07` → `2.08`.

## 15. TEST repo dates restored to real production dates, `shift_dates.py` to be removed — prepared 2026-08-28, not `index.html`-related

Jacco: "move data into test and remove shift dates?" — cloned both repos fresh to confirm the current state directly rather than working from memory. Production is at `APP_VERSION 2.08` (already deployed). TEST's `data.js` still carries the old rolling offset from the now-dead `shift_dates.py`: stage `iso` values `2026-08-23`→`2026-08-28` instead of the real `2026-09-13`→`2026-09-18`, and — found while checking — the stage `date` label text ("zo 13/9" etc.) was **never updated to match**, so TEST's own `data.js` was internally inconsistent (iso said August, the label text still said September) even before this fix.

**Confirmed `shift_dates.py` is genuinely dead**, not just deprioritized: `.github/workflows/weather.yaml`'s own header comment states it plainly — "no date-shifting step... this run does NOT use" the rolling `shift_dates.py` mechanism — and grepping the whole repo confirms no workflow invokes it. `build_offset_test.py` is a separate, still-relevant manual tool (its own docstring explicitly distinguishes itself from `shift_dates.py`) — not touched by this change.

**Diffed prod's `data.js` against TEST's field-by-field** (JSON-normalized, not text diff) to confirm the *only* differences anywhere in the file are date-related (23 `iso` values + the embedded `(dd/mm)` text in two `campSchedule` fields) — nothing else about TEST's data has drifted from production. Same check on `_points_data.json`: identical structure, only the `date` field per point differs. This means dropping production's `data.js` and `_points_data.json` straight into TEST is a complete, correct fix — not a partial one needing hand-reconciliation.

**This session has no push access to either GitHub repo** (confirmed directly — a throwaway test branch push to TEST was rejected by the git proxy as an unauthorized repository), so the corrected files are prepared and delivered for Jacco to drop in manually, same as every other build this project: `data.js` and `_points_data.json`, copied verbatim from production's current `main`. `shift_dates.py` should be deleted from the TEST repo entirely (it is not referenced anywhere, safe to remove outright, not just leave unused).

**Not touched by this fix**: TEST's `weather.json` (will self-correct on its own next hourly `fetch_weather.py` run against the corrected `_points_data.json` — no manual reset needed) and TEST's `index.html` (still at `2.06`, a separate, already-tracked gap behind production's `2.08` — the rose colour/icon/WhatsApp-button work from items 13–14 hasn't been pushed to TEST yet).

**Update**: Jacco applied this fix himself before this next entry was written — see item 17 below for the fresh repo comparison confirming it landed correctly.

## 16. Both WhatsApp icons replaced with the real WhatsApp glyph, from Jacco's reference image — `APP_VERSION` 2.08→2.09

Jacco sent a reference PNG (the real WhatsApp bubble+phone mark, solid fill) and asked for "the whatsapp logos styled like the image" — both WhatsApp buttons in the app, not just one.

**Extracted the glyph directly from the reference image**, rather than hand-building or guessing an SVG path: colour-distance alpha mask against the white background, with a flood-fill from the canvas border so the *enclosed* white phone-handset shape stays solid white instead of being knocked transparent along with the actual background (same "protected region" logic used for the app-icon extraction in item 13, applied here via connected-component labeling instead of a geometric box). Result: a clean transparent-background PNG of the solid green bubble-with-tail shape with a solid white phone cutout, closely preserving even the reference image's subtle soft edge/halo. Green sampled at `#009846` — close to, but not identical to, the `#25D366` WhatsApp-brand green already used for these buttons' borders (that's WhatsApp's outline/UI green, this is their logo-mark green) — flagged, not reconciled, since the ask was to match the image exactly.

**Both buttons switched to this one shared asset** via a new `--wa-icon` CSS custom property (the base64 PNG, defined once) and a `.wa-badge-icon` class:
- **WhatsApp-noodnummer button** (header): the green `<rect>` badge container + white glyph path built in item 13 is gone — the reference image's own bubble shape already reads as a complete badge, no separate rounded-square container needed.
- **"Whatsapp theride" button** (quick-links): the old thin ring-outline "brand icon" font glyph — which only reads clearly at large sizes, and looked like a faint green outline at this button's actual size, matching what Jacco flagged — is replaced with the same solid badge.

Both buttons now show the identical, real WhatsApp mark, differing only by their border colour and label. Dead code cleaned up in the process: `.lb-ic`/`.lb-ic svg` CSS rules, unused once both inline SVGs were removed.

Re-verified: full regression suite (partner rotation 16/12 blocks zero dupes, WhatsApp community href, Spotify href, neutral borders, campingschema margin, rapid-tap stress test) still clean, `APP_VERSION` reads `2.09`, zero console errors. Screenshots confirm both badges render as a small solid green bubble with a white phone glyph, matching the reference image.

`APP_VERSION`: `2.08` → `2.09`.

## 17. Repo comparison, requested by Jacco after he updated TEST himself

Jacco applied the TEST date fix (item 15) and asked for a full repo comparison. Cloned both fresh rather than trusting local state:

- **App code is now byte-identical between the two repos**: `index.html`, `manifest.webmanifest`, all 3 icons, `data.js`, and `fetch_weather.py` all diff clean. TEST's dates now read the real `2026-09-13`→`2026-09-18`, `shift_dates.py` is confirmed gone from TEST.
- **Live bug found in TEST, not yet fixed**: TEST's `gpx/gpx-etappe5.gpx` is still the *old*, pre-fix file — it still contains a `"PLACEHOLDER VP2 - KATY ZOEKT"` waypoint and the old VP2 location, while production has the corrected GPX from the 2026-08-26 batch build. This isn't just a stale reference file — `index.html`'s "Download GPX" button (`downloadGpx(r.gpxFile)`) serves this file straight to riders, so a TEST rider downloading Etappe 5's GPX today would get the wrong route. Fix: copy production's `gpx/gpx-etappe5.gpx` into TEST, overwriting it.
- **Pre-existing, unrelated to today's work**: `shift_dates.py` — the TEST-only tool, per its own docstring — is sitting in the *production* repo, added 2026-08-14 (well before this session's cleanup). Harmless (production's `fetch_weather.yml` never calls it) but shouldn't be there; recommend deleting it from production directly on GitHub.
- **Harmless clutter in TEST**: 4 old `sponsor-*.png` files left over from before the 7-partner rotation build (dead, unreferenced, already cleaned from production) and a stray, unreferenced `gpx/segment-gardena.png` (the real, in-use copy lives in `climbs/` and is byte-identical between repos already).
- **Dev-tooling-only, no functional effect**: production carries `tools/` (6 build scripts), `gen_points.py`, `gradient_speed_curve.json`, `CNAME`, and `partners/place.txt` that TEST doesn't have — none of these are read by `index.html` at runtime. Worth optionally mirroring `gen_points.py` into TEST so a future `data.js` wxPoints edit there can regenerate `_points_data.json` without needing `build_offset_test.py`'s date-shift side effect, but not urgent.
- **Cosmetic only**: the weather workflow file is named differently per repo (`fetch_weather.yml` vs `weather.yaml`) but both run the identical single step (`python fetch_weather.py`); TEST's copy still has a header comment referencing the now-removed `shift_dates.py` mechanism — stale wording, no functional impact.

---

## Not in this build

- **Bel-noodnummer icon** — Jacco asked for the cartoony-ambulance 112
  icon to be replaced with something more serious (cross or hospital
  symbol); two directions were proposed but Jacco hasn't picked one yet.
- **MIJN theride / WhatsApp theride button height matching** — these two
  buttons should carry the same height as the noodnummer buttons up top
  and the Spotify button below; confirmed in scope, not yet built.
- **"Whatsapp theride" button's own icon going solid-badge style** —
  mentioned alongside the height-matching ask, not yet built; also still
  open whether its border should switch to WhatsApp green like the new
  noodnummer button's did.
- **Campingschema list spacing** — more room needed between the date,
  diamond separator, and campsite name in the list view; confirmed in
  scope, not yet built.
- **TEST-environment cluster** (collapsible demo/sim banner so future
  Today-tab screenshots can be shared cleanly; the gate screen briefly
  flashing in TEST before the password screen, which should never happen
  in TEST at all; the weather-availability window uncapped for TEST only
  so it can be watched populating from Open-Meteo as the horizon opens;
  restoring TEST's dates to match production exactly, no artificial
  offset, and removing the now-dead `shift_dates.py`; and a general audit
  to confirm TEST never uses a different mechanism than production
  anywhere) — all discussed and root-caused, none built yet.
- **`climb_chart.py` / `climbs/segment-gardena.png`** — still on the old
  rose, not regenerated as part of this colour change (see above).
- **WhatsApp location-share button** — explicitly deferred by Jacco: "we
  will work on the whatsapp share location part later."
- **Wind speed+direction on the Today route card** — mockup approved
  2026-08-27, but not named in this build's go-ahead; held for a
  separate pass.

## Verified

- Headless (Playwright), simulated both preview phase (2026-08-27, before
  the Proloog) and live phase (2026-09-15, mid-event):
  - `APP_VERSION` reads `2.00`.
  - Preview: 4 tabs visible, 16 total partner blocks, 4 per tab, zero
    duplicate partners within any single tab.
  - Live: 3 tabs visible, 12 total partner blocks, 4 per tab, zero
    duplicate partners within any single tab.
  - All 7 partner PNGs load with zero failed requests.
  - WhatsApp button DOM: icon+logo only (no COMMUNITY text/stack), real
    href set, not in the disabled state.
  - Spotify link href matches the new playlist URL.
  - `.link-btn`/`.spotify-btn`/`.plogo` all compute to `1px solid`
    `var(--line)` (neutral) — confirmed via `getComputedStyle`.
  - Campingschema card's computed margin is `0px 16px 14px`, matching
    `.today-card`'s default.
  - Screenshotted the Prep tab (partner grid + quick-links + Spotify) and
    Event tab (campingschema card + partner grid) for visual confirmation.
  - Zero new console errors beyond this offline sandbox's known
    network-blocked noise (fonts/weather.json/cover-photo — not
    regressions, same category noted in every prior build's verification).
