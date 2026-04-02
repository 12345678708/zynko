self.addEventListener("install", e=>{
    e.waitUntil(
        caches.open("chat-cache").then(cache=>{
            return cache.addAll([
                "/",
                "/static/style.css",
                "/static/app.js"
            ]);
        })
    );
});
