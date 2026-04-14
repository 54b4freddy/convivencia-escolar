"""Generación de PDFs (ReportLab) para reportes de curso y estudiante."""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ce_sugerencias import generar_sugerencias

COLS = {
    "hbg": colors.HexColor("#0f0e17"),
    "hfg": colors.HexColor("#c9a84c"),
    "t1b": colors.HexColor("#eafaf1"),
    "t1f": colors.HexColor("#1a7a40"),
    "t2b": colors.HexColor("#fef5e7"),
    "t2f": colors.HexColor("#856c1a"),
    "t3b": colors.HexColor("#fdf2f8"),
    "t3f": colors.HexColor("#8b1a15"),
    "brd": colors.HexColor("#e5e0d8"),
    "mut": colors.HexColor("#888888"),
    "ink": colors.HexColor("#0f0e17"),
}


def ctype(t):
    if t == "Tipo I":
        return COLS["t1b"], COLS["t1f"]
    if t == "Tipo II":
        return COLS["t2b"], COLS["t2f"]
    return COLS["t3b"], COLS["t3f"]


def E():
    ss = getSampleStyleSheet()
    return {
        "T": ParagraphStyle(
            "T",
            parent=ss["Normal"],
            fontSize=15,
            fontName="Helvetica-Bold",
            textColor=COLS["hfg"],
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "S": ParagraphStyle(
            "S",
            parent=ss["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=COLS["mut"],
            spaceAfter=10,
            alignment=TA_CENTER,
        ),
        "H": ParagraphStyle(
            "H",
            parent=ss["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=COLS["ink"],
            spaceBefore=10,
            spaceAfter=4,
        ),
        "N": ParagraphStyle("N", parent=ss["Normal"], fontSize=9, fontName="Helvetica", textColor=COLS["ink"], leading=13),
        "Sm": ParagraphStyle("Sm", parent=ss["Normal"], fontSize=8, fontName="Helvetica", textColor=COLS["mut"], leading=11),
        "Tp": ParagraphStyle("Tp", parent=ss["Normal"], fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER),
    }


def ts_base():
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 0), (-1, 0), COLS["hbg"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLS["hfg"]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf8f4")]),
            ("GRID", (0, 0), (-1, -1), 0.3, COLS["brd"]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def pdf_cabecera(els, e, col_nom, titulo, sub=""):
    tbl = Table(
        [[Paragraph(col_nom, ParagraphStyle("ch", fontSize=13, fontName="Helvetica-Bold", textColor=COLS["hfg"]))]],
        colWidths=[17 * cm],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLS["hbg"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    els.append(tbl)
    els.append(Spacer(1, 8))
    els.append(Paragraph(titulo, e["T"]))
    if sub:
        els.append(Paragraph(sub, e["S"]))
    els.append(HRFlowable(width="100%", thickness=1, color=COLS["brd"]))
    els.append(Spacer(1, 8))


def pdf_resumen_nums(els, faltas, e):
    t1 = sum(1 for f in faltas if f.get("tipo_falta") == "Tipo I")
    t2 = sum(1 for f in faltas if f.get("tipo_falta") == "Tipo II")
    t3 = sum(1 for f in faltas if f.get("tipo_falta") == "Tipo III")

    def nP(n, col):
        return Paragraph(
            str(n),
            ParagraphStyle("n", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=col),
        )

    r = Table(
        [
            [Paragraph("Total", e["Tp"]), Paragraph("Tipo I", e["Tp"]), Paragraph("Tipo II", e["Tp"]), Paragraph("Tipo III", e["Tp"])],
            [nP(len(faltas), COLS["ink"]), nP(t1, COLS["t1f"]), nP(t2, COLS["t2f"]), nP(t3, COLS["t3f"])],
        ],
        colWidths=[4 * cm] * 4,
    )
    r.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLS["hbg"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.5, COLS["brd"]),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, COLS["brd"]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    els.append(r)
    els.append(Spacer(1, 12))


def generar_pdf_curso(col_nombre, curso, anio, faltas):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    e = E()
    els = []
    pdf_cabecera(
        els,
        e,
        col_nombre,
        f"Reporte de Faltas — Curso {curso}",
        f'Año {anio}  ·  Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
    )
    pdf_resumen_nums(els, faltas, e)
    sugs = generar_sugerencias(faltas)
    if sugs:
        els.append(Paragraph("Áreas de mejoramiento sugeridas", e["H"]))
        for s in sugs:
            els.append(Paragraph(f"• {s}", e["N"]))
        els.append(Spacer(1, 10))
    els.append(Paragraph("Detalle de faltas", e["H"]))
    hdrs = ["Fecha", "Estudiante", "Tipo", "Falta específica", "Proceso inicial", "Docente"]
    cw = [2.3 * cm, 4 * cm, 1.6 * cm, 5.2 * cm, 4.5 * cm, 3 * cm]
    data = [hdrs] + [
        [
            f.get("fecha", ""),
            f.get("estudiante", ""),
            f.get("tipo_falta", "").replace("Tipo ", "T"),
            f.get("falta_especifica", ""),
            f.get("proceso_inicial", ""),
            f.get("docente", ""),
        ]
        for f in faltas
    ]
    tbl = Table(data, colWidths=cw, repeatRows=1)
    ts = ts_base()
    for i, f in enumerate(faltas, 1):
        bg, fg = ctype(f.get("tipo_falta", ""))
        ts.add("BACKGROUND", (2, i), (2, i), bg)
        ts.add("TEXTCOLOR", (2, i), (2, i), fg)
        ts.add("FONTNAME", (2, i), (2, i), "Helvetica-Bold")
    tbl.setStyle(ts)
    els.append(tbl)
    els.append(Spacer(1, 16))
    if any(f.get("notas") for f in faltas):
        els.append(Paragraph("Seguimiento del proceso", e["H"]))
        for f in faltas:
            if not f.get("notas"):
                continue
            bg, fg = ctype(f.get("tipo_falta", ""))
            b = [
                Table(
                    [
                        [
                            Paragraph(
                                f.get("estudiante", ""),
                                ParagraphStyle("en", fontSize=9, fontName="Helvetica-Bold", textColor=fg),
                            ),
                            Paragraph(
                                f'{f.get("tipo_falta", "")} · {f.get("fecha", "")}',
                                ParagraphStyle("em", fontSize=8, textColor=COLS["mut"], alignment=TA_RIGHT),
                            ),
                        ]
                    ],
                    colWidths=[10 * cm, 7 * cm],
                ),
                Spacer(1, 2),
            ]
            for nota in str(f["notas"]).split(" | "):
                if nota.strip():
                    b.append(Paragraph(f"• {nota.strip()}", e["Sm"]))
            b.append(Spacer(1, 6))
            els.append(KeepTogether(b))
    doc.build(els)
    buf.seek(0)
    return buf


def generar_pdf_estudiante(col_nombre, nombre_est, faltas, est_info=None):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    e = E()
    els = []
    anios = sorted(set(str(f.get("anio", "")) for f in faltas))
    pdf_cabecera(
        els,
        e,
        col_nombre,
        f"Historial Disciplinar — {nombre_est}",
        f'Período: {" — ".join(anios)}  ·  {datetime.now().strftime("%d/%m/%Y %H:%M")}',
    )
    if est_info:
        idata = [
            [est_info.get("nombre", ""), "Doc:", est_info.get("documento_identidad", "—"), "Curso:", est_info.get("curso", "—")],
            [est_info.get("acudiente", "—"), "Tel:", est_info.get("telefono", "—"), "Disc:", est_info.get("discapacidad", "—")],
        ]
        it = Table(idata, colWidths=[5 * cm, 1.2 * cm, 3.5 * cm, 1.2 * cm, 5.6 * cm])
        it.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, COLS["brd"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        els.append(it)
        els.append(Spacer(1, 10))
    pdf_resumen_nums(els, faltas, e)
    by_year = {}
    for f in faltas:
        by_year.setdefault(str(f.get("anio", "")), []).append(f)
    for anio, flist in sorted(by_year.items()):
        els.append(Paragraph(f"Año {anio}", e["H"]))
        for f in flist:
            bg, fg = ctype(f.get("tipo_falta", ""))
            b = []
            enc = Table(
                [
                    [
                        Paragraph(f.get("tipo_falta", ""), ParagraphStyle("tp", fontSize=8, fontName="Helvetica-Bold", textColor=fg)),
                        Paragraph(
                            f.get("falta_especifica", ""),
                            ParagraphStyle("fp", fontSize=9, fontName="Helvetica-Bold", textColor=COLS["ink"]),
                        ),
                        Paragraph(f.get("fecha", ""), ParagraphStyle("dp", fontSize=8, textColor=COLS["mut"], alignment=TA_RIGHT)),
                    ]
                ],
                colWidths=[2 * cm, 11 * cm, 3.5 * cm],
            )
            enc.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("BOX", (0, 0), (-1, -1), 0.3, COLS["brd"]),
                    ]
                )
            )
            b.append(enc)
            cd = [["Descripción", f.get("descripcion", "")], ["Proceso inicial", f.get("proceso_inicial", "")], ["Docente", f.get("docente", "")]]
            if f.get("protocolo_aplicado"):
                cd.append(["Protocolo", f["protocolo_aplicado"]])
            if f.get("sancion_aplicada"):
                cd.append(["Sanción", f["sancion_aplicada"]])
            ct = Table(cd, colWidths=[3 * cm, 13.5 * cm])
            ct.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("TEXTCOLOR", (0, 0), (0, -1), COLS["mut"]),
                        ("GRID", (0, 0), (-1, -1), 0.3, COLS["brd"]),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            b.append(ct)
            if f.get("notas"):
                b.append(Spacer(1, 2))
                for nota in str(f["notas"]).split(" | "):
                    if nota.strip():
                        b.append(Paragraph(f"  ↳ {nota.strip()}", e["Sm"]))
            b.append(Spacer(1, 6))
            els.append(KeepTogether(b))
    doc.build(els)
    buf.seek(0)
    return buf


def _esc_para(txt):
    t = str(txt or "")
    return escape(t).replace("\n", "<br/>")


def generar_pdf_acta_proceso(col_nombre, f, anotaciones):
    """
    Acta en soporte físico: hecho, actuación del docente y trazabilidad de instancias
    (coordinación, orientación, dirección) según anotaciones registradas.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    e = E()
    cell_style = ParagraphStyle(
        "actaCell",
        parent=e["N"],
        fontSize=8,
        leading=11,
        textColor=COLS["ink"],
    )
    hdr_style = ParagraphStyle(
        "actaHdr",
        parent=e["N"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=COLS["ink"],
    )
    cron_hdr_style = ParagraphStyle(
        "actaCronHdr",
        parent=e["N"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=COLS["hfg"],
    )
    els = []
    sub = (
        f"Elaboración: {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
        f"Registro sistema N.º {f.get('id', '—')}"
    )
    pdf_cabecera(els, e, col_nombre, "ACTA DE REGISTRO Y SEGUIMIENTO DISCIPLINARIO", sub)

    els.append(Paragraph("<b>I. Identificación</b>", e["H"]))
    idata = [
        ["Institución", col_nombre],
        ["Fecha del hecho / registro", str(f.get("fecha", "—"))],
        ["Año lectivo", str(f.get("anio", "—"))],
        ["Estudiante", f.get("estudiante", "—")],
        ["Curso", f.get("curso", "—")],
        ["Docente que registra", f.get("docente", "—")],
    ]
    it = Table(
        [[Paragraph(_esc_para(a), hdr_style), Paragraph(_esc_para(b), cell_style)] for a, b in idata],
        colWidths=[4.2 * cm, 12.3 * cm],
    )
    it.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f1eb")),
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    els.append(it)
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>II. Descripción del hecho</b>", e["H"]))
    els.append(Paragraph(f"<b>Tipo:</b> {_esc_para(f.get('tipo_falta'))}", e["N"]))
    els.append(Paragraph(f"<b>Falta específica:</b> {_esc_para(f.get('falta_especifica'))}", e["N"]))
    els.append(Spacer(1, 4))
    els.append(Paragraph(f"<b>Relato / descripción:</b><br/>{_esc_para(f.get('descripcion'))}", e["N"]))
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>III. Actuación disciplinaria inicial (docente)</b>", e["H"]))
    els.append(Paragraph(_esc_para(f.get("proceso_inicial")), e["N"]))
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>IV. Cronología del proceso — siguientes instancias</b>", e["H"]))
    els.append(
        Paragraph(
            "Cada fila documenta una acción posterior al registro: dirección de grupo, "
            "coordinación, orientación escolar u otros roles autorizados.",
            e["Sm"],
        )
    )
    els.append(Spacer(1, 6))
    cron_hdr = [
        Paragraph(_esc_para("Fecha"), cron_hdr_style),
        Paragraph(_esc_para("Instancia / rol"), cron_hdr_style),
        Paragraph(_esc_para("Responsable"), cron_hdr_style),
        Paragraph(_esc_para("Acción u observación"), cron_hdr_style),
    ]
    cron_rows = [cron_hdr]
    cron_rows.append(
        [
            Paragraph(_esc_para(f.get("fecha", "—")), cell_style),
            Paragraph(_esc_para("Registro inicial"), cell_style),
            Paragraph(_esc_para(f.get("docente", "—")), cell_style),
            Paragraph(
                _esc_para(
                    "Constancia de falta y actuación inmediata. "
                    + (f.get("proceso_inicial") or "")
                ),
                cell_style,
            ),
        ]
    )
    for a in anotaciones or []:
        cron_rows.append(
            [
                Paragraph(_esc_para(a.get("fecha", "—")), cell_style),
                Paragraph(_esc_para(a.get("rol", "—")), cell_style),
                Paragraph(_esc_para(a.get("autor", "—")), cell_style),
                Paragraph(_esc_para(a.get("texto", "—")), cell_style),
            ]
        )
    ct = Table(cron_rows, colWidths=[2.2 * cm, 3.2 * cm, 3.5 * cm, 7.6 * cm], repeatRows=1)
    ct.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLS["hbg"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLS["hfg"]),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, COLS["brd"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf8f4")]),
            ]
        )
    )
    els.append(ct)
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>V. Protocolo y sanción de referencia (catálogo institucional)</b>", e["H"]))
    els.append(Paragraph(f"<b>Protocolo aplicado al registro:</b><br/>{_esc_para(f.get('protocolo_aplicado'))}", e["N"]))
    els.append(Spacer(1, 4))
    els.append(Paragraph(f"<b>Sanción / medida de referencia:</b><br/>{_esc_para(f.get('sancion_aplicada'))}", e["N"]))
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>VI. Constancias (firma manuscrita en copia impresa)</b>", e["H"]))
    els.append(
        Paragraph(
            "Este documento sirve como soporte del proceso disciplinar. "
            "Las firmas tienen valor en la versión impresa y archivada según el manual de convivencia.",
            e["Sm"],
        )
    )
    els.append(Spacer(1, 14))
    sig_style = ParagraphStyle("sig", parent=e["Sm"], fontSize=8, alignment=TA_CENTER, textColor=COLS["mut"])
    sig = Table(
        [
            [
                Paragraph("_______________________________<br/><i>Docente</i>", sig_style),
                Paragraph("_______________________________<br/><i>Director(a) de grupo</i>", sig_style),
            ],
            [
                Paragraph("_______________________________<br/><i>Coordinador(a)</i>", sig_style),
                Paragraph("_______________________________<br/><i>Orientación escolar</i>", sig_style),
            ],
        ],
        colWidths=[8.25 * cm, 8.25 * cm],
    )
    sig.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 18), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    els.append(sig)

    doc.build(els)
    buf.seek(0)
    return buf


def _actitud_txt(act: str) -> str:
    m = {
        "reconoce": "Reconoce los hechos",
        "niega": "Los niega",
        "parcial": "Los reconoce parcialmente",
        "no_pronuncia": "No desea pronunciarse",
    }
    return m.get((act or "").strip().lower(), "—")


def _tri_txt(v):
    if v is True:
        return "Sí"
    if v is False:
        return "No"
    return "—"


def generar_pdf_acta_descargos(col: dict, f: dict, datos: dict, verificacion_url: str):
    """Acta de descargos — versión estudiante (referencia Ley 1620/2013, Art. 29 C.P.)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.1 * cm,
        bottomMargin=1.1 * cm,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
    )
    e = E()
    cell_style = ParagraphStyle(
        "descCell",
        parent=e["N"],
        fontSize=8.5,
        leading=12,
        textColor=COLS["ink"],
    )
    hdr_style = ParagraphStyle(
        "descHdr",
        parent=e["N"],
        fontSize=8.5,
        fontName="Helvetica-Bold",
        textColor=COLS["ink"],
    )
    els = []
    nom_ie = col.get("nombre") or "Institución educativa"
    nit = col.get("nit") or "—"
    mun = col.get("municipio") or "—"
    sub = (
        f"Versión del estudiante · Art. 29 C.P. · Ley 1620/2013 · "
        f"Registro sistema N.º {f.get('id', '—')} · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    pdf_cabecera(els, e, nom_ie, "ACTA DE DESCARGOS", sub)
    els.append(
        Paragraph(
            f"<b>{_esc_para(nom_ie)}</b> · {_esc_para(mun)} · NIT {_esc_para(nit)}",
            e["S"],
        )
    )
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "<b>Derecho al debido proceso:</b> el estudiante conoce los hechos que se le atribuyen, puede expresarse "
            "libremente y sus descargos serán valorados antes de cualquier sanción. "
            "(Art. 29 C.P. · Decreto 1965/2013 Art. 40)",
            e["Sm"],
        )
    )
    fh = f"{datos.get('fecha_acta') or '—'} · Hora: {datos.get('hora_acta') or '—'}"
    meta_rows = [
        [Paragraph("<b>N.º Registro en sistema (falta)</b>", hdr_style), Paragraph(_esc_para(str(f.get("id", "—"))), cell_style)],
        [Paragraph("<b>Fecha y hora del acta</b>", hdr_style), Paragraph(_esc_para(fh), cell_style)],
    ]
    mt = Table(meta_rows, colWidths=[5.5 * cm, 11 * cm])
    mt.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f1eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    els.append(mt)
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>1. Conocimiento de los hechos</b>", e["H"]))
    c1 = [
        ["¿El estudiante fue informado de los hechos registrados en el sistema?", _tri_txt(datos.get("informedado_hechos_si"))],
        ["¿Desea expresar su versión?", _tri_txt(datos.get("desea_version_si"))],
    ]
    t1 = Table(
        [[Paragraph(_esc_para(a), hdr_style), Paragraph(_esc_para(b), cell_style)] for a, b in c1],
        colWidths=[11.5 * cm, 5 * cm],
    )
    t1.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f1eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    els.append(t1)
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>2. Versión libre del estudiante</b>", e["H"]))
    els.append(Paragraph("<i>Escribir con las propias palabras del estudiante. No editar ni resumir.</i>", e["Sm"]))
    els.append(Spacer(1, 4))
    els.append(Paragraph(_esc_para(datos.get("version_estudiante") or "(sin texto registrado)"), e["N"]))
    els.append(Spacer(1, 10))

    els.append(Paragraph("<b>3. Actitud frente a los hechos</b>", e["H"]))
    act_txt = _actitud_txt(datos.get("actitud"))
    cons = "Sí — " + str(datos.get("consideracion_cual") or "") if datos.get("consideracion_si") else "No"
    neg = (
        "Sí — Constancia: " + str(datos.get("constancia_negativa_firma") or "")
        if datos.get("estudiante_se_nego_firmar")
        else "No"
    )
    c3 = [
        ["Actitud declarada", act_txt],
        ["¿Solicita alguna consideración especial?", _esc_para(cons)],
        ["¿El estudiante se negó a firmar?", _esc_para(neg)],
    ]
    t3 = Table(
        [[Paragraph(_esc_para(a), hdr_style), Paragraph(_esc_para(b), cell_style)] for a, b in c3],
        colWidths=[6.5 * cm, 10 * cm],
    )
    t3.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f1eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    els.append(t3)
    els.append(Spacer(1, 14))

    sig_style = ParagraphStyle("descSig", parent=e["Sm"], fontSize=8, alignment=TA_CENTER, textColor=COLS["mut"])
    est_nom = datos.get("estud_nombre") or f.get("estudiante") or "—"
    est_doc = datos.get("estud_doc") or f.get("documento_identidad") or "—"
    doc_nom = datos.get("docente_nombre") or "—"
    doc_doc = datos.get("docente_doc") or "—"
    sig = Table(
        [
            [
                Paragraph(
                    f"<b>Estudiante</b><br/>Nombre: {_esc_para(est_nom)}<br/>C.C./T.I.: {_esc_para(est_doc)}<br/><br/>"
                    "_______________________________",
                    sig_style,
                ),
                Paragraph(
                    f"<b>Docente / directivo</b><br/>Nombre: {_esc_para(doc_nom)}<br/>C.C./T.I.: {_esc_para(doc_doc)}<br/><br/>"
                    "_______________________________",
                    sig_style,
                ),
            ],
        ],
        colWidths=[8.25 * cm, 8.25 * cm],
    )
    sig.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    els.append(sig)
    els.append(Spacer(1, 10))
    pie = (
        f"Adjuntar al registro N.º {f.get('id', '—')} en el sistema · "
        f"Verificación de autenticidad (copie en el navegador): {_esc_para(verificacion_url or '—')}"
    )
    els.append(Paragraph(pie, e["Sm"]))

    doc.build(els)
    buf.seek(0)
    return buf
