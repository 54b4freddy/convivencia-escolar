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


def _plantilla_ie_linea(col: dict) -> str:
    nom = (col.get("nombre") or "Institución educativa").strip()
    mun = (col.get("municipio") or "—").strip()
    nit = (col.get("nit") or "—").strip()
    return f"{nom} · {mun}  |  NIT {nit}"


def generar_pdf_plantilla_acta_descargos_vacia(col: dict):
    """Plantilla en blanco: acta de descargos (estudiante) — Art. 29 C.P., Ley 1620/2013."""
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
    nom_ie = col.get("nombre") or "Institución educativa"
    els = []
    pdf_cabecera(
        els,
        e,
        nom_ie,
        "ACTA DE DESCARGOS",
        "Versión del estudiante · Art. 29 C.P. · Ley 1620/2013 · Plantilla en blanco (llenar a mano y escanear)",
    )
    els.append(Paragraph(f"<b>{_esc_para(_plantilla_ie_linea(col))}</b>", e["S"]))
    els.append(Spacer(1, 8))
    els.append(
        Paragraph(
            "N.º Registro en sistema: _______________________ &nbsp;&nbsp; Fecha: ____________ &nbsp;&nbsp; Hora: ____________",
            e["N"],
        )
    )
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "<b>Derecho al debido proceso:</b> el estudiante conoce los hechos que se le atribuyen, puede expresarse "
            "libremente y sus descargos serán valorados antes de cualquier sanción. (Art. 29 C.P. · Decreto 1965/2013 Art. 40)",
            e["Sm"],
        )
    )
    els.append(Spacer(1, 10))
    els.append(Paragraph("<b>1. Conocimiento de los hechos</b>", e["H"]))
    els.append(Paragraph("El estudiante fue informado de los hechos registrados en el sistema &nbsp; ☐ Sí &nbsp; ☐ No", e["N"]))
    els.append(Paragraph("¿Desea expresar su versión? &nbsp; ☐ Sí &nbsp; ☐ No", e["N"]))
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>2. Versión libre del estudiante</b>", e["H"]))
    els.append(Paragraph("<i>Escribir con las propias palabras del estudiante. No editar ni resumir.</i>", e["Sm"]))
    for _ in range(10):
        els.append(Paragraph("_" * 92, e["Sm"]))
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>3. Actitud frente a los hechos</b>", e["H"]))
    els.append(
        Paragraph(
            "☐ Reconoce los hechos &nbsp; ☐ Los niega &nbsp; ☐ Los reconoce parcialmente &nbsp; ☐ No desea pronunciarse",
            e["N"],
        )
    )
    els.append(Paragraph("¿Solicita alguna consideración especial? &nbsp; ☐ No &nbsp; ☐ Sí — Cuál: _______________________________", e["N"]))
    els.append(Paragraph("¿El estudiante se negó a firmar? &nbsp; ☐ No &nbsp; ☐ Sí — Constancia: _______________________________", e["N"]))
    els.append(Spacer(1, 14))
    sig_style = ParagraphStyle("plSig", parent=e["Sm"], fontSize=8, alignment=TA_CENTER, textColor=COLS["mut"])
    sig = Table(
        [
            [
                Paragraph("_______________________________<br/><b>Estudiante</b><br/>Nombre: _________________<br/>C.C./T.I.: _______________", sig_style),
                Paragraph("_______________________________<br/><b>Docente / Directivo</b><br/>Nombre: _________________<br/>C.C./T.I.: _______________", sig_style),
            ],
        ],
        colWidths=[8.25 * cm, 8.25 * cm],
    )
    sig.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 10), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    els.append(sig)
    els.append(Spacer(1, 10))
    els.append(
        Paragraph(
            "Adjuntar al registro N.° _______ en el sistema · " + _esc_para(nom_ie) + " · Manual de convivencia",
            e["Sm"],
        )
    )
    doc.build(els)
    buf.seek(0)
    return buf


def generar_pdf_plantilla_acta_sesion_vacia(col: dict):
    """Plantilla en blanco: acta de sesión (Comité / acudientes / directivos) — Ley 1620/2013."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        leftMargin=1.3 * cm,
        rightMargin=1.3 * cm,
    )
    e = E()
    nom_ie = col.get("nombre") or "Institución educativa"
    els = []
    pdf_cabecera(
        els,
        e,
        nom_ie,
        "ACTA DE SESIÓN",
        "Comité de Convivencia / Reunión con padres y directivos · Ley 1620/2013 · Plantilla en blanco",
    )
    els.append(Paragraph(f"<b>{_esc_para(_plantilla_ie_linea(col))}</b>", e["S"]))
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "N.º Registro en sistema: _______________________ &nbsp;&nbsp; Fecha: ____________ &nbsp;&nbsp; Hora: ____________",
            e["N"],
        )
    )
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>1. Tipo de sesión</b>", e["H"]))
    els.append(
        Paragraph(
            "☐ Ordinaria del Comité &nbsp; ☐ Extraordinaria del Comité &nbsp; ☐ Reunión con acudiente y estudiante &nbsp; ☐ Otra: ___________________",
            e["Sm"],
        )
    )
    els.append(
        Paragraph(
            "Situación vinculada: &nbsp; ☐ Tipo I &nbsp; ☐ Tipo II &nbsp; ☐ Tipo III &nbsp;&nbsp; Acta de descargos N.°: _______",
            e["Sm"],
        )
    )
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>2. Asistentes y firmas</b>", e["H"]))
    els.append(
        Paragraph(
            "La firma certifica participación y conocimiento de los acuerdos. Quórum: mayoría simple de los integrantes del Comité.",
            e["Sm"],
        )
    )
    hdr = ["Nombre completo", "Rol", "Firma", "Asistió"]
    rows = [[Paragraph(f"<b>{h}</b>", e["Sm"]) for h in hdr]]
    for _ in range(6):
        rows.append([Paragraph("", e["Sm"]) for _ in hdr])
    at = Table(rows, colWidths=[5.5 * cm, 3.2 * cm, 4.5 * cm, 2.8 * cm])
    at.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1eb")),
                ("MINROWHEIGHT", (0, 1), (-1, -1), 18),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    els.append(at)
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "Total asistentes: _______ &nbsp;&nbsp; ¿Hay quórum? &nbsp; ☐ Sí &nbsp; ☐ No &nbsp;&nbsp; Hora inicio: _______ &nbsp;&nbsp; Fin: _______",
            e["N"],
        )
    )
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>3. Acuerdos y compromisos</b>", e["H"]))
    els.append(
        Paragraph(
            "Solo registrar lo acordado en esta reunión. Los antecedentes, hechos y seguimiento quedan en el sistema. "
            "Las medidas deben ser pedagógicas y proporcionales (Ley 1620/2013 Art. 22).",
            e["Sm"],
        )
    )
    h2 = ["Compromiso / Acción", "Responsable", "Fecha límite"]
    rows2 = [[Paragraph(f"<b>{h}</b>", e["Sm"]) for h in h2]]
    for _ in range(5):
        rows2.append([Paragraph("", e["Sm"]) for _ in h2])
    t2 = Table(rows2, colWidths=[8.5 * cm, 4.5 * cm, 3.5 * cm])
    t2.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, COLS["brd"]),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1eb")),
                ("MINROWHEIGHT", (0, 1), (-1, -1), 20),
            ]
        )
    )
    els.append(t2)
    els.append(Spacer(1, 8))
    els.append(Paragraph("<b>4. Medida disciplinaria adoptada</b>", e["H"]))
    els.append(
        Paragraph(
            "☐ Amonestación escrita &nbsp; ☐ Acción restaurativa &nbsp; ☐ Suspensión provisional (____ días) &nbsp; ☐ Matrícula en observación",
            e["Sm"],
        )
    )
    els.append(
        Paragraph(
            "☐ Cancelación de cupo año siguiente &nbsp; ☐ Remisión al ICBF / Policía de Infancia &nbsp; ☐ Ninguna",
            e["Sm"],
        )
    )
    els.append(Spacer(1, 4))
    els.append(Paragraph("Reporte SIUCE: ☐ Hecho &nbsp; ☐ Pendiente &nbsp;&nbsp; Notif. ICBF (Tipo III): ☐ Hecho &nbsp; ☐ No aplica", e["Sm"]))
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "¿Algún participante se negó a firmar? &nbsp; ☐ No &nbsp; ☐ Sí — Nombre y razón: _____________________________",
            e["N"],
        )
    )
    els.append(Spacer(1, 6))
    els.append(
        Paragraph(
            "Siendo las ________ horas, se da por cerrada la sesión. &nbsp;&nbsp; Próxima sesión: Fecha ________________ &nbsp; Hora ________",
            e["N"],
        )
    )
    els.append(Spacer(1, 10))
    els.append(
        Paragraph(
            "Adjuntar al registro N.° _______ en el sistema · " + _esc_para(nom_ie) + " · Manual de convivencia",
            e["Sm"],
        )
    )
    doc.build(els)
    buf.seek(0)
    return buf
