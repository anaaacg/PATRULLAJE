/* ══════════════════════════════════════════
   SENTINEL AI — map.js
   Mapa Leaflet + lógica de selección de puntos
   + fetch a Flask /calculate-route
   ══════════════════════════════════════════ */

// ── ESTADO GLOBAL ──
const state = {
  mode: 'A',          // qué punto estamos seleccionando
  pointA: null,       // { lat, lng }
  pointB: null,       // { lat, lng }
  markerA: null,
  markerB: null,
  routeLayer: null,
  calculating: false,
};

// ── INICIALIZAR MAPA ──
const map = L.map('map', {
  center: [-17.7833, -63.1821],   // Santa Cruz de la Sierra
  zoom: 13,
  zoomControl: true,
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap',
  maxZoom: 19,
}).addTo(map);

// ── RELOJ ──
function updateClock() {
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  document.getElementById('clock').textContent = `${h}:${m}:${s}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── ICONOS PERSONALIZADOS ──
function makeIcon(color, letter) {
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width:34px; height:34px;
        background:${color};
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        display:flex; align-items:center; justify-content:center;
        box-shadow: 0 0 14px ${color}88;
      ">
        <span style="
          transform:rotate(45deg);
          color:#080c0a;
          font-family:'Barlow Condensed',sans-serif;
          font-weight:800;
          font-size:14px;
          line-height:1;
        ">${letter}</span>
      </div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -36],
  });
}

const iconA = makeIcon('#00ff88', 'A');
const iconB = makeIcon('#ffb800', 'B');

// ── MODO DE SELECCIÓN ──
function setMode(mode) {
  state.mode = mode;
  document.getElementById('btnA').classList.toggle('active', mode === 'A');
  document.getElementById('btnB').classList.toggle('active', mode === 'B');
  updateHint();
}

function updateHint() {
  const hint = document.getElementById('mapHint');
  const target = document.getElementById('hintTarget');

  if (state.pointA && state.pointB) {
    hint.classList.add('hidden');
    return;
  }
  hint.classList.remove('hidden');

  if (state.mode === 'A') {
    target.textContent = 'Punto A (Origen)';
    target.style.color = '#00ff88';
  } else {
    target.textContent = 'Punto B (Destino)';
    target.style.color = '#ffb800';
  }
}

// ── CLIC EN MAPA ──
map.on('click', function (e) {
  if (state.calculating) return;

  const { lat, lng } = e.latlng;

  if (state.mode === 'A') {
    if (state.markerA) map.removeLayer(state.markerA);
    state.pointA = { lat, lng };
    state.markerA = L.marker([lat, lng], { icon: iconA })
      .addTo(map)
      .bindPopup(`<b>ORIGEN A</b><br/>${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    setCoordDisplay('coordA', lat, lng);
    // Pasar automáticamente a selección B si no tiene destino
    if (!state.pointB) setMode('B');

  } else {
    if (state.markerB) map.removeLayer(state.markerB);
    state.pointB = { lat, lng };
    state.markerB = L.marker([lat, lng], { icon: iconB })
      .addTo(map)
      .bindPopup(`<b>DESTINO B</b><br/>${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    setCoordDisplay('coordB', lat, lng);
    if (!state.pointA) setMode('A');
  }

  updateHint();
});

// ── MOSTRAR COORDS ──
function setCoordDisplay(id, lat, lng) {
  const el = document.getElementById(id);
  el.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  el.classList.add('filled');
}

// ── CALCULAR RUTA ──
async function calcularRuta() {
  if (!state.pointA || !state.pointB) {
    showError('Selecciona los dos puntos en el mapa primero.');
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
    showError('Error al conectar con el servidor. Verifica que Flask esté corriendo.');
    // ── DEMO: si no hay servidor, simulamos respuesta para probar UI ──
    const demo = {
      distancia: '4.7 km',
      tiempo: '12 min',
      combustible: '0.8 L',
      trafico: 'Moderado',
      patrulla: 'Unidad SC-07',
      coordenadas: generarRutaDemo(state.pointA, state.pointB),
    };
    mostrarResultados(demo);
    dibujarRuta(demo);
  } finally {
    state.calculating = false;
    setLoading(false);
  }
}

// ── DIBUJAR RUTA ──
function dibujarRuta(data) {
  if (state.routeLayer) map.removeLayer(state.routeLayer);

  let coords;

  if (data.coordenadas && data.coordenadas.length > 0) {
    coords = data.coordenadas.map(c => [c.lat ?? c[0], c.lng ?? c[1]]);
  } else if (data.geometry && data.geometry.coordinates) {
    coords = data.geometry.coordinates.map(c => [c[1], c[0]]);
  } else {
    // Línea recta entre A y B como fallback
    coords = [
      [state.pointA.lat, state.pointA.lng],
      [state.pointB.lat, state.pointB.lng],
    ];
  }

  // Línea de sombra (glow effect)
  L.polyline(coords, {
    color: '#00ff88',
    weight: 8,
    opacity: 0.15,
  }).addTo(map);

  // Línea principal
  state.routeLayer = L.polyline(coords, {
    color: '#00ff88',
    weight: 3,
    opacity: 0.9,
    dashArray: '8 4',
    lineCap: 'round',
  }).addTo(map);

  // Ajustar zoom para mostrar toda la ruta
  const group = L.featureGroup([state.routeLayer]);
  if (state.markerA) group.addLayer(state.markerA);
  if (state.markerB) group.addLayer(state.markerB);
  map.fitBounds(group.getBounds().pad(0.18));
}

// ── MOSTRAR RESULTADOS ──
function mostrarResultados(data) {
  document.getElementById('noResults').style.display = 'none';
  const metrics = document.getElementById('metrics');
  metrics.classList.add('visible');

  set('metricDist',    data.distancia    || data.distance    || '—');
  set('metricTime',    data.tiempo       || data.time        || '—');
  set('metricFuel',    data.combustible  || data.fuel        || '—');
  set('metricTraffic', data.trafico      || data.traffic     || '—');
  set('metricPatrol',  data.patrulla     || data.patrol      || '—');
}

function set(id, val) {
  document.getElementById(id).textContent = val;
}

// ── LIMPIAR MAPA ──
function limpiarMapa() {
  if (state.markerA) { map.removeLayer(state.markerA); state.markerA = null; }
  if (state.markerB) { map.removeLayer(state.markerB); state.markerB = null; }
  if (state.routeLayer) { map.removeLayer(state.routeLayer); state.routeLayer = null; }

  // También eliminar glow layer (polylines sin referencia)
  map.eachLayer(layer => {
    if (layer instanceof L.Polyline) map.removeLayer(layer);
  });

  state.pointA = null;
  state.pointB = null;
  state.mode = 'A';

  document.getElementById('coordA').textContent = '— Clic en el mapa —';
  document.getElementById('coordA').classList.remove('filled');
  document.getElementById('coordB').textContent = '— Clic en el mapa —';
  document.getElementById('coordB').classList.remove('filled');

  document.getElementById('metrics').classList.remove('visible');
  document.getElementById('noResults').style.display = '';

  setMode('A');
  updateHint();
}

// ── LOADING STATE ──
function setLoading(on) {
  const bar = document.getElementById('loadingBar');
  const btn = document.getElementById('calcBtn');
  bar.classList.toggle('active', on);
  btn.disabled = on;
  btn.textContent = on ? 'CALCULANDO...' : '';
  if (!on) {
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 12h18M13 6l6 6-6 6"/>
      </svg>
      CALCULAR RUTA`;
  }
}

// ── TOAST ERROR ──
function showError(msg) {
  let toast = document.querySelector('.error-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'error-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── DEMO: generar ruta simulada entre A y B ──
function generarRutaDemo(a, b) {
  const steps = 12;
  const coords = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const jitter = (Math.random() - 0.5) * 0.003;
    coords.push({
      lat: a.lat + (b.lat - a.lat) * t + jitter,
      lng: a.lng + (b.lng - a.lng) * t + jitter,
    });
  }
  return coords;
}

// ── INIT ──
updateHint();
