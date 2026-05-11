let productos = [];
let muebles = {};

const $ = (id) => document.getElementById(id);
const search = $('search');
const results = $('results');
const status = $('status');
const muebleImg = $('muebleImg');
const overlay = $('overlay');
const viewerTitle = $('viewerTitle');
const viewerMeta = $('viewerMeta');
const clearBtn = $('clearBtn');

const card = $('card');
const badgeUbic = $('badgeUbic');
const smallMueble = $('smallMueble');
const cardProducto = $('cardProducto');

function norm(s){
  return (s || '')
    .toString()
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu,'');
}

function setStatus(text, ok=true){
  status.textContent = text;
  status.style.color = ok ? '#64748b' : '#b91c1c';
  status.style.borderColor = ok ? '#e2e8f0' : 'rgba(185,28,28,.25)';
  status.style.background = ok ? '#fff' : 'rgba(185,28,28,.06)';
}

async function cargar(){
  try{
    const [p, m] = await Promise.all([
      fetch('data/productos.json').then(r=>r.json()),
      fetch('data/muebles.json').then(r=>r.json())
    ]);
    productos = p;
    muebles = m;
    setStatus(`Listo • ${productos.length} productos`);
    render('');
  }catch(e){
    console.error(e);
    setStatus('Error al cargar datos', false);
    results.innerHTML = `<div class="empty">No se pudo cargar <code>data/productos.json</code> o <code>data/muebles.json</code>.</div>`;
  }
}

function render(q){
  const query = norm(q);
  results.innerHTML = '';

  if(!query){
    results.innerHTML = `<div class="empty">Escribe para buscar (ej: <strong>comprimidos</strong>).</div>`;
    return;
  }

  const hits = productos
    .filter(p => norm(p.producto).includes(query))
    .slice(0, 80);

  if(hits.length === 0){
    results.innerHTML = `<div class="empty">Sin resultados para <strong>${escapeHtml(q)}</strong>.</div>`;
    return;
  }

  for(const p of hits){
    const div = document.createElement('div');
    div.className = 'item';
    div.innerHTML = `
      <div class="itemTitle">${escapeHtml(p.producto)}</div>
      <div class="itemMeta">Mueble: <strong>${escapeHtml(p.mueble)}</strong> • Ubicación: <strong>${escapeHtml(p.ubicacion)}</strong></div>
    `;
    div.addEventListener('click', () => seleccionar(p));
    results.appendChild(div);
  }
}

function seleccionar(p){
  const m = muebles[p.mueble];
  if(!m){
    viewerTitle.textContent = 'Mueble sin plano';
    viewerMeta.textContent = `No existe configuración para “${p.mueble}”.`;
    overlay.innerHTML = '';
    card.hidden = true;
    return;
  }

  // Set image
  muebleImg.src = m.image;
  muebleImg.onload = () => {
    // Zones are in image pixels; we need to scale to the rendered size
    const z = m.zones[p.ubicacion];
    overlay.innerHTML = '';

    if(!z){
      viewerTitle.textContent = p.producto;
      viewerMeta.textContent = `Mueble: ${p.mueble} • Ubicación: ${p.ubicacion} (sin zona definida)`;
      card.hidden = false;
      badgeUbic.textContent = `Ubicación ${p.ubicacion}`;
      smallMueble.textContent = p.mueble;
      cardProducto.textContent = p.producto;
      return;
    }

    const scaleX = muebleImg.clientWidth / muebleImg.naturalWidth;
    const scaleY = muebleImg.clientHeight / muebleImg.naturalHeight;

    const box = document.createElement('div');
    box.className = 'highlight';
    box.style.left = (z.x * scaleX) + 'px';
    box.style.top  = (z.y * scaleY) + 'px';
    box.style.width  = (z.w * scaleX) + 'px';
    box.style.height = (z.h * scaleY) + 'px';

    overlay.appendChild(box);

    viewerTitle.textContent = p.producto;
    viewerMeta.textContent = `Mueble: ${p.mueble} • Ubicación: ${p.ubicacion}`;

    card.hidden = false;
    badgeUbic.textContent = `Ubicación ${p.ubicacion}`;
    smallMueble.textContent = p.mueble;
    cardProducto.textContent = p.producto;

    // Auto-scroll a la imagen en móvil
    document.getElementById('imageWrap').scrollIntoView({behavior:'smooth', block:'start'});
  };
}

function limpiar(){
  overlay.innerHTML = '';
  viewerTitle.textContent = 'Selecciona un producto';
  viewerMeta.textContent = 'Se mostrará el mueble y la ubicación.';
  card.hidden = true;
  muebleImg.removeAttribute('src');
}

let t=null;
search.addEventListener('input', () => {
  clearTimeout(t);
  t = setTimeout(() => render(search.value), 80);
});

clearBtn.addEventListener('click', () => {
  search.value='';
  render('');
  limpiar();
});

function escapeHtml(str){
  return (str || '').toString()
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'",'&#039;');
}

cargar();
