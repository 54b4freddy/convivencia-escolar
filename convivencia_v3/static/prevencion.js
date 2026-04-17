// Tras app.js (globales): api, CU, CURSOS, CR_*, SEN_CAT_LBL, REP_CAT_LBL, REP_LUG_LBL, escHtml, getAnio, toast, openOv, closeOv, renderCurrentTab, patchRepEst, openRepBitacora, verFalta, _parseAfectadosJson

// ── Conductas de riesgo ───────────────────────────────────────────────────────
function refreshCrSubOpciones(){
  const t=document.getElementById('crTipo')?.value;
  const sub=document.getElementById('crSub');
  if(!sub)return;
  sub.innerHTML='<option value="">Seleccionar</option>';
  (CR_SUBS[t]||[]).forEach(x=>{const o=document.createElement('option');o.value=x.v;o.textContent=x.l;sub.appendChild(o);});
  refreshCrAccion();
}
function refreshCrAccion(){
  const t=document.getElementById('crTipo')?.value;
  const el=document.getElementById('crAccionText');
  if(el)el.textContent=t?CR_ACCION_TXT[t]||'—':'—';
}

// ── Tarjeta alerta reiteración (Conductas de riesgo) ───────────────────────────
const REIT_AUS_UMBRAL = 3; // umbral configurable (ej. 3 inasistencias recientes)
const REIT_FT1_UMBRAL = 3; // regla de 3 para Tipo I → escalar
function _isoDateNDaysAgo(n){
  const d=new Date();d.setDate(d.getDate()-n);
  return d.toISOString().slice(0,10);
}
function _normTxt(s){
  return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
}
function extractPlacesFromText(text){
  const t=_normTxt(text);
  const out=new Map(); // place -> count
  const bump=p=>out.set(p,(out.get(p)||0)+1);
  if(!t)return out;
  // mapeo simple de lugares comunes
  const pats=[
    {k:'baños',re:/\bban(?:o|os|os?)\b|\bbañ(?:o|os|os?)\b/},
    {k:'patio',re:/\bpatio\b/},
    {k:'cancha',re:/\bcancha\b/},
    {k:'cafetería',re:/\bcafeteria\b|\btienda\b/},
    {k:'pasillo',re:/\bpasillo\b/},
    {k:'entrada/salida',re:/\bentrada\b|\bsalida\b|\bporter(?:ia|ia)\b/},
    {k:'transporte',re:/\bruta\b|\bbus\b|\btransporte\b/},
    {k:'aula',re:/\baula\b/},
  ];
  pats.forEach(p=>{if(p.re.test(t))bump(p.k);});
  // aulas específicas: "aula 201", "salón 7", "salon 7", "201"
  const m1=t.match(/\b(aula|salon|sal[oó]n)\s*(\d{1,4}[a-z]?)\b/g);
  if(m1){m1.forEach(x=>{const m=x.match(/(\d{1,4}[a-z]?)/);if(m)bump(`${x.includes('aula')?'aula':'salón'} ${m[1]}`);});}
  return out;
}
function extractPeopleAffected(text){
  const s=String(text||'');
  const out=new Map(); // name -> count
  const bump=n=>out.set(n,(out.get(n)||0)+1);
  // heurística: nombres tras "a", "contra", "víctima:"
  const re=/(?:\bcontra\b|\ba\b|\bvictima\b|\bvíctima\b)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})/g;
  let m;
  while((m=re.exec(s))!==null){
    const name=(m[1]||'').trim();
    if(name && name.length>=3) bump(name);
  }
  return out;
}
async function _fetchFaltasAnioCached(){
  const y=getAnio();
  window._reitFaltasCache=window._reitFaltasCache||{};
  if(window._reitFaltasCache[y]) return window._reitFaltasCache[y];
  const raw=await api(`/api/faltas?anio=${encodeURIComponent(y)}`);
  const list=Array.isArray(raw)?raw:[];
  window._reitFaltasCache[y]=list;
  return list;
}
async function _fetchAsistenciaTomasCurso(curso){
  if(!curso) return [];
  // 60 días por defecto para rendimiento; ajustar si se requiere más histórico.
  const desde=_isoDateNDaysAgo(60);
  const raw=await api(`/api/asistencia/tomas?curso=${encodeURIComponent(curso)}&desde=${encodeURIComponent(desde)}`);
  return Array.isArray(raw)?raw:[];
}
function _kpiBadge(val,umbral){
  if(val>=umbral) return 'crit';
  if(val>=Math.max(1,Math.ceil(umbral*0.67))) return 'warn';
  return 'ok';
}
function _topMap(mapObj,limit=6){
  return Array.from(mapObj.entries()).sort((a,b)=>b[1]-a[1]).slice(0,limit);
}
function renderTarjetaReiteracion({faltas,asistencias,estudianteNombre,curso}){
  const fs=Array.isArray(faltas)?faltas:[];
  const tomas=Array.isArray(asistencias)?asistencias:[];
  const aus=(()=>{ // ausencias totales en el rango (tomas con detalle)
    let n=0;
    tomas.forEach(t=>{
      (t.detalles||[]).forEach(d=>{if(d && d.ausente) n++;});
    });
    return n;
  })();
  const ft1=fs.filter(f=>String(f.tipo_falta||'')==='Tipo I').length;
  const ft1Cls=_kpiBadge(ft1,REIT_FT1_UMBRAL);
  const ft1Msg=ft1>=REIT_FT1_UMBRAL
    ?'Escalamiento a Tipo II: reiteración (regla de 3) — revisar ruta de atención y medidas pedagógicas.'
    :'Seguimiento: aún no cumple la regla de 3 para escalamiento.';

  const placesAgg=new Map();
  const victimsAgg=new Map();
  fs.forEach(f=>{
    const lug=(f.lugar||'').trim();
    if(lug) placesAgg.set(lug,(placesAgg.get(lug)||0)+1);
    else{
      const d=f.descripcion||'';
      const pm=extractPlacesFromText(d);
      pm.forEach((c,k)=>placesAgg.set(k,(placesAgg.get(k)||0)+c));
    }
    const aj=_parseAfectadosJson(f.afectados_json||'');
    if(aj.length) aj.forEach(n=>victimsAgg.set(n,(victimsAgg.get(n)||0)+1));
    else{
      const d=f.descripcion||'';
      const vm=extractPeopleAffected(d);
      vm.forEach((c,k)=>victimsAgg.set(k,(victimsAgg.get(k)||0)+c));
    }
  });
  const topPlaces=_topMap(placesAgg,6);
  const topVictims=_topMap(victimsAgg,6);
  const ausCls=_kpiBadge(aus,REIT_AUS_UMBRAL);

  return `
  <div class="reit-card">
    <div class="reit-head">
      <div>
        <h4>Alerta de reiteración (ruta de atención)</h4>
        <div class="reit-sub">${escHtml(estudianteNombre||'Estudiante')} · ${escHtml(curso||'')}</div>
      </div>
      <div class="reit-kpi">
        <span class="reit-bdg ${ausCls}">Inasistencias: ${aus}</span>
        <span class="reit-bdg ${ft1Cls}">Tipo I: ${ft1}</span>
      </div>
    </div>
    <div class="reit-grid">
      <div class="reit-box">
        <div class="t">CONTADOR DE ASISTENCIA</div>
        <div class="v">
          <div class="reit-kpi"><span class="reit-bdg ${ausCls}">${aus} inasistencia(s)</span></div>
          <span class="bdg bg">Umbral: ${REIT_AUS_UMBRAL}</span>
        </div>
        <div class="reit-msg">${aus>=REIT_AUS_UMBRAL?'Crítico: supera el umbral configurado para alertar reiteración/abandono.':'Ok: dentro del umbral configurado.'}</div>
      </div>
      <div class="reit-box">
        <div class="t">ALERTA TIPO I (REGLA DE 3)</div>
        <div class="v">
          <div class="reit-kpi"><span class="reit-bdg ${ft1Cls}">${ft1} falta(s) Tipo I</span></div>
          <span class="bdg bg">Umbral: ${REIT_FT1_UMBRAL}</span>
        </div>
        <div class="reit-msg">${escHtml(ft1Msg)}</div>
      </div>
      <div class="reit-box">
        <div class="t">RECURRENCIA ESPACIAL</div>
        ${topPlaces.length?`<div class="reit-list">${topPlaces.map(([k,c])=>`<span class="reit-chip">${escHtml(k)} <strong>${c}</strong></span>`).join('')}</div>`
          :`<div class="reit-msg">Sin lugares detectables (depende de la calidad del texto en “Descripción”).</div>`}
      </div>
      <div class="reit-box">
        <div class="t">MAPA DE VÍCTIMAS / AFECTADOS</div>
        ${topVictims.length?`<div class="reit-list">${topVictims.map(([k,c])=>`<span class="reit-chip">${escHtml(k)} <strong>${c}</strong></span>`).join('')}</div>`
          :`<div class="reit-msg">No se identificaron nombres en descripciones (heurística conservadora).</div>`}
      </div>
    </div>
  </div>`;
}
async function refreshCrReiteracion(){
  const wrap=document.getElementById('crReitWrap');
  if(!wrap)return;
  const curso=document.getElementById('crCurso')?.value||'';
  const sel=document.getElementById('crEst');
  const eid=sel?.value;
  const estNom=sel?.options?.[sel.selectedIndex]?.text?.trim()||'';
  if(!eid){wrap.innerHTML='';return;}
  wrap.innerHTML=`<div class="mut" style="font-size:12px;padding:10px;border:1px dashed var(--brd);border-radius:var(--r)">Cargando análisis de reiteración…</div>`;
  const [faltasAll,tomas]=await Promise.all([_fetchFaltasAnioCached(),_fetchAsistenciaTomasCurso(curso)]);
  const fs=faltasAll.filter(f=>Number(f.estudiante_id)===Number(eid));
  // asistencia: contar ausencias del estudiante en el rango
  const as=tomas.map(t=>({...t,detalles:(t.detalles||[]).filter(d=>Number(d.estudiante_id)===Number(eid))}));
  wrap.innerHTML=renderTarjetaReiteracion({faltas:fs,asistencias:as,estudianteNombre:estNom,curso});
}
async function openOvSenal(){
  const sc=document.getElementById('crCurso');
  if(!sc)return;
  const keep=sc.options[0];
  sc.innerHTML='';sc.appendChild(keep);
  sc.disabled=false;
  const selEst=document.getElementById('crEst');
  if(selEst) selEst.disabled=false;
  if(CU.rol==='Director'&&CU.curso){
    const o=document.createElement('option');o.value=CU.curso;o.textContent=CU.curso;sc.appendChild(o);sc.value=CU.curso;
  }else if(CU.rol==='Acudiente'){
    const list=await api('/api/estudiantes');
    if(!Array.isArray(list)||!list.length){
      toast('No se pudo cargar el estudiante asociado.','e');
      return;
    }
    const e=list[0];
    const c=(e.curso||'').trim();
    if(!c){
      toast('El estudiante no tiene curso en ficha. Contacte al colegio.','e');
      return;
    }
    const o=document.createElement('option');o.value=c;o.textContent=c;sc.appendChild(o);sc.value=c;
    sc.disabled=true;
    selEst.innerHTML='';
    const eo=document.createElement('option');
    eo.value=String(e.id||'');
    eo.textContent=e.nombre||'Estudiante';
    selEst.appendChild(eo);
    selEst.value=String(e.id||'');
    selEst.disabled=true;
  }else{
    CURSOS.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;sc.appendChild(o);});
  }
  if(CU.rol!=='Acudiente') selEst.innerHTML='<option value="">Seleccionar</option>';
  document.getElementById('crTipo').value='';
  document.getElementById('crSub').innerHTML='<option value="">Primero elija tipo</option>';
  document.getElementById('crDesc').value='';
  document.getElementById('crUrg').value='moderada';
  const fe=document.getElementById('crEvid');if(fe)fe.value='';
  document.getElementById('crErr').textContent='';
  refreshCrAccion();
  if(CU.rol==='Director'&&CU.curso) await loadCrEstudiantes();
  if(CU.rol==='Acudiente') await refreshCrReiteracion();
  openOv('ov-senal');
}
async function loadCrEstudiantes(){
  const c=document.getElementById('crCurso').value;
  const sel=document.getElementById('crEst');
  sel.innerHTML='<option value="">Seleccionar</option>';
  if(!c)return;
  const list=await api('/api/estudiantes?curso='+encodeURIComponent(c));
  if(!Array.isArray(list))return;
  list.forEach(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.nombre;sel.appendChild(o);});
  refreshCrReiteracion();
}
async function guardarConducta(){
  const err=document.getElementById('crErr');
  err.textContent='';
  const eid=document.getElementById('crEst').value;
  const tipo=document.getElementById('crTipo').value;
  const sub=document.getElementById('crSub').value;
  const desc=document.getElementById('crDesc').value.trim();
  const urg=document.getElementById('crUrg').value;
  if(!eid){err.textContent='Seleccione estudiante';return;}
  if(!tipo||!sub){err.textContent='Seleccione tipo y opción';return;}
  if(desc.length<10){err.textContent='La descripción objetiva requiere al menos 10 caracteres.';return;}
  const fd=new FormData();
  fd.append('estudiante_id',eid);
  fd.append('tipo_conducta',tipo);
  fd.append('subtipo',sub);
  fd.append('descripcion_objetiva',desc);
  fd.append('urgencia',urg);
  const f=document.getElementById('crEvid')?.files?.[0];
  if(f)fd.append('evidencia',f);
  const r=await fetch('/api/senales-atencion',{method:'POST',body:fd,credentials:'same-origin'});
  const j=await r.json().catch(()=>({}));
  if(j.ok){closeOv('ov-senal');toast('Conducta registrada');renderCurrentTab();}
  else err.textContent=j.error||'No se pudo guardar';
}
function senEstadoLbl(e){
  const m={abierta:'Abierta',en_seguimiento:'En seguimiento',cerrada:'Cerrada'};
  return m[e]||e||'—';
}
async function patchSenal(sid){
  const stEl=document.querySelector(`select[data-sen-st="${sid}"]`);
  const ntEl=document.querySelector(`textarea[data-sen-nt="${sid}"]`);
  const estado=stEl?stEl.value:'abierta';
  const nota=ntEl?(ntEl.value||'').trim():'';
  const r=await api(`/api/senales-atencion/${sid}`,{method:'PATCH',body:JSON.stringify({estado,nota_seguimiento:nota})});
  if(r.ok) toast('Registro actualizado');else toast(r.error||'Error','e');
}
function _conductaTipoDesc(s){
  if(s.categoria==='conducta_riesgo'&&s.tipo_conducta){
    return`<span class="mut">${CR_TIPO_LBL[s.tipo_conducta]||s.tipo_conducta}</span><br><small>${CR_SUB_LBL[s.subtipo_clave]||s.subtipo_clave||'—'}</small>`;
  }
  return SEN_CAT_LBL[s.categoria]||s.categoria||'—';
}
function _senalesRowsHtml(rows,canSeg){
  const list=Array.isArray(rows)?rows:[];
  if(!list.length) return '<div class="empty">Sin registros</div>';
  return `<table class="tbl"><thead><tr><th>Fecha</th><th>Estudiante</th><th>Curso</th><th>Tipo / detalle</th><th>Urgencia</th><th>Descripción</th><th>Evid.</th><th>Estado</th><th>Registró</th>${canSeg?'<th>Seguimiento</th>':''}</tr></thead><tbody>
    ${list.map(s=>{
      const obs=(s.observacion||'').replace(/</g,'&lt;');
      const short=obs.length>100?obs.slice(0,100)+'…':obs;
      const urg=s.urgencia?(String(s.urgencia).charAt(0).toUpperCase()+String(s.urgencia).slice(1)):'—';
      const ev=s.evidencia_path?`<a class="btn btn-xs btn-g" href="/api/senales-atencion/${s.id}/evidencia" target="_blank" rel="noopener">Archivo</a>`:'—';
      return`<tr>
        <td>${s.fecha_registro||'—'}</td>
        <td>${String(s.estudiante_nombre||'—').replace(/</g,'&lt;')}</td>
        <td>${String(s.curso||'—').replace(/</g,'&lt;')}</td>
        <td style="max-width:160px;font-size:11px">${_conductaTipoDesc(s)}</td>
        <td>${urg}</td>
        <td style="max-width:200px;font-size:12px" title="${obs}">${short}</td>
        <td>${ev}</td>
        <td><span class="bdg bg">${senEstadoLbl(s.estado)}</span></td>
        <td style="font-size:11px">${s.registrado_por_nombre||'—'} <span class="mut">(${s.registrado_rol||''})</span></td>
        ${canSeg?`<td style="min-width:200px">
          <select data-sen-st="${s.id}" class="inp-sm" style="width:100%;margin-bottom:6px">
            <option value="abierta" ${s.estado==='abierta'?'selected':''}>Abierta</option>
            <option value="en_seguimiento" ${s.estado==='en_seguimiento'?'selected':''}>En seguimiento</option>
            <option value="cerrada" ${s.estado==='cerrada'?'selected':''}>Cerrada</option>
          </select>
          <textarea data-sen-nt="${s.id}" rows="2" placeholder="Nota de seguimiento" style="width:100%;font-size:12px">${(s.nota_seguimiento||'').replace(/</g,'&lt;')}</textarea>
          <button type="button" class="btn btn-xs" style="margin-top:4px" onclick="patchSenal(${s.id})">Guardar</button>
        </td>`:''}
      </tr>`;
    }).join('')}
  </tbody></table>`;
}
function _wirePrevEstTabs(){
  const root=document.getElementById('prevEstAlertasCard');
  if(!root) return;
  const tit=document.getElementById('prevEstCardTit');
  const btns=root.querySelectorAll('[data-prev-est]');
  const panes={ciudadana:document.getElementById('repEstPrevCiudadana'),conductas:document.getElementById('repEstPrevConductas')};
  const set=(k)=>{
    btns.forEach(b=>{
      const on=b.getAttribute('data-prev-est')===k;
      b.classList.toggle('btn-p',on);
      b.classList.toggle('btn-xs',true);
    });
    Object.keys(panes).forEach(key=>{
      const el=panes[key];
      if(el) el.style.display=key===k?'block':'none';
    });
    if(tit) tit.textContent=k==='conductas'?'Conductas de riesgo':'Alertas estudiantiles';
  };
  btns.forEach(b=>{
    b.addEventListener('click',()=>{
      const k=b.getAttribute('data-prev-est')||'ciudadana';
      set(k);
      if(k==='ciudadana') refreshAlertasEstPrev();
    });
  });
  set('ciudadana');
}
async function renderSenales(tab){
  if(CU.rol==='Acudiente'){
    tab.innerHTML=`
    <div class="abanner ab-i" style="font-size:11px;line-height:1.45">Aquí puede <strong>enviar un registro</strong> de conducta de riesgo observada en casa o en contexto del estudiante. El colegio lo revisa en convivencia; <strong>no verá aquí el historial ni el estado</strong> del caso (eso lo gestiona coordinación/orientación).</div>
    <div class="card">
      <div class="ch"><h3>Registrar conducta de riesgo</h3><button type="button" class="btn btn-p btn-xs" onclick="openOvSenal()">Abrir formulario</button></div>
      <div style="padding:12px;font-size:12px;line-height:1.5;color:var(--mut)">Si necesita seguimiento sobre un envío previo, comuníquese con el colegio por los canales habituales (reuniones, citas, etc.).</div>
    </div>`;
    return;
  }
  const raw=await api('/api/senales-atencion');
  if(raw&&raw.error){tab.innerHTML=`<div class="abanner ab-r">${raw.error}</div>`;return;}
  const rows=Array.isArray(raw)?raw:[];
  const conductaRows=rows.filter(s=>String(s.categoria||'')==='conducta_riesgo');
  const canNew=['Coordinador','Director','Orientador','Docente','Superadmin','Acudiente'].includes(CU.rol);
  const canSeg=['Coordinador','Orientador','Superadmin'].includes(CU.rol);
  const canPrev=['Coordinador','Director','Orientador','Superadmin'].includes(CU.rol);
  const canRepPrev=['Coordinador','Orientador','Director','Superadmin'].includes(CU.rol);
  const btnNueva=canNew?`<button type="button" class="btn btn-p btn-xs" onclick="openOvSenal()">+ Nueva conducta</button>`:'';
  tab.innerHTML=`
    <div class="abanner ab-i" style="font-size:12px;line-height:1.55;max-width:920px;padding:12px 14px">
      <p style="margin:0 0 8px"><strong>Conductas de riesgo</strong> — Área de convivencia. Revise <strong>alertas del estudiantado</strong> y la <strong>tabla de conductas</strong> según la pestaña; más abajo, el panel de <strong>reiteración y focos</strong> (faltas y asistencia en el rango elegido).</p>
      <ul style="margin:0;padding-left:1.15rem">
        <li style="margin-bottom:4px"><strong>Alertas ciudadanas:</strong> mensajes del canal estudiantil (Ley 1620). No crean falta hasta validación del equipo.</li>
        <li><strong>Conductas de riesgo:</strong> registros formales (tipo I, II o III) ingresados por coordinación, orientación, dirección o docentes.</li>
      </ul>
      <p style="margin:8px 0 0;font-size:11px;opacity:0.92">Tratamiento confidencial según política institucional.</p>
    </div>
    ${canRepPrev?`
    <div class="card" id="prevEstAlertasCard" style="margin-bottom:12px">
      <div class="ch">
        <h3 id="prevEstCardTit">Alertas estudiantiles</h3>
        <div class="ch-r" style="gap:8px;flex-wrap:wrap;align-items:center">
          ${btnNueva}
          <button type="button" class="btn btn-xs" onclick="renderCurrentTab()">Actualizar</button>
          <button type="button" class="btn btn-xs btn-i" onclick="openOv('ov-ayuda-prev')">¿Qué es esto?</button>
        </div>
      </div>
      <div style="padding:10px">
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button type="button" class="btn btn-xs btn-p" data-prev-est="ciudadana">Alertas ciudadanas</button>
          <button type="button" class="btn btn-xs" data-prev-est="conductas">Conductas de riesgo</button>
        </div>
        <div id="repEstPrevCiudadana" class="prev-est-pane"></div>
        <div id="repEstPrevConductas" class="prev-est-pane" style="display:none;padding-top:4px"><div style="overflow:auto">${_senalesRowsHtml(conductaRows,canSeg)}</div></div>
      </div>
    </div>`:''}
    ${canPrev?`
    <div class="card" style="margin-bottom:12px">
      <div class="ch">
        <h3>Prevención — Reiteración y focos</h3>
        <div class="ch-r" style="gap:8px">
          <select id="prevRango" style="font-size:12px;padding:5px 9px" onchange="refreshPrevencionReiteracion()">
            <option value="30d" selected>Últimos 30 días</option>
            <option value="anio">Año académico (selector superior)</option>
          </select>
          <button type="button" class="btn btn-xs" onclick="refreshPrevencionReiteracion()">Actualizar</button>
        </div>
      </div>
      <div id="prevBody" style="padding:10px"></div>
    </div>`:''}
    ${canRepPrev?'':`<div class="card">
      <div class="ch"><h3>${rows.length} registro(s)</h3>${btnNueva}</div>
      <div style="padding:9px;overflow:auto">${_senalesRowsHtml(rows,canSeg)}</div>
    </div>`}`;
  if(canRepPrev){
    _wirePrevEstTabs();
    refreshAlertasEstPrev();
  }
  if(canPrev) refreshPrevencionReiteracion();
}

async function refreshAlertasEstPrev(){
  const box=document.getElementById('repEstPrevCiudadana');
  if(!box) return;
  box.innerHTML='<div class="mut">Cargando alertas…</div>';
  let url='/api/reportes-convivencia?estado=pendiente_validacion';
  if(CU.rol==='Superadmin'&&CU.colegio_id) url+=`&colegio_id=${encodeURIComponent(String(CU.colegio_id))}`;
  const j=await api(url);
  if(j&&j.error){box.innerHTML=`<div class="abanner ab-r">${escHtml(j.error)}</div>`;return;}
  const list=Array.isArray(j)?j:[];
  const pend=list.filter(x=>(x.estado||'')==='pendiente_validacion');
  const urg=pend.filter(x=>(x.urgencia||'')==='urgente');
  const top=pend.slice(0,8);
  const header=`<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px">
    <span class="bdg bg">Pendientes: <strong>${pend.length}</strong></span>
    <span class="bdg bg">Urgentes: <strong>${urg.length}</strong></span>
    <span class="bdg bg">Canal ciudadano (no crea falta automáticamente)</span>
  </div>`;
  if(!top.length){
    box.innerHTML=header+`<div class="empty">Sin alertas pendientes de validación.</div>`;
    return;
  }
  const rows=top.map(r=>{
    const u=r.urgencia==='urgente'?'<span class="reit-bdg crit">Urgente</span>':'<span class="bdg bg">Puede esperar</span>';
    const cat=escHtml(REP_CAT_LBL[r.categoria_visual]||r.categoria_visual||'—');
    const lug=escHtml(REP_LUG_LBL[r.lugar_clave]||r.lugar_clave||'—');
    const desc=escHtml((r.descripcion||'').slice(0,90))+((r.descripcion||'').length>90?'…':'');
    const ev=r.evidencia_path?`<a class="btn btn-xs btn-g" href="/static/uploads/${escHtml(r.evidencia_path)}" target="_blank" rel="noopener">Archivo</a>`:'—';
    return `<tr>
      <td style="font-size:11px">${escHtml(r.creado_en||'—')}</td>
      <td>${u}</td>
      <td><strong>${escHtml(r.estudiante_nombre||'')}</strong><div class="mut">${escHtml(r.curso||'')}</div></td>
      <td style="font-size:11px">${cat}<div class="mut">${lug}</div></td>
      <td style="font-size:11px" title="${escHtml(r.descripcion||'')}">${desc}</td>
      <td style="font-size:11px">${ev}</td>
      <td style="font-size:11px">
        <button type="button" class="btn btn-xs btn-i" onclick="openRepBitacora(${Number(r.id)})">Bitácora</button>
        <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">
        <button type="button" class="btn btn-xs btn-p" onclick="patchRepEst(${Number(r.id)},'caso_abierto')">Abrir caso</button>
        <button type="button" class="btn btn-xs" onclick="patchRepEst(${Number(r.id)},'orientacion')">Orientación</button>
        <button type="button" class="btn btn-xs btn-d" onclick="patchRepEst(${Number(r.id)},'descartado')">Descartar</button>
        </div>
      </td>
    </tr>`;
  }).join('');
  box.innerHTML=header+`
    <div class="table-wrap">
      <table>
        <thead><tr><th style="width:92px">Recibido</th><th style="width:86px">Urgencia</th><th>Estudiante</th><th style="width:160px">Tema / lugar</th><th>Resumen</th><th style="width:70px">Evid.</th><th style="width:260px">Bitácora / acción</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    ${pend.length>top.length?`<div class="mut" style="margin-top:8px">Mostrando ${top.length} de ${pend.length}. Las demás quedan en el historial al cambiar el estado.</div>`:''}
  `;
}

function _hoyIso(){return new Date().toISOString().slice(0,10);}
function _rangoPrev(){
  const r=document.getElementById('prevRango')?.value||'30d';
  if(r==='anio'){
    const y=getAnio();
    return {desde:`${y}-01-01`,hasta:`${y}-12-31`,lbl:`Año ${y}`};
  }
  const hasta=_hoyIso();
  const desde=_isoDateNDaysAgo(30);
  return {desde,hasta,lbl:'Últimos 30 días'};
}
function _tblRank(title,cols,rows,empty){
  const head=cols.map(c=>`<th>${c}</th>`).join('');
  const body=rows.length?rows.map(r=>`<tr>${r.map(td=>`<td>${td}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${cols.length}" class="mut">${empty}</td></tr>`;
  return `<div class="card" style="margin:0">
    <div class="ch" style="padding:9px 12px"><h3 style="font-size:12px">${title}</h3></div>
    <div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>
  </div>`;
}
async function refreshPrevencionReiteracion(){
  const box=document.getElementById('prevBody');
  if(!box)return;
  const r=_rangoPrev();
  box.innerHTML=`<div class="mut">Cargando informe (${escHtml(r.lbl)})…</div>`;
  const j=await api(`/api/prevencion/reiteracion?desde=${encodeURIComponent(r.desde)}&hasta=${encodeURIComponent(r.hasta)}`);
  if(j&&j.error){box.innerHTML=`<div class="abanner ab-r">${escHtml(j.error)}</div>`;return;}
  const aus=(j.rank_ausencias||[]).map(x=>[
    `<button type="button" class="btn btn-xs btn-i" style="padding:3px 8px" onclick="openPrevDet('estudiante',${Number(x.estudiante_id||0)},'${String((x.estudiante||'').replace(/'/g,"&#39;"))}')">${escHtml(x.estudiante||'—')}</button><div class="mut">${escHtml(x.curso||'—')}</div>`,
    `<span class="reit-bdg crit">≥3</span> <strong>${Number(x.ausencias||0)}</strong>`
  ]);
  const t1=(j.rank_tipoI||[]).map(x=>[
    `<button type="button" class="btn btn-xs btn-i" style="padding:3px 8px" onclick="openPrevDet('estudiante',${Number(x.estudiante_id||0)},'${String((x.estudiante||'').replace(/'/g,"&#39;"))}')">${escHtml(x.estudiante||'—')}</button><div class="mut">${escHtml(x.curso||'—')}</div>`,
    `<span class="reit-bdg crit">≥3</span> <strong>${Number(x.tipoI||0)}</strong>`
  ]);
  const lug=(j.rank_lugares||[]).map(x=>[
    `<button type="button" class="btn btn-xs btn-i" style="padding:3px 8px" onclick="openPrevDet('lugar','${String((x.lugar||'').replace(/'/g,"&#39;"))}')">${escHtml(x.lugar||'—')}</button>`,
    `<span class="reit-bdg crit">≥3</span> <strong>${Number(x.faltas||0)}</strong>`
  ]);
  const vic=(j.rank_victimas||[]).map(x=>[
    `<button type="button" class="btn btn-xs btn-i" style="padding:3px 8px" onclick="openPrevDet('victima','${String((x.victima||'').replace(/'/g,"&#39;"))}')">${escHtml(x.victima||'—')}</button>`,
    `<span class="reit-bdg warn">≥2</span> <strong>${Number(x.menciones||0)}</strong>`
  ]);
  const scope=j.scope&&j.scope.curso?`<span class="bdg bg">Curso: ${escHtml(j.scope.curso)}</span>`:'<span class="bdg bg">Todos los cursos</span>';
  const na=(j.rank_ausencias||[]).length,nt=(j.rank_tipoI||[]).length,nl=(j.rank_lugares||[]).length,nv=(j.rank_victimas||[]).length;
  const emptyHint=(na+nt+nl+nv===0)?`<div class="abanner ab-i" style="font-size:12px;line-height:1.5;margin-bottom:10px">En este rango no hay filas por encima de los umbrales. Los datos provienen de <strong>asistencia</strong> (inasistencias por estudiante) y de <strong>faltas disciplinarias</strong> (Tipo I por estudiante; <em>lugar</em> y <em>afectados</em> en JSON para focos y víctimas). Amplíe fechas con <strong>Año académico</strong> o registre tomas de asistencia y faltas con esos campos.</div>`:'';
  box.innerHTML=`
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px">
      ${scope}
      <span class="bdg bg">Rango: ${escHtml(j.desde||r.desde)} → ${escHtml(j.hasta||r.hasta)}</span>
      <span class="bdg bg">Umbrales: ausencias ≥3 · Tipo I ≥3 · mismo lugar ≥3 · misma víctima ≥2</span>
    </div>
    ${emptyHint}
    <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">
      ${_tblRank('Top estudiantes — Ausencias (≥3)', ['Estudiante','Ausencias'], aus, 'Sin estudiantes que superen el umbral')}
      ${_tblRank('Top estudiantes — Faltas Tipo I (≥3)', ['Estudiante','Tipo I'], t1, 'Sin estudiantes que superen el umbral')}
      ${_tblRank('Ranking de lugares — Focos (≥3)', ['Lugar','Faltas'], lug, 'Sin lugares que superen el umbral')}
      ${_tblRank('Ranking de víctimas — Posible acoso (≥2)', ['Víctima','Menciones'], vic, 'Sin víctimas con menciones repetidas')}
    </div>`;
}

async function openPrevDet(kind,val,label){
  const r=_rangoPrev();
  const tit=document.getElementById('prevDetTit');
  const sub=document.getElementById('prevDetSub');
  const body=document.getElementById('prevDetBody');
  if(tit)tit.textContent=kind==='lugar'?'Faltas por lugar':kind==='victima'?'Faltas por víctima':'Faltas del estudiante';
  if(sub)sub.textContent=`${label||val||''} · ${r.desde} → ${r.hasta}`;
  if(body)body.innerHTML='<div class="mut">Cargando…</div>';
  let url=`/api/prevencion/reiteracion/detalle?desde=${encodeURIComponent(r.desde)}&hasta=${encodeURIComponent(r.hasta)}&kind=${encodeURIComponent(kind)}`;
  if(kind==='estudiante') url+=`&estudiante_id=${encodeURIComponent(String(val||''))}`;
  else if(kind==='lugar') url+=`&lugar=${encodeURIComponent(String(val||''))}`;
  else url+=`&victima=${encodeURIComponent(String(val||''))}`;
  const j=await api(url);
  if(j&&j.error){if(body)body.innerHTML=`<div class="abanner ab-r">${escHtml(j.error)}</div>`;openOv('ov-prev-det');return;}
  const items=Array.isArray(j.items)?j.items:[];
  if(!items.length){
    if(body)body.innerHTML='<div class="empty">Sin faltas en el rango seleccionado.</div>';
    openOv('ov-prev-det');return;
  }
  if(body){
    body.innerHTML=`
      <div class="table-wrap">
        <table>
          <thead><tr><th style="width:92px">Fecha</th><th>Estudiante</th><th style="width:70px">Curso</th><th style="width:70px">Tipo</th><th>Falta</th><th style="width:120px">Lugar</th><th style="width:90px"></th></tr></thead>
          <tbody>
            ${items.map(f=>`<tr>
              <td>${escHtml(f.fecha||'—')}</td>
              <td>${escHtml(f.estudiante||'—')}</td>
              <td>${escHtml(f.curso||'—')}</td>
              <td>${escHtml(f.tipo_falta||'—')}</td>
              <td title="${escHtml(f.falta_especifica||'')}">${escHtml(f.falta_especifica||'—')}</td>
              <td>${escHtml(f.lugar||'—')}</td>
              <td><button type="button" class="btn btn-xs btn-p" onclick="closeOv('ov-prev-det');verFalta(${Number(f.id||0)})">Abrir</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  }
  openOv('ov-prev-det');
}
