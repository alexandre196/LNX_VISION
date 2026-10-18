"""
app/core/report.py
Génère un rapport PDF pour une entité ou pour l'ensemble du réseau.
"""
import io
from datetime import datetime
import networkx as nx
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from app.core.graph_builder import load_graph, get_entity_dict

# ── COULEURS ──────────────────────────────────────────────────────────────────
DARK     = colors.HexColor("#07090f")
DARK2    = colors.HexColor("#0d1117")
DARK3    = colors.HexColor("#1e2d40")
ACCENT   = colors.HexColor("#00d4ff")
RED      = colors.HexColor("#ff3355")
AMBER    = colors.HexColor("#ffaa00")
GREEN    = colors.HexColor("#00ff88")
TEXTC    = colors.HexColor("#c8d8e8")
TEXT2    = colors.HexColor("#6a8aaa")
WHITE    = colors.white

W, H = A4

def risk_color(risk: int):
    if risk >= 75: return RED
    if risk >= 50: return AMBER
    return GREEN

def risk_label(risk: int):
    if risk >= 75: return "ÉLEVÉ"
    if risk >= 50: return "MOYEN"
    return "FAIBLE"

# ── STYLES ────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "title": ParagraphStyle("title",
            fontName="Helvetica-Bold", fontSize=22, textColor=ACCENT,
            spaceAfter=4, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("subtitle",
            fontName="Helvetica", fontSize=10, textColor=TEXT2,
            spaceAfter=16, alignment=TA_LEFT),
        "section": ParagraphStyle("section",
            fontName="Helvetica-Bold", fontSize=12, textColor=ACCENT,
            spaceBefore=16, spaceAfter=8, borderPad=4),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=9, textColor=TEXTC,
            spaceAfter=4, leading=14),
        "small": ParagraphStyle("small",
            fontName="Helvetica", fontSize=8, textColor=TEXT2,
            spaceAfter=2),
        "mono": ParagraphStyle("mono",
            fontName="Courier", fontSize=8, textColor=TEXTC,
            spaceAfter=2),
        "risk_high": ParagraphStyle("risk_high",
            fontName="Helvetica-Bold", fontSize=28, textColor=RED,
            alignment=TA_CENTER),
        "risk_med": ParagraphStyle("risk_med",
            fontName="Helvetica-Bold", fontSize=28, textColor=AMBER,
            alignment=TA_CENTER),
        "risk_low": ParagraphStyle("risk_low",
            fontName="Helvetica-Bold", fontSize=28, textColor=GREEN,
            alignment=TA_CENTER),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=7, textColor=TEXT2,
            alignment=TA_CENTER),
    }

# ── BACKGROUND ────────────────────────────────────────────────────────────────
def draw_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK2)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Header bar
    canvas.setFillColor(DARK)
    canvas.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    # Footer bar
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    # Accent line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(0, H - 18*mm, W, H - 18*mm)
    # Header text
    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(ACCENT)
    canvas.drawString(15*mm, H - 12*mm, "LNX.VISION")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT2)
    canvas.drawRightString(W - 15*mm, H - 12*mm,
        f"CONFIDENTIEL · {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC")
    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT2)
    canvas.drawCentredString(W/2, 4*mm,
        f"LNX Vision Platform · Document généré automatiquement · Page {doc.page}")
    canvas.restoreState()

# ── RAPPORT ENTITÉ ────────────────────────────────────────────────────────────
def generate_entity_report(entity_id: str) -> bytes:
    G = load_graph()
    if entity_id not in G:
        raise ValueError(f"Entité '{entity_id}' introuvable")

    data = dict(G.nodes[entity_id])
    risk = data.get("risk", 0)
    s = make_styles()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=22*mm, bottomMargin=14*mm)

    story = []

    # ── TITRE
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("RAPPORT D'ANALYSE", s["subtitle"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(data.get("name", entity_id), s["title"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"{entity_id}  ·  {data.get('type','—')}  ·  {data.get('ville','—')}",
        s["subtitle"]))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=DARK3, spaceAfter=10))

    # ── SCORE DE RISQUE
    story.append(Paragraph("SCORE DE RISQUE", s["section"]))
    rc = risk_color(risk)
    story.append(Paragraph(
        f'<font size="32" color="{rc.hexval()}">{risk}</font>'
        f'<font size="14" color="#6a8aaa">  /100  </font>'
        f'<font size="14" color="{rc.hexval()}"><b>{risk_label(risk)}</b></font>',
        ParagraphStyle("riskscore", fontName="Helvetica", fontSize=14,
            backColor=DARK, borderPad=10, leading=44,
            leftIndent=10, spaceAfter=12)
    ))
    story.append(Spacer(1, 4*mm))

    # ── ATTRIBUTS
    story.append(Paragraph("INFORMATIONS", s["section"]))
    skip = {"name","type","risk","lat","lon"}
    attr_rows = [
        [Paragraph(k.upper(), s["small"]), Paragraph(str(v), s["body"])]
        for k, v in data.items() if k not in skip and v is not None
    ]
    if attr_rows:
        attr_table = Table(attr_rows, colWidths=[45*mm, 120*mm])
        attr_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), DARK),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [DARK, DARK2]),
            ("TEXTCOLOR", (0,0), (0,-1), TEXT2),
            ("TEXTCOLOR", (1,0), (1,-1), TEXTC),
            ("BOX", (0,0), (-1,-1), 0.5, DARK3),
            ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(attr_table)

    # ── CONNEXIONS
    story.append(Paragraph("CONNEXIONS DIRECTES", s["section"]))
    neighbors = list(G.neighbors(entity_id))
    if neighbors:
        conn_rows = [
            [Paragraph("ENTITÉ", s["small"]), Paragraph("RELATION", s["small"]),
             Paragraph("FORCE", s["small"]), Paragraph("RISQUE", s["small"])]
        ]
        for n in neighbors:
            nd = dict(G.nodes[n])
            edge = G.get_edge_data(entity_id, n, default={})
            nr = nd.get("risk",0)
            nc = risk_color(nr)
            conn_rows.append([
                Paragraph(nd.get("name", n), s["body"]),
                Paragraph(edge.get("relation","—"), s["body"]),
                Paragraph(f"{int(edge.get('force',0)*100)}%", s["body"]),
                Paragraph(str(nr), ParagraphStyle("cr",
                    fontName="Helvetica-Bold", fontSize=9, textColor=nc)),
            ])
        conn_table = Table(conn_rows, colWidths=[55*mm, 65*mm, 20*mm, 20*mm])
        conn_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, DARK2]),
            ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8),
            ("BOX", (0,0), (-1,-1), 0.5, DARK3),
            ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(conn_table)
    else:
        story.append(Paragraph("Aucune connexion directe.", s["body"]))

    # ── ANALYSE RÉSEAU
    story.append(Paragraph("ANALYSE RÉSEAU", s["section"]))
    degree = G.degree(entity_id)
    try:
        centrality = nx.betweenness_centrality(G).get(entity_id, 0)
    except:
        centrality = 0

    net_rows = [
        [Paragraph("DEGRÉ DE CONNEXION", s["small"]), Paragraph(str(degree), s["body"])],
        [Paragraph("CENTRALITÉ (betweenness)", s["small"]), Paragraph(f"{centrality:.3f}", s["body"])],
        [Paragraph("COMMUNAUTÉ", s["small"]), Paragraph(data.get("type","—"), s["body"])],
    ]
    net_table = Table(net_rows, colWidths=[65*mm, 100*mm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [DARK, DARK2]),
        ("TEXTCOLOR", (0,0), (0,-1), TEXT2),
        ("BOX", (0,0), (-1,-1), 0.5, DARK3),
        ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(net_table)

    # ── TIMELINE ──────────────────────────────────────────────────────────────
    from app.core.graph_builder import load_events
    events = load_events().get(entity_id, [])
    if events:
        story.append(Paragraph("CHRONOLOGIE DES ACTIVITES", s["section"]))
        type_colors = {
            "Deplacement":  colors.HexColor("#00d4ff"),
            "Contact":      colors.HexColor("#ffaa00"),
            "Transaction":  colors.HexColor("#ff3355"),
            "Surveillance": colors.HexColor("#c084fc"),
            "Incident":     colors.HexColor("#ff6b35"),
        }
        ev_rows = [
            [Paragraph("DATE", s["small"]), Paragraph("TYPE", s["small"]),
             Paragraph("DESCRIPTION", s["small"]), Paragraph("LIEU", s["small"])]
        ]
        for ev in events:
            tc = type_colors.get(ev.get("type",""), TEXT2)
            ev_rows.append([
                Paragraph(ev.get("date","—"), s["mono"]),
                Paragraph(ev.get("type","—"), ParagraphStyle("et",
                    fontName="Helvetica-Bold", fontSize=8, textColor=tc)),
                Paragraph(ev.get("description","—"), s["body"]),
                Paragraph(ev.get("lieu","—"), s["small"]),
            ])
        ev_table = Table(ev_rows, colWidths=[22*mm, 24*mm, 95*mm, 24*mm], repeatRows=1)
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, DARK2]),
            ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8),
            ("BOX", (0,0), (-1,-1), 0.5, DARK3),
            ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(ev_table)

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    return buf.getvalue()


# ── RAPPORT GLOBAL ────────────────────────────────────────────────────────────
def generate_global_report() -> bytes:
    G = load_graph()
    entities = [{"id": nid, **data} for nid, data in G.nodes(data=True)]
    entities.sort(key=lambda e: e.get("risk", 0), reverse=True)
    s = make_styles()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=22*mm, bottomMargin=14*mm)

    story = []
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── TITRE
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("RAPPORT D'ANALYSE GLOBAL", s["subtitle"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("NEXUS — Vue d'ensemble du reseau", s["title"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f"Genere le {now} UTC · {len(entities)} entites · {G.number_of_edges()} liens", s["subtitle"]))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=DARK3, spaceAfter=10))

    # ── STATS GLOBALES
    story.append(Paragraph("STATISTIQUES GLOBALES", s["section"]))
    risks = [e.get("risk", 0) for e in entities]
    high_risk = [e for e in entities if e.get("risk",0) >= 75]
    stats_rows = [
        [Paragraph("ENTITÉS TOTALES", s["small"]),      Paragraph(str(len(entities)), s["body"]),
         Paragraph("LIENS ACTIFS", s["small"]),          Paragraph(str(G.number_of_edges()), s["body"])],
        [Paragraph("RISQUE MOYEN", s["small"]),          Paragraph(f"{sum(risks)/len(risks):.1f}/100" if risks else "—", s["body"]),
         Paragraph("RISQUE MAXIMUM", s["small"]),         Paragraph(f"{max(risks)}/100" if risks else "—", s["body"])],
        [Paragraph("ENTITÉS CRITIQUE (≥75)", s["small"]),Paragraph(str(len(high_risk)), s["body"]),
         Paragraph("GRAPHE CONNEXE", s["small"]),         Paragraph("OUI" if nx.is_connected(G) else "NON", s["body"])],
    ]
    stats_table = Table(stats_rows, colWidths=[55*mm, 35*mm, 55*mm, 35*mm])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [DARK, DARK2, DARK]),
        ("TEXTCOLOR", (0,0), (0,-1), TEXT2),
        ("TEXTCOLOR", (2,0), (2,-1), TEXT2),
        ("BOX", (0,0), (-1,-1), 0.5, DARK3),
        ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(stats_table)

    # ── TABLEAU ENTITÉS
    story.append(Paragraph("TOUTES LES ENTITÉS (triées par risque)", s["section"]))
    header = [
        Paragraph("ID", s["small"]), Paragraph("NOM", s["small"]),
        Paragraph("TYPE", s["small"]), Paragraph("VILLE", s["small"]),
        Paragraph("STATUT", s["small"]), Paragraph("RISQUE", s["small"]),
    ]
    rows = [header]
    for e in entities:
        r = e.get("risk", 0)
        rc = risk_color(r)
        rows.append([
            Paragraph(e["id"], s["mono"]),
            Paragraph(e.get("name","—"), s["body"]),
            Paragraph(e.get("type","—"), s["small"]),
            Paragraph(e.get("ville","—"), s["small"]),
            Paragraph(e.get("statut","—"), s["small"]),
            Paragraph(str(r), ParagraphStyle("rc",
                fontName="Helvetica-Bold", fontSize=9, textColor=rc)),
        ])

    ent_table = Table(rows, colWidths=[18*mm, 48*mm, 28*mm, 28*mm, 28*mm, 18*mm])
    ent_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, DARK2]),
        ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("BOX", (0,0), (-1,-1), 0.5, DARK3),
        ("INNERGRID", (0,0), (-1,-1), 0.3, DARK3),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(ent_table)

    # ── ALERTES
    if high_risk:
        story.append(PageBreak())
        story.append(Paragraph("ALERTES — ENTITÉS À RISQUE ÉLEVÉ", s["section"]))
        for e in high_risk:
            story.append(Paragraph(
                f"<b>{e.get('name','—')}</b> ({e['id']}) · Risque {e.get('risk',0)}/100 · {e.get('statut','—')} · {e.get('ville','—')}",
                ParagraphStyle("alert", fontName="Helvetica", fontSize=9,
                    textColor=RED, spaceAfter=4, borderPad=4,
                    backColor=DARK, borderColor=DARK3, borderWidth=0.5)
            ))

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    return buf.getvalue()