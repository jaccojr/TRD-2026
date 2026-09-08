const CACHE="ride-dolomites-v5"; // bumped 2026-09-08: the opportunistic-cache branch below
// (added in v4) means any already-cached asset -- like the old partners/usport.png -- keeps
// getting served forever once a device has it, even after the file changes in the repo,
// because the fetch handler only checks the cache, never the network, for a path it already
// has. Only a CACHE bump forces every existing install to drop its old copies and re-fetch.
// Same lesson as the v3/v4 bumps: cache-first with a static name never self-refreshes.
const SHELL=["./","data.js","manifest.webmanifest","icon-180.png","icon-192.png","icon-512.png","logo-transparent.png",
 "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js","https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
 "climbs/climb-brocon.png","climbs/climb-cereda.png","climbs/climb-coldeiper.png","climbs/climb-compet.png",
 "climbs/climb-crosetta.png","climbs/climb-fedaia.png","climbs/climb-forcella.png","climbs/climb-gardena.png",
 "climbs/climb-giau.png","climbs/climb-gobbera.png","climbs/climb-manghen.png","climbs/climb-nevegal.png",
 "climbs/climb-piandeipradi.png","climbs/climb-pordoi.png","climbs/climb-pramadiccio.png","climbs/climb-sanubaldo.png",
 "climbs/climb-sella.png","climbs/climb-staulanza.png","climbs/climb-valparola.png","climbs/segment-borsoi.png",
 "climbs/segment-cereda.png","climbs/segment-gardena.png","climbs/segment-manghen.png","climbs/segment-panarotta.png",
 "climbs/segment-pordoi.png"]; // 25 files, ~556KB total -- one-time install cost, not re-fetched per visit
const NETWORK_FIRST=["index.html","data.js","weather.json"]; // always try fresh; fall back to cache offline

self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});

self.addEventListener("fetch",e=>{
  const u=e.request.url;
  const isNetworkFirst = NETWORK_FIRST.some(p=>u.indexOf(p)>-1) || u.endsWith("/") || u.endsWith(".html");
  if(isNetworkFirst){
    e.respondWith(
      fetch(e.request, {cache:"no-store"}).then(r=>{
        const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r;
      }).catch(()=>caches.match(e.request))
    );
    return;
  }
  // Cache-first for SHELL assets (instant hit, no network at all). For everything else --
  // GPX files, partner logos, camp maps -- fall through to network but opportunistically
  // stash a successful response too (2026-09-05): a rider who's opened their own stage's
  // GPX once with signal still has it offline later, without forcing every visitor to
  // pre-download all ~6MB of GPX data whether they'll ever tap "Download GPX" or not.
  e.respondWith(
    caches.match(e.request).then(r=>{
      if(r)return r;
      return fetch(e.request).then(resp=>{
        if(resp&&resp.ok){const cp=resp.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));}
        return resp;
      });
    })
  );
});
