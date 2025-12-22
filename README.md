# Printbrigata Rechnungstool

Ein modernes Web-Tool zur Erstellung von Rechnungen, Angeboten und Lieferscheinen mit integriertem **Swiss QR-Bill Generator**.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Features

- **Swiss QR-Bill**: Automatische Generierung von konformen QR-Rechnungen.
- **Modernes UI**: "Catppuccin" Design-Schema für eine angenehme Benutzeroberfläche.
- **PDF Export**: Generiert saubere PDFs für Rechnungen und Angebote.
- **Flexible Preismodelle**: Unterstützt "Solidarische" und "Kommerzielle" Abrechnungsmodi mit automatischen Zuschlägen.
- **Kategorien**: Vordefinierte Preise für Siebbeschichtung, Textilien, Farben und mehr.

## 🛠️ Installation & Nutzung (Lokal)

### Voraussetzungen
- Python 3.12 oder neuer
- `pip`

### Installation
1. Repository klonen:
   ```bash
   git clone <repository-url>
   cd rechnungs-tool
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
   *Hinweis: Falls Probleme mit `cairosvg` auftreten, müssen ggf. System-Bibliotheken (`libcairo2`) installiert werden.*

### Starten
Starte die Applikation:
```bash
streamlit run Preislisten.py
```
Oder falls es Pfad-Probleme gibt:
```bash
python -m streamlit run Preislisten.py
```
Die App ist dann unter `http://localhost:8501` erreichbar.

---

## 🌐 Deployment (Ubuntu / DigitalOcean)

Für die Installation auf einem Ubuntu-Server wurde ein automatisches Setup-Skript bereitgestellt.

1. Dateien auf den Server kopieren.
2. Das Skript ausführbar machen und als **root** (oder mit `sudo`) starten:

   ```bash
   chmod +x setup_ubuntu.sh
   sudo ./setup_ubuntu.sh
   ```

Das Skript kümmert sich um:
- Installation aller System-Abhängigkeiten (`python3`, `cairo`, `nginx`, `certbot`...).
- Einrichtung des **Systemd Service** (automatischer Neustart bei Absturz/Reboot).
- Einrichtung des **Nginx Proxy** (Port 80/443 -> 8501).
- Einrichtung von **HTTPS** (Let's Encrypt SSL Zertifikat).

## 📄 Lizenz

Dieses Projekt ist unter der **MIT License** lizenziert. Siehe [LICENSE](LICENSE) für Details.

Copyright (c) 2025 Printbrigata
