static/js/map.js
let map = L.map("map").setView([-17.7833, -63.1821], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
}).addTo(map);

let startPoint = null;
let endPoint = null;
let startMarker = null;
let endMarker = null;
let routeLine = null;

map.on("click", function (e) {
    const point = {
        lat: e.latlng.lat,
        lng: e.latlng.lng
    };

    if (!startPoint) {
        startPoint = point;
        startMarker = L.marker([point.lat, point.lng]).addTo(map)
            .bindPopup("Punto A").openPopup();
    } else if (!endPoint) {
        endPoint = point;
        endMarker = L.marker([point.lat, point.lng]).addTo(map)
            .bindPopup("Punto B").openPopup();
    } else {
        alert("Ya seleccionaste punto A y B. Presiona reiniciar si quieres cambiar.");
    }
});

document.getElementById("calculateBtn").addEventListener("click", async function () {
    if (!startPoint || !endPoint) {
        alert("Selecciona punto A y punto B en el mapa.");
        return;
    }

    const hour = document.getElementById("hour").value;

    const response = await fetch("/calculate-route", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            start: startPoint,
            end: endPoint,
            hour: hour
        })
    });

    const data = await response.json();

    if (routeLine) {
        map.removeLayer(routeLine);
    }

    routeLine = L.polyline(data.route, {
        weight: 5
    }).addTo(map);

    map.fitBounds(routeLine.getBounds());

    document.getElementById("distance").textContent = data.distance_km;
    document.getElementById("time").textContent = data.time_min;
    document.getElementById("fuel").textContent = data.fuel_liters;
    document.getElementById("traffic").textContent = data.traffic_level;
    document.getElementById("patrol").textContent = data.assigned_patrol;
});

document.getElementById("resetBtn").addEventListener("click", function () {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    if (routeLine) map.removeLayer(routeLine);

    startPoint = null;
    endPoint = null;
    startMarker = null;
    endMarker = null;
    routeLine = null;

    document.getElementById("distance").textContent = "-";
    document.getElementById("time").textContent = "-";
    document.getElementById("fuel").textContent = "-";
    document.getElementById("traffic").textContent = "-";
    document.getElementById("patrol").textContent = "-";
});