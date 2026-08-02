#!/usr/bin/env python3
"""Génère le Passeport de l'Explorateur du Québec en PDF (imprimable A4),
à partir des mêmes fichiers JSON que la PWA (source unique de contenu).

Usage:
    python3 pdf/generate_pdf.py
Produit:
    pdf/passeport-explorateur.html   (page imprimable, source du PDF)
    pdf/Passeport-Explorateur-du-Quebec.pdf   (si Google Chrome est disponible)
"""
import json
import os
import subprocess
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "src", "data")
OUT_HTML = os.path.join(ROOT, "pdf", "passeport-explorateur.html")
OUT_PDF = os.path.join(ROOT, "pdf", "Passeport-Explorateur-du-Quebec.pdf")

STOP_FILES = [
    "etape-1-montreal.json",
    "etape-2-mauricie.json",
    "etape-3-lac-saint-jean.json",
    "etape-4-fjord-saguenay.json",
    "etape-5-tadoussac.json",
    "etape-6-quebec.json",
]

MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def esc(s):
    return htmllib.escape(str(s), quote=True)


def fmt_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MOIS[int(m) - 1]}"


def fmt_dates(dates):
    return f"{fmt_date(dates['debut'])} → {fmt_date(dates['fin'])} · {dates['duree']}"


def load_stops():
    stops = []
    for f in STOP_FILES:
        with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fh:
            stops.append(json.load(fh))
    stops.sort(key=lambda s: s["ordre"])
    return stops


def activity_html(a):
    t = a["type"]
    out = [f'<div class="pdf-activity"><h4>{"🎮"} {esc(a["titre"])}</h4><p class="consigne">{esc(a["consigne"])}</p>']
    d = a["donnees"]
    if t == "chercheEtTrouve":
        out.append('<ul class="pdf-checklist">')
        for it in d["items"]:
            out.append(f'<li><span class="box"></span>{esc(it)}</li>')
        out.append("</ul>")
    elif t == "bingo":
        out.append('<div class="pdf-bingo">')
        for c in d["cases"]:
            out.append(f'<div class="pdf-bingo-cell">{esc(c)}</div>')
        out.append("</div>")
    elif t == "vraiFaux":
        for q in d["questions"]:
            out.append(
                f'<div class="pdf-vf"><p class="affirmation">{esc(q["affirmation"])} '
                f'<span class="choice">☐ Vrai &nbsp; ☐ Faux</span></p>'
                f'<p class="explication">→ {esc(q["explication"])}</p></div>'
            )
    elif t == "quiz":
        for q in d["questions"]:
            choices = " &nbsp;&nbsp; ".join(f"☐ {esc(c)}" for c in q["choix"])
            out.append(
                f'<div class="pdf-vf"><p class="affirmation">{esc(q["question"])}</p>'
                f'<p class="choice">{choices}</p>'
                f'<p class="explication">→ {esc(q["explication"])}</p></div>'
            )
    elif t == "enigme":
        out.append(
            f'<div class="pdf-enigme"><p class="indice">💡 Indice : {esc(d["indice"])}</p>'
            f'<p class="reponse-flip">{esc(d["reponse"])}</p>'
            f'<p class="flip-note">(réponse à l\'envers — tourne le passeport !)</p></div>'
        )
    elif t == "motsMeles":
        out.append('<div class="pdf-grid">')
        for row in d["grille"]:
            out.append('<div class="pdf-grid-row">' + "".join(f'<span>{ch}</span>' for ch in row) + "</div>")
        out.append("</div>")
        out.append('<p class="mots-list">' + " · ".join(esc(w) for w in d["mots"]) + "</p>")
    elif t == "dessine":
        out.append('<div class="pdf-drawbox"></div>')
    out.append("</div>")
    return "".join(out)


def planned_item_html(a):
    label = esc(a["nom"])
    if a.get("details"):
        label += " — " + esc(a["details"])
    return f'<div class="pdf-planned-item"><b>{label}</b><p>{esc(a["description"])}</p></div>'


def stop_pages(s):
    badge = s["badge"]
    left = f"""
    <section class="pdf-page">
      <div class="pdf-page-header" style="--c:{badge['couleur']}">
        <div class="pdf-badge">{badge['emoji']}</div>
        <div>
          <div class="pdf-order">Étape {s['ordre']}</div>
          <h2>{esc(s['ville'])}</h2>
          <div class="pdf-dates">{esc(fmt_dates(s['dates']))}</div>
        </div>
        <div class="pdf-stamp-box">
          <div class="pdf-stamp-circle">{badge['emoji']}</div>
          <div class="pdf-stamp-label">Tampon</div>
        </div>
      </div>
      <p class="pdf-accroche">{esc(s['accroche'])}</p>

      <div class="pdf-two-col">
        <div class="pdf-box"><b>Où on est</b><p>{esc(s['carnet']['ouOnEst'])}</p></div>
        <div class="pdf-box"><b>À quoi ça ressemble</b><p>{esc(s['carnet']['aQuoiCaRessemble'])}</p></div>
      </div>

      <h3>📖 Histoire &amp; culture</h3>
      {''.join(f'<p class="anecdote"><b>{esc(h["titre"])}.</b> {esc(h["texte"])}</p>' for h in s['histoire'])}
      <p class="anecdote"><b>{esc(s['culture']['titre'])}.</b> {esc(s['culture']['texte'])}</p>

      <h3>🍴 Spécialité : {esc(s['specialite']['nom'])}</h3>
      <p>{esc(s['specialite']['texte'])}</p>
      <p class="a-gouter">À goûter : {' · '.join(esc(x) for x in s['specialite']['aGouter'])}</p>
    </section>
    """

    right = f"""
    <section class="pdf-page">
      <h3>📍 À ne pas manquer</h3>
      <div class="pdf-poi-grid">
        {''.join(f'<div class="pdf-poi"><b>{poi["emoji"]} {esc(poi["nom"])}</b><p>{esc(poi["texte"])}</p></div>' for poi in s['pointsInteret'])}
      </div>

      <div class="pdf-mot">
        <div class="mot">{esc(s['motQuebecois']['mot'])}</div>
        <div>{esc(s['motQuebecois']['signification'])}</div>
        <div class="ex">💬 {esc(s['motQuebecois']['exemple'])}</div>
        <div class="ex">🇫🇷 {esc(s['motQuebecois']['clinDoeil'])}</div>
      </div>

      <h3>🎮 À toi de jouer !</h3>
      {''.join(activity_html(a) for a in s['activites'])}

      <div class="pdf-filrouge">🇫🇷⇄🇨🇦 {esc(s['filRouge'])}</div>

      <div class="pdf-photo-box">
        <div class="pdf-photo-placeholder">Colle ta photo souvenir ici 📸</div>
      </div>
    </section>
    """

    planned = ""
    if s.get("activitesPrevues"):
        items = "".join(planned_item_html(a) for a in s["activitesPrevues"])
        planned = f"""
    <section class="pdf-page">
      <div class="pdf-page-header" style="--c:{badge['couleur']}">
        <div class="pdf-badge">{badge['emoji']}</div>
        <div>
          <div class="pdf-order">Étape {s['ordre']}</div>
          <h2>{esc(s['ville'])}</h2>
        </div>
      </div>
      <h3>🗓️ Nos activités prévues</h3>
      {items}
    </section>
    """

    return left + right + planned


def cover_page():
    return """
    <section class="pdf-page pdf-cover">
      <div class="cover-flags">🇫🇷 ⇄ 🇨🇦</div>
      <h1>Passeport de<br>l'Explorateur<br>du Québec</h1>
      <p class="cover-sub">Un carnet de voyage à tamponner, étape après étape,<br>de Montréal jusqu'à Québec.</p>
      <div class="cover-field">Ce passeport appartient à :<br><span class="line"></span></div>
      <div class="cover-field">Voyage du 13 au 28 août 2026</div>
    </section>
    """


def recap_page(stops):
    badges = "".join(
        f'<div class="recap-badge" style="--c:{s["badge"]["couleur"]}"><div class="circle">{s["badge"]["emoji"]}</div><div class="name">{esc(s["ville"])}</div></div>'
        for s in stops
    )
    return f"""
    <section class="pdf-page pdf-recap">
      <h1>🏅 Mes badges d'explorateur</h1>
      <div class="recap-grid">{badges}</div>
      <p class="cover-sub">Quand les 6 tampons sont collés, tu es officiellement...</p>
      <h2 class="confirm">Explorateur du Québec confirmé !</h2>
      <div class="cover-field">Signature de l'explorateur :<br><span class="line"></span></div>
    </section>
    """


CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Arial, sans-serif; color: #2B2118; margin: 0; }
.pdf-page {
  page-break-after: always;
  padding: 4mm 2mm;
}
.pdf-page:last-child { page-break-after: auto; }
h1 { font-size: 26pt; margin: 0 0 8pt; }
h2 { font-size: 18pt; margin: 0; }
h3 { font-size: 12.5pt; margin: 10pt 0 3pt; color: #E4572E; }
h4 { font-size: 10.5pt; margin: 8pt 0 2pt; }
p { font-size: 9pt; line-height: 1.32; margin: 2pt 0 5pt; }

.pdf-cover { text-align: center; padding-top: 40mm; }
.cover-flags { font-size: 28pt; margin-bottom: 6pt; }
.cover-sub { font-size: 11pt; color: #5A4A3A; margin-bottom: 24pt; }
.cover-field { font-size: 11pt; margin-top: 18pt; }
.cover-field .line { display: inline-block; width: 100%; border-bottom: 1px solid #999; margin-top: 10pt; height: 14pt; }

.pdf-page-header { display: flex; align-items: center; gap: 10pt; border-bottom: 3px solid var(--c, #F4A93B); padding-bottom: 8pt; }
.pdf-badge { font-size: 26pt; width: 46pt; height: 46pt; border-radius: 50%; border: 2px solid var(--c, #F4A93B); display: flex; align-items: center; justify-content: center; flex: none; }
.pdf-order { font-size: 8pt; text-transform: uppercase; color: #5A4A3A; letter-spacing: .05em; }
.pdf-dates { font-size: 9pt; color: #5A4A3A; }
.pdf-page-header > div:nth-child(2) { flex: 1; }
.pdf-stamp-box { text-align: center; }
.pdf-stamp-circle { width: 40pt; height: 40pt; border: 2px dashed #999; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16pt; opacity: .35; }
.pdf-stamp-label { font-size: 7pt; color: #999; }
.pdf-accroche { font-style: italic; color: #5A4A3A; margin-top: 6pt; }

.pdf-two-col { display: flex; gap: 8pt; margin: 8pt 0; }
.pdf-box { flex: 1; background: #FFF1D6; border-radius: 8pt; padding: 6pt 8pt; }
.pdf-box b { display: block; font-size: 7.5pt; text-transform: uppercase; color: #5A4A3A; margin-bottom: 2pt; }

.anecdote { }
.a-gouter { font-size: 9pt; font-style: italic; color: #5A4A3A; }

.pdf-poi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6pt; }
.pdf-poi { background: #FFF1D6; border-radius: 8pt; padding: 6pt 8pt; }
.pdf-poi p { margin: 2pt 0 0; }

.pdf-planned-item { background: #FFF1D6; border-left: 3px solid #E4572E; border-radius: 6pt; padding: 7pt 10pt; margin-bottom: 7pt; }
.pdf-planned-item b { font-size: 10pt; }
.pdf-planned-item p { margin: 2pt 0 0; font-size: 9pt; }

.pdf-mot { background: #F4A93B; color: #2B2118; border-radius: 10pt; padding: 8pt 10pt; margin: 8pt 0; }
.pdf-mot .mot { font-size: 15pt; font-weight: bold; }
.pdf-mot .ex { font-size: 8.5pt; margin-top: 3pt; }

.pdf-activity { margin-bottom: 8pt; }
.pdf-activity .consigne { font-size: 9pt; color: #5A4A3A; }
.pdf-checklist { list-style: none; margin: 0; padding: 0; columns: 1; }
.pdf-checklist li { font-size: 9.5pt; margin-bottom: 4pt; }
.pdf-checklist .box { display: inline-block; width: 9pt; height: 9pt; border: 1.5px solid #2B2118; margin-right: 6pt; vertical-align: middle; }
.pdf-bingo { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4pt; }
.pdf-bingo-cell { border: 1px solid #ccc; border-radius: 4pt; padding: 6pt; font-size: 8pt; text-align: center; min-height: 28pt; display: flex; align-items: center; justify-content: center; }
.pdf-vf { margin-bottom: 6pt; }
.pdf-vf .affirmation { font-weight: bold; font-size: 9.5pt; margin-bottom: 2pt; }
.pdf-vf .choice { font-size: 9pt; }
.pdf-vf .explication { font-size: 8pt; color: #5A4A3A; font-style: italic; }
.pdf-enigme { background: #FFF1D6; border-radius: 8pt; padding: 8pt; }
.pdf-enigme .indice { font-size: 9pt; }
.pdf-enigme .reponse-flip { transform: rotate(180deg); font-size: 9pt; margin-top: 8pt; }
.pdf-enigme .flip-note { font-size: 7.5pt; color: #999; text-align: center; }
.pdf-grid { display: inline-block; margin-bottom: 4pt; }
.pdf-grid-row { display: flex; }
.pdf-grid-row span { width: 13pt; height: 13pt; display: flex; align-items: center; justify-content: center; font-family: monospace; font-size: 8pt; border: .5px solid #eee; }
.mots-list { font-size: 8.5pt; color: #5A4A3A; }
.pdf-drawbox { border: 1.5px dashed #999; border-radius: 8pt; height: 60mm; }

.pdf-filrouge { font-size: 8.5pt; font-style: italic; background: #FFF1D6; border-left: 4px solid #2E86AB; padding: 6pt 8pt; border-radius: 6pt; margin: 8pt 0; }
.pdf-photo-box { margin-top: 8pt; }
.pdf-photo-placeholder { border: 1.5px dashed #999; border-radius: 8pt; height: 45mm; display: flex; align-items: center; justify-content: center; color: #999; font-size: 9pt; }

.pdf-recap { text-align: center; padding-top: 20mm; }
.recap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14pt; margin: 16pt 0; }
.recap-badge .circle { width: 60pt; height: 60pt; margin: 0 auto 4pt; border-radius: 50%; border: 3px dashed var(--c, #999); display: flex; align-items: center; justify-content: center; font-size: 22pt; opacity: .5; }
.recap-badge .name { font-size: 9pt; }
.confirm { color: #E4572E; }
"""


def build_html(stops):
    body = cover_page()
    for s in stops:
        body += stop_pages(s)
    body += recap_page(stops)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Passeport de l'Explorateur du Québec</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def find_chrome():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def main():
    stops = load_stops()
    html_out = build_html(stops)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"HTML imprimable généré : {OUT_HTML}")

    chrome = find_chrome()
    if chrome:
        subprocess.run([
            chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={OUT_PDF}", f"file://{OUT_HTML}"
        ], check=True)
        print(f"PDF généré : {OUT_PDF}")
    else:
        print("Google Chrome introuvable : ouvre le fichier HTML et utilise 'Imprimer > Enregistrer en PDF'.")


if __name__ == "__main__":
    main()
