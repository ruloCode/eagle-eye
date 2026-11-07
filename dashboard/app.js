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

const $ = (id) => document.getElementById(id);
const VACIO = "—";

async function obtener(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

// URL de la imagen de un hallazgo/estado ("frames/0231.jpg" → API /frames/0231.jpg).
// En mock no hay imágenes reales → null (se muestra el placeholder).
function urlFrame(imagen) {
  if (MOCK || !imagen) return null;
  return `${API_URL}/${imagen}`;
}

function esNumero(v) {
  return typeof v === "number" && Number.isFinite(v);
}

function usd(v) {
  return esNumero(v) ? `$${v.toFixed(2)}` : VACIO;
}

// Crea un elemento con clase y texto (textContent: los textos vienen del modelo, nunca innerHTML).
function el(tag, clase, texto) {
  const e = document.createElement(tag);
  if (clase) e.className = clase;
  if (texto !== undefined && texto !== null) e.textContent = texto;
  return e;
}

// (1) Header: logo, estado del stream, modo detectado.
function pintarHeader(estado, hallazgos) {
  $("pill-mock").hidden = !MOCK;

  const enVivo = estado?.estado_stream === "en_vivo";
  $("pill-stream").classList.toggle("sin-senal", !enVivo);
  $("txt-stream").textContent = enVivo ? "En vivo" : "Sin señal";

  const ultimo = hallazgos[0];
  $("txt-modo").textContent = ultimo ? ultimo.tipo : VACIO;
}

// (2) Frame actual. El src solo cambia si cambia la ruta (evita parpadeo).
let srcActual = null;
function pintarFrame(estado, hallazgos) {
  const ultimo = hallazgos[0];
  const ruta = estado?.ultimo_frame ?? ultimo?.imagen ?? null;
  const src = urlFrame(ruta);

  $("hud-hora").textContent = ultimo?.hora ?? "--:--:--";
  $("hud-tipo").textContent = ultimo ? ultimo.tipo.toUpperCase() : "";
  $("hud-ruta").textContent = ruta ?? VACIO;
  $("txt-placeholder").textContent = MOCK
    ? "Cero puntos ciegos · datos de prueba"
    : ruta ? "Cero puntos ciegos" : "Esperando frame del dron…";

  if (src === srcActual) return;
  srcActual = src;
  const foto = $("foto");
  const frame = $("frame");
  if (!src) {
    frame.classList.remove("con-imagen");
    foto.removeAttribute("src");
    return;
  }
  foto.onload = () => frame.classList.add("con-imagen");
  foto.onerror = () => frame.classList.remove("con-imagen"); // 404 → placeholder, nunca ícono roto
  foto.src = src;
}

// (3) Tarjetas: personas, % estrés con semáforo, frames analizados, barra de gasto.
//     Campos null → "—". El color sale de `severidad`, no del número.
function pintarTarjeta(id, valor, sufijo, severidad) {
  const tarjeta = $(id);
  const num = $(`${id}-num`);
  const hay = esNumero(valor);
  num.classList.toggle("vacio", !hay);
  num.textContent = "";
  if (hay) {
    num.append(String(valor));
    if (sufijo) num.append(el("small", null, sufijo));
  } else {
    num.textContent = VACIO;
  }
  if (hay && severidad) tarjeta.dataset.sev = severidad;
  else delete tarjeta.dataset.sev;
  $(`${id}-sev`).textContent = hay && severidad ? severidad : "";
}

function pintarTarjetas(estado, hallazgos) {
  const ultimo = hallazgos[0];
  pintarTarjeta("t-personas", ultimo?.personas, null, ultimo?.severidad);
  pintarTarjeta("t-estres", ultimo?.pct_estres, "%", ultimo?.severidad);

  $("t-frames-num").textContent = esNumero(estado?.frames_analizados) ? estado.frames_analizados : VACIO;

  const costo = estado?.costo_usd;
  const tope = estado?.presupuesto_usd;
  const pct = esNumero(costo) && esNumero(tope) && tope > 0 ? Math.min(100, (costo / tope) * 100) : 0;
  $("t-gasto").classList.toggle("agotado", presupuestoAgotado(estado));
  $("t-gasto-num").textContent = usd(costo);
  $("t-gasto-de").textContent = esNumero(tope) ? `de ${usd(tope)} · ${pct.toFixed(0)} %` : "";
  const barra = $("t-gasto-barra");
  barra.style.setProperty("--pct", `${pct}%`);
  barra.setAttribute("aria-valuenow", pct.toFixed(0));
}

function presupuestoAgotado(estado) {
  return esNumero(estado?.costo_usd) && esNumero(estado?.presupuesto_usd) && estado.costo_usd >= estado.presupuesto_usd;
}

// Estados derivados (design.md): sin señal y presupuesto agotado → aviso sobre el frame;
// analizando → en vivo pero sin hallazgos todavía o el último frame no cambió en este ciclo.
let frameAnterior;
function pintarEstados(estado, hallazgos) {
  const enVivo = estado?.estado_stream === "en_vivo";
  const agotado = presupuestoAgotado(estado);
  const frame = estado?.ultimo_frame ?? null;
  const analizando = enVivo && !agotado && (!hallazgos.length || frame === frameAnterior);
  frameAnterior = frame;

  $("frame").classList.toggle("sin-senal", !enVivo);
  $("analizando").hidden = !analizando;

  const avisos = [];
  if (agotado) {
    avisos.push(["agotado", "Presupuesto agotado", `${usd(estado.costo_usd)} de ${usd(estado.presupuesto_usd)} · el agente se detuvo`]);
  }
  if (!enVivo) {
    avisos.push(["sin-senal", "Sin señal", "No llegan frames del dron · revisa la transmisión"]);
  }
  $("avisos").replaceChildren(
    ...avisos.map(([clase, titulo, sub]) => {
      const a = el("div", `aviso vidrio ${clase}`);
      a.append(el("strong", null, titulo), el("span", null, sub));
      return a;
    }),
  );
}

// (4) Feed: los nuevos arriba (la API ya los manda así; se ordena por id por si acaso).
//     Los que no estaban en el ciclo anterior se resaltan un momento.
let idsAnteriores = null;
function pintarFeed(hallazgos) {
  const lista = $("lista");
  const items = [...hallazgos].sort((a, b) => (b.id ?? 0) - (a.id ?? 0));
  $("txt-total").textContent = items.length ? `${items.length} recientes` : "";

  const previos = idsAnteriores;
  idsAnteriores = new Set(items.map((h) => h.id));
  // Si no cambió nada, no se re-pinta (así la animación de "nuevo" no se repite cada 2 s).
  const firma = items.map((h) => h.id).join(",");
  if (lista.dataset.firma === firma) return;
  lista.dataset.firma = firma;

  if (!items.length) {
    lista.replaceChildren(el("li", "vacio-feed", "Todavía no hay hallazgos."));
    return;
  }

  lista.replaceChildren(
    ...items.map((h) => {
      const li = el("li", "item");
      li.dataset.sev = h.severidad;
      if (previos && !previos.has(h.id)) li.classList.add("nuevo");

      const meta = el("div", "meta");
      meta.append(el("span", "hora", h.hora), el("span", "chip tipo", h.tipo), el("span", "chip sev", h.severidad));
      const dato = h.tipo === "cultivo" ? h.pct_estres : h.personas;
      if (esNumero(dato)) {
        meta.append(el("span", "dato black", h.tipo === "cultivo" ? `${dato} %` : `${dato} pers.`));
      }

      li.append(meta, el("p", "descripcion", h.descripcion), el("p", "recomendacion", h.recomendacion));
      return li;
    }),
  );
}

// Visor sobre el ojo del águila. Coordenadas del iris en assets/aguila.jpg, como fracción
// de la imagen (x, y) y del ancho (r). POS = object-position de .aguila en styles.css.
const OJO = { x: 0.64, y: 0.42, r: 0.0556 };
const POS = { x: 0.64, y: 0.42 };
function ubicarOjo() {
  const hero = $("frame");
  const img = $("aguila");
  if (!img?.naturalWidth) return;
  const cw = hero.clientWidth;
  const ch = hero.clientHeight;
  // object-fit: cover → escala y desplazamiento reales de la foto dentro del hero
  const s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
  const dw = img.naturalWidth * s;
  const dh = img.naturalHeight * s;
  const ox = (cw - dw) * POS.x;
  const oy = (ch - dh) * POS.y;
  hero.style.setProperty("--ojo-x", `${ox + OJO.x * dw}px`);
  hero.style.setProperty("--ojo-y", `${oy + OJO.y * dh}px`);
  hero.style.setProperty("--ojo-r", `${OJO.r * dw}px`);
}
$("aguila").addEventListener("load", ubicarOjo);
$("aguila").addEventListener("error", (e) => e.target.remove());
new ResizeObserver(ubicarOjo).observe($("frame"));
ubicarOjo();

// API caída: aviso discreto, se conservan los últimos datos y el polling sigue.
// El error se registra una sola vez por racha para no llenar la consola.
let enRachaDeError = false;
async function tick() {
  try {
    const [estado, hallazgos] = await Promise.all([obtener(RUTAS.estado), obtener(RUTAS.hallazgos)]);
    const lista = Array.isArray(hallazgos) ? hallazgos : [];
    if (enRachaDeError) console.info("[eagle-eye] conexión recuperada");
    enRachaDeError = false;
    $("pill-conexion").hidden = true;
    pintarHeader(estado, lista);
    pintarFrame(estado, lista);
    pintarEstados(estado, lista);
    pintarTarjetas(estado, lista);
    pintarFeed(lista);
  } catch (err) {
    if (!enRachaDeError) console.warn("[eagle-eye] sin conexión con la API:", err.message);
    enRachaDeError = true;
    $("pill-conexion").hidden = false;
  }
}

tick();
setInterval(tick, POLL_MS);
