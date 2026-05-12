let productos = [];
let muebles = {};

const search = document.getElementById("search");
const results = document.getElementById("results");
const overlay = document.getElementById("overlay");
const img = document.getElementById("muebleImg");
const status = document.getElementById("status");

// ✅ Carga robusta
async function cargar() {
  try {
    const resProd = await fetch('data/productos.json');
    const resMueb = await fetch('data/muebles.json');

    productos = await resProd.json();
    muebles = await resMueb.json();

    status.textContent = "Listo ✅";
  } catch (e) {
    console.error(e);
    status.textContent = "Error cargando datos ❌";
  }
}

search.addEventListener("input", () => {
  const q = search.value.toLowerCase();
  results.innerHTML = "";

  if (!q) return;

  productos
    .filter(p => p.producto.toLowerCase().includes(q))
    .slice(0, 100)
    .forEach(p => {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <strong>${p.producto}</strong><br>
        Mueble: ${p.mueble} · Ubicación: ${p.ubicacion}
      `;
      div.onclick = () => seleccionar(p);
      results.appendChild(div);
    });
});

function seleccionar(p) {
  overlay.innerHTML = "";

  const m = muebles[p.id_mueble] || muebles[p.mueble];

  // ✅ fallback si no hay mueble
  if (!m) {
    img.src = "";
    return;
  }

  img.src = m.image;

  img.onload = () => {
    overlay.innerHTML = "";

    const z = m.zones[p.ubicacion];

    if (!z) return;

    const sx = img.clientWidth / img.naturalWidth;
    const sy = img.clientHeight / img.naturalHeight;

    const box = document.createElement("div");
    box.style.position = "absolute";
    box.style.background = "rgba(232,44,154,0.2)";
    box.style.border = "3px solid #E82C9A";

    // ✅ POLÍGONO
    if (z.poly) {
      const pts = z.poly.map(pt =>
        `${pt[0] * sx}px ${pt[1] * sy}px`
      ).join(",");

      box.style.clipPath = `polygon(${pts})`;
      box.style.left = "0";
      box.style.top = "0";
      box.style.width = "100%";
      box.style.height = "100%";
    } else {
      // fallback rectángulo
      box.style.left = z.x * sx + "px";
      box.style.top = z.y * sy + "px";
      box.style.width = z.w * sx + "px";
      box.style.height = z.h * sy + "px";
    }

    overlay.appendChild(box);
  };
}

// 🚀 iniciar
cargar();
