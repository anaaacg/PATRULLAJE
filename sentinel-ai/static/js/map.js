/* SENTINEL AI — map.js
   Mapa Leaflet + selección de puntos + conexión Flask
*/

const state = {
  mode: 'A',
  pointA: null,
  pointB: null,
  markerA: null,
  markerB: null,
  routeLayer: null,
  glowLayer: null,
  calculating: false,
};

const map = L.map('map', {
  center: [-17.7833, -63.1821],
  zoom: 13,
  zoomControl: true,
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap',
  maxZoom: 19,
}).addTo(map);

function makeIcon(color, letter) {
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width:34px;
        height:34px;
        background:${color};
        border:2px solid #ffffff;
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.25);
      ">
        <span style="
          transform:rotate(45deg);
          color:#212529;
          font-family:Arial, sans-serif;
          font-weight:700;
          font-size:14px;
        ">${letter}</span>
      </div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -36],
  });
}

const iconA = makeIcon('#198754', 'A');
const iconB = makeIcon('#ffc107', 'B');

function setMode(mode) {
  state.mode = mode;

  const btnA = document.getElementById('btnA');
  const btnB = document.getElementById('btnB');

  if (btnA) btnA.classList.toggle('active', mode === 'A');
  if (btnB) btnB.classList.toggle('active', mode === 'B');

  updateHint();
}

function updateHint() {
  const hint = document.getElementById('mapHint');
  const target = document.getElementById('hintTarget');

  if (!hint || !target) return;

  if (state.pointA && state.pointB) {
    hint.style.display = 'none';
    return;
  }

  hint.style.display = 'block';

  if (state.mode === 'A') {
    target.textContent = 'Punto A';
  } else {
    target.textContent = 'Punto B';
  }
}

map.on('click', function (e) {
  if (state.calculating) return;

  const { lat, lng } = e.latlng;

  if (state.mode === 'A') {
    if (state.markerA) map.removeLayer(state.markerA);

    state.pointA = { lat, lng };
    state.markerA = L.marker([lat, lng], { icon: iconA })
      .addTo(map)
      .bindPopup(`<b>Origen</b><br>${lat.toFixed(5)}, ${lng.toFixed(5)}`);

    setCoordDisplay('coordA', lat, lng);

    if (!state.pointB) setMode('B');
  } else {
    if (state.markerB) map.removeLayer(state.markerB);

    state.pointB = { lat, lng };
    state.markerB = L.marker([lat, lng], { icon: iconB })
      .addTo(map)
      .bindPopup(`<b>Destino</b><br>${lat.toFixed(5)}, ${lng.toFixed(5)}`);

    setCoordDisplay('coordB', lat, lng);

    if (!state.pointA) setMode('A');
  }

  updateHint();
});

function setCoordDisplay(id, lat, lng) {
  const el = document.getElementById(id);
  if (!el) return;

  el.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  el.classList.add('filled');
}

async function calcularRuta() {
  if (!state.pointA || !state.pointB) {
    showError('Selecciona origen y destino en el mapa.');
    return;
  }

  if (state.calculating) return;

  state.calculating = true;
  setLoading(true);

  const hora = document.getElementById('timeInput').value;

  const payload = {
    punto_a: state.pointA,
    punto_b: state.pointB,
    hora: hora,
  };

  try {
    const res = await fetch('/calculate-route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();

    mostrarResultados(data);
    dibujarRuta(data);
  } catch (err) {
    console.error('Error al calcular ruta:', err);
    showError('No se pudo calcular la ruta. Revisa Flask o la consola.');
  } finally {
    state.calculating = false;
    setLoading(false);
  }
}

function dibujarRuta(data) {
  if (state.routeLayer) map.removeLayer(state.routeLayer);
  if (state.glowLayer) map.removeLayer(state.glowLayer);

  let coords;

  if (data.coordenadas && data.coordenadas.length > 0) {
    coords = data.coordenadas.map(c => [c.lat ?? c[0], c.lng ?? c[1]]);
  } else if (data.route && data.route.length > 0) {
    coords = data.route.map(c => [c.lat ?? c[0], c.lng ?? c[1]]);
  } else {
    coords = [
      [state.pointA.lat, state.pointA.lng],
      [state.pointB.lat, state.pointB.lng],
    ];
  }

  state.glowLayer = L.polyline(coords, {
    color: '#0056b3',
    weight: 7,
    opacity: 0.18,
  }).addTo(map);

  state.routeLayer = L.polyline(coords, {
    color: '#0056b3',
    weight: 4,
    opacity: 0.95,
    lineCap: 'round',
  }).addTo(map);

  const group = L.featureGroup([state.routeLayer]);

  if (state.markerA) group.addLayer(state.markerA);
  if (state.markerB) group.addLayer(state.markerB);

  map.fitBounds(group.getBounds().pad(0.18));
}

function mostrarResultados(data) {
  const noResults = document.getElementById('noResults');
  if (noResults) noResults.style.display = 'none';

  setText('metricDist', data.distancia || data.distance_km || '—');
  setText('metricTime', data.tiempo || data.time_min || '—');
  setText('metricFuel', data.combustible || data.fuel_liters || '—');
  setText('metricTraffic', data.trafico || data.traffic_level || '—');
  setText('metricPatrol', data.patrulla || data.assigned_patrol || '—');
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (!el) return;

  el.textContent = value;
}

function limpiarMapa() {
  if (state.markerA) map.removeLayer(state.markerA);
  if (state.markerB) map.removeLayer(state.markerB);
  if (state.routeLayer) map.removeLayer(state.routeLayer);
  if (state.glowLayer) map.removeLayer(state.glowLayer);

  state.markerA = null;
  state.markerB = null;
  state.routeLayer = null;
  state.glowLayer = null;
  state.pointA = null;
  state.pointB = null;
  state.mode = 'A';

  const coordA = document.getElementById('coordA');
  const coordB = document.getElementById('coordB');

  if (coordA) {
    coordA.textContent = 'Seleccione en el mapa';
    coordA.classList.remove('filled');
  }

  if (coordB) {
    coordB.textContent = 'Seleccione en el mapa';
    coordB.classList.remove('filled');
  }

  setText('metricDist', '—');
  setText('metricTime', '—');
  setText('metricFuel', '—');
  setText('metricTraffic', '—');
  setText('metricPatrol', '—');

  const noResults = document.getElementById('noResults');
  if (noResults) noResults.style.display = '';

  setMode('A');
  updateHint();
}

function setLoading(on) {
  const bar = document.getElementById('loadingBar');
  const btn = document.getElementById('calcBtn');

  if (bar) bar.style.display = on ? 'block' : 'none';

  if (btn) {
    btn.disabled = on;
    btn.textContent = on ? 'Calculando...' : 'Calcular ruta';
  }
}

function showError(msg) {
  let toast = document.querySelector('.error-toast');

  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'error-toast';
    document.body.appendChild(toast);
  }

  toast.textContent = msg;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

updateHint();