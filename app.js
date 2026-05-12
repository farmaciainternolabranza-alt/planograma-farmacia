let productos = [];
let muebles = {};

const search = document.getElementById("search");
const results = document.getElementById("results");
const overlay = document.getElementById("overlay");
const img = document.getElementById("muebleImg");

fetch('data/productos.json').then(r=>r.json()).then(d=>productos=d);
fetch('data/muebles.json').then(r=>r.json()).then(d=>muebles=d);

search.addEventListener("input",()=>{
  const q=search.value.toLowerCase();
  results.innerHTML="";
  productos.filter(p=>p.producto.toLowerCase().includes(q)).forEach(p=>{
    const div=document.createElement("div");
    div.innerText=p.producto;
    div.onclick=()=>select(p);
    results.appendChild(div);
  });
});

function select(p){
  overlay.innerHTML="";
  const m=muebles[p.mueble]||muebles[p.id_mueble];
  if(!m){img.src="";return;}
  img.src=m.image;
  img.onload=()=>{
    const z=m.zones[p.ubicacion];
    if(!z)return;
    const sx=img.clientWidth/img.naturalWidth;
    const sy=img.clientHeight/img.naturalHeight;
    const d=document.createElement("div");
    d.style.position="absolute";
    d.style.background="rgba(232,44,154,.2)";
    d.style.border="3px solid #E82C9A";
    if(z.poly){
      const pts=z.poly.map(pt=>pt[0]*sx+"px "+pt[1]*sy+"px").join(",");
      d.style.clipPath='polygon('+pts+')';
      d.style.left=0;d.style.top=0;
      d.style.width="100%";d.style.height="100%";
    }else{
      d.style.left=z.x*sx+"px";
      d.style.top=z.y*sy+"px";
      d.style.width=z.w*sx+"px";
      d.style.height=z.h*sy+"px";
    }
    overlay.appendChild(d);
  }
}
