// Free map helpers: Leaflet + OpenStreetMap tiles, Photon place search,
// Nominatim reverse geocoding and OSRM routing. None of these need an API key.
var BroMap = (function () {
    var TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    var ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
    var ROUTER = 'https://routing.openstreetmap.de/routed-car/route/v1/driving/';
    var INDIA_BBOX = '68,6,98,36';

    function isDark() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    }

    function create(el, center, zoom) {
        var map = L.map(el, { zoomControl: true, attributionControl: true })
            .setView([center.lat, center.lng], zoom);
        L.tileLayer(TILES, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(map);
        // There is no free dark tile set, so dark mode recolours the tiles with a CSS filter
        el.classList.toggle('bm-dark', isDark());
        window.addEventListener('theme-changed', function (e) {
            el.classList.toggle('bm-dark', e.detail.theme === 'dark');
        });
        return map;
    }

    // Round coloured pin with an optional letter, e.g. pin(map, lat, lng, {color: 'green', label: 'A'})
    function pin(map, lat, lng, opts) {
        opts = opts || {};
        var icon = L.divIcon({
            className: 'bm-pin-wrap',
            html: '<div class="bm-pin bm-' + (opts.color || 'red') + '"><span>' + (opts.label || '') + '</span></div>',
            iconSize: [28, 28],
            iconAnchor: [14, 28]
        });
        var marker = L.marker([lat, lng], { icon: icon, title: opts.title || '' }).addTo(map);
        if (opts.title) marker.bindTooltip(opts.title);
        return marker;
    }

    function fit(map, points) {
        var valid = points.filter(function (p) { return p && p[0] && p[1]; });
        if (valid.length > 1) map.fitBounds(L.latLngBounds(valid), { padding: [30, 30] });
    }

    function describe(p) {
        var parts = [p.name, p.street, p.district || p.locality, p.city, p.state];
        return parts.filter(function (x, i) { return x && parts.indexOf(x) === i; }).join(', ');
    }

    // Returns a Promise of [{lat, lng, label}], biased towards `near`
    function search(query, near) {
        var url = 'https://photon.komoot.io/api/?limit=5&bbox=' + INDIA_BBOX + '&q=' + encodeURIComponent(query);
        if (near) url += '&lat=' + near.lat + '&lon=' + near.lng;
        return fetch(url)
            .then(function (r) { return r.ok ? r.json() : { features: [] }; })
            .then(function (data) {
                return data.features.map(function (f) {
                    return { lat: f.geometry.coordinates[1], lng: f.geometry.coordinates[0], label: describe(f.properties) };
                });
            });
    }

    // Returns a Promise of an address string (or '' if none)
    function reverse(lat, lng) {
        return fetch('https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=17&lat=' + lat + '&lon=' + lng)
            .then(function (r) { return r.ok ? r.json() : {}; })
            .then(function (d) { return d.display_name || ''; })
            .catch(function () { return ''; });
    }

    // Driving route through [[lat, lng], ...]. Resolves to {distanceKm, coords, tolls}.
    function route(points) {
        var path = points.map(function (p) { return p[1] + ',' + p[0]; }).join(';');
        return fetch(ROUTER + path + '?overview=full&geometries=geojson&steps=true')
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.code !== 'Ok' || !d.routes.length) throw new Error(d.code || 'No route');
                var r = d.routes[0];
                // Count each separate stretch of toll road as one toll
                var tolls = 0, onToll = false;
                r.legs.forEach(function (leg) {
                    leg.steps.forEach(function (step) {
                        var toll = (step.intersections || []).some(function (i) {
                            return (i.classes || []).indexOf('toll') !== -1;
                        });
                        if (toll && !onToll) tolls++;
                        onToll = toll;
                    });
                });
                return {
                    distanceKm: r.distance / 1000,
                    coords: r.geometry.coordinates.map(function (c) { return [c[1], c[0]]; }),
                    tolls: tolls
                };
            });
    }

    function drawRoute(map, coords, color, existing) {
        if (existing) map.removeLayer(existing);
        var line = L.polyline(coords, { color: color, weight: 6, opacity: 0.9 }).addTo(map);
        map.fitBounds(line.getBounds(), { padding: [30, 30] });
        return line;
    }

    // Search-as-you-type dropdown under `input`. onSelect({lat, lng, label}) fires on pick.
    function autocomplete(input, near, onSelect) {
        var box = document.createElement('div');
        box.className = 'bm-suggest';
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(box);
        input.setAttribute('autocomplete', 'off');
        var timer = null, seq = 0;

        function close() { box.innerHTML = ''; box.style.display = 'none'; }

        input.addEventListener('input', function () {
            clearTimeout(timer);
            var q = input.value.trim();
            if (q.length < 3) return close();
            timer = setTimeout(function () {
                var mine = ++seq;
                search(q, near).then(function (results) {
                    if (mine !== seq) return;
                    box.innerHTML = '';
                    results.forEach(function (res) {
                        var item = document.createElement('div');
                        item.className = 'bm-suggest-item';
                        item.textContent = res.label;
                        item.addEventListener('mousedown', function (e) {
                            e.preventDefault();
                            input.value = res.label;
                            close();
                            onSelect(res);
                        });
                        box.appendChild(item);
                    });
                    box.style.display = results.length ? 'block' : 'none';
                }).catch(close);
            }, 350);
        });
        input.addEventListener('blur', function () { setTimeout(close, 150); });
        close();
    }

    return { create: create, pin: pin, fit: fit, search: search, reverse: reverse,
             route: route, drawRoute: drawRoute, autocomplete: autocomplete };
})();
