const CURSOS=['Preescolar A','Preescolar B','Primero A','Primero B','Segundo A','Tercero A','Cuarto A','Quinto A','6A','6B','7A','8A','9A','10A','11A'];
const NAV={
  Superadmin:[
    {sep:'PANEL'},{id:'sa-col',l:'Instituciones'},
    {sep:'PREVENCIÓN'},{id:'sa-sen',l:'Conductas de riesgo'},
  ],
  Coordinador:[
    {sep:'PANEL'},{id:'co-ini',l:'Resumen'},
    {sep:'FALTAS'},{id:'co-f',l:'Todas las faltas'},{id:'co-asist',l:'Asistencia'},
    {sep:'PROMOCIÓN'},{id:'co-prom',l:'Actividades de promoción'},
    {sep:'PREVENCIÓN'},{id:'co-sen',l:'Conductas de riesgo'},
    {sep:'GESTIÓN'},{id:'co-est',l:'Estudiantes'},{id:'co-usr',l:'Usuarios'},{id:'co-cat',l:'Catálogo faltas'},{id:'co-proto',l:'Protocolos'},{id:'co-rep',l:'Reportes'},
    {id:'co-anio',l:'Cierre de año',variant:'cierre'},
  ],
  Director:[
    {sep:'PANEL'},{id:'di-ini',l:'Mi resumen'},
    {sep:'FALTAS'},{id:'di-f',l:'Faltas del curso'},{id:'di-asist',l:'Asistencia'},
    {sep:'PROMOCIÓN'},{id:'di-prom',l:'Actividades de promoción'},
    {sep:'PREVENCIÓN'},{id:'di-sen',l:'Conductas de riesgo'},
    {sep:'GESTIÓN'},{id:'di-est',l:'Mis estudiantes'},
  ],
  Orientador:[
    {sep:'PANEL'},{id:'or-ini',l:'Resumen'},
    {sep:'FALTAS'},{id:'or-f',l:'Todas las faltas'},{id:'or-asist',l:'Asistencia'},{id:'or-perf',l:'Perfil estudiante'},
    {sep:'PROMOCIÓN'},{id:'or-prom',l:'Actividades de promoción'},
    {sep:'PREVENCIÓN'},{id:'or-sen',l:'Conductas de riesgo'},
  ],
  Docente:[
    {sep:'PANEL'},{id:'doc-ini',l:'Mis registros'},
    {sep:'FALTAS'},{id:'doc-f',l:'Mis faltas'},{id:'doc-asist',l:'Asistencia'},
    {sep:'PROMOCIÓN'},{id:'doc-prom',l:'Actividades de promoción'},
    {sep:'PREVENCIÓN'},{id:'doc-sen',l:'Conductas de riesgo'},
  ],
  Acudiente:[
    {sep:'PANEL'},{id:'acu-ini',l:'Inicio'},
    {sep:'PREVENCIÓN'},{id:'acu-sen',l:'Registrar conducta de riesgo'},
    {sep:'FALTAS'},{id:'acu-f',l:'Faltas de mi hijo/a'},
  ],
};
const TTLS={
  'sa-col':'Instituciones educativas','sa-sen':'Conductas de riesgo',
  'co-ini':'Resumen general','di-ini':'Mi resumen','or-ini':'Resumen orientación','doc-ini':'Mis registros','acu-ini':'Portal de acudiente',
  'co-prom':'Actividades de promoción','di-prom':'Actividades de promoción','or-prom':'Actividades de promoción','doc-prom':'Actividades de promoción',
  'co-sen':'Conductas de riesgo','di-sen':'Conductas de riesgo','or-sen':'Conductas de riesgo','doc-sen':'Conductas de riesgo','acu-sen':'Registrar conducta de riesgo',
  'co-f':'Registro de faltas','di-f':'Faltas de mi curso','or-f':'Consulta de faltas','doc-f':'Mis faltas registradas','acu-f':'Faltas de mi hijo/a',
  'co-asist':'Asistencia','di-asist':'Asistencia','doc-asist':'Asistencia','or-asist':'Asistencia',
  'or-perf':'Perfil de estudiante',
  'co-est':'Gestión de estudiantes','di-est':'Mis estudiantes',
  'co-usr':'Gestión de usuarios','co-cat':'Catálogo de faltas','co-proto':'Protocolos y procesos','co-rep':'Reportes y seguimiento','co-anio':'Cierre de año'
};
// Iconos nav: SVG inline monocromo (currentColor). Sin “logos” de color para lectura homogénea en barra oscura.
const NAV_SVG = {
  instituciones: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linejoin="round"><path d="M3 20h18V10l-9-6-9 6v10z"/><path d="M8 20v-6h3v6M13 20v-9h3v9"/></svg>',
  riesgo: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="M12 3.2L2.6 20h18.8L12 3.2z"/><line x1="12" y1="9" x2="12" y2="12.5" stroke-linecap="round" stroke-width="2"/><circle cx="12" cy="16.2" r="0.9" fill="currentColor" stroke="none"/></svg>',
  reportes: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h4V10H4v9zM10 19h4V5h-4v14zM16 19h4v-7h-4v7z"/></svg>',
  megafono: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 10.5V13a1.5 1.5 0 0 0 1.5 1.5H5l3.2 3.2V5.3L5 8.5H4A1.5 1.5 0 0 0 2.5 10z"/><path d="M16 6.5a6 6 0 0 1 0 11" stroke-width="1.4"/><path d="M19 4.5a9 9 0 0 1 0 15" stroke-width="1.2"/></svg>',
  asistencia: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><circle cx="12" cy="12" r="7.2"/><line x1="12" y1="8" x2="12" y2="12.3"/><line x1="12" y1="12.3" x2="15.2" y2="14.5"/></svg>',
  catalogo: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 2.5H15l2.2 2.2v17.3H4.2V2.5h2.3z"/><line x1="6.2" y1="6" x2="12.5" y2="6"/><line x1="6.2" y1="8.5" x2="14" y2="8.5"/><line x1="6.2" y1="11" x2="11" y2="11"/><circle cx="15.2" cy="16.2" r="1.8"/><path d="M16.3 17.4l1.6 1.5"/></svg>',
  panel: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linejoin="round"><path d="M12 3.8l8.2 8.2-8.2 8.2-8.2-8.2L12 3.8z"/><path d="M12 8.2l4.2 3.8L12 15.8l-4.2-3.8L12 8.2z"/></svg>',
  lista: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><line x1="8.5" y1="7" x2="19" y2="7"/><line x1="8.5" y1="12" x2="19" y2="12"/><line x1="8.5" y1="17" x2="15" y2="17"/><circle cx="5" cy="7" r="1.15" fill="currentColor" stroke="none"/><circle cx="5" cy="12" r="1.15" fill="currentColor" stroke="none"/><circle cx="5" cy="17" r="1.15" fill="currentColor" stroke="none"/></svg>',
  faltas: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linejoin="round" stroke-linecap="round"><path d="M12 2.8l2.2 6.4h6.6l-5.3 3.9 2 6.5-5.5-4-5.5 4 2-6.5L3.2 9.2h6.6L12 2.8z"/></svg>',
  cierreAnio: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14.5" rx="2"/><path d="M3.5 9.5h17"/><line x1="8" y1="3.2" x2="8" y2="6"/><line x1="16" y1="3.2" x2="16" y2="6"/><path d="M8 14.5h5M8 17.5h8"/></svg>',
  protocolos: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M12 2v1.2l1.1.3a8 8 0 0 1 1.4.5l1-.6 1.7 1.7-.6 1a8 8 0 0 1 .5 1.4l.3 1.1H20v2.4h-1.2l-.3 1.1a8 8 0 0 1-.5 1.4l.6 1-1.7 1.7-1-.6a8 8 0 0 1-1.4.5l-1.1.3V20h-2.4v-1.2l-1.1-.3a8 8 0 0 1-1.4-.5l-1 .6-1.7-1.7.6-1a8 8 0 0 1-.5-1.4L6.2 16H4v-2.4h1.2l.3-1.1a8 8 0 0 1 .5-1.4l-.6-1 1.7-1.7 1 .6a8 8 0 0 1 1.4-.5L9.6 4H12z"/><circle cx="12" cy="12" r="2.2" fill="none"/></svg>',
  usuarios: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="7" r="2.8"/><path d="M3.2 20.2v0a4.2 4.2 0 0 1 4.1-3.1H11"/><circle cx="16.2" cy="6.2" r="2.2"/><path d="M20.2 20.2V19a2.7 2.7 0 0 0-1.2-2.1"/></svg>',
  estudiante: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8.5" r="3.2"/><path d="M6 20.5v-.8a4.5 4.5 0 0 1 4.5-4.5h3A4.5 4.5 0 0 1 18 19.7v.8"/></svg>',
};
function makeNavIcon(name) {
  const wrap = document.createElement("span");
  wrap.className = "ni-ic";
  wrap.setAttribute("aria-hidden", "true");
  wrap.innerHTML = NAV_SVG[name] || NAV_SVG.panel;
  return wrap;
}
function tabIconName(id) {
  if (id === "or-perf") return "estudiante";
  if (id === "sa-col") return "instituciones";
  if (id.endsWith("-sen")) return "riesgo";
  if (id.endsWith("-prom")) return "megafono";
  if (id.endsWith("-asist")) return "asistencia";
  if (id.endsWith("-f")) return "lista";
  if (id.endsWith("-est")) return "estudiante";
  if (id === "co-usr") return "usuarios";
  if (id.endsWith("-cat")) return "catalogo";
  if (id.endsWith("-proto")) return "protocolos";
  if (id.endsWith("-rep")) return "reportes";
  if (id.endsWith("-anio")) return "cierreAnio";
  if (id.endsWith("-ini")) return "panel";
  if (id === "acu-f") return "lista";
  return "panel";
}
function colegioAbbr(n) {
  if (!n || !String(n).trim()) return "CE";
  const w = String(n).trim().split(/\s+/).filter(Boolean);
  if (w.length >= 2) return (w[0][0] + w[1][0]).toUpperCase();
  return String(n).slice(0, 2).toUpperCase();
}
function updateSbToggle() {
  const t = document.getElementById("sbToggle");
  if (!t) return;
  const n = document.documentElement.classList.contains("sb-narrow");
  t.setAttribute("aria-pressed", n ? "true" : "false");
  t.setAttribute("title", n ? "Expandir barra" : "Contraer barra");
  t.setAttribute("aria-label", n ? "Expandir barra lateral" : "Contraer barra lateral");
  t.textContent = n ? "\u203a" : "\u2039";
}
function initSidebarChrome() {
  const t = document.getElementById("sbToggle");
  if (t && !t._boundSbToggle) {
    t._boundSbToggle = true;
    t.addEventListener("click", () => {
      const on = !document.documentElement.classList.contains("sb-narrow");
      document.documentElement.classList.toggle("sb-narrow", on);
      try { localStorage.setItem("sbNarrow", on ? "1" : "0"); } catch (e) { }
      updateSbToggle();
    });
  }
  if (t) updateSbToggle();
  const abbr = document.getElementById("sbAbbr");
  if (abbr && CU) {
    if (CU.rol === "Superadmin") abbr.textContent = "SA";
    else abbr.textContent = colegioAbbr(CU.colegio_nombre);
  }
  const ini = document.getElementById("sbInicial");
  if (ini && CU && CU.nombre) {
    const n = String(CU.nombre).trim();
    ini.textContent = n ? n[0].toUpperCase() : "?";
  }
  if (!window._boundSbResize) {
    window._boundSbResize = true;
    window.addEventListener("resize", syncSbNarrowToViewport);
  }
}
function syncSbNarrowToViewport() {
  const w = window.innerWidth;
  if (w <= 720) document.documentElement.classList.remove("sb-narrow");
  else {
    try {
      if (localStorage.getItem("sbNarrow") === "1") document.documentElement.classList.add("sb-narrow");
      else document.documentElement.classList.remove("sb-narrow");
    } catch (e) {
      document.documentElement.classList.remove("sb-narrow");
    }
  }
  updateSbToggle();
}
const REP_CAT_LBL={mal:'Me siento mal / necesito ayuda',molestan:'Me molestan',mal_colegio:'Algo malo en el colegio',peligro:'Peligro en el entorno'};
const REP_LUG_LBL={patio:'Patio',salon:'Salón',banos:'Baños',comedor:'Comedor',entrada:'Entrada',redes:'Redes / chat',otro:'Otro'};
const SEN_CAT_LBL={alimentacion:'Alimentación / hábitos',familia_acomp:'Acompañamiento familiar',abandono_riesgo:'Riesgo de deserción',bienestar_general:'Bienestar emocional o social',discapacidad_apoyo:'Apoyo (sin diagnóstico)',otro:'Otra'};
const CR_TIPO_LBL={conv_i:'Tipo I (convivencia)',conv_ii:'Tipo II (riesgo moderado)',conv_iii:'Tipo III (grave/delito)'};
const CR_SUB_LBL={conflictos_manejables:'Conflictos manejables',sin_dano:'No hay daño significativo',bullying_incipiente:'Bullying incipiente',afectacion_emocional:'Afectación emocional',conflictos_reiterados:'Conflictos reiterados',violencia_fisica:'Violencia física',abuso_sexual:'Abuso sexual',consumo_micro:'Consumo o microtráfico',intento_suicidio:'Intento de suicidio'};
const CR_SUBS={conv_i:[{v:'conflictos_manejables',l:'Conflictos manejables'},{v:'sin_dano',l:'No hay daño significativo'}],conv_ii:[{v:'bullying_incipiente',l:'Bullying incipiente'},{v:'afectacion_emocional',l:'Afectación emocional'},{v:'conflictos_reiterados',l:'Conflictos reiterados'}],conv_iii:[{v:'violencia_fisica',l:'Violencia física'},{v:'abuso_sexual',l:'Abuso sexual'},{v:'consumo_micro',l:'Consumo o microtráfico'},{v:'intento_suicidio',l:'Intento de suicidio'}]};
const CR_ACCION_TXT={conv_i:'Manejo: docente + mediación pedagógica',conv_ii:'Activación de ruta | Remisión a orientación escolar.',conv_iii:'Activación inmediata de ruta | Notificación a entidades externas (ICBF, salud, policía).'};
const TLCLS={Docente:'tl-doc',Director:'tl-dir',Coordinador:'tl-co',Orientador:'tl-ori',Acudiente:'tl-acu',Superadmin:'tl-co'};
const TLINI={Docente:'D',Director:'DG',Coordinador:'CO',Orientador:'OR',Acudiente:'AC',Superadmin:'SA'};
const TLBLS={Director:'Observación del director de grupo',Coordinador:'Observación del coordinador',Orientador:'Nota de orientación — proceso psicosocial',Docente:'Seguimiento del docente'};
const TGCLS={Superadmin:'t-sa',Coordinador:'t-co',Director:'t-di',Orientador:'t-or',Docente:'t-doc',Acudiente:'t-acu'};

let CU=null,curTab=null,editEstId=null,editUsrId=null,editColId=null,verFId=null,catFil='Tipo I',catCache=[],_TEMATICAS=[];

// ── API helper ───────────────────────────────────────────────────────────────
/** Interpreta el cuerpo de una Response como JSON; evita SyntaxError si llega HTML (login, 404, proxy). */
async function parseFetchBodyAsJson(r){
  const txt=await r.text();
  const trimmed=txt.trimStart();
  const low=trimmed.slice(0,16).toLowerCase();
  const looksHtml=low.startsWith('<!doctype html')||low.startsWith('<html');
  if(looksHtml){
    const u=(r.url||'').toLowerCase();
    if(r.status===401||r.status===403||u.includes('/login')){
      window.location.href='/login';
      return {error:'No autenticado',status:r.status};
    }
    if(r.status===404){
      return {error:'Ruta no encontrada',status:404};
    }
    console.warn('[api] Respuesta HTML en lugar de JSON',r.status,r.url);
    return {error:'El servidor devolvió una página HTML en lugar de datos. Revise la URL o intente iniciar sesión de nuevo.',status:r.status};
  }
  if(!trimmed.length){
    if(r.ok)return {ok:true};
    return {error:`HTTP ${r.status}`,status:r.status};
  }
  const ct=(r.headers.get('content-type')||'').toLowerCase();
  if(ct.includes('application/json')||trimmed.startsWith('{')||trimmed.startsWith('[')){
    try{return JSON.parse(txt);}
    catch(e){
      console.warn('[api] JSON inválido',e);
      return {error:'Respuesta del servidor no es JSON válido',status:r.status,raw:trimmed.slice(0,160)};
    }
  }
  try{return JSON.parse(txt);}
  catch(_){
    return {error:trimmed.slice(0,200)||`Error HTTP ${r.status}`,status:r.status};
  }
}

async function api(url,opts={}){
  const{headers:ho,...rest}=opts;
  const headers=ho instanceof Headers?Object.fromEntries(ho.entries()):{...(ho||{})};
  const hasBody=rest.body!=null&&rest.body!=='';
  if(hasBody&&typeof rest.body==='string'&&!headers['Content-Type']&&!headers['content-type']){
    headers['Content-Type']='application/json';
  }
  const cred=rest.credentials!=null?rest.credentials:'same-origin';
  const r=await fetch(url,{...rest,headers,credentials:cred});
  return parseFetchBodyAsJson(r);
}

// ── Sidebar (mobile) ──────────────────────────────────────────────────────────
function isMobile(){return window.matchMedia && window.matchMedia('(max-width: 720px)').matches;}
function openSidebar(){
  document.body.classList.add('sb-open');
  document.getElementById('sbBackdrop')?.classList.add('open');
}
function closeSidebar(){
  document.body.classList.remove('sb-open');
  document.getElementById('sbBackdrop')?.classList.remove('open');
}
function toggleSidebar(){
  if(document.body.classList.contains('sb-open')) closeSidebar();
  else openSidebar();
}

// ── Validaciones ─────────────────────────────────────────────────────────────
function valNom(el){
  const clean=el.value.replace(/[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ\s]/g,'');
  if(el.value!==clean)el.value=clean;
  const err=document.getElementById(el.id+'Err');
  if(err)err.textContent=clean.trim().length<2?'Mínimo 2 letras':'';
  el.classList.toggle('ok',clean.trim().length>=2);
}
function valCed(el){
  el.value=el.value.replace(/[^0-9]/g,'');
  const err=document.getElementById('eCedErr');
  if(err)err.textContent=el.value.length<5?'Mínimo 5 dígitos':'';
  el.classList.toggle('ok',el.value.length>=5);
}
function valTel(el){
  el.value=el.value.replace(/[^0-9]/g,'');
  const err=document.getElementById(el.id+'Err')||document.getElementById('eTelErr');
  if(err)err.textContent=el.value.length<7?'Mínimo 7 dígitos':'';
  el.classList.toggle('ok',el.value.length>=7);
}
function getAnio(){
  const el=document.getElementById('yrSel');
  const v=el&&el.value;
  return v||String(new Date().getFullYear());
}
function initYearSel(){
  const y=new Date().getFullYear();
  const sel=document.getElementById('yrSel');
  if(!sel)return;
  sel.innerHTML='';
  for(let iy=y+1;iy>=y-6;iy--){
    const o=document.createElement('option');
    o.value=String(iy);
    o.textContent=String(iy);
    if(iy===y)o.selected=true;
    sel.appendChild(o);
  }
}
function _usrMuestraAsignatura(rol){return ['Docente','Coordinador','Orientador','Superadmin'].includes(rol);}

// ── Init ─────────────────────────────────────────────────────────────────────
async function init(){
  const me=await api('/api/me');
  if(me.error){window.location.href='/login';return;}
  CU=me;
  if(CU.rol==='Estudiante'){window.location.href='/estudiante/reportar';return;}
  document.getElementById('sbSchool').textContent=CU.colegio_nombre||(CU.rol==='Superadmin'?'Multi-institución':'—');
  document.getElementById('sbNombre').textContent=CU.nombre;
  document.getElementById('sbRol').textContent=CU.rol+(CU.curso?' · '+CU.curso:'');
  initYearSel();
  buildNav();poblarSels();
  initSidebarChrome();
  refreshCitasPendientes();
  try{
    const tr=await api('/api/catalogo/tematicas');
    _TEMATICAS=Array.isArray(tr.tematicas)?tr.tematicas:[];
  }catch(_e){
    _TEMATICAS=[];
  }
  const first=document.querySelector('.ni');if(first)first.click();
}

function buildNav(){
  const nav=document.getElementById('mainNav');nav.innerHTML='';
  // Acción rápida global: registrar falta (solo roles autorizados)
  if(['Coordinador','Orientador','Director','Docente'].includes(CU.rol)){
    const wrap=document.createElement('div');
    wrap.className='sb-nav-cta';
    const b=document.createElement('button');
    b.type='button';
    b.className='btn btn-p flex w-full items-center justify-center gap-2.5 rounded-xl px-3 py-3 text-[13px] shadow-md shadow-black/20';
    b.setAttribute('aria-label','Registrar falta');
    b.appendChild(makeNavIcon('faltas'));
    const sp=document.createElement('span');
    sp.className='ni-txt';
    sp.textContent='+ Registrar falta';
    b.appendChild(sp);
    b.onclick=()=>{
      openOv('ov-falta');
      if(isMobile()) closeSidebar();
    };
    wrap.appendChild(b);
    nav.appendChild(wrap);
  }
  (NAV[CU.rol]||[]).forEach(item=>{
    if(item.sep){const d=document.createElement('div');d.className='ni-sep';d.textContent=item.sep;nav.appendChild(d);return;}
    if(item.variant==='cierre'){
      const wrap=document.createElement('div');
      wrap.className='sb-nav-cta sb-nav-cierre';
      const b=document.createElement('button');
      b.type='button';
      b.className='sb-cierre-anio flex w-full items-center justify-center gap-2.5 rounded-xl px-3 py-3 text-[13px] shadow-md shadow-black/25';
      b.setAttribute('data-tab',item.id);
      const ttl=TTLS[item.id]||item.l;
      b.title=ttl;
      b.setAttribute('aria-label',ttl);
      b.appendChild(makeNavIcon('cierreAnio'));
      const sp=document.createElement('span');
      sp.className='ni-txt';
      sp.textContent=item.l;
      b.appendChild(sp);
      b.onclick=()=>{showTab(item.id,b);if(isMobile())closeSidebar();};
      wrap.appendChild(b);
      nav.appendChild(wrap);
      return;
    }
    const d=document.createElement('div');
    d.className='ni';
    d.classList.add('ni-pill');
    d.setAttribute('data-tab',item.id);
    d.setAttribute('role','button');
    d.setAttribute('tabindex','0');
    const ttl=TTLS[item.id]||item.l;
    d.title=ttl;
    d.setAttribute('aria-label',ttl);
    d.appendChild(makeNavIcon(tabIconName(item.id)));
    const lab=document.createElement('span');
    lab.className='ni-txt';
    lab.textContent=item.l;
    d.appendChild(lab);
    d.onclick=()=>showTab(item.id,d);
    d.addEventListener('keydown',(e)=>{
      if(e.key==='Enter'||e.key===' '){e.preventDefault();showTab(item.id,d);}
    });
    nav.appendChild(d);
  });
}

function showTab(id,el){
  curTab=id;
  document.querySelectorAll('.ni').forEach(n=>{
    n.classList.remove('on');
    n.removeAttribute('aria-current');
  });
  document.querySelectorAll('.sb-cierre-anio').forEach(n=>{
    n.classList.remove('on');
    n.removeAttribute('aria-current');
  });
  document.getElementById('topTitle').textContent=TTLS[id]||id;
  const active=el||document.querySelector(`.ni[data-tab="${id}"]`)||document.querySelector(`.sb-cierre-anio[data-tab="${id}"]`);
  if(active){
    active.classList.add('on');
    active.setAttribute('aria-current','page');
  }
  renderTab(id);
  if(isMobile()) closeSidebar();
}
function renderCurrentTab(){if(curTab)renderTab(curTab);}

function poblarSels(){
  ['rCurso','eCurso','uCurso','impCurso'].forEach(id=>{
    const el=document.getElementById(id);if(!el)return;
    const first=el.options[0];el.innerHTML='';el.appendChild(first);
    CURSOS.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;el.appendChild(o);});
  });
}

// ── Router ───────────────────────────────────────────────────────────────────
async function renderTab(id){
  const mc=document.getElementById('mainContent');mc.innerHTML='';
  const tab=document.createElement('div');tab.className='tab on';tab.id='t-'+id;mc.appendChild(tab);
  const mapa={'sa-col':renderSACol,'sa-sen':renderSenales,'co-ini':renderInicio,'di-ini':renderInicio,'or-ini':renderInicio,'doc-ini':renderInicio,'acu-ini':renderInicio,
    'co-prom':renderPromocion,'di-prom':renderPromocion,'or-prom':renderPromocion,'doc-prom':renderPromocion,
    'co-f':renderFaltas,'di-f':renderFaltas,'or-f':renderFaltas,'doc-f':renderFaltas,'acu-f':renderFaltas,
    'co-est':renderEstudiantes,'di-est':renderEstudiantes,
    'co-sen':renderSenales,'di-sen':renderSenales,'or-sen':renderSenales,'doc-sen':renderSenales,'acu-sen':renderSenales,
    'co-asist':renderAsistencia,'di-asist':renderAsistencia,'doc-asist':renderAsistencia,'or-asist':renderAsistencia,
    'co-usr':renderUsuarios,'co-cat':renderCatalogo,'co-proto':renderProto,
    'co-rep':renderReportes,'co-anio':renderAnio,'or-perf':renderPerfil};
  if(mapa[id])await mapa[id](tab);
  else tab.innerHTML='<div class="empty">Sección en construcción</div>';
}

// ── Inicio: pendiente (por rol), gravedad II/III, recientes ────────────────────
function gravedadRank(t){
  if(t==='Tipo III') return 0;
  if(t==='Tipo II') return 1;
  return 2;
}
function cmpFechaDesc(a,b){
  const da=a.fecha||'',db=b.fecha||'';
  if(da!==db) return db.localeCompare(da);
  return (b.id||0)-(a.id||0);
}
function cmpGravedad(a,b){
  const g=gravedadRank(a.tipo_falta)-gravedadRank(b.tipo_falta);
  return g!==0?g:cmpFechaDesc(a,b);
}
/**
 * Siguiente rol esperado en el proceso: Docente → Director → (Tipo II/III) Coordinador → Orientador → Docente (cierre) → fin.
 */
function inicioNextRole(f){
  const t=f.tipo_falta;
  const T23=t==='Tipo II'||t==='Tipo III';
  const a=f.anotaciones||[];
  if(!a.length) return 'Director';
  const last=a[a.length-1].rol;
  if(last==='Docente'){
    if(T23 && a.length>=2 && a[a.length-2].rol==='Orientador') return null;
    return 'Director';
  }
  if(last==='Director') return T23?'Coordinador':null;
  if(last==='Coordinador') return T23?'Orientador':null;
  if(last==='Orientador') return T23?'Docente':null;
  return null;
}
function inicioRolEfectivo(){
  if(CU.rol==='Superadmin') return 'Coordinador';
  return CU.rol;
}
function inicioEsMiTurno(f){
  if(f.estado_gestion==='cerrada')return false;
  const nr=inicioNextRole(f);
  if(!nr) return false;
  const role=inicioRolEfectivo();
  if(nr!==role) return false;
  if(role==='Director'){
    if(CU.curso && f.curso===CU.curso) return true;
    if(f.docente===CU.nombre) return true;
    return false;
  }
  if(role==='Docente') return f.docente===CU.nombre;
  return true;
}
/** Hasta `lim` textos distintos de falta_especifica con conteo (por defecto 5). */
function iniTopFaltasEspecificas(faltas, lim){
  const n=Math.min(5,Math.max(1,lim==null?5:lim));
  const map={};
  faltas.forEach(f=>{
    const k=String(f.falta_especifica||'').trim();
    const key=k||'(Sin texto en catálogo)';
    map[key]=(map[key]||0)+1;
  });
  return Object.entries(map).sort((a,b)=>b[1]-a[1]).slice(0,n);
}
/** Curso con más faltas en la lista; null si vacío. */
function iniCursoMasFaltas(faltas){
  if(!faltas.length) return null;
  const map={};
  faltas.forEach(f=>{
    const k=String(f.curso||'').trim()||'(Sin curso)';
    map[k]=(map[k]||0)+1;
  });
  const ent=Object.entries(map).sort((a,b)=>b[1]-a[1]);
  return ent[0];
}
// ── Inicio ───────────────────────────────────────────────────────────────────
const EST_GEST_TXT={pendiente:'Pendiente',en_revision:'En revisión',cerrada:'Cerrada'};

async function renderInicio(tab){
  const faltasAll=await api(`/api/faltas?anio=${getAnio()}`);
  const rep=await api(`/api/reportes?anio=${getAnio()}`);
  const canReg=['Coordinador','Director','Docente','Superadmin'].includes(CU.rol);
  const t2t3=faltasAll.filter(f=>f.tipo_falta==='Tipo II'||f.tipo_falta==='Tipo III');
  const rT1=rep.reincidencias_tipo_i||[];
  const proc=faltasAll.filter(inicioEsMiTurno).sort(cmpGravedad);
  const atn=faltasAll.filter(f=>f.tipo_falta==='Tipo II'||f.tipo_falta==='Tipo III').sort(cmpGravedad);
  const rec=[...faltasAll].sort(cmpFechaDesc);
  const topEsp=iniTopFaltasEspecificas(faltasAll,5);
  const curTop=iniCursoMasFaltas(faltasAll);
  const rankBlock=!faltasAll.length
    ?'<div class="empty" style="padding:14px">Sin faltas registradas en este año.</div>'
    :(!topEsp.length
      ?'<div class="empty" style="padding:14px">Sin datos para clasificar.</div>'
      :`<ol class="ini-rk-list">${topEsp.map(([lab,cnt],i)=>`<li><span class="ini-rk-txt" title="${escHtml(lab)}"><span class="ini-rk-idx">${i+1}</span>${escHtml(lab)}</span><span class="ini-rk-cnt">${cnt}</span></li>`).join('')}</ol>`);
  const curBlock=!faltasAll.length||!curTop
    ?'<div class="mut" style="font-size:12px;padding:4px 0">Aparecerá cuando haya faltas con curso asignado.</div>'
    :`<div class="ini-cur-box"><div class="ini-cur-lbl">Curso con más faltas (${getAnio()})</div><div class="ini-cur-val"><strong>${escHtml(curTop[0])}</strong><span class="ini-rk-cnt">${curTop[1]}</span></div><div class="ini-cur-hint">Útil para focalizar acompañamiento o charlas de convivencia.</div></div>`;
  const temList=_TEMATICAS.length?_TEMATICAS:['Relaciones Respetuosas','Normas de convivencia','Gestión Emocional','Ambiente Físico y seguro','Participación activa','Prevención de conflictos'];
  const temCounts={};
  temList.forEach(t=>{temCounts[t]=0;});
  faltasAll.forEach(f=>{
    const tx=(f.tematica||'').trim();
    if(tx)temCounts[tx]=(temCounts[tx]||0)+1;
  });
  const temTiles=temList.map(t=>`<div class="ini-tem-tile"><div class="ini-tem-n">${temCounts[t]||0}</div><div class="ini-tem-l">${temBdg(t)}</div></div>`).join('');
  const temBlock=`<div class="card mb-4"><div class="ch"><h3>Por dimensión temática</h3><span class="mut" style="font-size:11px;font-weight:500">${getAnio()} · clasificación del registro</span></div><div class="ini-tem-grid">${temTiles}</div></div>`;
  tab.innerHTML=`
    <div class="stats mb-4 grid grid-cols-2 gap-2.5 lg:grid-cols-4 max-[720px]:flex max-[720px]:gap-2.5 max-[720px]:overflow-x-auto max-[720px]:pb-2 max-[720px]:[-webkit-overflow-scrolling:touch] max-[720px]:snap-x max-[720px]:snap-mandatory">
      <div class="stat relative overflow-hidden rounded-xl border border-[var(--brd)] bg-white p-3.5 shadow-sm shadow-black/[0.04] max-[720px]:min-w-[170px] max-[720px]:shrink-0 max-[720px]:snap-start max-[720px]:py-3 max-[720px]:px-3"><div class="n max-[720px]:text-xl">${faltasAll.length}</div><div class="l">Total ${getAnio()}</div><div class="stat-ln sl-b"></div></div>
      <div class="stat relative overflow-hidden rounded-xl border border-[var(--brd)] bg-white p-3.5 shadow-sm shadow-black/[0.04] max-[720px]:min-w-[170px] max-[720px]:shrink-0 max-[720px]:snap-start max-[720px]:py-3 max-[720px]:px-3"><div class="n max-[720px]:text-xl">${faltasAll.filter(f=>f.tipo_falta==='Tipo I').length}</div><div class="l">Tipo I — Leves</div><div class="stat-ln sl-g"></div></div>
      <div class="stat relative overflow-hidden rounded-xl border border-[var(--brd)] bg-white p-3.5 shadow-sm shadow-black/[0.04] max-[720px]:min-w-[170px] max-[720px]:shrink-0 max-[720px]:snap-start max-[720px]:py-3 max-[720px]:px-3"><div class="n max-[720px]:text-xl">${faltasAll.filter(f=>f.tipo_falta==='Tipo II').length}</div><div class="l">Tipo II — Graves</div><div class="stat-ln sl-a"></div></div>
      <div class="stat relative overflow-hidden rounded-xl border border-[var(--brd)] bg-white p-3.5 shadow-sm shadow-black/[0.04] max-[720px]:min-w-[170px] max-[720px]:shrink-0 max-[720px]:snap-start max-[720px]:py-3 max-[720px]:px-3"><div class="n max-[720px]:text-xl">${faltasAll.filter(f=>f.tipo_falta==='Tipo III').length}</div><div class="l">Tipo III — Muy graves</div><div class="stat-ln sl-r"></div></div>
    </div>
    ${temBlock}
    <div class="ini-grid grid grid-cols-1 gap-4 min-[1021px]:grid-cols-3">
      <div class="card">
        <div class="ch"><h3>Pendiente <span class="ini-count">(${proc.length})</span></h3></div>
        <div class="ini-list">${proc.length?fCards(proc):'<div class="empty">Nada pendiente con usted en este momento según ese orden.</div>'}</div>
      </div>
      <div class="card">
        <div class="ch"><h3>Gravedad <span style="font-size:12px;font-weight:500;color:var(--mut)">(Tipo II y III)</span></h3></div>
        <div class="ini-list">${atn.length?fCards(atn):'<div class="empty">Sin faltas Tipo II o III en este año.</div>'}</div>
      </div>
      <div class="card">
        <div class="ch"><h3>Faltas recientes</h3>${canReg?`<button type="button" class="btn btn-p btn-xs" onclick="openOv('ov-falta')">+ Registrar</button>`:''}</div>
        <div class="ini-list">${fCards(rec)}</div>
      </div>
    </div>
    <div class="card mt-1">
      <div class="ch"><h3>Panorama para la acción</h3></div>
      <div class="ini-panorama">
        <div class="ini-pan-col">
          <div class="ini-pan-sub">Faltas específicas más frecuentes <span class="mut">(hasta 5)</span></div>
          ${rankBlock}
        </div>
        <div class="ini-pan-col ini-pan-col-cur">
          ${curBlock}
        </div>
      </div>
    </div>`;
}

// ── Tarjetas faltas ───────────────────────────────────────────────────────────
function escHtml(s){
  return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
const _TEM_STY={
  'Relaciones Respetuosas':'background:#ede9fe;color:#5b21b6;border:1px solid #ddd6fe',
  'Normas de convivencia':'background:#dbeafe;color:#1e40af;border:1px solid #bfdbfe',
  'Gestión Emocional':'background:#fce7f3;color:#9d174d;border:1px solid #fbcfe8',
  'Ambiente Físico y seguro':'background:#d1fae5;color:#047857;border:1px solid #a7f3d0',
  'Participación activa':'background:#ffedd5;color:#c2410c;border:1px solid #fed7aa',
  'Prevención de conflictos':'background:#e0e7ff;color:#3730a3;border:1px solid #c7d2fe',
};
function temBdg(lab){
  const t=String(lab==null?'':lab).trim();
  if(!t)return'';
  const st=_TEM_STY[t]||'background:#f1f5f9;color:#475569;border:1px solid #e2e8f0';
  return`<span class="tem-pill" style="${st}">${escHtml(t)}</span>`;
}
function estGestionBdg(f){
  const eg=f.estado_gestion||'pendiente';
  const cls=eg==='cerrada'?'ce':eg==='en_revision'?'er':'pe';
  return`<span class="bdg beg-${cls}">${EST_GEST_TXT[eg]||eg}</span>`;
}
function fCitaBlock(f){
  const c=f.cita_acudiente;
  const canSol=CU.rol==='Acudiente';
  const parts=[];
  if(c){
    const st=c.estado;
    const fh=(c.fecha_hora||'').replace('T',' ');
    if(st==='pendiente_agenda'){
      parts.push(`<div class="fc-cita" onclick="event.stopPropagation()"><strong>Cita</strong> · Solicitud al <strong>${escHtml(c.rol_destino)}</strong> (esperando fecha desde la institución)</div>`);
    }else if(st==='pendiente_confirmacion_acudiente'){
      let row=`<div class="fc-cita" onclick="event.stopPropagation()"><strong>Cita</strong> · Propuesta: <strong>${escHtml(fh||'—')}</strong> `;
      if(canSol){
        row+=`<button type="button" class="btn btn-g btn-xs" onclick="event.stopPropagation();citaConfirmar(${c.id})">Confirmar</button> <button type="button" class="btn btn-d btn-xs" onclick="event.stopPropagation();citaRechazar(${c.id})">Rechazar</button>`;
      }else{
        row+=`<span style="color:var(--mut);font-size:11px">(pendiente confirmación del acudiente)</span>`;
      }
      row+='</div>';
      parts.push(row);
    }else if(st==='confirmada'){
      parts.push(`<div class="fc-cita" onclick="event.stopPropagation()"><strong>Cita confirmada</strong> · ${escHtml(fh||'—')}</div>`);
    }else if(st==='rechazada'||st==='cancelada'){
      parts.push(`<div class="fc-cita" onclick="event.stopPropagation()"><span style="color:var(--mut)">Cita ${st==='rechazada'?'rechazada':'cancelada'}</span></div>`);
    }
  }
  return parts.join('');
}
function fCards(faltas){
  if(!faltas.length)return`<div class="empty">Sin registros</div>`;
  return faltas.map(f=>`
    <div class="fcard ${f.tipo_falta==='Tipo III'?'t3':f.tipo_falta==='Tipo II'?'t2':''}" onclick="verFalta(${f.id})">
      <div class="fc-top">
        <span class="fc-est">${f.estudiante}</span>
        <div class="fc-bdg">${bdg(f.tipo_falta)}${estGestionBdg(f)}${(f.tematica||'').trim()?temBdg(f.tematica):''}<span class="bdg bg">${f.curso}</span>${(f.anotaciones?.length||0)>0?`<span class="bdg bi">${f.anotaciones.length} seg.</span>`:''}</div>
      </div>
      <div class="fc-meta"><span>${f.fecha}</span><span>${f.docente}</span></div>
      <div class="fc-desc">${f.falta_especifica} — ${f.descripcion}</div>
      ${fCitaBlock(f)}
      <div class="fc-foot"><span class="fc-proc">${f.proceso_inicial}</span><span style="font-size:11px;color:var(--mut)">Ver →</span></div>
    </div>`).join('');
}

function bdg(t){
  const m={'Tipo I':`<span class="bdg b1"><span class="dot dg"></span>Tipo I</span>`,'Tipo II':`<span class="bdg b2"><span class="dot da"></span>Tipo II</span>`,'Tipo III':`<span class="bdg b3"><span class="dot dr"></span>Tipo III</span>`};
  return m[t]||t;
}

async function refreshCitasPendientes(){
  const bar=document.getElementById('citaPendBar');
  if(!bar||!CU)return;
  if(!['Acudiente','Coordinador','Director','Orientador','Docente'].includes(CU.rol)){bar.style.display='none';bar.innerHTML='';return;}
  const r=await api('/api/me/citas-pendientes');
  if(r.error){bar.style.display='none';return;}
  const pc=r.por_confirmar||[];
  const pa=r.por_agendar||[];
  if(!pc.length&&!pa.length){bar.style.display='none';bar.innerHTML='';return;}
  let html='<div class="cita-pend-inner">';
  if(pa.length){
    html+=`<div class="abanner ab-a" style="margin:0 0 8px 0"><strong>Citas por agendar (${pa.length})</strong> — un acudiente solicitó reunión; indique fecha y hora para enviar la propuesta al acudiente.</div>`;
    pa.forEach(c=>{
      html+=`<div class="cita-pend-row"><span><strong>${escHtml(c.estudiante)}</strong> · ${escHtml(c.falta_especifica||'')} · con <strong>${escHtml(c.rol_destino)}</strong></span>`;
      html+=`<input type="datetime-local" id="citaDt-${c.id}" aria-label="Fecha y hora cita">`;
      html+=`<button type="button" class="btn btn-p btn-xs" onclick="propCitaStaff(${c.id})">Enviar propuesta</button></div>`;
    });
  }
  if(pc.length&&CU.rol==='Acudiente'){
    html+=`<div class="abanner ab-i" style="margin:0"><strong>${pc.length} cita(s) por confirmar</strong> — en la lista de faltas use <strong>Confirmar</strong> o <strong>Rechazar</strong> en el bloque de cita de cada registro.</div>`;
  }
  html+='</div>';
  bar.innerHTML=html;
  bar.style.display='block';
}

async function propCitaStaff(cid){
  const el=document.getElementById('citaDt-'+cid);
  const v=el&&el.value;
  if(!v){toast('Seleccione fecha y hora','e');return;}
  const r=await api('/api/citas/'+cid,{method:'PATCH',body:JSON.stringify({fecha_hora:v})});
  if(r.ok){toast('Propuesta enviada; el acudiente debe confirmar');await refreshCitasPendientes();renderCurrentTab();}
  else toast(r.error||'Error','e');
}

async function citaConfirmar(id){
  const r=await api('/api/citas/'+id,{method:'PATCH',body:JSON.stringify({accion:'confirmar'})});
  if(r.ok){toast('Cita confirmada');await refreshCitasPendientes();renderCurrentTab();}
  else toast(r.error||'Error','e');
}

async function citaRechazar(id){
  if(!confirm('¿Rechazar esta propuesta de cita?'))return;
  const r=await api('/api/citas/'+id,{method:'PATCH',body:JSON.stringify({accion:'rechazar'})});
  if(r.ok){toast('Cita rechazada');await refreshCitasPendientes();renderCurrentTab();}
  else toast(r.error||'Error','e');
}

function abrirSolicitudCita(fid){
  const row=document.getElementById('solFaltaRow');
  if(row)row.style.display='none';
  document.getElementById('solFaltaId').value=String(fid);
  document.getElementById('solRolDest').value='';
  const e=document.getElementById('solCitaErr');if(e)e.textContent='';
  openOv('ov-cita-solic');
}

function abrirSolicitudCitaGlobal(){
  const lista=window._faltasTabRaw||[];
  if(!lista.length){
    toast('No hay faltas en el año seleccionado. Si acaba de cambiar el año en la barra superior, elija el año en que está registrada la falta.','e');
    return;
  }
  document.getElementById('solFaltaId').value='';
  document.getElementById('solRolDest').value='';
  const row=document.getElementById('solFaltaRow');
  const ssel=document.getElementById('solFaltaSel');
  if(row)row.style.display='block';
  if(ssel){
    ssel.innerHTML='<option value="">Seleccione la falta asociada</option>'+lista.map(f=>{
      const t=`${f.fecha||''} · ${(f.falta_especifica||'').slice(0,48)}${(f.falta_especifica||'').length>48?'…':''} (${f.tipo_falta||''})`;
      return`<option value="${f.id}">${escHtml(t)}</option>`;
    }).join('');
  }
  const e=document.getElementById('solCitaErr');if(e)e.textContent='';
  openOv('ov-cita-solic');
}

async function enviarSolicitudCita(){
  const row=document.getElementById('solFaltaRow');
  let fid='';
  if(row&&row.style.display!=='none'){
    fid=(document.getElementById('solFaltaSel')?.value||'').trim();
  }else{
    fid=(document.getElementById('solFaltaId')?.value||'').trim();
  }
  const rol=document.getElementById('solRolDest').value;
  const err=document.getElementById('solCitaErr');
  if(err)err.textContent='';
  if(!fid){if(err)err.textContent='Seleccione la falta asociada';return;}
  if(!rol){if(err)err.textContent='Seleccione con quién desea la cita';return;}
  const r=await api('/api/faltas/'+fid+'/cita/solicitud',{method:'POST',body:JSON.stringify({rol_destino:rol})});
  if(r.ok){closeOv('ov-cita-solic');toast('Solicitud enviada');await refreshCitasPendientes();renderCurrentTab();}
  else{if(err)err.textContent=r.error||'Error';else toast(r.error||'Error','e');}
}

function toggleRCita(){
  const on=document.getElementById('rCitarAcu')?.checked;
  const el=document.getElementById('rCitaFields');
  if(el)el.style.display=on?'block':'none';
  refreshAcudienteCitaPanel();
}

function refreshAcudienteCitaPanel(){
  const wrap=document.getElementById('rAcuCitaDatos');
  const body=document.getElementById('rAcuCitaBody');
  const fields=document.getElementById('rCitaFields');
  if(!wrap||!body)return;
  if(!document.getElementById('rCitarAcu')?.checked||!fields||fields.style.display==='none'){
    wrap.style.display='none';
    return;
  }
  const eid=document.getElementById('rEst')?.value;
  if(!eid){
    body.innerHTML='<span style="color:var(--mut)">Seleccione primero al estudiante en el paso 1.</span>';
    wrap.style.display='block';
    return;
  }
  const e=window._rEstById&&window._rEstById[Number(eid)];
  if(!e){
    body.innerHTML='<span style="color:var(--mut)">Cargue el curso y el estudiante en el paso 1 para ver los datos de contacto.</span>';
    wrap.style.display='block';
    return;
  }
  const nomAcu=(e.acudiente||'').trim()||[e.apellido1_acu,e.apellido2_acu,e.nombre1_acu,e.nombre2_acu].filter(Boolean).join(' ').trim()||'—';
  const docAcu=((e.cedula_acudiente||'')+'').trim().replace(/\s/g,'');
  const docDisp=docAcu||'—';
  const tel=((e.telefono||'')+'').trim()||'—';
  const tipoAcu=(e.tipo_doc_acu||'').trim();
  const docLine=tipoAcu?`${escHtml(tipoAcu)} · ${escHtml(docDisp)}`:escHtml(docDisp);
  const telDigits=String(tel).replace(/\D/g,'');
  const telHtml=tel!=='—'&&telDigits.length>=7?`<a href="tel:${telDigits}">${escHtml(tel)}</a>`:escHtml(tel);
  body.innerHTML=`<div><strong>Acudiente:</strong> ${escHtml(nomAcu)}</div><div><strong>Documento:</strong> ${docLine}</div><div><strong>Teléfono:</strong> ${telHtml}</div>`;
  wrap.style.display='block';
}

// ── Faltas tab (tabla + filtros en cliente) ───────────────────────────────────
function _ftTipoRank(t){if(t==='Tipo III')return 0;if(t==='Tipo II')return 1;if(t==='Tipo I')return 2;return 3;}
function _ftEstadoRank(e){if(e==='pendiente')return 0;if(e==='en_revision')return 1;if(e==='cerrada')return 2;return 3;}
function faltasTabFiltered(){
  const raw=window._faltasTabRaw||[];
  const c=(document.getElementById('ftCurso')?.value||'').trim();
  const t=(document.getElementById('ftTipo')?.value||'').trim();
  const e=(document.getElementById('ftEstado')?.value||'').trim();
  const d0=document.getElementById('ftDesde')?.value||'';
  const d1=document.getElementById('ftHasta')?.value||'';
  const qq=(document.getElementById('fcSrch')?.value||'').trim().toLowerCase();
  return raw.filter(f=>{
    if(c&&f.curso!==c)return false;
    if(t&&f.tipo_falta!==t)return false;
    const eg=f.estado_gestion||'pendiente';
    if(e&&eg!==e)return false;
    const fd=f.fecha||'';
    if(d0&&fd<d0)return false;
    if(d1&&fd>d1)return false;
    if(!qq)return true;
    return Object.values(f).some(v=>String(v).toLowerCase().includes(qq));
  });
}
function faltasTabSorted(list){
  const s=window._faltasTabSort||{key:'fecha',dir:'desc'};
  const mul=s.dir==='asc'?1:-1;
  return [...list].sort((a,b)=>{
    let c=0;
    if(s.key==='estudiante') c=String(a.estudiante||'').localeCompare(String(b.estudiante||''),'es');
    else if(s.key==='curso') c=String(a.curso||'').localeCompare(String(b.curso||''),'es');
    else if(s.key==='fecha') c=String(a.fecha||'').localeCompare(String(b.fecha||''));
    else if(s.key==='tipo') c=_ftTipoRank(a.tipo_falta)-_ftTipoRank(b.tipo_falta);
    else if(s.key==='estado') c=_ftEstadoRank(a.estado_gestion||'pendiente')-_ftEstadoRank(b.estado_gestion||'pendiente');
    c*=mul;
    if(c!==0)return c;
    return String(b.fecha||'').localeCompare(String(a.fecha||''))||(b.id||0)-(a.id||0);
  });
}
function faltasTabToggleSort(key){
  const s=window._faltasTabSort||(window._faltasTabSort={key:'fecha',dir:'desc'});
  if(s.key===key)s.dir=s.dir==='asc'?'desc':'asc';
  else{s.key=key;s.dir=key==='fecha'?'desc':'asc';}
  faltasTabRender();
}
function faltasTabRender(){
  const list=faltasTabSorted(faltasTabFiltered());
  window._fc=list;
  const tit=document.getElementById('fcCountTit');
  if(tit) tit.textContent=`${list.length} faltas — ${getAnio()}`;
  const tb=document.getElementById('ftBody');
  if(!tb) return;
  const egTxt={pendiente:'Pendiente',en_revision:'En revisión',cerrada:'Cerrada'};
  if(!list.length){
    tb.innerHTML=`<tr><td colspan="5" class="empty" style="padding:28px">Sin registros con estos criterios</td></tr>`;
  }else{
    tb.innerHTML=list.map(f=>{
      const eg=f.estado_gestion||'pendiente';
      const cls=eg==='cerrada'?'ce':eg==='en_revision'?'er':'pe';
      const tb_=f.tipo_falta==='Tipo III'?'b3':f.tipo_falta==='Tipo II'?'b2':'b1';
      return`<tr onclick="verFalta(${f.id})">
        <td title="${escHtml(f.estudiante)}">${escHtml(f.estudiante)}</td>
        <td>${escHtml(f.curso)}</td>
        <td>${escHtml(f.fecha)}</td>
        <td><span class="bdg ${tb_}"><span class="dot ${f.tipo_falta==='Tipo III'?'dr':f.tipo_falta==='Tipo II'?'da':'dg'}"></span>${escHtml(f.tipo_falta)}</span></td>
        <td><span class="bdg beg-${cls}">${egTxt[eg]||eg}</span></td>
      </tr>`;
    }).join('');
  }
  document.querySelectorAll('#ftTable thead th.ft-sort').forEach(th=>{
    const k=th.getAttribute('data-sort');
    const s=window._faltasTabSort||{};
    const ind=th.querySelector('.ft-ind');
    if(ind) ind.textContent=s.key===k?(s.dir==='asc'?'▲':'▼'):'';
    th.classList.toggle('ft-sorted',s.key===k);
  });
}
function faltasTabResetFilt(){
  ['ftCurso','ftTipo','ftEstado'].forEach(id=>{const el=document.getElementById(id);if(el) el.selectedIndex=0;});
  const d0=document.getElementById('ftDesde');if(d0) d0.value='';
  const d1=document.getElementById('ftHasta');if(d1) d1.value='';
  const sc=document.getElementById('fcSrch');if(sc) sc.value='';
  faltasTabRender();
}
async function renderFaltas(tab){
  const canReg=['Coordinador','Director','Docente','Superadmin'].includes(CU.rol);
  const plantillasFaltasBar=['Docente','Director','Orientador'].includes(CU.rol)
    ?`<div class="card" style="margin-bottom:12px;padding:10px 14px;background:var(--ibg);border:1px solid var(--brd)">
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px">
        <div style="font-size:12px;color:var(--mut);line-height:1.45;flex:1;min-width:200px">
          <strong style="color:var(--ink)">Formatos en blanco</strong> — PDF con datos del colegio para imprimir o completar a mano; luego adjúntelo al registro de la falta.
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;flex-shrink:0">
          <button type="button" class="btn btn-xs btn-p" onclick="window.open('/api/pdf/plantilla/acta-descargos','_blank')">Acta de descargos</button>
          <button type="button" class="btn btn-xs" onclick="window.open('/api/pdf/plantilla/acta-sesion','_blank')">Acta de sesión</button>
        </div>
      </div>
    </div>`
    :'';
  const acuAgenda=CU.rol==='Acudiente'?`
    <div class="card" style="margin-bottom:12px">
      <div class="ch" style="align-items:flex-start;flex-wrap:wrap;gap:12px">
        <div style="flex:1;min-width:200px">
          <h3 style="margin-bottom:4px">Agendar cita con la institución</h3>
          <p style="font-size:12px;color:var(--mut);line-height:1.45;max-width:560px">Este botón es independiente de cada falta: puede usarlo en cualquier momento. Elija la falta vinculada a la reunión y el rol con quien desea hablar; la institución propondrá fecha y hora y usted confirmará en el portal.</p>
        </div>
        <button type="button" class="btn btn-p" style="flex-shrink:0" onclick="abrirSolicitudCitaGlobal()">Agendar cita</button>
      </div>
    </div>`:'';
  const optsCurso=`<option value="">Curso</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}`;
  tab.innerHTML=`
    ${acuAgenda}
    ${plantillasFaltasBar}
    <div class="card">
      <div class="ch"><h3 id="fcCountTit">Cargando…</h3>
        <div class="ch-r">
          <input class="srch ft-srch" id="fcSrch" placeholder="Buscar…" oninput="faltasTabRender()">
          ${canReg?`<button class="btn btn-p btn-xs" onclick="openOv('ov-falta')">+ Registrar</button>`:''}
        </div>
      </div>
      <div class="ft-toolbar">
        <select id="ftCurso" class="ft-inp" onchange="faltasTabRender()">${optsCurso}</select>
        <input type="date" id="ftDesde" class="ft-inp" title="Desde" oninput="faltasTabRender()" onchange="faltasTabRender()">
        <input type="date" id="ftHasta" class="ft-inp" title="Hasta" oninput="faltasTabRender()" onchange="faltasTabRender()">
        <select id="ftTipo" class="ft-inp" onchange="faltasTabRender()">
          <option value="">Tipo</option><option>Tipo I</option><option>Tipo II</option><option>Tipo III</option>
        </select>
        <select id="ftEstado" class="ft-inp" onchange="faltasTabRender()">
          <option value="">Estado</option><option value="pendiente">Pendiente</option><option value="en_revision">En revisión</option><option value="cerrada">Cerrada</option>
        </select>
        <button type="button" class="btn btn-xs" onclick="faltasTabResetFilt()">Limpiar</button>
      </div>
      <div class="table-wrap ft-tw">
        <table id="ftTable" class="table-faltas">
          <thead>
            <tr>
              <th class="ft-sort" data-sort="estudiante" onclick="faltasTabToggleSort('estudiante')">Estudiante <span class="ft-ind"></span></th>
              <th class="ft-sort" data-sort="curso" onclick="faltasTabToggleSort('curso')">Curso <span class="ft-ind"></span></th>
              <th class="ft-sort" data-sort="fecha" onclick="faltasTabToggleSort('fecha')">Fecha <span class="ft-ind"></span></th>
              <th class="ft-sort" data-sort="tipo" onclick="faltasTabToggleSort('tipo')">Tipo <span class="ft-ind"></span></th>
              <th class="ft-sort" data-sort="estado" onclick="faltasTabToggleSort('estado')">Estado <span class="ft-ind"></span></th>
            </tr>
          </thead>
          <tbody id="ftBody"></tbody>
        </table>
      </div>
    </div>`;
  window._faltasTabSort={key:'fecha',dir:'desc'};
  const raw=await api(`/api/faltas?anio=${encodeURIComponent(getAnio())}`);
  window._faltasTabRaw=Array.isArray(raw)?raw:[];
  const ftC=document.getElementById('ftCurso');
  if(ftC&&CU.rol==='Director'&&CU.curso) ftC.value=CU.curso;
  faltasTabRender();
}


// ── Asistencia ────────────────────────────────────────────────────────────────
function asistJusTxt(v){
  if(v===true||v===1)return'Justificada';
  if(v===false||v===0)return'Sin justificar';
  return'Pendiente';
}
async function asistSetJust(lid,val){
  const r=await api(`/api/asistencia/linea/${lid}`,{method:'PATCH',body:JSON.stringify({justificada:val})});
  if(r.ok){toast('Actualizado');renderCurrentTab();}else toast(r.error||'Error','e');
}
window._asistAusentes=new Map();
window._asistEstList=[];
async function asistOnCursoChange(){
  window._asistAusentes=new Map();
  const cur=document.getElementById('asistCurso')?.value;
  const wrap=document.getElementById('asistChips');
  const tb=document.getElementById('asistAbsBody');
  if(wrap)wrap.innerHTML='';
  if(tb)tb.innerHTML='';
  if(!cur){window._asistEstList=[];return;}
  const list=await api('/api/estudiantes?curso='+encodeURIComponent(cur));
  window._asistEstList=Array.isArray(list)?list:[];
  if(wrap){
    wrap.innerHTML=window._asistEstList.map(e=>
      `<button type="button" class="btn btn-xs" style="margin:4px" data-aid="${e.id}" onclick="asistToggleEst(${e.id})">${String(e.nombre).replace(/</g,'&lt;')}</button>`
    ).join('')||'<span class="mut">Sin estudiantes en este curso</span>';
  }
  asistPaintAbsRows();
}
function asistToggleEst(id){
  const m=window._asistAusentes;
  if(m.has(id)) m.delete(id);
  else{
    const e=window._asistEstList.find(x=>x.id===id);
    m.set(id,{nombre:e?e.nombre:'—',justificada:null});
  }
  asistPaintChips();
  asistPaintAbsRows();
}
function asistPaintChips(){
  document.querySelectorAll('#asistChips [data-aid]').forEach(btn=>{
    const id=Number(btn.getAttribute('data-aid'));
    btn.classList.toggle('btn-p',window._asistAusentes.has(id));
  });
}
function asistPaintAbsRows(){
  const tb=document.getElementById('asistAbsBody');
  if(!tb)return;
  const m=window._asistAusentes;
  const canTri=['Coordinador','Director','Docente','Superadmin'].includes(CU.rol);
  if(!m.size){tb.innerHTML='<tr><td colspan="3" class="mut">Pulse un nombre para marcar ausencia</td></tr>';return;}
  tb.innerHTML=[...m.entries()].map(([id,v])=>{
    const sel=`<select class="inp-sm" data-aj="${id}" onchange="asistJusPick(${id},this.value)" style="min-width:110px">
      <option value="" ${v.justificada===null?'selected':''}>Pendiente</option>
      <option value="1" ${v.justificada===true?'selected':''}>Justificada</option>
      <option value="0" ${v.justificada===false?'selected':''}>No justif.</option>
    </select>`;
    return`<tr><td>${String(v.nombre).replace(/</g,'&lt;')}</td><td>${canTri?sel:'<span class="mut">Pendiente</span>'}</td><td><button type="button" class="btn btn-xs" onclick="asistToggleEst(${id})">Quitar</button></td></tr>`;
  }).join('');
}
function asistJusPick(id,val){
  const rec=window._asistAusentes.get(id);
  if(!rec)return;
  rec.justificada=val===''?null:val==='1';
  window._asistAusentes.set(id,rec);
}
async function guardarAsistToma(){
  const fecha=document.getElementById('asistFecha')?.value;
  let cur=document.getElementById('asistCurso')?.value;
  if(CU.rol==='Director'&&CU.curso) cur=CU.curso;
  const asig=(document.getElementById('asistAsig')?.value||'').trim();
  const err=document.getElementById('asistErr');
  if(err)err.textContent='';
  if(!fecha){if(err)err.textContent='Indique la fecha';return;}
  if(!cur){if(err)err.textContent='Indique el curso';return;}
  const lineas=[...window._asistAusentes.keys()].map(eid=>({estudiante_id:eid,ausente:true,justificada:window._asistAusentes.get(eid).justificada}));
  if(!lineas.length){if(err)err.textContent='Marque al menos un ausente';return;}
  const r=await api('/api/asistencia/toma',{method:'POST',body:JSON.stringify({fecha,curso:cur,asignatura:asig,lineas})});
  if(r.ok){
    toast('Toma de asistencia guardada');
    window._asistAusentes=new Map();
    const tb=document.getElementById('asistAbsBody');if(tb)tb.innerHTML='';
    asistPaintChips();
    renderCurrentTab();
  }else if(err) err.textContent=r.error||'Error';
  else toast(r.error||'Error','e');
}
async function guardarAsigPred(){
  const asig=(document.getElementById('asistAsig')?.value||'').trim();
  const r=await api('/api/me/asignatura',{method:'PATCH',body:JSON.stringify({asignatura:asig})});
  if(r.ok){CU.asignatura=asig;toast('Asignatura predeterminada guardada');}else toast(r.error||'Error','e');
}
async function renderAsistencia(tab){
  window._asistAusentes=new Map();
  const tomas=await api('/api/asistencia/tomas');
  const list=Array.isArray(tomas)?tomas:(tomas&&tomas.error?[]:[]);
  const errApi=tomas&&tomas.error;
  const hoy=new Date().toISOString().slice(0,10);
  const canTri=['Coordinador','Director','Docente','Superadmin'].includes(CU.rol);
  const cursoSel=CU.rol==='Director'&&CU.curso
    ?`<select id="asistCurso" disabled style="width:100%"><option value="${CU.curso}">${CU.curso}</option></select>`
    :`<select id="asistCurso" onchange="asistOnCursoChange()" style="width:100%"><option value="">Seleccionar</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}</select>`;
  const predAsig=(CU.asignatura||'').replace(/"/g,'&quot;');
  const canJustReview=['Coordinador','Director','Superadmin'].includes(CU.rol);
  tab.innerHTML=`
    ${errApi?`<div class="abanner ab-r">${errApi}</div>`:''}
    <div class="abanner ab-i" style="font-size:11px">Los ausentes pueden marcarse como justificados o no; coordinación y dirección pueden revisar y corregir el estado después del registro.</div>
    ${canTri?`
    <div class="card">
      <div class="ch"><h3>Nueva toma</h3></div>
      <div style="padding:12px;display:grid;gap:10px;max-width:640px">
        <div class="fr"><div><label class="fl">Fecha</label><input type="date" id="asistFecha" value="${hoy}"></div><div><label class="fl">Curso</label>${cursoSel}</div></div>
        <div><label class="fl">Asignatura / espacio</label>
          <input id="asistAsig" placeholder="Ej: Matemáticas" maxlength="120" value="${predAsig}">
          ${CU.rol==='Docente'?`<button type="button" class="btn btn-xs" style="margin-left:8px" onclick="guardarAsigPred()">Guardar como predeterminada</button>`:''}
        </div>
        <div><label class="fl">Estudiantes — pulse para marcar ausencia</label><div id="asistChips" class="mut" style="line-height:1.6">Elija curso primero</div></div>
        <table class="tbl" style="max-width:520px"><thead><tr><th>Ausente</th><th>Justificación (al registrar)</th><th></th></tr></thead><tbody id="asistAbsBody"><tr><td colspan="3" class="mut">Elija curso y pulse nombres</td></tr></tbody></table>
        <p class="ferr" id="asistErr" style="font-size:12px"></p>
        <button type="button" class="btn btn-p" onclick="guardarAsistToma()">Guardar toma</button>
      </div>
    </div>
    `:''}
    <div class="card">
      <div class="ch"><h3>Historial reciente</h3></div>
      <div style="padding:9px">${list.length?list.map(t=>{
        const det=(t.detalles||[]).filter(d=>d.ausente);
        return`<div class="fcard" style="margin-bottom:10px;cursor:default">
          <div class="fc-top"><span class="fc-est">${t.fecha} · ${t.curso}</span><span class="bdg bg">${t.asignatura||'—'}</span></div>
          <div class="fc-meta"><span>${t.docente_nombre||''}</span><span>${t.creado_en||''}</span></div>
          ${det.length?`<table class="tbl" style="margin-top:8px;font-size:12px"><thead><tr><th>Estudiante</th><th>Justificada</th>${canJustReview?'<th>Revisar</th>':''}</tr></thead><tbody>
            ${det.map(d=>{
              const j=d.justificada;
              const review=canJustReview?`<td><button type="button" class="btn btn-xs" onclick="asistSetJust(${d.id},true)">Marcar sí</button> <button type="button" class="btn btn-xs" onclick="asistSetJust(${d.id},false)">Marcar no</button></td>`:'';
              return`<tr><td>${String(d.estudiante_nombre||'—').replace(/</g,'&lt;')}</td><td>${asistJusTxt(j)}</td>${review}</tr>`;
            }).join('')}
          </tbody></table>`:'<div class="mut" style="margin-top:6px">Sin ausencias registradas</div>'}
        </div>`;
      }).join(''):'<div class="empty">Sin tomas</div>'}</div>
    </div>`;
  if(CU.rol==='Director'&&CU.curso) asistOnCursoChange();
}

// ── Estudiantes ───────────────────────────────────────────────────────────────
async function renderEstudiantes(tab){
  const ests=await api('/api/estudiantes');window._ec=ests;
  tab.innerHTML=`
    <div class="card">
      <div class="ch"><h3>${ests.length} estudiantes</h3>
        <div class="ch-r">
          <select id="fECur" style="font-size:12px;padding:5px 9px" onchange="filtEst()"><option value="">Todos los cursos</option>${CURSOS.map(c=>`<option>${c}</option>`).join('')}</select>
          <button class="btn btn-p btn-xs" onclick="openNuevoEst()">+ Agregar</button>
          <button class="btn btn-g btn-xs" onclick="openOv('ov-import')">Carga masiva</button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th style="width:12%">Documento</th><th style="width:22%">Nombre</th><th style="width:7%">Curso</th><th style="width:16%">Acudiente</th><th style="width:9%">Doc. acu.</th><th style="width:11%">Teléfono</th><th>Barreras</th><th style="width:75px"></th></tr></thead>
          <tbody id="tEst">${filasEst(ests)}</tbody>
        </table>
      </div>
    </div>`;
}
function filasEst(lista){
  if(!lista.length)return`<tr><td colspan="8" class="empty">No hay estudiantes</td></tr>`;
  return lista.map(e=>`<tr>
    <td style="font-family:monospace;font-size:11px">${e.documento_identidad||'—'}</td>
    <td style="font-weight:500">${e.nombre}</td><td>${e.curso}</td>
    <td>${e.acudiente||'—'}</td><td style="font-family:monospace;font-size:11px">${e.cedula_acudiente||'—'}</td>
    <td>${e.telefono||'—'}</td><td>${e.barreras||e.discapacidad||'—'}</td>
    <td style="display:flex;gap:3px">
      <button class="btn btn-xs btn-i" onclick="editarEst(${e.id})">Editar</button>
      ${['Coordinador','Superadmin'].includes(CU.rol)?`<button class="btn btn-xs btn-d" onclick="borrarEst(${e.id})">✕</button>`:''}
    </td>
  </tr>`).join('');
}
function filtEst(){const cur=document.getElementById('fECur')?.value||'';const lista=(window._ec||[]).filter(e=>!cur||e.curso===cur);const tb=document.getElementById('tEst');if(tb)tb.innerHTML=filasEst(lista);}

// ── Usuarios ──────────────────────────────────────────────────────────────────
async function renderUsuarios(tab){
  const usrs=await api('/api/usuarios');
  tab.innerHTML=`
    <div class="card">
      <div class="ch"><h3>${usrs.length} usuarios</h3><button class="btn btn-p btn-xs" onclick="openNuevoUsr()">+ Nuevo usuario</button></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th style="width:14%">Usuario</th><th>Nombre</th><th style="width:12%">Rol</th><th style="width:10%">Curso</th><th style="width:110px">Acciones</th></tr></thead>
          <tbody>${usrs.map(u=>`<tr>
            <td><code style="font-size:11px;background:#f0ece4;padding:2px 5px;border-radius:3px">${u.usuario}</code></td>
            <td>${u.nombre}</td><td><span class="tag ${TGCLS[u.rol]||'t-doc'}">${u.rol}</span></td><td>${u.curso||'—'}</td>
            <td style="display:flex;gap:3px">
              <button class="btn btn-xs btn-i" onclick="editarUsr(${u.id})">Editar</button>
              ${u.id!==CU.id?`<button class="btn btn-xs btn-d" onclick="borrarUsr(${u.id})">✕</button>`:''}
            </td>
          </tr>`).join('')}</tbody>
        </table>
      </div>
    </div>`;
}

// ── Catálogo ──────────────────────────────────────────────────────────────────
async function renderCatalogo(tab){
  const cat=await api('/api/catalogo');catCache=cat;
  tab.innerHTML=`
    <div class="card">
      <div class="ch"><h3>Catálogo de faltas</h3><div class="ch-r"><button class="btn btn-g btn-xs" onclick="openOv('ov-cat-bulk')">Carga masiva</button><button class="btn btn-p btn-xs" onclick="openOv('ov-cat-new')">+ Nueva falta</button></div></div>
      <div class="tbar">
        <button class="tb-btn on" onclick="setCF('Tipo I',this)">Tipo I — Leves</button>
        <button class="tb-btn" onclick="setCF('Tipo II',this)">Tipo II — Graves</button>
        <button class="tb-btn" onclick="setCF('Tipo III',this)">Tipo III — Muy graves</button>
      </div>
      <div class="table-wrap">
        <table><thead><tr><th style="width:24%">Descripción</th><th style="width:8%">Tipo</th><th style="width:16%">Temática</th><th>Protocolo</th><th>Sanción</th><th style="width:55px"></th></tr></thead>
        <tbody id="tCat">${filasCat(cat,catFil)}</tbody></table>
      </div>
    </div>`;
}
function filasCat(cat,tipo){
  const lista=cat.filter(f=>f.tipo===tipo);
  if(!lista.length)return`<tr><td colspan="6" class="empty">No hay faltas en este tipo</td></tr>`;
  return lista.map(f=>`<tr>
    <td style="font-weight:500;white-space:normal">${f.descripcion}</td>
    <td>${bdg(f.tipo)}</td>
    <td style="white-space:normal;vertical-align:middle">${(f.tematica||'').trim()?temBdg(f.tematica):'<span class="mut" style="font-size:11px">—</span>'}</td>
    <td style="font-size:11px;color:var(--mut);white-space:normal;line-height:1.4">${f.protocolo||'<span style=color:#c9a84c>Sin definir — edite en Protocolos</span>'}</td>
    <td style="font-size:11px;color:var(--mut);white-space:normal;line-height:1.4">${f.sancion||'<span style=color:#c9a84c>Sin definir — edite en Protocolos</span>'}</td>
    <td><button type="button" class="btn btn-xs btn-d" onclick="borrarCat(${f.id})" title="Eliminar del catálogo">✕</button></td>
  </tr>`).join('');
}
function setCF(tipo,btn){catFil=tipo;document.querySelectorAll('.tbar .tb-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');const tb=document.getElementById('tCat');if(tb)tb.innerHTML=filasCat(catCache,tipo);}

// ── Protocolos ────────────────────────────────────────────────────────────────
function htmlFilasProtoCat(cat){
  if(!cat||!cat.length)return'<tr><td colspan="6" class="empty">No hay ítems en el catálogo. Agréguelos en «Catálogo de faltas».</td></tr>';
  return cat.slice().sort((a,b)=>(a.tipo+a.descripcion).localeCompare(b.tipo+b.descripcion)).map(f=>`<tr>
    <td style="font-weight:500;white-space:normal">${f.descripcion}</td>
    <td>${bdg(f.tipo)}</td>
    <td style="white-space:normal;vertical-align:middle">${(f.tematica||'').trim()?temBdg(f.tematica):'<span class="mut" style="font-size:11px">—</span>'}</td>
    <td style="font-size:11px;color:var(--mut);white-space:normal;line-height:1.35">${f.protocolo||'<span style=color:#c9a84c>Sin definir</span>'}</td>
    <td style="font-size:11px;color:var(--mut);white-space:normal;line-height:1.35">${f.sancion||'<span style=color:#c9a84c>Sin definir</span>'}</td>
    <td><button type="button" class="btn btn-xs btn-i" onclick="editarProtoPorId(${f.id})">Editar protocolo, sanción y temática</button></td>
  </tr>`).join('');
}

async function renderProto(tab){
  const cat=await api('/api/catalogo');
  catCache=cat;
  tab.innerHTML=`
    <div id="coProtoRoot" style="background:var(--surf);border:1px solid var(--brd);border-radius:var(--rl) var(--rl) 0 0;overflow:hidden">
      <div class="tbar">
        <button type="button" class="tb-btn" onclick="showP2('pp1',this)">Protocolos de atención</button>
        <button type="button" class="tb-btn" onclick="showP2('pp2',this)">Procesos disciplinares</button>
        <button type="button" class="tb-btn on" id="tbProtoP3" onclick="showP2('pp3',this)">Protocolo por falta del catálogo</button>
      </div>
    </div>
    <div class="proto-toolstrip" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 14px;border:1px solid var(--brd);border-top:none;background:rgba(0,0,0,.02)">
      <span style="font-size:11px;color:var(--mut);line-height:1.4;flex:1;min-width:200px">Las pestañas <strong>I / II / III</strong> son referencia general. La edición es por ítem del catálogo (tabla de abajo) o en <strong>Catálogo de faltas</strong>.</span>
      <button type="button" class="btn btn-xs btn-i" onclick="showTab('co-cat',null)">Catálogo de faltas</button>
      <button type="button" class="btn btn-xs btn-g" onclick="openOv('ov-cat-bulk')">Carga masiva al catálogo</button>
    </div>
    <div id="pp1" class="pgrid" style="margin-top:10px;display:none">
      <div class="pc"><div class="pc-h ph1">Protocolo Tipo I — Leve</div><div class="pc-b"><p>El docente reúne a las partes para mediar pedagógicamente.</p><p>• Fijar solución de manera imparcial.</p><p>• Diálogo con el director o coordinación.</p><p>• Con <strong>4 situaciones tipo I acumuladas</strong> se convoca el Comité de Convivencia y se activa proceso tipo II.</p></div></div>
      <div class="pc"><div class="pc-h ph2">Protocolo Tipo II — Grave</div><div class="pc-b"><p>• El director hace llamado formal además de las acciones tipo I.</p><p>• Atención en salud si la situación lo amerita.</p><p>• El coordinador rinde informe al rector.</p><p>• Citar e informar a acudientes inmediatamente.</p><p>• Remisión al Comité Escolar de Convivencia.</p></div></div>
      <div class="pc"><div class="pc-h ph3">Protocolo Tipo III — Muy grave</div><div class="pc-b"><p>• Garantizar atención inmediata en salud.</p><p>• Anotación en el observador firmada por el estudiante.</p><p>• Informar a padres o acudientes de manera inmediata.</p><p>• Remisión al Comité Escolar de Convivencia.</p><p>• Activación de la Ruta de Atención Integral (RAI).</p></div></div>
    </div>
    <div id="pp2" class="pgrid" style="margin-top:10px;display:none">
      <div class="pc"><div class="pc-h ph1">Proceso — Tipo I</div><div class="pc-b"><p>• Llamado de atención verbal con acción pedagógica.</p><p>• Llamado escrito en el observador del estudiante.</p><p>• Compromisos concertados con el acudiente (1 a 3 días).</p><p>• <strong>3 reincidencias Tipo I activan proceso Tipo II.</strong></p></div></div>
      <div class="pc"><div class="pc-h ph2">Proceso — Tipo II</div><div class="pc-b"><p>• Trabajo pedagógico evaluado 3 días después del reintegro.</p><p>• El acudiente garantiza la reparación del daño.</p><p>• La desescolarización no aplica en tipos I o II.</p><p>• 4 situaciones tipo II = 1 situación tipo III.</p></div></div>
      <div class="pc"><div class="pc-h ph3">Proceso — Tipo III</div><div class="pc-b"><p>• En riesgo inminente: llamar a Policía Nacional.</p><p>• Informe inmediato al rector y convocatoria del Comité.</p><p>• Activación de la Ruta de Atención Integral.</p></div></div>
    </div>
    <div id="pp3" style="display:block;margin-top:10px">
      <div class="card">
        <div class="ch"><h3>Protocolo y sanción por ítem del catálogo</h3></div>
        <div class="mb" style="padding:12px 14px">
          <p class="mut" style="font-size:11px;margin:0 0 10px;line-height:1.45">Texto que verá el docente al registrar una falta (pasos 2 y 4). Use <strong>Editar protocolo y sanción</strong> en cada fila.</p>
          <div class="table-wrap">
            <table><thead><tr><th>Descripción</th><th style="width:9%">Tipo</th><th style="width:14%">Temática</th><th>Protocolo</th><th>Sanción / medida</th><th style="width:150px"></th></tr></thead>
            <tbody id="tProtoCat">${htmlFilasProtoCat(cat)}</tbody></table>
          </div>
        </div>
      </div>
    </div>`;
}

function showP2(id,btn){
  ['pp1','pp2','pp3'].forEach(p=>{const el=document.getElementById(p);if(el)el.style.display='none';});
  const el=document.getElementById(id);
  if(el)el.style.display=(id==='pp3')?'block':'grid';
  document.querySelectorAll('#coProtoRoot .tb-btn').forEach(b=>b.classList.remove('on'));
  if(btn)btn.classList.add('on');
}


// ── Alertas ciudadanas (reporte estudiantil, Ley 1620) ───────────────────────
async function patchRepEst(id, estado) {
  const nota =
    prompt(
      'Nota para la bitácora y el equipo (mínimo 10 caracteres). Explique el criterio, acuerdos o siguiente paso:',
    ) || '';
  if (nota.trim().length < 10) {
    toast('La nota debe tener al menos 10 caracteres.', 'e');
    return;
  }
  const body = { estado, nota_comite: nota.trim() };
  if (CU.rol === 'Superadmin' && CU.colegio_id) body.colegio_id = CU.colegio_id;
  const r = await api(`/api/reportes-convivencia/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
  if (r.ok) {
    toast('Estado actualizado');
    renderCurrentTab();
  } else toast(r.error || 'Error', 'e');
}

async function openRepBitacora(id) {
  const body = document.getElementById('repBitBody');
  if (body) body.innerHTML = '<div class="mut">Cargando…</div>';
  let url = `/api/reportes-convivencia/${encodeURIComponent(String(id))}/bitacora`;
  if (CU.rol === 'Superadmin') {
    const cid = CU.colegio_id || '';
    if (cid) url += `?colegio_id=${encodeURIComponent(String(cid))}`;
  }
  const rows = await api(url);
  if (rows && rows.error) {
    if (body) body.innerHTML = `<div class="abanner ab-r">${escHtml(rows.error)}</div>`;
    openOv('ov-rep-bit');
    return;
  }
  const list = Array.isArray(rows) ? rows : [];
  const stLbl = {
    pendiente_validacion: 'Pendiente validación',
    caso_abierto: 'Caso abierto',
    orientacion: 'Orientación',
    descartado: 'Descartado',
  };
  if (body) {
    body.innerHTML = list.length
      ? `<table class="tbl"><thead><tr><th>Cuándo</th><th>Quién</th><th>Cambio</th><th>Nota</th></tr></thead><tbody>${list
          .map((b) => {
            const ant = stLbl[b.estado_anterior] || b.estado_anterior || '—';
            const nv = stLbl[b.estado_nuevo] || b.estado_nuevo || '—';
            const who = `${escHtml(b.usuario_nombre || '—')} <span class="mut">(${escHtml(b.rol || '')})</span>`;
            return `<tr>
            <td style="font-size:11px;white-space:nowrap">${escHtml(b.creado_en || '—')}</td>
            <td style="font-size:11px">${who}</td>
            <td style="font-size:11px">${escHtml(ant)} → <strong>${escHtml(nv)}</strong></td>
            <td style="font-size:12px">${escHtml(b.nota || '')}</td>
          </tr>`;
          })
          .join('')}</tbody></table>`
      : '<div class="empty">Aún no hay movimientos registrados en bitácora (aparecen al cambiar estado con nota).</div>';
  }
  openOv('ov-rep-bit');
}

async function renderReportesEst(tab) {
  if (CU.rol === 'Superadmin' && !CU.colegio_id) {
    tab.innerHTML =
      '<div class="abanner ab-i">Asigne o seleccione una institución en su perfil de superadmin para ver alertas de ese colegio.</div>';
    return;
  }
  let url = '/api/reportes-convivencia';
  if (CU.rol === 'Superadmin' && CU.colegio_id) url += `?colegio_id=${encodeURIComponent(String(CU.colegio_id))}`;
  const rows = await api(url);
  if (rows && rows.error) {
    tab.innerHTML = `<div class="abanner ab-r">${escHtml(rows.error)}</div>`;
    return;
  }
  const list = Array.isArray(rows) ? rows : [];
  const tbody = list.length
    ? list
        .map((r) => {
          const urg = r.urgencia === 'urgente' ? '<span class="reit-bdg crit">Urgente</span>' : '<span class="bdg bg">Puede esperar</span>';
          const st = escHtml(r.estado || '');
          const cat = escHtml(REP_CAT_LBL[r.categoria_visual] || r.categoria_visual || '—');
          const lug = escHtml(REP_LUG_LBL[r.lugar_clave] || r.lugar_clave || '—');
          const desc = escHtml((r.descripcion || '').slice(0, 120)) + ((r.descripcion || '').length > 120 ? '…' : '');
          const ev = r.evidencia_path
            ? `<a href="/static/uploads/${escHtml(r.evidencia_path)}" target="_blank" rel="noopener">Archivo</a>`
            : '—';
          const bitBtn = `<button type="button" class="btn btn-xs btn-i" onclick="openRepBitacora(${Number(r.id)})">Bitácora</button>`;
          const btns =
            r.estado === 'pendiente_validacion'
              ? `${bitBtn}<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">
                 <button type="button" class="btn btn-xs btn-p" onclick="patchRepEst(${Number(r.id)},'caso_abierto')">Abrir caso formal</button>
                 <button type="button" class="btn btn-xs" onclick="patchRepEst(${Number(r.id)},'orientacion')">Orientación privada</button>
                 <button type="button" class="btn btn-xs btn-d" onclick="patchRepEst(${Number(r.id)},'descartado')">Descartar</button>
                 </div>`
              : bitBtn;
          return `<tr>
            <td style="font-size:11px">${escHtml(r.creado_en || '—')}</td>
            <td>${urg}</td>
            <td><strong>${escHtml(r.estudiante_nombre || '')}</strong><div class="mut">${escHtml(r.curso || '')}</div></td>
            <td style="font-size:11px">${cat}</td>
            <td style="font-size:11px;max-width:200px" title="${escHtml(r.descripcion || '')}">${desc}</td>
            <td style="font-size:11px">${lug}</td>
            <td><span class="tag t-or">${st}</span>${r.nota_comite ? `<div class="mut" style="margin-top:4px">${escHtml(r.nota_comite)}</div>` : ''}</td>
            <td style="font-size:11px">${ev}<div style="margin-top:6px">${btns}</div></td>
          </tr>`;
        })
        .join('')
    : '<tr><td colspan="8" class="empty">Sin alertas registradas</td></tr>';
  tab.innerHTML = `
    <div class="card">
      <div class="ch"><h3>Cómo entra el estudiante</h3></div>
      <div class="mb" style="padding:12px 14px;font-size:13px;line-height:1.55;color:var(--mut)">
        <p style="margin:0 0 8px"><strong>Cómo entra el estudiante</strong> — debe existir su ficha en el colegio (alta o carga masiva), que crea el acceso al portal. En <code>/login</code> marca <strong>«Soy estudiante»</strong>, usuario = <strong>documento</strong> (sin puntos) y la contraseña que definió la institución (por defecto los <strong>4 últimos dígitos</strong> del documento si no se indicó otra). Si el documento está en más de un colegio, el sistema pide el <strong>nombre de la I.E.</strong> La página pública <code>/reporte/&lt;institución&gt;</code> usa el mismo documento y contraseña. El personal autorizado puede <strong>restablecer la contraseña</strong> desde <strong>Editar estudiante</strong>.</p>
        <p style="margin:0">Las alertas <strong>no crean falta</strong> solas: quedan pendientes hasta que usted elija abrir caso, orientación o descartar. Cada cambio de estado exige una <strong>nota de al menos 10 caracteres</strong> y queda registrada en la <strong>bitácora</strong> del reporte.</p>
      </div>
    </div>
    <div class="card">
      <div class="ch"><h3>Bandeja de alertas ciudadanas</h3></div>
      <div class="table-wrap mb" style="padding:0 8px 12px">
        <table>
          <thead><tr><th>Recibido</th><th>Urgencia</th><th>Estudiante</th><th>Tema (lo que eligió)</th><th>Resumen</th><th>Lugar</th><th>Estado / nota</th><th>Evidencia / acciones</th></tr></thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>
    </div>`;
}

// ── Reportes ──────────────────────────────────────────────────────────────────
async function renderReportes(tab){
  const rep=await api(`/api/reportes?anio=${getAnio()}`);
  const meses=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  const mData=new Array(12).fill(0);Object.entries(rep.por_mes||{}).forEach(([m,v])=>{const i=parseInt(m)-1;if(i>=0&&i<12)mData[i]=v;});
  const maxM=Math.max(...mData,1);
  const bars=(data,color)=>{if(!data||!Object.keys(data).length)return`<div style="font-size:11px;color:var(--mut);padding:6px 0">Sin datos</div>`;const entries=Array.isArray(data)?data:Object.entries(data).sort((a,b)=>b[1]-a[1]);const mx=Math.max(...(Array.isArray(data)?data.map(d=>d[1]):Object.values(data)),1);return entries.map(([k,v])=>`<div class="brow"><div class="blbl">${k}</div><div class="btrk"><div class="bfil" style="width:${Math.round(v/mx*100)}%;background:${color}"></div></div><div class="bval">${v}</div></div>`).join('');};
  tab.innerHTML=`
    <div class="rep-grid">
      <div class="rc"><h4>POR TIPO DE FALTA</h4>${bars(rep.por_tipo,'#378ADD')}</div>
      <div class="rc"><h4>TOP ESTUDIANTES</h4>${bars(rep.top_estudiantes,'#e74c3c')}</div>
      <div class="rc"><h4>POR CURSO</h4>${bars(rep.por_curso,'#639922')}</div>
      <div class="rc"><h4>POR DOCENTE</h4>${bars(rep.por_docente,'#BA7517')}</div>
    </div>
    <div class="card">
      <div class="ch"><h3>Distribución mensual ${getAnio()}</h3></div>
      <div style="padding:14px;display:flex;gap:5px;align-items:flex-end;height:90px">
        ${mData.map((v,i)=>`<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px">
          <div style="font-size:10px;color:var(--mut)">${v||''}</div>
          <div style="width:100%;background:#e74c3c;border-radius:2px 2px 0 0;height:${Math.round(v/maxM*58)}px;min-height:${v?2:0}px"></div>
          <div style="font-size:9px;color:var(--mut)">${meses[i]}</div>
        </div>`).join('')}
      </div>
    </div>
    <div class="card">
      <div class="ch"><h3>Áreas de mejoramiento</h3></div>
      <div style="padding:13px" id="mejoramientoPanel">Cargando sugerencias...</div>
    </div>
    <div class="card">
      <div class="ch"><h3>Generar reportes</h3></div>
      <div style="padding:14px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div>
            <label class="fl">Reporte por curso (PDF)</label>
            <div style="display:flex;gap:6px;margin-top:4px">
              <select id="repCursoSel" style="flex:1;font-size:12px;padding:6px 8px">${CURSOS.map(c=>`<option>${c}</option>`).join('')}</select>
              <button class="btn btn-p btn-xs" onclick="dlRepCurso('pdf')">PDF</button>
            </div>
            <div class="fhint">Reporte completo del curso con seguimiento</div>
          </div>
          <div>
            <label class="fl">Historial del estudiante (PDF)</label>
            <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
              <select id="repEstCurso" style="font-size:12px;padding:6px 8px;width:110px" onchange="cargarEstRep()">${CURSOS.map(c=>`<option>${c}</option>`).join('')}</select>
              <select id="repEstSel" style="flex:1;font-size:12px;padding:6px 8px;min-width:140px"><option value="">Seleccionar estudiante</option></select>
              <button class="btn btn-p btn-xs" onclick="dlRepEst('pdf')">PDF</button>
            </div>
            <div class="fhint">Historial completo — seleccione curso y luego el estudiante</div>
          </div>
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--brd);display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-p btn-xs" onclick="window.location.href='/api/pdf/general?anio='+getAnio()">PDF general del año</button>
          <a href="/api/exportar-csv?anio=${getAnio()}" class="btn btn-xs" style="text-decoration:none">CSV completo</a>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="ch"><h3>Formatos convivencia (plantillas vacías)</h3></div>
      <div style="padding:14px;font-size:12px;color:var(--mut)">
        <p style="margin:0 0 10px;line-height:1.45">PDF con nombre, municipio y NIT del colegio. Descargue, imprima o complete y firme a mano; luego adjunte el archivo al registro de la falta (desde el detalle o al crearla).</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button type="button" class="btn btn-p btn-xs" onclick="window.open('/api/pdf/plantilla/acta-descargos','_blank')">Acta de descargos</button>
          <button type="button" class="btn btn-p btn-xs" onclick="window.open('/api/pdf/plantilla/acta-sesion','_blank')">Acta de sesión (comité / acudientes)</button>
        </div>
      </div>
    </div>`;
  setTimeout(()=>{document.querySelectorAll('.bfil').forEach(b=>{const w=b.style.width;b.style.width='0';setTimeout(()=>b.style.width=w,80);});},50);
  if(['Director','Coordinador','Orientador','Superadmin'].includes(CU.rol)){
    const mp=document.getElementById('mejoramientoPanel');
    if(mp){
      api('/api/mejoramiento?anio='+getAnio()).then(data=>{
        if(data.error){mp.innerHTML='<div class="empty">No disponible</div>';return;}
        let html='';
        Object.entries(data).sort().forEach(([curso,info])=>{
          const hasSug=info.sugerencias&&info.sugerencias.length>0;
          if(!hasSug)return;
          html+=`<div style="margin-bottom:14px;padding-bottom:14px;border-bottom:0.5px solid var(--brd)">`;
          html+=`<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">`;
          html+=`<span style="font-size:12px;font-weight:600">Curso ${curso}</span>`;
          html+=`<span class="bdg bg">${info.total} faltas</span>`;
          html+=`<span class="bdg b1">${info.t1} tipo I</span>`;
          if(info.t2>0)html+=`<span class="bdg b2">${info.t2} tipo II</span>`;
          if(info.t3>0)html+=`<span class="bdg b3">${info.t3} tipo III</span>`;
          html+='</div>';
          info.sugerencias.forEach(s=>{ html+=`<div style="margin-bottom:4px;font-size:11px;color:var(--mut)">${s}</div>`; });
          html+='</div>';
        });
        mp.innerHTML=html||'<div class="empty">No hay sugerencias para este período</div>';
      });
    }
  }
}

function dlRepCurso(fmt='pdf'){
  const cur=document.getElementById('repCursoSel')?.value;
  if(!cur){toast('Selecciona un curso','e');return;}
  window.location.href=`/api/pdf/curso?curso=${encodeURIComponent(cur)}&anio=${getAnio()}`;
}
async function cargarEstRep(){
  const cur=document.getElementById('repEstCurso')?.value;
  const sel=document.getElementById('repEstSel');
  if(!sel)return;
  sel.innerHTML='<option value="">Cargando...</option>';
  if(!cur)return;
  const ests=await api(`/api/estudiantes?curso=${encodeURIComponent(cur)}`);
  sel.innerHTML='<option value="">Seleccionar estudiante</option>'+ests.map(e=>`<option value="${e.id}" data-nom="${e.nombre}">${e.nombre}</option>`).join('');
}
function dlRepEst(fmt='pdf'){
  const sel=document.getElementById('repEstSel');
  const opt=sel?.options[sel.selectedIndex];
  const estId=sel?.value;
  const nom=opt?.getAttribute('data-nom')||'';
  if(!estId){toast('Selecciona un estudiante','e');return;}
  window.location.href=`/api/pdf/estudiante?est_id=${estId}&estudiante=${encodeURIComponent(nom)}&anio=todos`;
}

// ── Cierre de año ─────────────────────────────────────────────────────────────
function renderAnio(tab){
  tab.innerHTML=`<div class="card"><div class="ch"><h3>Cierre de año escolar</h3></div>
    <div style="padding:14px">
      <div class="abanner ab-a" style="margin-bottom:12px">Esta acción archiva las faltas del año actual. Se pueden consultar filtrando por año en la barra superior.</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-d" onclick="if(confirm('¿Archivar el año actual?')){api('/api/cerrar-anio',{method:'POST',body:JSON.stringify({})}).then(()=>toast('Año archivado'))}">Cerrar año actual (mantener estudiantes)</button>
        <button class="btn btn-d" onclick="if(confirm('¿Archivar año y limpiar lista de estudiantes?')){api('/api/cerrar-anio',{method:'POST',body:JSON.stringify({limpiar_estudiantes:true})}).then(()=>{toast('Año archivado y lista limpiada');renderCurrentTab()})}">Cerrar año y limpiar estudiantes</button>
      </div>
    </div></div>`;
}

// ── Perfil estudiante ─────────────────────────────────────────────────────────
async function renderPerfil(tab){
  const ests=await api('/api/estudiantes');
  tab.innerHTML=`
    <div class="card" style="margin-bottom:12px">
      <div style="padding:13px">
        <label class="fl">Seleccionar estudiante</label>
        <select id="perfSel" style="max-width:320px" onchange="renderPerfilDet()">
          <option value="">Seleccionar...</option>
          ${ests.map(e=>`<option value="${e.id}" data-nom="${e.nombre}" data-cur="${e.curso}">${e.nombre} — ${e.curso}</option>`).join('')}
        </select>
      </div>
    </div>
    <div id="perfDet"></div>`;
}

async function renderPerfilDet(){
  const sel=document.getElementById('perfSel');const eid=parseInt(sel?.value);const det=document.getElementById('perfDet');if(!det)return;
  if(!eid){det.innerHTML='';return;}
  const nom=sel.options[sel.selectedIndex].getAttribute('data-nom');
  const cur=sel.options[sel.selectedIndex].getAttribute('data-cur');
  const faltas=(await api(`/api/faltas?anio=${getAnio()}`)).filter(f=>f.estudiante_id===eid||f.estudiante===nom);
  const ini=nom.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase();
  det.innerHTML=`
    <div class="card">
      <div style="display:flex;align-items:center;gap:12px;padding:14px;border-bottom:1px solid var(--brd)">
        <div style="width:44px;height:44px;border-radius:50%;background:var(--ibg);color:var(--ic);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;flex-shrink:0">${ini}</div>
        <div>
          <div style="font-size:14px;font-weight:600">${nom}</div>
          <div style="font-size:12px;color:var(--mut)">Curso ${cur} · ${faltas.length} faltas en ${getAnio()}</div>
        </div>
        <div style="margin-left:auto;display:flex;gap:5px;flex-wrap:wrap">${['Tipo I','Tipo II','Tipo III'].map(t=>`${bdg(t)} <span style="font-size:12px;font-weight:600;margin-right:4px">${faltas.filter(f=>f.tipo_falta===t).length}</span>`).join('')}</div>
        <button class="btn btn-g btn-xs" onclick="window.location.href='/api/reporte-estudiante?estudiante=${encodeURIComponent(nom)}&anio=todos'">CSV historial</button>
      </div>
      <div style="padding:9px">${fCards(faltas)}</div>
    </div>`;
}

// ── Superadmin colegios ───────────────────────────────────────────────────────
async function renderSACol(tab){
  const cols=await api('/api/colegios');
  const tagR={Coordinador:'t-co',Director:'t-di',Orientador:'t-or',Docente:'t-doc'};
  tab.innerHTML=`<div style="display:flex;justify-content:flex-end;margin-bottom:10px"><button class="btn btn-p" onclick="openNuevoCol()">+ Nueva institución</button></div>`;
  cols.forEach(col=>{
    const d=document.createElement('div');d.className='col-card';
    d.innerHTML=`
      <div class="col-head">
        <div><h3>${col.nombre}</h3><small>NIT: ${col.nit||'—'} · ${col.municipio||'—'} · Rector: ${col.rector||'—'}</small></div>
        <div style="display:flex;gap:6px;align-items:center">
          <span style="color:rgba(255,255,255,.4);font-size:11px">${col.num_estudiantes} est · ${col.num_usuarios} usr</span>
          <button class="btn btn-xs btn-i" onclick="editarCol(${col.id})">Editar</button>
        </div>
      </div>
      <div class="col-body">
        <div class="col-datos">
          <div class="cd"><label>DIRECCIÓN</label><span>${col.direccion||'—'}</span></div>
          <div class="cd"><label>TELÉFONO</label><span>${col.telefono||'—'}</span></div>
          <div class="cd"><label>EMAIL</label><span>${col.email||'—'}</span></div>
        </div>
        <div style="font-size:11px;font-weight:600;color:var(--mut);letter-spacing:.06em;margin-bottom:7px">USUARIOS (${col.num_usuarios})</div>
        <div class="col-users">${(col.usuarios||[]).map(u=>`<div class="cu-chip"><span class="tag ${tagR[u.rol]||'t-doc'}">${u.rol}</span><span>${u.nombre}${u.curso?' ('+u.curso+')':''}</span></div>`).join('')}</div>
      </div>`;
    tab.appendChild(d);
  });
}

// ── Ver falta con timeline ────────────────────────────────────────────────────
async function verFalta(id){
  const prevId=verFId;
  verFId=id;
  const f=await api(`/api/faltas/${id}`);
  window.verFObj=f;
  document.getElementById('verTitle').textContent=`Falta — ${f.estudiante}`;
  document.getElementById('verBdgs').innerHTML=bdg(f.tipo_falta)+((f.tematica||'').trim()?temBdg(f.tematica):'')+estGestionBdg(f)+`<span class="bdg bg">${f.curso}</span><span class="bdg bg">${f.anio}</span>`;
  const vtr=document.getElementById('vTemRow');
  const vtb=document.getElementById('vTemBdg');
  const ttx=(f.tematica||'').trim();
  if(vtr&&vtb){
    if(ttx){vtb.innerHTML=temBdg(ttx);vtr.style.display='block';}
    else{vtb.innerHTML='';vtr.style.display='none';}
  }
  document.getElementById('vFecha').value=f.fecha;document.getElementById('vEst').value=f.estudiante;
  document.getElementById('vCurso').value=f.curso;document.getElementById('vTipo').value=f.tipo_falta;
  document.getElementById('vEsp').value=f.falta_especifica;document.getElementById('vDesc').value=f.descripcion;
  const lro=document.getElementById('vLugarRo');
  const aro=document.getElementById('vAfectRo');
  if(lro)lro.value=(f.lugar||'').trim()||'—';
  if(aro){
    const aj=_parseAfectadosJson(f.afectados_json||'');
    aro.value=aj.length?aj.join(', '):'—';
  }
  const ps=document.getElementById('vProtoSec');
  if(f.protocolo_aplicado||f.sancion_aplicada){
    ps.style.display='block';
    const cls=f.tipo_falta==='Tipo III'?'t3':f.tipo_falta==='Tipo II'?'t2':'t1';
    document.getElementById('vProto').className=`pbox ${cls}`;document.getElementById('vProto').textContent=f.protocolo_aplicado||'—';
    document.getElementById('vSancion').className=`pbox ${cls}`;document.getElementById('vSancion').textContent=f.sancion_aplicada||'—';
  } else ps.style.display='none';
  const as=document.getElementById('vAcuSec');
  if(['Coordinador','Superadmin','Director','Orientador'].includes(CU.rol)&&f.acudiente){
    as.style.display='block';
    document.getElementById('vAcu').value=f.acudiente||'—';document.getElementById('vCed').value=f.cedula_acudiente||'—';document.getElementById('vTel').value=f.tel_acudiente||'—';
  } else as.style.display='none';
  const vc=document.getElementById('vCitaSec');
  const vb=document.getElementById('vCitaBody');
  if(f.cita_acudiente&&vb&&vc){
    vc.style.display='block';
    const c=f.cita_acudiente;
    const fh=(c.fecha_hora||'').replace('T',' ');
    let h='';
    if(c.origen==='escuela'&&c.estado==='pendiente_confirmacion_acudiente'){
      h=`<p>La institución propuso una cita: <strong>${escHtml(fh||'—')}</strong>.</p>`;
    }else if(c.origen==='acudiente'&&c.estado==='pendiente_agenda'){
      h=`<p>Usted solicitó cita con <strong>${escHtml(c.rol_destino)}</strong>. Estado: en espera de que la institución proponga fecha y hora.</p>`;
    }else if(c.estado==='pendiente_confirmacion_acudiente'){
      h=`<p>Fecha propuesta: <strong>${escHtml(fh||'—')}</strong>. Pendiente su confirmación.</p>`;
    }else if(c.estado==='confirmada'){
      h=`<p><strong>Cita confirmada</strong> · ${escHtml(fh||'—')}</p>`;
    }else if(c.estado==='rechazada'||c.estado==='cancelada'){
      h=`<p style="color:var(--mut)">Cita ${c.estado==='rechazada'?'rechazada':'cancelada'}.</p>`;
    }else{
      h=`<p>${escHtml(c.estado||'—')}</p>`;
    }
    if(CU.rol==='Acudiente'&&c.estado==='pendiente_confirmacion_acudiente'){
      h+=`<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap"><button type="button" class="btn btn-g btn-xs" onclick="closeOv('ov-ver');citaConfirmar(${c.id})">Confirmar cita</button><button type="button" class="btn btn-d btn-xs" onclick="closeOv('ov-ver');citaRechazar(${c.id})">Rechazar</button></div>`;
    }
    vb.innerHTML=h;
  }else if(vc)vc.style.display='none';
  const vg=document.getElementById('vGestionSec');
  const vgt=document.getElementById('vGestionTxt');
  const vgb=document.getElementById('vGestionBtn');
  if(vg&&vgt){
    vg.style.display='block';
    const eg=f.estado_gestion||'pendiente';
    const sr=f.siguiente_rol;
    let t=`<strong>${EST_GEST_TXT[eg]||eg}</strong>. `;
    if(eg==='cerrada'){
      t+='El coordinador cerró este expediente.';
    }else if(f.gestion_coordinador==='en_revision'){
      t+='Marcado en seguimiento por coordinación. ';
      if(sr)t+=`Siguiente paso sugerido por el flujo: <strong>${sr}</strong>. `;
    }else if(sr){
      t+=`Siguiente rol en el flujo: <strong>${sr}</strong>. `;
    }else{
      t+='Sin otro paso obligatorio en el flujo automático; coordinación puede dejarlo en revisión o cerrarlo. ';
    }
    vgt.innerHTML=t;
    if(vgb)vgb.style.display=['Coordinador','Superadmin'].includes(CU.rol)?'inline-block':'none';
  }
  const anots=[{rol:'Docente',autor:f.docente,fecha:f.fecha,texto:`Registro inicial: ${f.proceso_inicial}`},...(f.anotaciones||[])];
  document.getElementById('verTL').innerHTML=anots.map(a=>`
    <div class="tl-item">
      <div class="tl-dot ${TLCLS[a.rol]||'tl-doc'}">${TLINI[a.rol]||'D'}</div>
      <div class="tl-body">
        <div class="tl-meta"><strong>${a.autor}</strong><span>${a.fecha}</span><span class="tag ${TGCLS[a.rol]||'t-doc'}">${a.rol}</span></div>
        <div class="tl-txt">${a.texto}</div>
      </div>
    </div>`).join('');
  const puedeAnotar=['Director','Coordinador','Orientador'].includes(CU.rol)||(CU.rol==='Docente'&&f.docente===CU.nombre);
  const as2=document.getElementById('verAnotSec');const sb=document.getElementById('verSaveBtn');
  if(puedeAnotar){as2.style.display='block';sb.style.display='block';document.getElementById('verAnotLbl').textContent=TLBLS[CU.rol]||'Observación';document.getElementById('vAnotTxt').value='';}
  else{as2.style.display='none';sb.style.display='none';}
  syncAdjuntosUI(f);
  openOv('ov-ver');
}

function _parseAfectadosJson(s){
  try{
    const a=JSON.parse(s||'[]');
    return Array.isArray(a)?a:[];
  }catch{ return []; }
}
function _normListaNombre(s){
  return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
}
// ── Lugar y personas afectadas (registro inicial de falta) ────────────────────
function toggleRLugarOtro(){
  const sel=document.getElementById('rLugar');
  const ot=document.getElementById('rLugarOtro');
  if(!sel||!ot)return;
  ot.style.display=sel.value==='Otro'?'block':'none';
}
function _renderRAfect(){
  const wrap=document.getElementById('rAfectChips');
  if(!wrap)return;
  const arr=window._rAfectArr||[];
  wrap.innerHTML=arr.map((n,i)=>`<span class="reit-chip" style="cursor:pointer" title="Quitar" onclick="rmRAfect(${i})">${escHtml(n)} <strong>×</strong></span>`).join('');
}
function addRAfect(){
  const inp=document.getElementById('rAfectInp');
  if(!inp)return;
  const v=(inp.value||'').trim();
  if(!v)return;
  window._rAfectArr=window._rAfectArr||[];
  if(window._rAfectArr.length>=20){toast('Máximo 20 personas afectadas','e');return;}
  if(!window._rAfectArr.some(x=>_normListaNombre(x)===_normListaNombre(v))) window._rAfectArr.push(v);
  inp.value='';
  _renderRAfect();
}
function rmRAfect(i){
  window._rAfectArr=window._rAfectArr||[];
  window._rAfectArr.splice(i,1);
  _renderRAfect();
}
function resetRegFaltaLugar(){
  window._rAfectArr=[];
  const s=document.getElementById('rLugar');
  const o=document.getElementById('rLugarOtro');
  const inp=document.getElementById('rAfectInp');
  if(s)s.value='';
  if(o){o.value='';o.style.display='none';}
  if(inp)inp.value='';
  _renderRAfect();
}

function openOvGestion(){
  const f=window.verFObj;
  if(!f||!verFId){toast('Abra el detalle de la falta','e');return;}
  const gc=f.gestion_coordinador||null;
  document.getElementById('gestDec_auto').checked=!gc;
  document.getElementById('gestDec_cerr').checked=gc==='cerrada';
  document.getElementById('gestDec_rev').checked=gc==='en_revision';
  openOv('ov-gestion');
}

async function guardarGestionOverlay(){
  let decision=null;
  if(document.getElementById('gestDec_cerr')?.checked)decision='cerrada';
  else if(document.getElementById('gestDec_rev')?.checked)decision='en_revision';
  else decision=null;
  const r=await api('/api/faltas/'+verFId+'/gestion',{method:'PATCH',body:JSON.stringify({decision})});
  if(r.ok){
    closeOv('ov-gestion');
    toast('Estado de gestión actualizado');
    renderCurrentTab();
    if(document.getElementById('ov-ver')?.classList.contains('open'))await verFalta(verFId);
  }else toast(r.error||'Error','e');
}

async function guardarAnotacion(){
  const txt=document.getElementById('vAnotTxt').value.trim();
  if(!txt){toast('Escribe una observación','e');return;}
  const r=await api(`/api/faltas/${verFId}/anotaciones`,{method:'POST',body:JSON.stringify({texto:txt})});
  if(r.ok){closeOv('ov-ver');toast('Observación guardada');renderCurrentTab();}else toast(r.error||'Error','e');
}

// ── Registrar falta ───────────────────────────────────────────────────────────
async function loadREstudiantes(){
  const curso=document.getElementById('rCurso').value;const sel=document.getElementById('rEst');
  sel.innerHTML='<option value="">Cargando...</option>';
  if(!curso){
    sel.innerHTML='<option value="">Primero seleccione curso</option>';
    window._rEstById={};
    refreshAcudienteCitaPanel();
    return;
  }
  const r=await api(`/api/estudiantes?curso=${encodeURIComponent(curso)}`);
  const arr=Array.isArray(r)?r:[];
  window._rEstById={};
  arr.forEach(e=>{window._rEstById[e.id]=e;});
  sel.innerHTML='<option value="">Seleccionar</option>'+arr.map(e=>`<option value="${e.id}">${e.nombre}</option>`).join('');
  sel.onchange=()=>refreshAcudienteCitaPanel();
  refreshAcudienteCitaPanel();
}
async function loadRFaltasEsp(){
  const tipo=document.getElementById('rTipo').value;
  document.getElementById('rAlerta').style.display=(tipo==='Tipo II'||tipo==='Tipo III')?'flex':'none';
  const ref=document.getElementById('rCatRef');
  if(ref)ref.style.display='none';
  window._rCatList=[];
  const sel=document.getElementById('rFaltaEsp');
  sel.innerHTML='<option value="">Cargando...</option>';
  if(!tipo){sel.innerHTML='<option value="">Primero seleccione tipo</option>';return;}
  const r=await api(`/api/catalogo?tipo=${encodeURIComponent(tipo)}`);
  window._rCatList=Array.isArray(r)?r:[];
  sel.innerHTML='';
  const o0=document.createElement('option');o0.value='';o0.textContent='Seleccionar';sel.appendChild(o0);
  window._rCatList.forEach(item=>{
    const o=document.createElement('option');
    o.value=item.descripcion;
    o.textContent=item.descripcion;
    sel.appendChild(o);
  });
}

function _findCatItemPorDesc(esp){
  const t=(esp||'').trim();
  return(window._rCatList||[]).find(x=>(x.descripcion||'').trim()===t);
}

function updateRCatSugerencia(){
  const ref=document.getElementById('rCatRef');
  const pEl=document.getElementById('rProtoSug');
  const sEl=document.getElementById('rSancSug');
  const mini=document.getElementById('rCatRefMini');
  const pMini=document.getElementById('rProtoSugMini');
  const sMini=document.getElementById('rSancSugMini');
  const tw=document.getElementById('rTemWrap');
  const ts=document.getElementById('rTemSug');
  const tMini=document.getElementById('rTemSugMini');
  const esp=document.getElementById('rFaltaEsp').value;
  const hide=()=>{
    if(ref)ref.style.display='none';
    if(mini)mini.style.display='none';
    if(tw)tw.style.display='none';
  };
  if(!pEl||!sEl){hide();return;}
  if(!esp){hide();return;}
  const item=_findCatItemPorDesc(esp);
  if(!item){hide();return;}
  const miss='(Sin texto en catálogo — completar en «Protocolos» → Protocolo por falta del catálogo.)';
  const pt=(item.protocolo||'').trim()||miss;
  const st=(item.sancion||'').trim()||miss;
  pEl.textContent=pt;
  sEl.textContent=st;
  const tm=(item.tematica||'').trim();
  if(tm){
    if(ts)ts.innerHTML=temBdg(tm);
    if(tw)tw.style.display='block';
    if(tMini)tMini.innerHTML=temBdg(tm);
  }else{
    if(tw)tw.style.display='none';
    if(tMini)tMini.innerHTML='—';
  }
  if(ref){ref.style.display='block';ref.scrollIntoView({behavior:'smooth',block:'nearest'});}
  if(pMini)pMini.textContent=pt;
  if(sMini)sMini.textContent=st;
  if(mini)mini.style.display='block';
}

function aplicarSugerenciaAProc(){
  const esp=document.getElementById('rFaltaEsp').value;
  const item=_findCatItemPorDesc(esp);
  if(!item){toast('Seleccione primero la falta específica','e');return;}
  const parts=[];
  if((item.protocolo||'').trim())parts.push('Protocolo (referencia catálogo): '+item.protocolo.trim());
  if((item.sancion||'').trim())parts.push('Medida de referencia (catálogo): '+item.sancion.trim());
  if(!parts.length){toast('No hay texto de referencia en el catálogo para esta falta','e');return;}
  const t=document.getElementById('rProc');
  const block=parts.join('\n\n');
  if(t.value.trim())t.value=t.value.trim()+'\n\n'+block;else t.value=block;
  toast('Referencia copiada al paso 4; ajústela a lo que hizo en aula.');
}

function descargarActaFalta(){
  if(!verFId)return;
  window.open(`/api/pdf/acta/${verFId}`,'_blank');
}

function toggleAdjuntosPanel(){
  // Compat: el panel ya no es desplegable en el detalle, pero mantenemos la función
  // para no romper llamados antiguos.
  const p=document.getElementById('vAdjPanel');
  if(!p)return;
  p.scrollIntoView({block:'nearest',behavior:'smooth'});
}

function catAdjLbl(c){
  if(c==='descargos_inicial')return'Acta de descargos (inicial)';
  if(c==='sesion_instancias')return'Acta de sesión';
  return c;
}
function puedeSubirAdjDesc(f){
  return CU.rol==='Docente'&&f.docente===CU.nombre;
}
function puedeSubirAdjSes(f){
  if(['Coordinador','Superadmin'].includes(CU.rol))return true;
  if(CU.rol==='Director'&&(f.curso===CU.curso||f.docente===CU.nombre))return true;
  return false;
}
function puedeBorrarAdj(a){
  if(['Coordinador','Superadmin'].includes(CU.rol))return true;
  if(CU.id!=null&&a.subido_por_id!=null&&Number(a.subido_por_id)===Number(CU.id))return true;
  return false;
}

function _syncAdjUploader(f){
  const wrap=document.getElementById('vAdjUp');
  const sel=document.getElementById('vAdjCat');
  const canDesc=puedeSubirAdjDesc(f);
  const canSes=puedeSubirAdjSes(f);
  const canAny=canDesc||canSes;
  if(!wrap||!sel)return;
  wrap.style.display=canAny?'block':'none';
  if(!canAny)return;
  const prev=sel.value||'';
  sel.innerHTML='';
  if(canDesc){const o=document.createElement('option');o.value='descargos_inicial';o.textContent='Acta de descargos';sel.appendChild(o);}
  if(canSes){const o=document.createElement('option');o.value='sesion_instancias';o.textContent='Acta de sesión';sel.appendChild(o);}
  // mantener selección si sigue disponible
  if(prev && Array.from(sel.options).some(o=>o.value===prev)) sel.value=prev;
}

function syncAdjuntosUI(f){
  _syncAdjUploader(f);
  const chip=document.getElementById('vAdjChip');
  const n=(f.adjuntos||[]).length;
  if(chip){
    if(n){chip.style.display='inline';chip.textContent=n+(n===1?' archivo':' archivos');}
    else{chip.style.display='none';chip.textContent='';}
  }
  const box=document.getElementById('vAdjBody');
  if(!box)return;
  const adj=f.adjuntos||[];
  if(!adj.length){
    box.innerHTML='<div class="empty" style="font-size:12px;padding:6px 0">Sin archivos.</div>';
    return;
  }
  box.innerHTML=adj.map(a=>`<div class="adj-row" style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--brd)">
    <div><span class="bdg bg">${escHtml(catAdjLbl(a.categoria))}</span> <strong>${escHtml(a.nombre_original||'archivo')}</strong>
    <div style="font-size:10px;color:var(--mut);margin-top:3px">${escHtml(a.subido_por_nombre||'')} · ${escHtml(a.creado_en||'')}</div></div>
    <div style="display:flex;gap:4px;flex-shrink:0;flex-wrap:wrap">
      <a class="btn btn-xs btn-g" href="/api/faltas/${f.id}/adjuntos/${a.id}" target="_blank" rel="noopener">Descargar</a>
      ${puedeBorrarAdj(a)?`<button type="button" class="btn btn-xs btn-d" onclick="borrarAdjunto(${f.id},${a.id})">Eliminar</button>`:''}
    </div></div>`).join('');
}
async function uploadFaltaAdjunto(fid,categoria,fileInput){
  if(!fileInput||!fileInput.files||!fileInput.files[0]){toast('Seleccione un archivo','e');return null;}
  const fd=new FormData();
  fd.append('categoria',categoria);
  fd.append('archivo',fileInput.files[0]);
  const r=await fetch(`/api/faltas/${fid}/adjuntos`,{method:'POST',body:fd,credentials:'same-origin'});
  return parseFetchBodyAsJson(r);
}
async function subirAdjuntoFalta(){
  if(!verFId)return;
  const sel=document.getElementById('vAdjCat');
  const inp=document.getElementById('vAdjFile');
  const cat=(sel&&sel.value)||'';
  if(!cat){toast('Seleccione el tipo de documento','e');return;}
  const j=await uploadFaltaAdjunto(verFId,cat,inp);
  if(j&&j.ok){
    if(inp)inp.value='';
    toast('Archivo adjuntado');
    await verFalta(verFId);
  }
  else toast((j&&j.error)||'Error','e');
}
async function borrarAdjunto(fid,aid){
  if(!confirm('¿Eliminar este adjunto del expediente?'))return;
  const r=await fetch(`/api/faltas/${fid}/adjuntos/${aid}`,{method:'DELETE',credentials:'same-origin',headers:{'Content-Type':'application/json'}});
  const j=await parseFetchBodyAsJson(r);
  if(j&&j.ok){toast('Adjunto eliminado');await verFalta(fid);}
  else toast((j&&j.error)||'Error','e');
}

async function guardarFalta(){
  const curso=document.getElementById('rCurso').value;
  const sel=document.getElementById('rEst');
  const eid=sel.value;
  const est=sel.options[sel.selectedIndex]?.text?.trim()||'';
  const tipo=document.getElementById('rTipo').value,esp=document.getElementById('rFaltaEsp').value,
    desc=document.getElementById('rDesc').value.trim(),proc=document.getElementById('rProc').value.trim();
  if(!curso||!eid||!tipo||!esp||!desc||!proc){toast('Completa todos los campos','e');return;}
  const citar=document.getElementById('rCitarAcu')?.checked;
  const citaDt=(document.getElementById('rCitaDt')?.value||'').trim();
  if(citar&&!citaDt){toast('Indique fecha y hora de la cita o desactive «Citar a acudiente»','e');return;}
  const rLug=document.getElementById('rLugar');
  const rLot=document.getElementById('rLugarOtro');
  let lugar=(rLug&&rLug.value)||'';
  if(lugar==='Otro')lugar=(rLot&&rLot.value||'').trim();
  const afectados=(window._rAfectArr||[]).slice(0,20);
  const body={anio:getAnio(),curso,estudiante_id:Number(eid),estudiante:est,tipo_falta:tipo,falta_especifica:esp,descripcion:desc,proceso_inicial:proc,lugar,afectados};
  if(citar&&citaDt)body.cita_acudiente={activar:true,fecha_hora:citaDt};
  const r=await api('/api/faltas',{method:'POST',body:JSON.stringify(body)});
  if(r.ok){
    const fid=r.id;
    const rCat=document.getElementById('rAdjCat');
    const rFile=document.getElementById('rAdjFile');
    const cat=(rCat&&rCat.value)||'';
    if(fid&&rFile&&rFile.files&&rFile.files[0]&&cat){
      const up=await uploadFaltaAdjunto(fid,cat,rFile);
      if(!up||!up.ok)toast(up.error||'Falta guardada; no se pudo adjuntar el acta','e');
    }
    closeOv('ov-falta');
    toast(citar?'Falta registrada con citación al acudiente':'Falta registrada');
    resetRegFaltaLugar();
    ['rCurso','rEst','rTipo','rFaltaEsp','rDesc','rProc'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
    const rFile2=document.getElementById('rAdjFile');if(rFile2)rFile2.value='';
    const rCat2=document.getElementById('rAdjCat');if(rCat2)rCat2.value='descargos_inicial';
    const rc=document.getElementById('rCitarAcu');if(rc){rc.checked=false;toggleRCita();}const rd=document.getElementById('rCitaDt');if(rd)rd.value='';document.getElementById('rAlerta').style.display='none';const cr=document.getElementById('rCatRef');if(cr)cr.style.display='none';const cm=document.getElementById('rCatRefMini');if(cm)cm.style.display='none';const rtw=document.getElementById('rTemWrap');if(rtw)rtw.style.display='none';window._rCatList=[];await refreshCitasPendientes();renderCurrentTab();
  }
  else toast(r.error||'Error','e');
}

// ── Estudiantes CRUD ──────────────────────────────────────────────────────────
const _IDS_EST=['eTipoDocEst','eDocId','eAp1Est','eAp2Est','eNom1Est','eNom2Est','eBarreras','eTipoDocAcu','eAp1Acu','eAp2Acu','eNom1Acu','eNom2Acu','eParentescoAcu','eCed','eTel','eDir'];
function openNuevoEst(){
  editEstId=null;document.getElementById('estTit').textContent='Nuevo estudiante';
  _IDS_EST.forEach(id=>{const el=document.getElementById(id);if(el){el.value='';el.classList.remove('ok','err-inp');}});
  document.getElementById('eCurso').value='';
  document.getElementById('eErr').textContent='';
  const rb=document.getElementById('eResetClaveBtn');if(rb)rb.style.display='none';
  ['eCedErr','eTelErr'].forEach(id=>{const el=document.getElementById(id);if(el)el.textContent='';});
  openOv('ov-est');
}

function editarEst(id){
  const e=(window._ec||[]).find(x=>x.id===id);if(!e)return;
  editEstId=id;document.getElementById('estTit').textContent='Editar estudiante';
  document.getElementById('eCurso').value=e.curso;
  document.getElementById('eTipoDocEst').value=e.tipo_doc_est||'';
  document.getElementById('eDocId').value=e.documento_identidad||'';
  document.getElementById('eAp1Est').value=e.apellido1_est||'';
  document.getElementById('eAp2Est').value=e.apellido2_est||'';
  document.getElementById('eNom1Est').value=e.nombre1_est||(e.nombre||'').split(' ').pop()||'';
  document.getElementById('eNom2Est').value=e.nombre2_est||'';
  if(!e.apellido1_est&&e.nombre){const p=e.nombre.split(/\s+/);if(p.length>=2){document.getElementById('eAp1Est').value=p[0]||'';document.getElementById('eNom1Est').value=p.slice(1).join(' ')||'';}}
  document.getElementById('eBarreras').value=e.barreras||e.discapacidad||'Ninguna identificada';
  document.getElementById('eTipoDocAcu').value=e.tipo_doc_acu||'';
  document.getElementById('eAp1Acu').value=e.apellido1_acu||'';
  document.getElementById('eAp2Acu').value=e.apellido2_acu||'';
  document.getElementById('eNom1Acu').value=e.nombre1_acu||'';
  document.getElementById('eNom2Acu').value=e.nombre2_acu||'';
  if(!e.apellido1_acu&&e.acudiente){const p=(e.acudiente||'').split(/\s+/);if(p.length)document.getElementById('eNom1Acu').value=e.acudiente;}
  document.getElementById('eParentescoAcu').value=e.parentesco_acu||'';
  document.getElementById('eCed').value=e.cedula_acudiente||'';
  document.getElementById('eTel').value=e.telefono||'';
  document.getElementById('eDir').value=e.direccion||'';
  const rb=document.getElementById('eResetClaveBtn');
  if(rb)rb.style.display=(CU.rol==='Coordinador'||CU.rol==='Superadmin'||CU.rol==='Director')?'inline-block':'none';
  openOv('ov-est');
}

async function resetClavePortalEstudiante(){
  if(!editEstId)return;
  if(!confirm('¿Restablecer la contraseña del estudiante a los 4 últimos dígitos de su documento?'))return;
  const r=await api(`/api/estudiantes/${editEstId}/reset-clave-portal`,{method:'POST',body:'{}'});
  if(r.ok)toast('Contraseña restablecida');
  else toast(r.error||'Error','e');
}

async function guardarEstudiante(){
  const curso=document.getElementById('eCurso').value;
  const ap1=document.getElementById('eAp1Est').value.trim();
  const n1=document.getElementById('eNom1Est').value.trim();
  const cedula=document.getElementById('eCed').value.trim();
  const tel=document.getElementById('eTel').value.trim();
  const docId=document.getElementById('eDocId')?.value.trim()||'';
  const err=document.getElementById('eErr');
  err.textContent='';
  if(!ap1||!n1||!curso){err.textContent='Apellido 1 y nombre 1 del estudiante, y curso, son obligatorios';return;}
  if(!document.getElementById('eNom1Acu').value.trim()||!document.getElementById('eAp1Acu').value.trim()){err.textContent='Complete nombres del acudiente (apellido 1 y nombre 1)';return;}
  if(!document.getElementById('eParentescoAcu').value.trim()){err.textContent='Indique parentesco';return;}
  if(!cedula||cedula.length<5){document.getElementById('eCedErr').textContent='Documento del acudiente inválido';return;}
  if(!tel||tel.length<7){document.getElementById('eTelErr').textContent='Teléfono inválido';return;}
  const body={
    curso,
    tipo_doc_est:document.getElementById('eTipoDocEst').value,
    documento_identidad:docId,
    apellido1_est:ap1,apellido2_est:document.getElementById('eAp2Est').value.trim(),
    nombre1_est:n1,nombre2_est:document.getElementById('eNom2Est').value.trim(),
    barreras:document.getElementById('eBarreras').value,
    tipo_doc_acu:document.getElementById('eTipoDocAcu').value,
    apellido1_acu:document.getElementById('eAp1Acu').value.trim(),
    apellido2_acu:document.getElementById('eAp2Acu').value.trim(),
    nombre1_acu:document.getElementById('eNom1Acu').value.trim(),
    nombre2_acu:document.getElementById('eNom2Acu').value.trim(),
    parentesco_acu:document.getElementById('eParentescoAcu').value.trim(),
    cedula_acudiente:cedula,telefono:tel,direccion:document.getElementById('eDir').value.trim(),
  };
  const url=editEstId?`/api/estudiantes/${editEstId}`:'/api/estudiantes';
  const r=await api(url,{method:editEstId?'PATCH':'POST',body:JSON.stringify(body)});
  if(r.ok){closeOv('ov-est');toast(editEstId?'Estudiante actualizado':'Estudiante agregado. Usuario acudiente creado.');editEstId=null;renderCurrentTab();}
  else{err.textContent=r.error||'Error';toast(r.error||'Error','e');}
}

async function borrarEst(id){if(!confirm('¿Eliminar este estudiante?'))return;const r=await api(`/api/estudiantes/${id}`,{method:'DELETE'});if(r.ok){toast('Eliminado');renderCurrentTab();}else toast(r.error,'e');}

// ── Usuarios CRUD ─────────────────────────────────────────────────────────────
const _IDS_USR=['uTipoDoc','uDocPer','uAp1','uAp2','uNom1','uNom2','uUsr','uPas','uAsig','uTel'];
async function openNuevoUsr(){
  editUsrId=null;document.getElementById('usrTit').textContent='Nuevo usuario';
  _IDS_USR.forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  document.getElementById('uRol').value='';document.getElementById('uCurso').value='';
  document.getElementById('uCursoRow').style.display='none';document.getElementById('uAsigRow').style.display='none';
  const colRow=document.getElementById('uColegioRow');
  const colSel=document.getElementById('uColegioId');
  colRow.style.display='none';
  colSel.innerHTML='<option value="">Seleccionar institución</option>';
  if(CU&&CU.rol==='Superadmin'){
    const cols=await api('/api/colegios');
    if(Array.isArray(cols)){
      cols.forEach(c=>{const o=document.createElement('option');o.value=String(c.id);o.textContent=c.nombre||('Institución '+c.id);colSel.appendChild(o);});
      const needPick=cols.length>1||!CU.colegio_id;
      colRow.style.display=needPick?'block':'none';
      if(CU.colegio_id)colSel.value=String(CU.colegio_id);
    }
  }
  document.getElementById('uErr').textContent='';openOv('ov-usr');toggleUsrF();
}
async function editarUsr(id){
  const r=await api('/api/usuarios');const u=r.find(x=>x.id===id);if(!u)return;
  editUsrId=id;document.getElementById('usrTit').textContent='Editar usuario';
  document.getElementById('uTipoDoc').value=u.tipo_doc||'';
  document.getElementById('uDocPer').value=u.documento_personal||'';
  document.getElementById('uAp1').value=u.apellido1||'';
  document.getElementById('uAp2').value=u.apellido2||'';
  document.getElementById('uNom1').value=u.nombre1||'';
  document.getElementById('uNom2').value=u.nombre2||'';
  if(!u.apellido1&&u.nombre){const p=u.nombre.split(/\s+/);document.getElementById('uAp1').value=p[0]||'';document.getElementById('uNom1').value=p.slice(1).join(' ')||u.nombre;}
  document.getElementById('uUsr').value=u.usuario;document.getElementById('uPas').value='';
  document.getElementById('uRol').value=u.rol;document.getElementById('uCurso').value=u.curso||'';
  document.getElementById('uAsig').value=u.asignatura||'';
  document.getElementById('uTel').value=u.telefono||'';
  document.getElementById('uColegioRow').style.display='none';
  document.getElementById('uCursoRow').style.display=u.rol==='Director'?'block':'none';
  document.getElementById('uAsigRow').style.display=_usrMuestraAsignatura(u.rol)?'block':'none';
  document.getElementById('uErr').textContent='';openOv('ov-usr');
}
function toggleUsrF(){
  const r=document.getElementById('uRol').value;
  document.getElementById('uCursoRow').style.display=r==='Director'?'block':'none';
  document.getElementById('uAsigRow').style.display=_usrMuestraAsignatura(r)?'block':'none';
}
async function guardarUsuario(){
  const usr=document.getElementById('uUsr').value.trim(),
    pas=document.getElementById('uPas').value,rol=document.getElementById('uRol').value,cur=document.getElementById('uCurso').value;
  const asig=(document.getElementById('uAsig')?.value||'').trim();
  const err=document.getElementById('uErr');
  const ap1=document.getElementById('uAp1').value.trim();
  const n1=document.getElementById('uNom1').value.trim();
  if(!ap1||!n1||!usr||!rol){err.textContent='Apellido 1, nombre 1, usuario y rol son obligatorios';return;}
  if(!editUsrId&&!pas){err.textContent='La contraseña es obligatoria';return;}
  if(pas&&pas.length<6){err.textContent='La contraseña debe tener mínimo 6 caracteres';return;}
  const url=editUsrId?`/api/usuarios/${editUsrId}`:'/api/usuarios';
  const body={
    usuario:usr,contrasena:pas,rol,curso:cur,asignatura:asig,
    tipo_doc:document.getElementById('uTipoDoc').value,
    documento_personal:document.getElementById('uDocPer').value.trim(),
    apellido1:ap1,apellido2:document.getElementById('uAp2').value.trim(),
    nombre1:n1,nombre2:document.getElementById('uNom2').value.trim(),
    telefono:document.getElementById('uTel').value.trim(),
  };
  if(!editUsrId&&CU&&CU.rol==='Superadmin'){
    const colRow=document.getElementById('uColegioRow');
    const colSel=document.getElementById('uColegioId');
    let colId=CU.colegio_id;
    if(colRow.style.display!=='none'){
      const v=parseInt(colSel.value,10);
      if(!v){err.textContent='Seleccione la institución.';return;}
      colId=v;
    }else if(!colId){
      const cols=await api('/api/colegios');
      if(Array.isArray(cols)&&cols.length===1)colId=cols[0].id;
    }
    if(!colId){err.textContent='No se pudo determinar la institución del usuario.';return;}
    body.colegio_id=colId;
  }
  const r=await api(url,{method:editUsrId?'PATCH':'POST',body:JSON.stringify(body)});
  if(r.ok){closeOv('ov-usr');toast('Usuario guardado');editUsrId=null;renderCurrentTab();}else err.textContent=r.error||'Error al guardar';
}
async function borrarUsr(id){if(!confirm('¿Eliminar este usuario?'))return;const r=await api(`/api/usuarios/${id}`,{method:'DELETE'});if(r.ok){toast('Eliminado');renderCurrentTab();}else toast(r.error,'e');}

// ── Colegios (Superadmin) ─────────────────────────────────────────────────────
function openNuevoCol(){editColId=null;document.getElementById('colTit').textContent='Nueva institución';['colNom','colNit','colMun','colRec','colTel','colDir','colEmail'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});openOv('ov-col');}
async function editarCol(id){const cols=await api('/api/colegios');const c=cols.find(x=>x.id===id);if(!c)return;editColId=id;document.getElementById('colTit').textContent='Editar institución';document.getElementById('colNom').value=c.nombre;document.getElementById('colNit').value=c.nit||'';document.getElementById('colMun').value=c.municipio||'';document.getElementById('colRec').value=c.rector||'';document.getElementById('colTel').value=c.telefono||'';document.getElementById('colDir').value=c.direccion||'';document.getElementById('colEmail').value=c.email||'';openOv('ov-col');}
async function guardarColegio(){
  const nom=document.getElementById('colNom').value.trim();if(!nom){toast('El nombre es obligatorio','e');return;}
  const body={nombre:nom,nit:document.getElementById('colNit').value,municipio:document.getElementById('colMun').value,rector:document.getElementById('colRec').value,telefono:document.getElementById('colTel').value,direccion:document.getElementById('colDir').value,email:document.getElementById('colEmail').value};
  const r=await api(editColId?`/api/colegios/${editColId}`:'/api/colegios',{method:editColId?'PATCH':'POST',body:JSON.stringify(body)});
  if(r.ok){closeOv('ov-col');toast('Institución guardada');editColId=null;renderCurrentTab();}else toast(r.error||'Error','e');
}

// ── Catálogo CRUD ─────────────────────────────────────────────────────────────
async function guardarNuevaCat(){
  const tipo=document.getElementById('ctTipo')?.value,desc=document.getElementById('ctDesc')?.value.trim();
  if(!desc){toast('Escribe la descripción','e');return;}
  const r=await api('/api/catalogo',{method:'POST',body:JSON.stringify({tipo,descripcion:desc,protocolo:'',sancion:''})});
  if(r.ok){closeOv('ov-cat-new');toast('Falta agregada. Complete protocolo y sanción en «Protocolos» → Protocolo por falta del catálogo.');const cat=await api('/api/catalogo');catCache=cat;const tb=document.getElementById('tCat');if(tb)tb.innerHTML=filasCat(cat,catFil);const tp=document.getElementById('tProtoCat');if(tp)tp.innerHTML=htmlFilasProtoCat(cat);}else toast(r.error||'Error','e');
}
async function guardarCatBulk(){
  const txt=document.getElementById('catBulkTxt')?.value||'';
  const err=document.getElementById('catBulkErr');
  if(err)err.textContent='';
  if(!txt.trim()){if(err)err.textContent='Pegue al menos una línea';return;}
  const r=await api('/api/catalogo/importar',{method:'POST',body:JSON.stringify({texto:txt})});
  if(r.ok){closeOv('ov-cat-bulk');toast(`${r.insertados||0} ítems importados al catálogo`);const cat=await api('/api/catalogo');catCache=cat;const tb=document.getElementById('tCat');if(tb)tb.innerHTML=filasCat(cat,catFil);const tp=document.getElementById('tProtoCat');if(tp)tp.innerHTML=htmlFilasProtoCat(cat);}
  else{if(err)err.textContent=r.error||'Error';else toast(r.error||'Error','e');}
}
let editProtoCatId=null;
function fillPeTemSelect(val){
  const sel=document.getElementById('peTematica');
  if(!sel)return;
  const list=_TEMATICAS.length?_TEMATICAS:['Relaciones Respetuosas','Normas de convivencia','Gestión Emocional','Ambiente Físico y seguro','Participación activa','Prevención de conflictos'];
  sel.innerHTML=list.map(t=>`<option value="${escHtml(t)}">${escHtml(t)}</option>`).join('');
  const v=(val||'').trim();
  if(v&&list.includes(v))sel.value=v;
  else sel.selectedIndex=0;
}
function editarProtoPorId(id){
  const f=(catCache||[]).find(x=>x.id===id);
  if(!f){toast('Actualice la pestaña Protocolos (vuelva a entrar)','e');return;}
  editarProtoSancion(f.id,f.descripcion,f.protocolo||'',f.sancion||'',f.tematica||'');
}
function editarProtoSancion(id,desc,proto,sancion,tematica){
  editProtoCatId=id;
  document.getElementById('peDesc').textContent=desc;
  fillPeTemSelect(tematica);
  document.getElementById('peProto').value=proto||'';
  document.getElementById('peSancion').value=sancion||'';
  openOv('ov-proto-edit');
}
async function guardarProtoSancion(){
  const proto=document.getElementById('peProto').value.trim();
  const sancion=document.getElementById('peSancion').value.trim();
  const tematica=(document.getElementById('peTematica')?.value||'').trim();
  const r=await api(`/api/catalogo/${editProtoCatId}`,{method:'PATCH',body:JSON.stringify({protocolo:proto,sancion,tematica})});
  if(r.ok){closeOv('ov-proto-edit');toast('Catálogo actualizado');const cat=await api('/api/catalogo');catCache=cat;const tb=document.getElementById('tCat');if(tb)tb.innerHTML=filasCat(cat,catFil);const tp=document.getElementById('tProtoCat');if(tp)tp.innerHTML=htmlFilasProtoCat(cat);}
  else toast(r.error||'Error','e');
}
async function borrarCat(id){if(!confirm('¿Eliminar esta falta del catálogo?'))return;const r=await api(`/api/catalogo/${id}`,{method:'DELETE'});if(r.ok){toast('Falta eliminada');const cat=await api('/api/catalogo');catCache=cat;const tb=document.getElementById('tCat');if(tb)tb.innerHTML=filasCat(cat,catFil);const tp=document.getElementById('tProtoCat');if(tp)tp.innerHTML=htmlFilasProtoCat(cat);}else toast(r.error||'Error','e');}

// ── Importar estudiantes ──────────────────────────────────────────────────────
function splitCsvLine(line){
  const r=[];let c='';let q=0;
  for(let i=0;i<line.length;i++){
    const ch=line[i];
    if(ch==='"'){q^=1;continue;}
    if(!q&&ch===','){r.push(c.trim());c='';continue;}
    c+=ch;
  }
  r.push(c.trim());
  return r;
}
function previewImport(){
  const raw=document.getElementById('impData').value;
  const cd=document.getElementById('impCurso').value;
  const lineas=raw.split('\n').map(l=>l.trim()).filter(l=>l&&!l.startsWith('#'));
  let ext=0,leg=0;const muestra=[];
  lineas.forEach(l=>{
    const pts=l.includes('"')?splitCsvLine(l):l.split(',').map(x=>x.trim());
    const h=(pts[0]||'').toLowerCase().replace(/_/g,' ');
    if(h==='tipo doc est')return;
    if(pts.length>=15){
      ext++;
      const nom=[pts[2],pts[3],pts[4],pts[5]].filter(Boolean).join(' ').trim();
      const cur=(pts[6]||'').trim()||cd;
      if(muestra.length<3)muestra.push((nom||'(sin nombre)')+' · '+cur+' [extendido]');
    }else{
      leg++;
      const nom=(pts[0]||'').trim();const cur=(pts[1]||'').trim()||cd;
      if(nom&&muestra.length<3)muestra.push(nom+' · '+cur+' [legado]');
    }
  });
  const tot=ext+leg;
  const prev=document.getElementById('impPreview');
  if(prev)prev.innerHTML=`<div class="abanner ab-i" style="margin-top:6px">Se importarán <strong>${tot}</strong> fila(s) (${ext} extendido, ${leg} legado). Ejemplos: ${muestra.join(' · ')||'—'}</div>`;
}
function onImpFileChange(ev){
  const f=ev.target?.files?.[0];
  if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{
    const t=(typeof rd.result==='string'?rd.result:'');
    const ta=document.getElementById('impData');
    if(ta)ta.value=t;
    previewImport();
  };
  rd.onerror=()=>toast('No se pudo leer el archivo','e');
  rd.readAsText(f,'UTF-8');
}
async function ejecutarImport(){
  const texto=document.getElementById('impData').value;const curso_default=document.getElementById('impCurso').value;
  const r=await api('/api/estudiantes/importar',{method:'POST',body:JSON.stringify({texto,curso_default})});
  if(r.ok){
    const ne=(r.errores&&r.errores.length)||0;
    let msg=`${r.insertados||0} estudiantes importados`;
    if(ne)msg+=` — ${ne} fila(s) con aviso o error`;
    toast(msg,ne&&!r.insertados?'e':undefined);
    if(ne){
      const prev=document.getElementById('impPreview');
      if(prev)prev.innerHTML=`<div class="abanner" style="margin-top:8px;font-size:12px;max-height:220px;overflow:auto;border-left:3px solid #e74c3c;padding-left:8px">`+
        (r.errores||[]).slice(0,40).map(e=>`<div>${escHtml(String(e))}</div>`).join('')+
        (ne>40?`<div class="mut" style="margin-top:6px">… y ${ne-40} más</div>`:'')+`</div>`;
    }
    if(!ne)closeOv('ov-import');
    if(r.insertados)renderCurrentTab();
  }else toast(r.error||'Error','e');
}

// ── Overlays & Toast ──────────────────────────────────────────────────────────
function openOv(id){
  document.getElementById(id)?.classList.add('open');
  if(id==='ov-falta')resetRegFaltaLugar();
  if(id==='ov-import'){
    const f=document.getElementById('impFile');
    if(f)f.value='';
    const pv=document.getElementById('impPreview');
    if(pv)pv.innerHTML='';
  }
}
function closeOv(id){document.getElementById(id)?.classList.remove('open');}
document.querySelectorAll('.ov').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)o.classList.remove('open');}));

let toastT;
function toast(msg,type){
  const t=document.getElementById('toast');
  t.textContent=msg;
  const r=getComputedStyle(document.documentElement);
  t.style.borderLeftColor=type==='e'?'#e74c3c':(r.getPropertyValue('--emerald').trim()||'#009368');
  t.classList.add('show');
  clearTimeout(toastT);
  toastT=setTimeout(()=>t.classList.remove('show'),3500);
}

async function doLogout(){await api('/api/logout',{method:'POST'});window.location.href='/login';}

init();
