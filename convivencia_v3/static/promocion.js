// Tras app.js (globales): api, CU, CURSOS, escHtml, toast, renderCurrentTab, openOv, closeOv

const PROM_TEMAS=[
  {v:'relaciones_respetuosas',l:'Relaciones respetuosas'},
  {v:'normas_convivencia',l:'Normas de convivencia'},
  {v:'gestion_emocional',l:'Gestión emocional'},
  {v:'ambiente_fisico_seguro',l:'Ambiente físico y seguro'},
  {v:'participacion_activa',l:'Participación activa'},
  {v:'prevencion_conflictos',l:'Prevención de conflictos'},
];
function promTemaLbl(v){return (PROM_TEMAS.find(x=>x.v===v)||{}).l||v||'—';}

// ── Focos → dashboard por tema de promoción ───────────────────────────────────
window._promCalorFilas=[];
function _promAggCalorPorTema(filas){
  const by={};
  PROM_TEMAS.forEach(t=>{by[t.v]={u:0,r:0,tot:0,items:[]};});
  (filas||[]).forEach(r=>{
    const tm=(r.tema_promocion||'').trim();
    if(!by[tm]) return;
    by[tm].u+=Number(r.urgente)||0;
    by[tm].r+=Number(r.no_urgente)||0;
    by[tm].tot+=Number(r.total)||0;
    by[tm].items.push(r);
  });
  return by;
}
async function promRefreshCalor(){
  const wrap=document.getElementById('promCalorWrap');
  if(!wrap)return;
  const sel=document.getElementById('promCalorDias');
  const dias=Math.min(90,Math.max(7,Number(sel?.value)||30));
  if(sel) sel.value=String(dias);
  wrap.innerHTML='<div class="mut">Cargando indicadores…</div>';
  let url=`/api/promocion/focos-calor?dias=${encodeURIComponent(String(dias))}`;
  if(CU.rol==='Superadmin'&&CU.colegio_id) url+=`&colegio_id=${encodeURIComponent(String(CU.colegio_id))}`;
  const j=await api(url);
  if(j&&j.error){wrap.innerHTML=`<div class="abanner ab-r">${escHtml(j.error)}</div>`;return;}
  const filas=Array.isArray(j.filas)?j.filas:[];
  window._promCalorFilas=filas;
  const by=_promAggCalorPorTema(filas);
  const maxTot=Math.max(...PROM_TEMAS.map(t=>by[t.v].tot),1);
  const rango=`<div class="mut" style="font-size:11px;margin-bottom:10px">Período: <strong>${escHtml(j.desde||'')} → ${escHtml(j.hasta||'')}</strong>. Los registros agrupan <strong>alertas ciudadanas</strong> y <strong>conductas de riesgo</strong> según su tipo, y se muestran bajo el <em>tema de promoción</em> correspondiente.</div>`;
  const cards=PROM_TEMAS.map(t=>{
    const b=by[t.v];
    const u=b.u,r=b.r,tot=b.tot;
    const pctU=tot>0?Math.round((u/tot)*100):0;
    const pctR=100-pctU;
    const wTot=maxTot>0?Math.min(100,Math.round((tot/maxTot)*100)):0;
    return `<div class="fcard" style="padding:12px 14px;min-height:0;border:1px solid var(--brd);border-radius:var(--r);background:var(--card)">
      <div style="font-weight:600;font-size:13px;line-height:1.3">${escHtml(t.l)}</div>
      <div style="display:flex;align-items:baseline;gap:8px;margin:8px 0 6px">
        <span style="font-size:24px;font-weight:700">${tot}</span>
        <span class="mut" style="font-size:11px">registros</span>
      </div>
      <div style="height:8px;border-radius:6px;background:rgba(0,0,0,.06);overflow:hidden;margin-bottom:4px" title="Intensidad relativa al tema más frecuente">
        <div style="height:100%;width:${wTot}%;background:linear-gradient(90deg,var(--emerald),#007a56);border-radius:6px;min-width:${tot?4:0}px"></div>
      </div>
      <div style="display:flex;height:10px;border-radius:6px;overflow:hidden;background:rgba(0,0,0,.06);margin-bottom:4px" title="Urgente/alta vs resto">
        ${tot?`<div style="width:${pctU}%;min-width:${u?3:0}px;background:rgba(200,50,60,.75)"></div><div style="width:${pctR}%;background:rgba(40,90,160,.55)"></div>`:'<div style="width:100%;background:transparent"></div>'}
      </div>
      <div class="mut" style="font-size:11px;line-height:1.35">Urgente/alta: ${u} · Resto: ${r}</div>
      <button type="button" class="btn btn-xs btn-p" style="margin-top:10px;width:100%" onclick="promPlanDesdeTema(${JSON.stringify(t.v)})">Programar desde foco</button>
    </div>`;
  }).join('');
  wrap.innerHTML=rango+`
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px">${cards}</div>
    ${filas.length?`<details style="margin-top:14px;font-size:12px"><summary class="mut" style="cursor:pointer">Detalle por origen (${filas.length})</summary>
      <div class="table-wrap" style="margin-top:8px"><table class="tbl"><thead><tr><th>Origen</th><th>Urg./alta</th><th>Resto</th><th>Total</th><th></th></tr></thead><tbody>
        ${filas.map((r,i)=>{
          const u=Number(r.urgente)||0,nr=Number(r.no_urgente)||0,tot=Number(r.total)||0;
          return `<tr><td style="font-size:12px"><strong>${escHtml(r.label||'')}</strong><div class="mut">${escHtml(promTemaLbl(r.tema_promocion))}</div>${r.curso_sugerido?`<div class="mut">Curso frecuente: ${escHtml(r.curso_sugerido)}</div>`:''}</td>
            <td style="text-align:center">${u}</td><td style="text-align:center">${nr}</td><td style="text-align:center">${tot}</td>
            <td><button type="button" class="btn btn-xs" onclick="promPlanDesdeCalor(${i})">Usar esta fila</button></td></tr>`;
        }).join('')}
      </tbody></table></div></details>`:`<div class="empty" style="margin-top:12px">Sin datos en el rango. Cuando haya alertas o conductas registradas, aparecerán aquí.</div>`}`;
}
function promFillCreateFormSelects(){
  const tema=document.getElementById('promTema');
  if(tema) tema.innerHTML='<option value="">Seleccionar</option>'+PROM_TEMAS.map(x=>`<option value="${x.v}">${x.l}</option>`).join('');
  const cur=document.getElementById('promCurso');
  if(cur) cur.innerHTML='<option value="">Seleccionar</option>'+CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('');
  const est=document.getElementById('promEstCurso');
  if(est) est.innerHTML='<option value="">Seleccionar</option>'+CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('');
}
function openPromCrear(){
  promFillCreateFormSelects();
  const hoy=new Date().toISOString().slice(0,10);
  const tit=document.getElementById('promTit');
  const tema=document.getElementById('promTema');
  const fecha=document.getElementById('promFecha');
  const lugar=document.getElementById('promLugar');
  const rec=document.getElementById('promRec');
  const desc=document.getElementById('promDesc');
  const pub=document.getElementById('promPub');
  const ev=document.getElementById('promEvid');
  const err=document.getElementById('promErr');
  if(tit) tit.value='';
  if(tema) tema.value='';
  if(fecha) fecha.value=hoy;
  if(lugar) lugar.value='';
  if(rec) rec.value='';
  if(desc) desc.value='';
  if(pub){pub.value='colegio';promPubChanged();}
  if(ev) ev.value='';
  if(err) err.textContent='';
  const box=document.getElementById('promEstPick');
  if(box) box.innerHTML='<span class="mut">Seleccione curso</span>';
  openOv('ov-prom-create');
}
function promPlanDesdeTema(temaKey){
  const filas=(window._promCalorFilas||[]).filter(r=>(r.tema_promocion||'')===temaKey);
  if(!filas.length){
    promFillCreateFormSelects();
    const tema=document.getElementById('promTema');
    if(tema) tema.value=temaKey;
    const err=document.getElementById('promErr');if(err) err.textContent='';
    const fecha=document.getElementById('promFecha');
    if(fecha) fecha.value=new Date().toISOString().slice(0,10);
    const tit=document.getElementById('promTit');if(tit) tit.value='';
    const desc=document.getElementById('promDesc');if(desc) desc.value='';
    const pub=document.getElementById('promPub');if(pub){pub.value='colegio';promPubChanged();}
    openOv('ov-prom-create');
    toast('Sin focos en este tema en el período; planifique desde cero o amplíe los días.');
    return;
  }
  filas.sort((a,b)=>(Number(b.total)||0)-(Number(a.total)||0));
  const row=filas[0];
  const idx=(window._promCalorFilas||[]).indexOf(row);
  if(idx>=0) promPlanDesdeCalor(idx);
}
function promPlanDesdeCalor(i){
  const row=(window._promCalorFilas||[])[i];
  if(!row)return;
  promFillCreateFormSelects();
  const tit=document.getElementById('promTit');
  const tema=document.getElementById('promTema');
  const desc=document.getElementById('promDesc');
  const pub=document.getElementById('promPub');
  const cur=document.getElementById('promCurso');
  if(tit) tit.value=(row.titulo_sugerido||'').slice(0,120);
  if(tema&&row.tema_promocion) tema.value=row.tema_promocion;
  if(desc) desc.value=row.descripcion_bosquejo||'';
  if(pub){
    if(row.curso_sugerido){
      pub.value='curso';
      promPubChanged();
      if(cur) cur.value=row.curso_sugerido;
    }else{
      pub.value='colegio';
      promPubChanged();
    }
  }
  const err=document.getElementById('promErr');if(err) err.textContent='';
  openOv('ov-prom-create');
  toast('Revise título, fecha y público antes de guardar.');
}

// ── Promoción (actividades) ───────────────────────────────────────────────────
function _promPublicoLbl(a){
  if(!a)return'—';
  const t=a.publico_tipo||'';
  if(t==='colegio') return 'Todo el colegio';
  if(t==='curso') return `Curso: ${a.publico_curso||'—'}`;
  if(t==='estudiantes'){
    try{
      const js=JSON.parse(a.publico_json||'{}');
      const n=(js.estudiantes_ids||[]).length||0;
      return `Estudiantes (${n})${js.curso?` · ${js.curso}`:''}`;
    }catch{return 'Estudiantes seleccionados';}
  }
  return t||'—';
}

async function _promFetchList(){
  const q=(document.getElementById('promBuscar')?.value||'').trim();
  const qp=[];
  if(q) qp.push('q='+encodeURIComponent(q));
  const url='/api/promocion/actividades'+(qp.length?('?'+qp.join('&')):'');
  const list=await api(url);
  return Array.isArray(list)?list:[];
}

function _promTblRows(rows){
  if(!rows.length)return`<tr><td colspan="5" class="empty">Sin actividades</td></tr>`;
  return rows.map(a=>{
    const btn=`<button type="button" class="btn btn-xs btn-i" onclick="openPromDet(${Number(a.id)})">Abrir</button>`;
    return `<tr>
      <td>${escHtml(a.fecha||'—')}</td>
      <td><strong>${escHtml(a.titulo||'—')}</strong><div class="mut">${escHtml(a.lugar||'')}</div></td>
      <td style="font-size:12px">${escHtml(promTemaLbl(a.tema))}</td>
      <td style="font-size:12px">${escHtml(_promPublicoLbl(a))}</td>
      <td style="width:88px">${btn}</td>
    </tr>`;
  }).join('');
}

async function promAplicarFiltros(){
  const tb=document.getElementById('promListBody');
  if(!tb)return;
  tb.innerHTML='<tr><td colspan="5" class="mut">Cargando…</td></tr>';
  const rows=await _promFetchList();
  tb.innerHTML=_promTblRows(rows);
}
function promPubChanged(){
  const v=document.getElementById('promPub')?.value||'colegio';
  const c=document.getElementById('promPubCursoRow');
  const e=document.getElementById('promPubEstRow');
  if(c)c.style.display=v==='curso'?'flex':'none';
  if(e)e.style.display=v==='estudiantes'?'block':'none';
}
async function promLoadEstSel(){
  const c=document.getElementById('promEstCurso')?.value||'';
  const box=document.getElementById('promEstPick');
  if(!box)return;
  if(!c){box.innerHTML='<span class="mut">Seleccione curso</span>';return;}
  box.innerHTML='<span class="mut">Cargando…</span>';
  const list=await api('/api/estudiantes?curso='+encodeURIComponent(c));
  const rows=Array.isArray(list)?list:[];
  box.innerHTML=rows.length?`<div style="display:flex;gap:8px;flex-wrap:wrap;max-height:120px;overflow:auto">
    ${rows.map(s=>`<label style="display:flex;gap:6px;align-items:center;padding:6px 8px;border:1px solid var(--brd);border-radius:10px;cursor:pointer">
      <input type="checkbox" class="prom-est-chk" value="${Number(s.id)}"> <span style="font-size:12px">${escHtml(s.nombre||'—')}</span>
    </label>`).join('')}
  </div>`:'<div class="empty">Sin estudiantes en el curso</div>';
}
async function promCrear(){
  const err=document.getElementById('promErr'); if(err)err.textContent='';
  const tit=(document.getElementById('promTit')?.value||'').trim();
  const tema=document.getElementById('promTema')?.value||'';
  const fecha=document.getElementById('promFecha')?.value||'';
  const lugar=(document.getElementById('promLugar')?.value||'').trim();
  const rec=(document.getElementById('promRec')?.value||'').trim();
  const desc=(document.getElementById('promDesc')?.value||'').trim();
  const pub=document.getElementById('promPub')?.value||'colegio';
  if(tit.length<4){if(err)err.textContent='Título: mínimo 4 caracteres';return;}
  if(!tema){if(err)err.textContent='Seleccione un tema';return;}
  if(!fecha){if(err)err.textContent='Seleccione una fecha';return;}
  const fd=new FormData();
  fd.append('titulo',tit);
  fd.append('tema',tema);
  fd.append('fecha',fecha);
  fd.append('lugar',lugar);
  fd.append('recursos',rec);
  fd.append('descripcion',desc);
  fd.append('publico_tipo',pub);
  if(pub==='curso'){
    const c=document.getElementById('promCurso')?.value||'';
    if(!c){if(err)err.textContent='Seleccione curso';return;}
    fd.append('publico_curso',c);
  }else if(pub==='estudiantes'){
    const c=document.getElementById('promEstCurso')?.value||'';
    const ids=[...document.querySelectorAll('.prom-est-chk:checked')].map(x=>Number(x.value)).filter(Boolean);
    if(!ids.length){if(err)err.textContent='Seleccione al menos un estudiante';return;}
    fd.append('publico_json',JSON.stringify({curso:c||'',estudiantes_ids:ids}));
  }
  const f=document.getElementById('promEvid')?.files?.[0];
  if(f) fd.append('evidencia',f);
  const r=await fetch('/api/promocion/actividades',{method:'POST',body:fd,credentials:'same-origin'});
  const j=await parseFetchBodyAsJson(r);
  if(j.ok){toast('Actividad guardada');closeOv('ov-prom-create');renderCurrentTab();}
  else{if(err)err.textContent=j.error||'Error';toast(j.error||'Error','e');}
}
async function renderPromocion(tab){
  const rows=await _promFetchList();
  tab.innerHTML=`
    <div class="abanner ab-i voice-lead" style="font-size:12px;line-height:1.5;max-width:none">
      Actividades de <strong>Promoción</strong> en convivencia (planeación, público objetivo y evidencias). No visible para acudientes ni estudiantes.
    </div>
    <div class="card">
      <div class="ch">
        <h3>Indicadores por tema (focos recurrentes)</h3>
        <div class="ch-r" style="gap:8px;align-items:center;flex-wrap:wrap">
          <label class="mut" style="font-size:11px;display:flex;align-items:center;gap:6px">Últimos
            <select id="promCalorDias" class="inp-sm" style="padding:4px 8px">
              <option value="7">7 días</option>
              <option value="14">14 días</option>
              <option value="30" selected>30 días</option>
              <option value="60">60 días</option>
              <option value="90">90 días</option>
            </select>
          </label>
          <button type="button" class="btn btn-xs" onclick="promRefreshCalor()">Actualizar</button>
        </div>
      </div>
      <div class="mb" style="padding:10px 14px">
        <div id="promCalorWrap"><div class="mut">Cargando…</div></div>
      </div>
    </div>
    <div class="card" style="border-style:dashed">
      <div class="mb" style="padding:16px 18px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px">
        <div>
          <h3 style="margin:0 0 4px;font-size:15px">Registrar actividad</h3>
          <p class="mut" style="margin:0;font-size:12px;max-width:520px">Complete título, tema, fecha y público en el formulario. Las evidencias y el detalle se gestionan al abrir la actividad.</p>
        </div>
        <button type="button" class="btn btn-p" onclick="openPromCrear()">Nueva actividad</button>
      </div>
    </div>
    <div class="card">
      <div class="ch"><h3>Historial</h3></div>
      <div class="mb" style="padding:10px 14px">
        <div class="fr" style="align-items:flex-end;gap:10px;flex-wrap:wrap">
          <div style="flex:1;min-width:200px"><label class="fl">Buscar</label>
            <input type="search" id="promBuscar" placeholder="Título, lugar o descripción…" style="width:100%" onkeydown="if(event.key==='Enter')promAplicarFiltros()"></div>
          <button type="button" class="btn btn-xs" onclick="promAplicarFiltros()">Buscar</button>
        </div>
      </div>
      <div class="table-wrap mb" style="padding:0 8px 12px">
        <table>
          <thead><tr><th style="width:92px">Fecha</th><th>Actividad / problemática</th><th style="width:22%">Tema</th><th style="width:22%">Público objetivo</th><th style="width:88px"></th></tr></thead>
          <tbody id="promListBody">${_promTblRows(rows)}</tbody>
        </table>
      </div>
    </div>`;
  promRefreshCalor();
}

// ── Promoción: detalle / edición / evidencias ────────────────────────────────
window._promDetId=null;
function promEPubChanged(){
  const v=document.getElementById('promEPub')?.value||'colegio';
  const c=document.getElementById('promEPubCursoRow');
  const e=document.getElementById('promEPubEstRow');
  if(c)c.style.display=v==='curso'?'flex':'none';
  if(e)e.style.display=v==='estudiantes'?'block':'none';
}
async function promELoadEstSel(){
  const c=document.getElementById('promEEstCurso')?.value||'';
  const box=document.getElementById('promEEstPick');
  if(!box)return;
  if(!c){box.innerHTML='<span class="mut">Seleccione curso</span>';return;}
  box.innerHTML='<span class="mut">Cargando…</span>';
  const list=await api('/api/estudiantes?curso='+encodeURIComponent(c));
  const rows=Array.isArray(list)?list:[];
  box.innerHTML=rows.length?`<div style="display:flex;gap:8px;flex-wrap:wrap;max-height:160px;overflow:auto">
    ${rows.map(s=>`<label style="display:flex;gap:6px;align-items:center;padding:6px 8px;border:1px solid var(--brd);border-radius:10px;cursor:pointer">
      <input type="checkbox" class="promE-est-chk" value="${Number(s.id)}"> <span style="font-size:12px">${escHtml(s.nombre||'—')}</span>
    </label>`).join('')}
  </div>`:'<div class="empty">Sin estudiantes en el curso</div>';
}
async function openPromDet(id){
  window._promDetId=id;
  const err=document.getElementById('promEErr');if(err)err.textContent='';
  const det=await api(`/api/promocion/actividades/${id}`);
  if(det&&det.error){toast(det.error||'Error','e');return;}
  document.getElementById('promDetTit').textContent='Actividad de promoción';
  document.getElementById('promDetSub').textContent=`#${id} · ${det.fecha||'—'} · ${det.creado_por_nombre||'—'}`;
  const temaSel=document.getElementById('promETema');
  if(temaSel) temaSel.innerHTML=`<option value="">Seleccionar</option>${PROM_TEMAS.map(t=>`<option value="${t.v}">${t.l}</option>`).join('')}`;
  const cursoSel=document.getElementById('promECurso');
  const estCursoSel=document.getElementById('promEEstCurso');
  if(cursoSel) cursoSel.innerHTML=`<option value="">Seleccionar</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}`;
  if(estCursoSel) estCursoSel.innerHTML=`<option value="">Seleccionar</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}`;

  document.getElementById('promETit').value=det.titulo||'';
  document.getElementById('promETema').value=det.tema||'';
  document.getElementById('promEFecha').value=det.fecha||'';
  document.getElementById('promELugar').value=det.lugar||'';
  document.getElementById('promERec').value=det.recursos||'';
  document.getElementById('promEDesc').value=det.descripcion||'';
  document.getElementById('promEPub').value=det.publico_tipo||'colegio';
  promEPubChanged();
  if(det.publico_tipo==='curso'){
    document.getElementById('promECurso').value=det.publico_curso||'';
  }else if(det.publico_tipo==='estudiantes'){
    try{
      const js=JSON.parse(det.publico_json||'{}');
      document.getElementById('promEEstCurso').value=js.curso||'';
      await promELoadEstSel();
      const ids=new Set((js.estudiantes_ids||[]).map(Number));
      document.querySelectorAll('.promE-est-chk').forEach(ch=>{if(ids.has(Number(ch.value)))ch.checked=true;});
    }catch{}
  }

  const canDel=['Superadmin','Coordinador'].includes(CU.rol);
  const delBtn=document.getElementById('promDelBtn');
  if(delBtn) delBtn.style.display=canDel?'inline-flex':'none';

  await promEvidList();
  openOv('ov-prom');
}
async function promSave(){
  const id=window._promDetId;
  if(!id)return;
  const err=document.getElementById('promEErr');if(err)err.textContent='';
  const titulo=(document.getElementById('promETit')?.value||'').trim();
  const tema=document.getElementById('promETema')?.value||'';
  const fecha=document.getElementById('promEFecha')?.value||'';
  const lugar=(document.getElementById('promELugar')?.value||'').trim();
  const recursos=(document.getElementById('promERec')?.value||'').trim();
  const descripcion=(document.getElementById('promEDesc')?.value||'').trim();
  const pub=document.getElementById('promEPub')?.value||'colegio';
  let publico_curso='', publico_json='';
  if(titulo.length<4){if(err)err.textContent='Título: mínimo 4 caracteres';return;}
  if(!tema){if(err)err.textContent='Tema obligatorio';return;}
  if(!fecha){if(err)err.textContent='Fecha obligatoria';return;}
  if(pub==='curso'){
    publico_curso=document.getElementById('promECurso')?.value||'';
    if(!publico_curso){if(err)err.textContent='Seleccione curso';return;}
  }else if(pub==='estudiantes'){
    const c=document.getElementById('promEEstCurso')?.value||'';
    const ids=[...document.querySelectorAll('.promE-est-chk:checked')].map(x=>Number(x.value)).filter(Boolean);
    if(!ids.length){if(err)err.textContent='Seleccione al menos un estudiante';return;}
    publico_json=JSON.stringify({curso:c||'',estudiantes_ids:ids});
  }
  const body={titulo,tema,fecha,lugar,recursos,descripcion,publico_tipo:pub,publico_curso,publico_json};
  const r=await api(`/api/promocion/actividades/${id}`,{method:'PATCH',body:JSON.stringify(body)});
  if(r.ok){toast('Actividad actualizada');promAplicarFiltros();closeOv('ov-prom');}
  else{if(err)err.textContent=r.error||'Error';toast(r.error||'Error','e');}
}
async function promDelete(){
  const id=window._promDetId;
  if(!id)return;
  if(!confirm('¿Eliminar esta actividad? Se borrarán también sus evidencias.'))return;
  const r=await api(`/api/promocion/actividades/${id}`,{method:'DELETE'});
  if(r.ok){toast('Actividad eliminada');closeOv('ov-prom');promAplicarFiltros();}
  else toast(r.error||'Error','e');
}
async function promEvidList(){
  const id=window._promDetId;
  const box=document.getElementById('promEvidList');
  if(!id||!box)return;
  box.innerHTML='<div class="mut">Cargando evidencias…</div>';
  const rows=await api(`/api/promocion/actividades/${id}/evidencias`);
  if(rows&&rows.error){box.innerHTML=`<div class="abanner ab-r">${escHtml(rows.error)}</div>`;return;}
  const list=Array.isArray(rows)?rows:[];
  if(!list.length){box.innerHTML='<div class="empty">Sin evidencias todavía.</div>';return;}
  const canDel=true;
  box.innerHTML=`<div class="table-wrap"><table>
    <thead><tr><th>Archivo</th><th style="width:120px">Subió</th><th style="width:120px">Fecha</th><th style="width:140px"></th></tr></thead>
    <tbody>
      ${list.map(e=>{
        const name=escHtml(e.nombre_original||('Evidencia #'+e.id));
        const dl=`<a class="btn btn-xs btn-g" href="/api/promocion/evidencias/${Number(e.id)}/file" target="_blank" rel="noopener">Abrir</a>`;
        const del=canDel?`<button type="button" class="btn btn-xs btn-d" onclick="promEvidDel(${Number(e.id)})">Eliminar</button>`:'';
        return `<tr><td>${name}</td><td style="font-size:11px">${escHtml(e.subido_por_nombre||'—')}</td><td style="font-size:11px">${escHtml(e.creado_en||'—')}</td><td style="display:flex;gap:6px">${dl}${del}</td></tr>`;
      }).join('')}
    </tbody>
  </table></div>`;
}
async function promEvidAdd(){
  const id=window._promDetId;
  const err=document.getElementById('promEErr');if(err)err.textContent='';
  const f=document.getElementById('promEAddFile')?.files?.[0];
  if(!id||!f){if(err)err.textContent='Seleccione un archivo';return;}
  const fd=new FormData();
  fd.append('evidencia',f);
  if(document.getElementById('promESetMain')?.checked) fd.append('set_como_principal','1');
  const r=await fetch(`/api/promocion/actividades/${id}/evidencias`,{method:'POST',body:fd,credentials:'same-origin'});
  const j=await parseFetchBodyAsJson(r);
  if(j.ok){
    toast('Evidencia subida');
    const inp=document.getElementById('promEAddFile');if(inp)inp.value='';
    const ck=document.getElementById('promESetMain');if(ck)ck.checked=false;
    await promEvidList();
    await promAplicarFiltros();
  }else{if(err)err.textContent=j.error||'Error';toast(j.error||'Error','e');}
}
async function promEvidDel(eid){
  if(!confirm('¿Eliminar esta evidencia?'))return;
  const r=await api(`/api/promocion/evidencias/${eid}`,{method:'DELETE'});
  if(r.ok){toast('Evidencia eliminada');promEvidList();promAplicarFiltros();}
  else toast(r.error||'Error','e');
}
