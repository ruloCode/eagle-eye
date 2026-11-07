// Eagle Eye — dashboard. Dueña: Daniela.
// Change de OpenSpec: add-live-dashboard. Contrato: contracts/api.md.
//
// Modo real: consulta la API cada 2 s.
// Modo mock (?mock=1): lee contracts/fixtures/*.json (no necesita API).

const PARAMS = new URLSearchParams(location.search);
const MOCK = PARAMS.get("mock") === "1";
const API_URL = PARAMS.get("api") || "http://localhost:8000";
const POLL_MS = 2000;

const RUTAS = MOCK
  ? {
      estado: "../contracts/fixtures/estado.sample.json",
      hallazgos: "../contracts/fixtures/hallazgos.sample.json",
    }
  : {
      estado: `${API_URL}/estado`,
      hallazgos: `${API_URL}/hallazgos?limit=20`,
    };

async function obtener(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

// URL de la imagen de un hallazgo/estado ("frames/0231.jpg" → API /frames/0231.jpg).
function urlFrame(imagen) {
  // TODO(daniela): en mock no hay imágenes reales → placeholder.
  return `${API_URL}/${imagen}`;
}

// (1) Header: logo, estado del stream, modo detectado.
function pintarHeader(estado, hallazgos) {
  // TODO(daniela)
}

// (2) Frame actual + overlays: sin señal / analizando / presupuesto agotado.
function pintarFrame(estado) {
  // TODO(daniela)
}

// (3) Tarjetas: personas, % estrés con semáforo, frames analizados, barra de gasto.
//     Campos null → "—".
function pintarTarjetas(estado, hallazgos) {
  // TODO(daniela)
}

// (4) Feed: los nuevos arriba.
function pintarFeed(hallazgos) {
  // TODO(daniela)
}

async function tick() {
  try {
    const [estado, hallazgos] = await Promise.all([obtener(RUTAS.estado), obtener(RUTAS.hallazgos)]);
    pintarHeader(estado, hallazgos);
    pintarFrame(estado);
    pintarTarjetas(estado, hallazgos);
    pintarFeed(hallazgos);
  } catch (err) {
    // TODO(daniela): API caída → mostrar "sin conexión" sin romper la página.
    console.warn("[eagle-eye]", err);
  }
}

tick();
setInterval(tick, POLL_MS);
