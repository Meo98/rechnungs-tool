import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image
import io
from qrbill import QRBill
import cairosvg

st.set_page_config(page_title="Rechnungsgenerator", page_icon=":money_with_wings:", layout="centered")

# Catppuccin Mocha Colors
PRIMARY_COLOR = "#89b4fa"  # Blue
ACCENT_COLOR = "#f9e2af"   # Yellow
BG_COLOR = "#1e1e2e"       # Base
TEXT_COLOR = "#cdd6f4"     # Text
Card_BG = "#313244"        # Surface0

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    /* Global Text and Background */
    html, body, [class*="css"] {
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stApp {
        background-color: #11111b; /* Crust/Darker Base */
        color: #cdd6f4;
    }
    
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        font-family: 'JetBrains Mono', monospace !important;
        color: #cdd6f4 !important;
    }

    /* Inputs - Industrial Look */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        color: #cdd6f4;
        background-color: #181825; /* Mantle */
        border: 1px solid #45475a; /* Surface1 */
        border-radius: 0px; /* Sharp edges */
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #89b4fa; /* Blue focus */
        box-shadow: none;
    }

    .stSelectbox>div>div>div {
        color: #cdd6f4;
        background-color: #181825;
        border: 1px solid #45475a;
        border-radius: 0px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Buttons - Brutalist/Sharp */
    .stButton>button {
        color: #11111b;
        background-color: #89b4fa; /* Blue */
        border-radius: 0px;
        border: 1px solid #89b4fa;
        font-weight: bold;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: transparent;
        color: #89b4fa;
        border: 1px solid #89b4fa;
    }
    
    /* Download Button - Accent */
    .stDownloadButton>button {
        color: #11111b;
        background-color: #f9e2af; /* Yellow */
        border-radius: 0px;
        border: 1px solid #f9e2af;
        font-weight: bold;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stDownloadButton>button:hover {
        background-color: transparent;
        color: #f9e2af;
        border: 1px solid #f9e2af;
    }
    
    /* Expander/Cards */
    .streamlit-expanderHeader {
        background-color: #181825;
        border-radius: 0px;
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Rechnungsgenerator mit offiziellem Swiss QR")

# Feste Absender- und Empfängeradresse für QR
CREDITOR_ADDR = {
    "name": "Solidarisches Siebdruck Kollektiv",
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
    firma_name = st.text_input("Firmenname", "Printbrigata")

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

# Tabellen-Header
h_cols = st.columns([2, 3, 2, 2, 2, 1])
h_cols[0].markdown("**Typ**")
h_cols[1].markdown("**Produkt**")
h_cols[2].markdown("**Menge / Gramm**")
h_cols[3].markdown("**Preis (CHF)**")
h_cols[4].markdown("**Gesamt**")

if st.button("Position hinzufügen"):
    st.session_state["rows"].append({
        "Typ": "Farbe", "Produkt": "", "Menge": 1, "Preis": 0.0, "Gramm": None
    })

for idx, row in enumerate(st.session_state["rows"]):
    cols = st.columns([2, 3, 2, 2, 2, 1])
    # Typ-Auswahl
    with cols[0]:
        typ_options = ["Farbe", "Kleidung", "Siebbeschichtung", "Folien", "Eigenes"]
        try:
            curr_index = typ_options.index(row["Typ"])
        except ValueError:
            curr_index = 0
            
        typ = st.selectbox(
            "Typ",
            typ_options,
            key=f"typ_{idx}",
            index=curr_index
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
            st.rerun()

# Personalkosten (nur Kommerziell)
arbeitskosten = 0
if modus == "Kommerziell":
    st.header("Arbeitsstunden")
    
    if "staff_rows" not in st.session_state:
        st.session_state["staff_rows"] = [{"Name": "Person 1", "Stunden": 0.0, "Rate": 100.0}]

    if st.button("Person hinzufügen"):
        st.session_state["staff_rows"].append({"Name": f"Person {len(st.session_state['staff_rows'])+1}", "Stunden": 0.0, "Rate": 100.0})

    for idx, staff in enumerate(st.session_state["staff_rows"]):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1:
            staff["Name"] = st.text_input("Name", value=staff["Name"], key=f"staff_name_{idx}")
        with c2:
            staff["Stunden"] = st.number_input("Stunden", min_value=0.0, step=0.5, value=float(staff.get("Stunden", 0.0)), key=f"staff_hrs_{idx}")
        with c3:
            staff["Rate"] = st.number_input("Ansatz (CHF/h)", min_value=0.0, step=10.0, value=float(staff.get("Rate", 100.0)), key=f"staff_rate_{idx}")
        with c4:
            line_total = staff["Stunden"] * staff["Rate"]
            st.write(f"CHF {line_total:.2f}")
        with c5:
             if st.button("❌", key=f"del_staff_{idx}"):
                st.session_state["staff_rows"].pop(idx)
                st.rerun()
        arbeitskosten += staff["Stunden"] * staff["Rate"]

    st.write(f"**Total Personalkosten: CHF {arbeitskosten:.2f}**")

# Rabatt
st.header("Rabatt")
rabatt_prozent = st.number_input("Rabatt (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)

# Gesamtsumme berechnen
total_items = 0
for row in st.session_state["rows"]:
    if not row["Produkt"]:
        continue
    if row["Typ"] == "Farbe":
        total_items += row["Preis"]
    else:
        total_items += row["Preis"] * row["Menge"]

# Zwischensumme (Material + Arbeit)
subtotal = total_items + arbeitskosten

# Rabatt berechnen
rabatt_betrag = subtotal * (rabatt_prozent / 100)
subtotal_discounted = subtotal - rabatt_betrag

verbrauch_betrag = subtotal_discounted * zuschlag_verbrauch
betrieb_betrag = subtotal_discounted * zuschlag_betrieb
total_all = subtotal_discounted + verbrauch_betrag + betrieb_betrag

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
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Firmenlogo und Kopfzeile
        if logo_file:
            pdf.image(logo_file, x=10, y=10, w=40)
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
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Personalkosten", ln=1)
            pdf.set_font("Arial", "", 12)
            for staff in st.session_state.get("staff_rows", []):
                if staff["Stunden"] > 0:
                    line_sum = staff["Stunden"] * staff["Rate"]
                    pdf.cell(140, 10, f"{staff['Name']} ({staff['Stunden']}h @ {staff['Rate']} CHF/h)", 1)
                    pdf.cell(40, 10, f"{line_sum:.2f}", 1, ln=1)
            # Falls man nur die Summe will oder Details. Hier Details.
            
        # Rabatt
        if rabatt_betrag > 0:
             pdf.ln(5)
             pdf.cell(140, 10, f"Rabatt ({rabatt_prozent}%)", 1)
             pdf.cell(40, 10, f"-{rabatt_betrag:.2f}", 1, ln=1)
             
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
        pdf_bytes = pdf.output()
        st.success(f"{beleg_typ} inkl. QR erstellt!")
        st.download_button("PDF herunterladen", data=bytes(pdf_bytes), file_name=f"{beleg_typ}_{doc_nr}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Fehler beim Erstellen des PDFs: {e}")
