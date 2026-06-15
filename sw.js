const CACHE="ride-dolomites-v1";
const SHELL=["./","index.html","data.js","manifest.webmanifest","icon.svg","icon-192.png","icon-512.png",
 "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js","https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener("fetch",e=>{
  const u=e.request.url;
  if(u.indexOf("weather.json")>-1){ // always try network first for fresh weather
    e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});