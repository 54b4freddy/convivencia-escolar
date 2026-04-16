// Tras app.js (globales): api, CU, CURSOS, escHtml, toast, renderCurrentTab, openOv, closeOv

// ── Promoción (actividades) ───────────────────────────────────────────────────
const PROM_TEMAS=[
  {v:'relaciones_respetuosas',l:'Relaciones respetuosas'},
  {v:'normas_convivencia',l:'Normas de convivencia'},
  {v:'gestion_emocional',l:'Gestión emocional'},
  {v:'ambiente_fisico_seguro',l:'Ambiente físico y seguro'},
  {v:'participacion_activa',l:'Participación activa'},
  {v:'prevencion_conflictos',l:'Prevención de conflictos'},
];
function promTemaLbl(v){return (PROM_TEMAS.find(x=>x.v===v)||{}).l||v||'—';}
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

function _promValCurso(a){
  if(!a)return'';
  if((a.publico_tipo||'')==='curso')return a.publico_curso||'';
  if((a.publico_tipo||'')==='estudiantes'){
    try{const js=JSON.parse(a.publico_json||'{}');return js.curso||'';}catch{return'';}
  }
  return '';
}

async function _promFetchList(){
  const tema=document.getElementById('promFTema')?.value||'';
  const desde=document.getElementById('promFDesde')?.value||'';
  const hasta=document.getElementById('promFHasta')?.value||'';
  const pub=document.getElementById('promFPub')?.value||'';
  const cur=document.getElementById('promFCurso')?.value||'';
  const cread=document.getElementById('promFCreador')?.value||'';
  const qp=[];
  if(tema)qp.push('tema='+encodeURIComponent(tema));
  if(desde)qp.push('desde='+encodeURIComponent(desde));
  if(hasta)qp.push('hasta='+encodeURIComponent(hasta));
  if(pub)qp.push('publico_tipo='+encodeURIComponent(pub));
  if(cur)qp.push('curso='+encodeURIComponent(cur));
  if(cread)qp.push('creado_por_id='+encodeURIComponent(cread));
  const url='/api/promocion/actividades'+(qp.length?('?'+qp.join('&')):'');
  const list=await api(url);
  return Array.isArray(list)?list:[];
}

function _promTblRows(rows){
  if(!rows.length)return`<tr><td colspan="7" class="empty">Sin actividades con esos filtros</td></tr>`;
  return rows.map(a=>{
    const curso=_promValCurso(a);
    const ev=a.evidencia_path?`<a class="btn btn-xs btn-g" href="/api/promocion/actividades/${Number(a.id)}/evidencia" target="_blank" rel="noopener">Principal</a>`:'—';
    const btn=`<button type="button" class="btn btn-xs btn-i" onclick="openPromDet(${Number(a.id)})">Abrir</button>`;
    return `<tr>
      <td>${escHtml(a.fecha||'—')}</td>
      <td><strong>${escHtml(a.titulo||'—')}</strong><div class="mut">${escHtml(a.lugar||'')}</div></td>
      <td style="font-size:11px">${escHtml(promTemaLbl(a.tema))}</td>
      <td style="font-size:11px">${escHtml(_promPublicoLbl(a))}${curso?`<div class="mut">${escHtml(curso)}</div>`:''}</td>
      <td style="font-size:11px">${escHtml(a.creado_por_nombre||'—')} <span class="mut">(${escHtml(a.creado_por_rol||'')})</span></td>
      <td style="font-size:11px">${ev}</td>
      <td style="width:80px">${btn}</td>
    </tr>`;
  }).join('');
}

async function promAplicarFiltros(){
  const tb=document.getElementById('promListBody');
  if(!tb)return;
  tb.innerHTML='<tr><td colspan="7" class="mut">Cargando…</td></tr>';
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
  const j=await r.json().catch(()=>({}));
  if(j.ok){toast('Actividad guardada');renderCurrentTab();}
  else{if(err)err.textContent=j.error||'Error';toast(j.error||'Error','e');}
}
async function renderPromocion(tab){
  const rows=await _promFetchList();
  const hoy=new Date().toISOString().slice(0,10);
  tab.innerHTML=`
    <div class="abanner ab-i" style="font-size:11px;line-height:1.45">
      Actividades de <strong>Promoción</strong> en convivencia (planeación, público objetivo y evidencias). No visible para acudientes ni estudiantes.
    </div>
    <div class="card">
      <div class="ch"><h3>Crear actividad</h3></div>
      <div class="mb" style="padding:12px 14px;max-width:780px">
        <div class="fr">
          <div style="flex:2"><label class="fl">Título *</label><input id="promTit" maxlength="120" placeholder="Ej: Taller de gestión emocional"></div>
          <div><label class="fl">Tema *</label>
            <select id="promTema"><option value="">Seleccionar</option>${PROM_TEMAS.map(t=>`<option value="${t.v}">${t.l}</option>`).join('')}</select>
          </div>
        </div>
        <div class="fr" style="margin-top:10px">
          <div><label class="fl">Fecha *</label><input type="date" id="promFecha" value="${hoy}"></div>
          <div style="flex:2"><label class="fl">Lugar</label><input id="promLugar" maxlength="120" placeholder="Ej: Biblioteca / Patio / Aula 203"></div>
        </div>
        <div class="fr" style="margin-top:10px">
          <div style="flex:2"><label class="fl">Recursos</label><input id="promRec" maxlength="240" placeholder="Ej: Proyector, cartillas, parlante"></div>
          <div><label class="fl">Público objetivo *</label>
            <select id="promPub" onchange="promPubChanged()">
              <option value="colegio">Todo el colegio</option>
              <option value="curso">Un curso</option>
              <option value="estudiantes">Estudiantes seleccionados</option>
            </select>
          </div>
        </div>
        <div id="promPubCursoRow" class="fr" style="margin-top:10px;display:none">
          <div><label class="fl">Curso</label><select id="promCurso"><option value="">Seleccionar</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}</select></div>
        </div>
        <div id="promPubEstRow" style="margin-top:10px;display:none">
          <div class="fr">
            <div><label class="fl">Curso base</label><select id="promEstCurso" onchange="promLoadEstSel()"><option value="">Seleccionar</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}</select></div>
            <div style="flex:2"><label class="fl">Estudiantes (marcar varios)</label><div id="promEstPick" class="mut">Seleccione curso</div></div>
          </div>
        </div>
        <div style="margin-top:10px"><label class="fl">Descripción / planeación</label><textarea id="promDesc" rows="3" placeholder="Objetivo, actividades, responsables, logística…"></textarea></div>
        <div class="fr" style="margin-top:10px">
          <div style="flex:2"><label class="fl">Evidencia (opcional)</label><input type="file" id="promEvid" accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"></div>
        </div>
        <p class="ferr" id="promErr" style="font-size:12px;margin-top:6px"></p>
        <button type="button" class="btn btn-p" onclick="promCrear()">Guardar actividad</button>
      </div>
    </div>
    <div class="card">
      <div class="ch"><h3>Actividades registradas</h3><button type="button" class="btn btn-xs" onclick="promAplicarFiltros()">Actualizar</button></div>
      <div class="mb" style="padding:10px 14px">
        <div class="fr" style="align-items:flex-end">
          <div><label class="fl">Tema</label><select id="promFTema" onchange="promAplicarFiltros()"><option value="">Todos</option>${PROM_TEMAS.map(t=>`<option value="${t.v}">${t.l}</option>`).join('')}</select></div>
          <div><label class="fl">Desde</label><input type="date" id="promFDesde" onchange="promAplicarFiltros()"></div>
          <div><label class="fl">Hasta</label><input type="date" id="promFHasta" onchange="promAplicarFiltros()"></div>
          <div><label class="fl">Público</label><select id="promFPub" onchange="promAplicarFiltros()">
            <option value="">Todos</option><option value="colegio">Colegio</option><option value="curso">Curso</option><option value="estudiantes">Estudiantes</option>
          </select></div>
          <div><label class="fl">Curso</label><select id="promFCurso" onchange="promAplicarFiltros()"><option value="">Todos</option>${CURSOS.map(c=>`<option value="${c}">${c}</option>`).join('')}</select></div>
          <div><label class="fl">Creador (id)</label><input id="promFCreador" placeholder="Ej: ${CU.id||''}" style="max-width:120px" oninput="this.value=this.value.replace(/\\D/g,'');"></div>
          <div><button type="button" class="btn btn-xs" onclick="promAplicarFiltros()">Filtrar</button></div>
        </div>
        <div class="mut" style="margin-top:6px;font-size:11px">Tip: “Curso” filtra tanto actividades por curso como por estudiantes (si el curso fue seleccionado al escoger estudiantes).</div>
      </div>
      <div class="table-wrap mb" style="padding:0 8px 12px">
        <table>
          <thead><tr><th style="width:92px">Fecha</th><th>Título</th><th style="width:18%">Tema</th><th style="width:18%">Público</th><th style="width:14%">Registró</th><th style="width:92px">Evid.</th><th style="width:80px"></th></tr></thead>
          <tbody id="promListBody">${_promTblRows(rows)}</tbody>
        </table>
      </div>
    </div>`;
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
  const j=await r.json().catch(()=>({}));
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
