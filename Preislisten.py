import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image
import io
from qrbill import QRBill
import cairosvg

st.set_page_config(page_title="Rechnungsgenerator", page_icon=":money_with_wings:", layout="centered")

PRIMARY_COLOR = "#3575D3"
ACCENT_COLOR = "#F7B801"
BG_COLOR = "#F1F4FA"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    .stButton>button {{ color: white; background: {PRIMARY_COLOR}; border-radius:8px; }}
    .stDownloadButton>button {{ color: white; background: {ACCENT_COLOR}; border-radius:8px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("Rechnungsgenerator mit offiziellem Swiss QR")

# Feste Absender- und Empfängeradresse für QR
CREDITOR_ADDR = {
    "name": "Print Brigata",
    "street": "Oberer Deutweg",
    "house_num": "36",
    "pcode": "8400",
    "city": "Winterthur",
    "country": "CH"
}

iban = "CH76 0070 0114 9019 6709 0"  # Deine IBAN, anpassen!

# Kopfbereich
col1, col2 = st.columns([1, 3])
with col1:
    logo_file = st.file_uploader("Firmenlogo (PNG/JPG)", type=["png", "jpg", "jpeg"])
with col2:
    firma_name = st.text_input("Firmenname", "Print Brigata")

# Modus
modus = st.selectbox("Abrechnungsmodus wählen", ["Solidarisch", "Kommerziell"])
if modus == "Kommerziell":
    zuschlag_verbrauch = 0.15
    zuschlag_betrieb = 0.40
    personalkosten = True
else:
    zuschlag_verbrauch = 0.05
    zuschlag_betrieb = 0.10
    personalkosten = False

# Belegtyp und Meta
beleg_typ = st.selectbox("Belegtyp wählen", ["Rechnung", "Angebot", "Lieferschein"])
doc_nr = st.text_input(f"{beleg_typ}-Nummer", f"{date.today().strftime('%Y%m%d')}-01")
doc_date = st.date_input(f"{beleg_typ}-Datum", value=date.today())

# Adressen für PDF-Anzeige (Empfänger im QR bleibt fix)
st.header("Adressen")
adr1, adr2 = st.columns(2)
with adr1:
    sender = st.text_area("Absender (Name, Adresse)", height=80, value=firma_name)
with adr2:
    recipient = st.text_area("Empfänger (Name, Adresse)", height=80, value="")

# Kategorien
farben_data = [
    ("PAPYRO PRINT, Papierfarbe", 37),
    ("Textilfarbe, wasserbasiert", 37),
    ("Plastisolfarbe", 25),
]
kleidung_data = [
    ("T-Shirts", 7),
    ("Pullis", 13),
    ("Longsleeves", 11),
    ("Chäppli", 7),
]
siebe_data = [
    ("Siebbeschichtung A5", 12),
    ("Siebbeschichtung A4", 20),
    ("Siebbeschichtung A3", 25),
    ("Siebbeschichtung A2", 30),
    ("Siebbeschichtung A1", 35),
]
folien_data = [
    ("Folienpreis A5", 5),
    ("Folienpreis A4", 10),
    ("Folienpreis A3", 20),
    ("Folienpreis A2", 30),
    ("Folienpreis A1", 40),
]

kategorien = {
    "Farbe": farben_data,
    "Kleidung": kleidung_data,
    "Siebbeschichtung": siebe_data,
    "Folien": folien_data,
}

# Default-Positionen
default_rows = [
    {"Typ": "Farbe", "Produkt": "PAPYRO PRINT, Papierfarbe", "Gramm": 100, "Menge": 100, "Preis": 37/10},
    {"Typ": "Kleidung", "Produkt": "T-Shirts", "Menge": 1, "Preis": 7, "Gramm": None},
    {"Typ": "Siebbeschichtung", "Produkt": "Siebbeschichtung A4", "Menge": 1, "Preis": 20, "Gramm": None},
    {"Typ": "Folien", "Produkt": "Folienpreis A4", "Menge": 1, "Preis": 10, "Gramm": None},
]

st.header("Positionen")

if "rows" not in st.session_state or not st.session_state["rows"]:
    st.session_state["rows"] = default_rows.copy()

if st.button("Position hinzufügen"):
    st.session_state["rows"].append({
        "Typ": "Farbe", "Produkt": "", "Menge": 1, "Preis": 0.0, "Gramm": None
    })

for idx, row in enumerate(st.session_state["rows"]):
    cols = st.columns([2, 3, 2, 2, 2, 1])
    # Typ-Auswahl
    with cols[0]:
        typ = st.selectbox(
            "Typ",
            ["Farbe", "Kleidung", "Siebbeschichtung", "Folien", "Eigenes"],
            key=f"typ_{idx}",
            index=(["Farbe", "Kleidung", "Siebbeschichtung", "Folien", "Eigenes"].index(row["Typ"]) if row["Typ"] in ["Farbe", "Kleidung", "Siebbeschichtung", "Folien", "Eigenes"] else 0)
        )
        row["Typ"] = typ
    # Produktauswahl abhängig vom Typ
    with cols[1]:
        if row["Typ"] in kategorien:
            prod_choices = [p[0] for p in kategorien[row["Typ"]]]
            if row["Produkt"] in prod_choices:
                idx_prod = prod_choices.index(row["Produkt"])
            else:
                idx_prod = 0
                row["Produkt"] = prod_choices[0]
            prod = st.selectbox("Produkt", prod_choices, key=f"prod_{idx}", index=idx_prod)
            row["Produkt"] = prod
        else:
            row["Produkt"] = st.text_input("Eigenes Produkt", value=row.get("Produkt", ""), key=f"eig_{idx}")
    # Menge/Gramm abhängig vom Typ
    with cols[2]:
        if row["Typ"] == "Farbe":
            gramm = st.number_input("Gramm", min_value=1, value=row.get("Gramm", 100) or 100, key=f"gramm_{idx}")
            row["Gramm"] = gramm
            row["Menge"] = gramm
        else:
            menge = st.number_input("Menge", min_value=1, value=row.get("Menge", 1), key=f"menge_{idx}")
            row["Menge"] = menge
    # Preis
    with cols[3]:
        if row["Typ"] == "Farbe":
            preis_kg = dict(farben_data)[row["Produkt"]]
            preis = preis_kg / 1000 * row["Gramm"]
            row["Preis"] = preis
            st.write(f"CHF {preis:.2f}")
        elif row["Typ"] in kategorien:
            preis = dict(kategorien[row["Typ"]])[row["Produkt"]]
            row["Preis"] = preis
            st.write(f"CHF {preis:.2f}")
        else:
            preis = st.number_input("Preis", value=row.get("Preis", 0.0), min_value=0.0, key=f"preis_{idx}")
            row["Preis"] = preis
    # Gesamt
    with cols[4]:
        if row["Typ"] == "Farbe":
            gesamt = row["Preis"]
        else:
            gesamt = row["Preis"] * row["Menge"]
        st.write(f"Gesamt: CHF {gesamt:.2f}")
    # Entfernen-Button
    with cols[5]:
        if st.button("❌", key=f"del_{idx}"):
            st.session_state["rows"].pop(idx)
            st.experimental_rerun()

# Personalkosten (nur Kommerziell)
arbeitskosten = 0
if modus == "Kommerziell":
    st.header("Arbeitsstunden")
    personen = st.radio("Anzahl Personen", [1, 2], horizontal=True)
    stunden = st.number_input("Arbeitsstunden", min_value=0.0, step=0.5, value=0.0)
    preis_arbeitsstunde = 100 if personen == 1 else 150
    arbeitskosten = stunden * preis_arbeitsstunde

# Gesamtsumme berechnen
total = 0
for row in st.session_state["rows"]:
    if not row["Produkt"]:
        continue
    if row["Typ"] == "Farbe":
        total += row["Preis"]
    else:
        total += row["Preis"] * row["Menge"]
total += arbeitskosten
verbrauch_betrag = total * zuschlag_verbrauch
betrieb_betrag = total * zuschlag_betrieb
total_all = total + verbrauch_betrag + betrieb_betrag

# SWISS QR erzeugen (SVG ➜ PNG)
bill = QRBill(
    account=iban.replace(" ", ""),
    creditor=CREDITOR_ADDR,
    amount=f"{total_all:.2f}",
    currency="CHF",
    additional_information=f"{beleg_typ} {doc_nr}"
)
svg_buf = io.StringIO()
bill.as_svg(svg_buf)
svg_content = svg_buf.getvalue()

# In Streamlit anzeigen
st.markdown(f"<div>{svg_content}</div>", unsafe_allow_html=True)

# SVG zu PNG konvertieren für PDF
png_bytes = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
buf = io.BytesIO(png_bytes)
buf.seek(0)

# PDF-Export
if st.button(f"{beleg_typ} generieren"):
    pdf = FPDF()
    pdf.add_page()

    # Firmenlogo und Kopfzeile
    if logo_file:
        image = Image.open(logo_file)
        image.save("logo_temp.png")
        pdf.image("logo_temp.png", x=10, y=10, w=40)
    pdf.set_font("Arial", "B", 24)
    pdf.set_xy(60, 18)
    pdf.cell(0, 15, f"{beleg_typ}", ln=1)
    
    pdf.set_font("Arial", "", 14)
    pdf.set_xy(10, 35)
    pdf.cell(100, 10, "Rechnungsstellerin:", ln=0)
    pdf.cell(0, 10, "Empfänger:", ln=1)
    pdf.set_font("Arial", "", 12)
    pdf.set_xy(10, 45)
    pdf.multi_cell(80, 8, sender)
    pdf.set_xy(110, 45)
    pdf.multi_cell(80, 8, recipient)

    pdf.set_xy(10, 80)
    pdf.set_font("Arial", "", 13)
    pdf.cell(100, 8, f"Rechnungsnummer: {doc_nr}")
    pdf.cell(0, 8, f"Datum: {doc_date}", ln=1)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 10, "Leistungen & Material", ln=1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Produkt", 1)
    pdf.cell(30, 10, "Menge", 1)
    pdf.cell(30, 10, "Einzelpreis", 1)
    pdf.cell(40, 10, "Gesamt", 1, ln=1)
    pdf.set_font("Arial", "", 12)
    for row in st.session_state["rows"]:
        if not row["Produkt"]:
            continue
        if row["Typ"] == "Farbe":
            einheit = "g"
            menge = row["Gramm"]
            preis = float(row["Preis"])
            gesamt = preis
        else:
            einheit = "Stk"
            menge = row["Menge"]
            preis = float(row["Preis"])
            gesamt = preis * menge
        pdf.cell(80, 10, row["Produkt"], 1)
        pdf.cell(30, 10, f"{menge} {einheit}", 1)
        pdf.cell(30, 10, f"{preis:.2f}", 1)
        pdf.cell(40, 10, f"{gesamt:.2f}", 1, ln=1)
    # Personalkosten aufführen
    if arbeitskosten > 0:
        pdf.cell(140, 10, "Personalkosten", 1)
        pdf.cell(40, 10, f"{arbeitskosten:.2f}", 1, ln=1)
    # Zuschläge
    pdf.cell(140, 10, f"Verbrauchsmaterial ({int(zuschlag_verbrauch*100)}%)", 1)
    pdf.cell(40, 10, f"{verbrauch_betrag:.2f}", 1, ln=1)
    pdf.cell(140, 10, f"Betriebskosten ({int(zuschlag_betrieb*100)}%)", 1)
    pdf.cell(40, 10, f"{betrieb_betrag:.2f}", 1, ln=1)
    
    # FETTER TOTAL-Bereich
    pdf.set_font("Arial", "B", 16)
    pdf.cell(140, 15, "TOTAL", 1)
    pdf.cell(40, 15, f"{total_all:.2f} CHF", 1, ln=1)
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Empfänger: {CREDITOR_ADDR['name']}", ln=1, align="C")
    pdf.cell(0, 10, f"IBAN: {iban}", ln=1, align="C")
    pdf.cell(0, 10, f"Betrag: {total_all:.2f} CHF", ln=1, align="C")
    pdf.cell(0, 8, "Zahlbar innert 30 Tagen.", ln=1, align="C")

    # Nächste Seite: QR-Code
    pdf.add_page()
    pdf.image(buf, x=25, y=30, w=160)  # Möglichst groß


    # Speichern und Download anbieten
    pdf_file = f"{beleg_typ}_{doc_nr}.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as f:
        st.success(f"{beleg_typ} inkl. QR erstellt!")
        st.download_button("PDF herunterladen", f, file_name=pdf_file)
