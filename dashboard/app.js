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
//     TODO(daniela): overlays sin señal / analizando / presupuesto agotado (Hito 2).
let srcActual = null;
function pintarFrame(estado, hallazgos) {
  const ultimo = hallazgos[0];
  const ruta = estado?.ultimo_frame ?? ultimo?.imagen ?? null;
  const src = urlFrame(ruta);

  $("hud-hora").textContent = ultimo?.hora ?? "--:--:--";
  $("hud-tipo").textContent = ultimo ? ultimo.tipo.toUpperCase() : "";
  $("hud-ruta").textContent = ruta ?? VACIO;
  $("txt-placeholder").textContent = MOCK
    ? "Modo prueba · sin imágenes reales"
    : ruta ? "Imagen no disponible" : "Esperando frame del dron";

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
  $("t-gasto-num").textContent = usd(costo);
  $("t-gasto-de").textContent = esNumero(tope) ? `de ${usd(tope)} · ${pct.toFixed(0)} %` : "";
  const barra = $("t-gasto-barra");
  barra.style.setProperty("--pct", `${pct}%`);
  barra.setAttribute("aria-valuenow", pct.toFixed(0));
}

// (4) Feed: los nuevos arriba (la API ya los manda así; se ordena por id por si acaso).
function pintarFeed(hallazgos) {
  const lista = $("lista");
  const items = [...hallazgos].sort((a, b) => (b.id ?? 0) - (a.id ?? 0));
  $("txt-total").textContent = items.length ? `${items.length} recientes` : "";

  if (!items.length) {
    lista.replaceChildren(el("li", "vacio-feed", "Todavía no hay hallazgos."));
    return;
  }

  lista.replaceChildren(
    ...items.map((h) => {
      const li = el("li", "item");
      li.dataset.sev = h.severidad;

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

async function tick() {
  try {
    const [estado, hallazgos] = await Promise.all([obtener(RUTAS.estado), obtener(RUTAS.hallazgos)]);
    const lista = Array.isArray(hallazgos) ? hallazgos : [];
    pintarHeader(estado, lista);
    pintarFrame(estado, lista);
    pintarTarjetas(estado, lista);
    pintarFeed(lista);
  } catch (err) {
    // TODO(daniela): API caída → mostrar "sin conexión" sin romper la página (Hito 2, tarea 2.3).
    console.warn("[eagle-eye]", err);
  }
}

tick();
setInterval(tick, POLL_MS);
