const CACHE="ride-dolomites-v2";
const SHELL=["./","data.js","manifest.webmanifest","icon-180.png","icon-192.png","icon-512.png","logo-transparent.png",
 "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js","https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"];
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
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
