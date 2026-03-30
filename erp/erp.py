"""
ERP Lite v2.0 - Tam Entegre Sürüm
Python + PyQt6 + SQLite | Cari, Stok, Fatura + Döviz/FX Modülleri
"""
import sys
import traceback
import pandas as pd
import sys
import sqlite3
import json
import os
import threading
from datetime import datetime, date
from typing import Optional

import requests
import os
from google import genai

from xml.etree import ElementTree

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QMessageBox, QSplitter, QFrame, QScrollArea,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox,
    QSpinBox, QAbstractItemView, QSizePolicy, QTextEdit, QTabWidget,
    QStackedWidget, QGridLayout, QFileDialog, QProgressBar, QGroupBox
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QMessageBox, QSplitter, QFrame, QScrollArea,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox,
    QSpinBox, QAbstractItemView, QSizePolicy, QTextEdit, QTabWidget,
    QStackedWidget, QGridLayout, QFileDialog, QProgressBar, QGroupBox,
    QCheckBox  # <--- BU SATIRI EKLE (Sonuna virgül koymayı unutma)
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QDate, QTimer, QSize
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QBrush
)

# ─────────────────────────────────────────────
#  CONSTANTS & CONFIG
# ─────────────────────────────────────────────
DB_PATH = "erp.db"
APP_TITLE = "ERP Lite v2.0"
TCMB_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e222d; 
    color: #e0e0e0;
    font-family: 'Segoe UI', Roboto, Arial;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #161922; 
    border-right: 1px solid #2d333b;
}
QPushButton#navBtn {
    background-color: transparent;
    color: #9ea7b3;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
}
QPushButton#navBtn:hover {
    background-color: #2a2f3b;
    color: #ffffff;
}
QPushButton#navBtn:checked {
    background-color: #38761d;
    color: #ffffff;
    font-weight: bold;
}
QPushButton {
    background-color: #2da042;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 500;
}
QPushButton:hover { background-color: #3fb950; }
QPushButton:pressed { background-color: #238636; }

QPushButton#dangerBtn {
    background-color: #da3633;
}
QPushButton#dangerBtn:hover { background-color: #f85149; }

QPushButton#secondaryBtn {
    background-color: #2d333b;
    border: 1px solid #444c56;
    color: #adbac7;
}
QPushButton#secondaryBtn:hover { background-color: #444c56; }

QPushButton#infoBtn {
    background-color: #316dca;
}
QPushButton#infoBtn:hover { background-color: #539bf5; }

QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit {
    background-color: #22272e;  /* Giriş alanları: Daha belirgin */
    color: #adbac7;
    border: 1px solid #444c56;
    border-radius: 6px;
    padding: 6px 10px;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #539bf5;
    background-color: #2d333b;
}

QTableWidget {
    background-color: #22272e;
    color: #adbac7;
    gridline-color: #2d333b;
    border: 1px solid #444c56;
    border-radius: 6px;
    selection-background-color: #2d333b;
}
QHeaderView::section {
    background-color: #1c2128;
    color: #768390;
    border: none;
    border-bottom: 1px solid #444c56;
    padding: 8px;
    font-weight: bold;
}

QFrame#card {
    background-color: #22272e;
    border: 1px solid #444c56;
    border-radius: 10px;
    padding: 10px;
}
QLabel#sectionTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
}
QLabel#cardValue {
    color: #539bf5; /* Rakamlar daha okunaklı mavi */
    font-size: 22px;
    font-weight: bold;
}
QLabel#cardLabel {
    color: #768390;
}


QFrame#cardGreen { border-left: 4px solid #3fb950; }
QFrame#cardRed   { border-left: 4px solid #f85149; }
QFrame#cardBlue  { border-left: 4px solid #539bf5; }
QFrame#cardGold  { border-left: 4px solid #dbab09; }
QFrame#cardPurple{ border-left: 4px solid #8957e5; }

QTabWidget::pane {
    border: 1px solid #444c56;
    background-color: #1e222d;
}
QTabBar::tab {
    background-color: #161922;
    color: #768390;
    padding: 8px 20px;
    border: 1px solid #444c56;
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #316dca;
    color: white;
}
"""

# ─────────────────────────────────────────────
#  DATABASE MANAGER
# ─────────────────────────────────────────────
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_database(self):
        with self.get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cariler (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    unvan       TEXT NOT NULL,
                    vergi_no    TEXT,
                    telefon     TEXT,
                    email       TEXT,
                    adres       TEXT,
                    bakiye_tl   REAL DEFAULT 0,
                    bakiye_usd  REAL DEFAULT 0,
                    bakiye_eur  REAL DEFAULT 0,
                    cari_tipi   TEXT DEFAULT 'MUSTERI',
                    olusturma   TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS stoklar (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    stok_kodu     TEXT UNIQUE NOT NULL,
                    stok_adi      TEXT NOT NULL,
                    birim         TEXT DEFAULT 'Adet',
                    miktar        REAL DEFAULT 0,
                    alis_fiyati   REAL DEFAULT 0,
                    satis_fiyati  REAL DEFAULT 0,
                    kategori      TEXT DEFAULT 'Genel',
                    olusturma     TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS faturalar (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_no       TEXT UNIQUE NOT NULL,
                    cari_id         INTEGER NOT NULL REFERENCES cariler(id),
                    tarih           TEXT NOT NULL,
                    fatura_tipi     TEXT NOT NULL CHECK(fatura_tipi IN ('ALIS','SATIS')),
                    genel_toplam    REAL DEFAULT 0,
                    doviz_birimi    TEXT DEFAULT 'TL',
                    doviz_kuru      REAL DEFAULT 1.0,
                    doviz_tutari    REAL DEFAULT 0,
                    notlar          TEXT,
                    olusturma       TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS fatura_satirlari (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_id       INTEGER NOT NULL REFERENCES faturalar(id) ON DELETE CASCADE,
                    stok_id         INTEGER NOT NULL REFERENCES stoklar(id),
                    malzeme_kodu    TEXT,
                    miktar          REAL NOT NULL,
                    birim_fiyat     REAL NOT NULL,
                    kdv_orani       REAL DEFAULT 0,
                    kdv_tutari      REAL DEFAULT 0,
                    satir_toplami   REAL NOT NULL,
                    satir_kdv_dahil REAL NOT NULL,
                    doviz_birimi    TEXT DEFAULT 'TL',
                    doviz_kuru      REAL DEFAULT 1.0,
                    doviz_tutari    REAL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS kur_gecmisi (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih       TEXT NOT NULL,
                    usd_kur     REAL NOT NULL,
                    eur_kur     REAL NOT NULL,
                    kaynak      TEXT DEFAULT 'TCMB',
                    olusturma   TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS odemeler (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_id       INTEGER NOT NULL REFERENCES faturalar(id) ON DELETE CASCADE,
                    cari_id         INTEGER NOT NULL REFERENCES cariler(id),
                    tarih           TEXT NOT NULL,
                    tutar_tl        REAL NOT NULL,
                    doviz_birimi    TEXT DEFAULT 'TL',
                    doviz_kuru      REAL DEFAULT 1.0,
                    doviz_tutari    REAL DEFAULT 0,
                    odeme_yontemi   TEXT DEFAULT 'Nakit',
                    aciklama        TEXT,
                    olusturma       TEXT DEFAULT (datetime('now','localtime'))
                );
            """)
            # Migration: add missing columns if upgrading
            self._migrate(conn)

    def _migrate(self, conn):
        """Add missing columns safely for upgrades."""
        migrations = [
            ("cariler", "email", "TEXT"),
            ("cariler", "adres", "TEXT"),
            ("cariler", "bakiye_eur", "REAL DEFAULT 0"),
            ("cariler", "cari_tipi", "TEXT DEFAULT 'MUSTERI'"),
            ("faturalar", "doviz_birimi", "TEXT DEFAULT 'TL'"),
            ("faturalar", "doviz_kuru", "REAL DEFAULT 1.0"),
            ("faturalar", "doviz_tutari", "REAL DEFAULT 0"),
            ("faturalar", "notlar", "TEXT"),
            ("faturalar", "kdv_toplam", "REAL DEFAULT 0"),
            ("faturalar", "odenen_toplam", "REAL DEFAULT 0"),
            ("faturalar", "odeme_durumu", "TEXT DEFAULT 'BEKLIYOR'"),
            ("fatura_satirlari", "malzeme_kodu", "TEXT"),
            ("fatura_satirlari", "kdv_orani", "REAL DEFAULT 0"),
            ("fatura_satirlari", "kdv_tutari", "REAL DEFAULT 0"),
            ("fatura_satirlari", "satir_kdv_dahil", "REAL DEFAULT 0"),
            ("fatura_satirlari", "doviz_birimi", "TEXT DEFAULT 'TL'"),
            ("fatura_satirlari", "doviz_kuru", "REAL DEFAULT 1.0"),
            ("fatura_satirlari", "doviz_tutari", "REAL DEFAULT 0"),
        ]
        for table, col, col_type in migrations:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # Column already exists


# ─────────────────────────────────────────────
#  TCMB KUR ÇEKİCİ THREAD
# ─────────────────────────────────────────────
class KurCekiciThread(QThread):
    kur_yuklendi = pyqtSignal(float, float)  # usd, eur
    hata_olustu = pyqtSignal(str)

    def run(self):
        try:
            resp = requests.get(TCMB_URL, timeout=10)
            resp.raise_for_status()
            root = ElementTree.fromstring(resp.content)
            usd = eur = None
            for currency in root.findall(".//Currency"):
                code = currency.get("CurrencyCode", "")
                try:
                    if code == "USD":
                        usd = float(currency.find("ForexSelling").text.replace(",", "."))
                    elif code == "EUR":
                        eur = float(currency.find("ForexSelling").text.replace(",", "."))
                except (AttributeError, ValueError, TypeError):
                    pass
            if usd and eur:
                self.kur_yuklendi.emit(usd, eur)
            else:
                self.hata_olustu.emit("Kur verisi parse edilemedi.")
        except requests.exceptions.ConnectionError:
            self.hata_olustu.emit("İnternet bağlantısı yok. Varsayılan kurlar kullanılıyor.")
        except Exception as e:
            self.hata_olustu.emit(f"Kur çekme hatası: {str(e)}")


# ─────────────────────────────────────────────
#  ÖZET KART WİDGET
# ─────────────────────────────────────────────
class OzetKart(QFrame):
    def __init__(self, baslik: str, deger: str, ikon: str, renk_class: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("class", renk_class)
        self.setMinimumWidth(180)
        self.setMaximumHeight(110)

        # Apply border color via stylesheet
        color_map = {
            "cardGreen": "#2ea043",
            "cardRed": "#f85149",
            "cardBlue": "#1f6feb",
            "cardGold": "#d29922",
            "cardPurple": "#8957e5",
        }
        border_color = color_map.get(renk_class, "#30363d")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-left: 4px solid {border_color};
                border-radius: 10px;
                padding: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Icon + label row
        top = QHBoxLayout()
        icon_lbl = QLabel(ikon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        top.addWidget(icon_lbl)
        top.addStretch()
        lbl = QLabel(baslik)
        lbl.setObjectName("cardLabel")
        top.addWidget(lbl)
        layout.addLayout(top)

        self.deger_lbl = QLabel(deger)
        self.deger_lbl.setObjectName("cardValue")
        layout.addWidget(self.deger_lbl)

    def set_deger(self, deger: str):
        self.deger_lbl.setText(deger)


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
class DashboardWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.usd_kur = 32.50
        self.eur_kur = 35.20
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Dashboard")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.kur_lbl = QLabel("🔄 Kurlar yükleniyor...")
        self.kur_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        header.addWidget(self.kur_lbl)

        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.setObjectName("secondaryBtn")
        yenile_btn.setFixedWidth(90)
        yenile_btn.clicked.connect(self.refresh)
        header.addWidget(yenile_btn)
        layout.addLayout(header)

        # Kart grid
        self.kart_grid = QGridLayout()
        self.kart_grid.setSpacing(14)

        self.kart_alacak = OzetKart("Toplam Alacak (TL)", "₺0", "📈", "cardGreen")
        self.kart_borc = OzetKart("Toplam Borç (TL)", "₺0", "📉", "cardRed")
        self.kart_fatura = OzetKart("Toplam Fatura", "0", "🧾", "cardBlue")
        self.kart_usd = OzetKart("Toplam USD Bakiye", "$0", "💵", "cardGold")
        self.kart_eur = OzetKart("Toplam EUR Bakiye", "€0", "💶", "cardPurple")

        self.kart_grid.addWidget(self.kart_alacak, 0, 0)
        self.kart_grid.addWidget(self.kart_borc, 0, 1)
        self.kart_grid.addWidget(self.kart_fatura, 0, 2)
        self.kart_grid.addWidget(self.kart_usd, 1, 0)
        self.kart_grid.addWidget(self.kart_eur, 1, 1)
        layout.addLayout(self.kart_grid)

        # Son faturalar
        son_lbl = QLabel("🧾 Son 10 Fatura")
        son_lbl.setStyleSheet("color: #c9d1d9; font-size: 15px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(son_lbl)

        self.son_fatura_tbl = QTableWidget(0, 6)
        self.son_fatura_tbl.setHorizontalHeaderLabels(
            ["Fatura No", "Cari", "Tarih", "Tip", "TL Tutar", "Döviz"]
        )
        self.son_fatura_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.son_fatura_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.son_fatura_tbl.setMaximumHeight(250)
        layout.addWidget(self.son_fatura_tbl)
        layout.addStretch()

    def set_kurlar(self, usd: float, eur: float):
        self.usd_kur = usd
        self.eur_kur = eur
        self.kur_lbl.setText(
            f"💱 USD: ₺{usd:.4f}  |  EUR: ₺{eur:.4f}  |  "
            f"🕐 {datetime.now().strftime('%H:%M')}"
        )
        self.kur_lbl.setStyleSheet("color: #2ea043; font-size: 12px;")

    def refresh(self):
        try:
            with self.db.get_conn() as conn:
                # Cari bakiyeler
                row = conn.execute(
                    "SELECT COALESCE(SUM(CASE WHEN bakiye_tl > 0 THEN bakiye_tl ELSE 0 END), 0) as alacak, "
                    "COALESCE(SUM(CASE WHEN bakiye_tl < 0 THEN ABS(bakiye_tl) ELSE 0 END), 0) as borc, "
                    "COALESCE(SUM(bakiye_usd), 0) as usd, "
                    "COALESCE(SUM(COALESCE(bakiye_eur,0)), 0) as eur "
                    "FROM cariler"
                ).fetchone()
                alacak = row["alacak"] or 0
                borc = row["borc"] or 0
                usd_bak = row["usd"] or 0
                eur_bak = row["eur"] or 0

                # Fatura sayısı
                f_count = conn.execute("SELECT COUNT(*) as c FROM faturalar").fetchone()["c"]

                # Son faturalar
                faturalar = conn.execute("""
                    SELECT f.fatura_no, c.unvan, f.tarih, f.fatura_tipi,
                        f.genel_toplam, f.doviz_birimi, f.doviz_tutari, f.doviz_kuru
                    FROM faturalar f JOIN cariler c ON f.cari_id = c.id
                    ORDER BY f.id DESC LIMIT 10
                """).fetchall()

            # Update cards
            self.kart_alacak.set_deger(f"₺{alacak:,.2f}")
            self.kart_borc.set_deger(f"₺{borc:,.2f}")
            self.kart_usd.set_deger(f"${usd_bak:,.2f}")
            self.kart_eur.set_deger(f"€{eur_bak:,.2f}")
            self.kart_fatura.set_deger(str(f_count))

            # Son faturalar tablosu
            self.son_fatura_tbl.setRowCount(0)
            for f in faturalar:
                row_idx = self.son_fatura_tbl.rowCount()
                self.son_fatura_tbl.insertRow(row_idx)
                tip_color = "#2ea043" if f["fatura_tipi"] == "SATIS" else "#1f6feb"
                doviz_str = (
                    f"{f['doviz_birimi']} {f['doviz_tutari']:,.2f} (₺{f['doviz_kuru']:.4f})"
                    if f["doviz_birimi"] != "TL" else "TL"
                )
                cells = [
                    f["fatura_no"], f["unvan"], f["tarih"], f["fatura_tipi"],
                    f"₺{f['genel_toplam']:,.2f}", doviz_str
                ]
                for col_idx, val in enumerate(cells):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col_idx == 3:
                        item.setForeground(QColor(tip_color))
                    self.son_fatura_tbl.setItem(row_idx, col_idx, item)
        except Exception as e:
            print(f"Dashboard refresh error: {e}")


# ─────────────────────────────────────────────
#  CARİ MODÜLÜ
# ─────────────────────────────────────────────
class CariDialog(QDialog):
    def __init__(self, db: DatabaseManager, cari_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.cari_id = cari_id
        self.setWindowTitle("Cari Ekle/Düzenle")
        self.setMinimumWidth(420)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        if cari_id:
            self._load_cari()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.unvan = QLineEdit()
        self.vergi_no = QLineEdit()
        self.telefon = QLineEdit()
        self.email = QLineEdit()
        self.adres = QTextEdit()
        self.adres.setMaximumHeight(70)
        self.cari_tipi = QComboBox()
        self.cari_tipi.addItems(["MUSTERI", "TEDARIKCI", "HEM MUSTERI HEM TEDARIKCI"])

        layout.addRow("Ünvan *:", self.unvan)
        layout.addRow("Vergi No:", self.vergi_no)
        layout.addRow("Telefon:", self.telefon)
        layout.addRow("E-Posta:", self.email)
        layout.addRow("Adres:", self.adres)
        layout.addRow("Cari Tipi:", self.cari_tipi)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _load_cari(self):
        with self.db.get_conn() as conn:
            row = conn.execute("SELECT * FROM cariler WHERE id=?", (self.cari_id,)).fetchone()
            if row:
                self.unvan.setText(row["unvan"] or "")
                self.vergi_no.setText(row["vergi_no"] or "")
                self.telefon.setText(row["telefon"] or "")
                self.email.setText(row["email"] or "")
                self.adres.setPlainText(row["adres"] or "")
                idx = self.cari_tipi.findText(row["cari_tipi"] or "MUSTERI")
                if idx >= 0:
                    self.cari_tipi.setCurrentIndex(idx)

    def _save(self):
        unvan = self.unvan.text().strip()
        if not unvan:
            QMessageBox.warning(self, "Hata", "Ünvan zorunludur!")
            return
        try:
            with self.db.get_conn() as conn:
                if self.cari_id:
                    conn.execute("""
                        UPDATE cariler SET unvan=?, vergi_no=?, telefon=?, email=?, adres=?, cari_tipi=?
                        WHERE id=?
                    """, (unvan, self.vergi_no.text(), self.telefon.text(),
                        self.email.text(), self.adres.toPlainText(),
                        self.cari_tipi.currentText(), self.cari_id))
                else:
                    conn.execute("""
                        INSERT INTO cariler (unvan, vergi_no, telefon, email, adres, cari_tipi)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (unvan, self.vergi_no.text(), self.telefon.text(),
                        self.email.text(), self.adres.toPlainText(),
                        self.cari_tipi.currentText()))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class CariWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QHBoxLayout()
        title = QLabel("👥 Cari Hesaplar")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.arama = QLineEdit()
        self.arama.setPlaceholderText("🔍 Ara...")
        self.arama.setFixedWidth(220)
        self.arama.textChanged.connect(self.refresh)
        header.addWidget(self.arama)

        ekle_btn = QPushButton("➕ Yeni Cari")
        ekle_btn.clicked.connect(self._yeni_cari)
        header.addWidget(ekle_btn)

        excel_btn = QPushButton("📊 Excel")
        excel_btn.setObjectName("infoBtn")
        excel_btn.clicked.connect(self._excel_export)
        header.addWidget(excel_btn)
        layout.addLayout(header)

        # Filter row
        filtre = QHBoxLayout()
        filtre.addWidget(QLabel("Tür:"))
        self.tip_combo = QComboBox()
        self.tip_combo.addItems(["Tümü", "MUSTERI", "TEDARIKCI"])
        self.tip_combo.setFixedWidth(150)
        self.tip_combo.currentTextChanged.connect(self.refresh)
        filtre.addWidget(self.tip_combo)
        filtre.addStretch()
        layout.addLayout(filtre)

        # Table
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Ünvan", "Vergi No", "Telefon", "TL Bakiye", "USD Bakiye", "EUR Bakiye", "Tür"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.tbl)

        # Bottom buttons
        btn_row = QHBoxLayout()
        duzenle_btn = QPushButton("✏️ Düzenle")
        duzenle_btn.setObjectName("secondaryBtn")
        duzenle_btn.clicked.connect(self._duzenle)
        sil_btn = QPushButton("🗑️ Sil")
        sil_btn.setObjectName("dangerBtn")
        sil_btn.clicked.connect(self._sil)
        btn_row.addWidget(duzenle_btn)
        btn_row.addWidget(sil_btn)
        btn_row.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #8b949e;")
        btn_row.addWidget(self.count_lbl)
        layout.addLayout(btn_row)

    def refresh(self):
        try:
            arama = self.arama.text().strip()
            tip = self.tip_combo.currentText()
            with self.db.get_conn() as conn:
                query = "SELECT * FROM cariler WHERE (unvan LIKE ? OR vergi_no LIKE ?)"
                params = [f"%{arama}%", f"%{arama}%"]
                if tip != "Tümü":
                    query += " AND cari_tipi=?"
                    params.append(tip)
                query += " ORDER BY unvan"
                rows = conn.execute(query, params).fetchall()

            self.tbl.setRowCount(0)
            for r in rows:
                ri = self.tbl.rowCount()
                self.tbl.insertRow(ri)
                bakiye_tl = r["bakiye_tl"] or 0
                bakiye_usd = r["bakiye_usd"] or 0
                bakiye_eur = r["bakiye_eur"] if "bakiye_eur" in r.keys() else 0
                cells = [
                    str(r["id"]), r["unvan"], r["vergi_no"] or "", r["telefon"] or "",
                    f"₺{bakiye_tl:,.2f}", f"${bakiye_usd:,.2f}",
                    f"€{bakiye_eur or 0:,.2f}", r["cari_tipi"] or "MUSTERI"
                ]
                for ci, val in enumerate(cells):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if ci == 4:
                        item.setForeground(
                            QColor("#2ea043") if bakiye_tl >= 0 else QColor("#f85149")
                        )
                    self.tbl.setItem(ri, ci, item)
            self.count_lbl.setText(f"Toplam: {len(rows)} kayıt")
        except Exception as e:
            print(f"Cari refresh error: {e}")

    def _yeni_cari(self):
        dlg = CariDialog(self.db, parent=self)
        if dlg.exec():
            self.refresh()

    def _duzenle(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Lütfen bir cari seçin.")
            return
        cari_id = int(self.tbl.item(row, 0).text())
        dlg = CariDialog(self.db, cari_id, parent=self)
        if dlg.exec():
            self.refresh()

    def _sil(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        cari_id = int(self.tbl.item(row, 0).text())
        unvan = self.tbl.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{unvan}' carisini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db.get_conn() as conn:
                    conn.execute("DELETE FROM cariler WHERE id=?", (cari_id,))
                self.refresh()
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Hata", "Bu cariye ait faturalar var, silinemez!")

    def _excel_export(self):
        try:
            import pandas as pd
            with self.db.get_conn() as conn:
                rows = conn.execute("SELECT * FROM cariler ORDER BY unvan").fetchall()
            data = [dict(r) for r in rows]
            if not data:
                QMessageBox.information(self, "Bilgi", "Dışa aktarılacak veri yok.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Excel Kaydet", "cariler.xlsx", "Excel (*.xlsx)")
            if path:
                df = pd.DataFrame(data)
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Başarılı", f"Excel dosyası kaydedildi:\n{path}")
        except ImportError:
            QMessageBox.critical(self, "Hata", "pandas ve openpyxl kurulu değil.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ─────────────────────────────────────────────
#  STOK MODÜLÜ
# ─────────────────────────────────────────────
class StokDialog(QDialog):
    def __init__(self, db: DatabaseManager, stok_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.stok_id = stok_id
        self.setWindowTitle("Stok Ekle/Düzenle")
        self.setMinimumWidth(400)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        if stok_id:
            self._load()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.stok_kodu = QLineEdit()
        self.stok_adi = QLineEdit()
        self.birim = QComboBox()
        self.birim.addItems(["Adet", "KG", "LT", "MT", "M2", "M3", "Paket", "Kutu", "Ton"])
        self.miktar = QDoubleSpinBox()
        self.miktar.setRange(0, 9999999)
        self.miktar.setDecimals(3)
        self.alis_fiyati = QDoubleSpinBox()
        self.alis_fiyati.setRange(0, 9999999)
        self.alis_fiyati.setDecimals(4)
        self.satis_fiyati = QDoubleSpinBox()
        self.satis_fiyati.setRange(0, 9999999)
        self.satis_fiyati.setDecimals(4)
        self.kategori = QLineEdit()
        self.kategori.setText("Genel")

        layout.addRow("Stok Kodu *:", self.stok_kodu)
        layout.addRow("Stok Adı *:", self.stok_adi)
        layout.addRow("Birim:", self.birim)
        layout.addRow("Mevcut Miktar:", self.miktar)
        layout.addRow("Alış Fiyatı (₺):", self.alis_fiyati)
        layout.addRow("Satış Fiyatı (₺):", self.satis_fiyati)
        layout.addRow("Kategori:", self.kategori)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _load(self):
        with self.db.get_conn() as conn:
            row = conn.execute("SELECT * FROM stoklar WHERE id=?", (self.stok_id,)).fetchone()
            if row:
                self.stok_kodu.setText(row["stok_kodu"] or "")
                self.stok_adi.setText(row["stok_adi"] or "")
                idx = self.birim.findText(row["birim"] or "Adet")
                if idx >= 0:
                    self.birim.setCurrentIndex(idx)
                self.miktar.setValue(row["miktar"] or 0)
                self.alis_fiyati.setValue(row["alis_fiyati"] or 0)
                self.satis_fiyati.setValue(row["satis_fiyati"] or 0)
                self.kategori.setText(row["kategori"] or "Genel")

    def _save(self):
        kodu = self.stok_kodu.text().strip()
        adi = self.stok_adi.text().strip()
        if not kodu or not adi:
            QMessageBox.warning(self, "Hata", "Stok kodu ve adı zorunludur!")
            return
        try:
            with self.db.get_conn() as conn:
                if self.stok_id:
                    conn.execute("""
                        UPDATE stoklar SET stok_kodu=?, stok_adi=?, birim=?, miktar=?,
                        alis_fiyati=?, satis_fiyati=?, kategori=? WHERE id=?
                    """, (kodu, adi, self.birim.currentText(), self.miktar.value(),
                        self.alis_fiyati.value(), self.satis_fiyati.value(),
                        self.kategori.text(), self.stok_id))
                else:
                    conn.execute("""
                        INSERT INTO stoklar (stok_kodu, stok_adi, birim, miktar,
                        alis_fiyati, satis_fiyati, kategori)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (kodu, adi, self.birim.currentText(), self.miktar.value(),
                        self.alis_fiyati.value(), self.satis_fiyati.value(),
                        self.kategori.text()))
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Hata", "Bu stok kodu zaten mevcut!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class StokWidget(QWidget):
    def excel_yukle(self):
        path, _ = QFileDialog.getOpenFileName(self, "Excel Listesi Seç", "", "Excel Dosyası (*.xlsx)")
        if not path:
            return  # Şimdi doğru fonksiyonun içinde

        try:
            import pandas as pd
            df = pd.read_excel(path)
            # Veritabanı işlemleri buraya gelir...
            QMessageBox.information(self, "Başarılı", "Dosya işlendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        # Üst Panel (Başlık ve Araçlar)
        header = QHBoxLayout()
        title = QLabel("📦 Stok Yönetimi")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        # Arama Kutusu
        self.arama = QLineEdit()
        self.arama.setPlaceholderText("🔍 Stok adı veya kodu ile ara...")
        self.arama.setFixedWidth(250)
        self.arama.textChanged.connect(self.refresh)
        header.addWidget(self.arama)

        # Yeni Stok Butonu
        self.yeni_btn = QPushButton("➕ Yeni Stok")
        self.yeni_btn.clicked.connect(self._yeni)
        header.addWidget(self.yeni_btn)

        # --- EXCEL BUTONU BURADA ---
        self.btn_excel = QPushButton("📥 Excel'den Yükle")
        self.btn_excel.setObjectName("secondaryBtn") # Mavi/Gri stil için
        self.btn_excel.clicked.connect(self.excel_yukle)
        header.addWidget(self.btn_excel) # BUTONU LAYOUT'A EKLİYORUZ
        # ---------------------------

        layout.addLayout(header)

        # Stok Tablosu
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Stok Kodu", "Stok Adı", "Birim", 
            "Miktar", "Alış Fiyatı", "Satış Fiyatı", "Kategori"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.doubleClicked.connect(self._duzenle)
        
        layout.addWidget(self.tbl)

        btn_row = QHBoxLayout()
        duzenle_btn = QPushButton("✏️ Düzenle")
        duzenle_btn.setObjectName("secondaryBtn")
        duzenle_btn.clicked.connect(self._duzenle)
        sil_btn = QPushButton("🗑️ Sil")
        sil_btn.setObjectName("dangerBtn")
        sil_btn.clicked.connect(self._sil)
        btn_row.addWidget(duzenle_btn)
        btn_row.addWidget(sil_btn)
        btn_row.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #8b949e;")
        btn_row.addWidget(self.count_lbl)
        layout.addLayout(btn_row)

    def refresh(self):
        try:
            arama = self.arama.text().strip()
            with self.db.get_conn() as conn:
                rows = conn.execute("""
                    SELECT * FROM stoklar WHERE stok_kodu LIKE ? OR stok_adi LIKE ?
                    ORDER BY stok_adi
                """, (f"%{arama}%", f"%{arama}%")).fetchall()

            self.tbl.setRowCount(0)
            for r in rows:
                ri = self.tbl.rowCount()
                self.tbl.insertRow(ri)
                miktar = r["miktar"] or 0
                satis = r["satis_fiyati"] or 0
                cells = [
                    str(r["id"]), r["stok_kodu"], r["stok_adi"], r["birim"] or "Adet",
                    f"{miktar:,.3f}", f"₺{r['alis_fiyati'] or 0:,.4f}",
                    f"₺{satis:,.4f}"
                ]
                for ci, val in enumerate(cells):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if ci == 4 and miktar <= 0:
                        item.setForeground(QColor("#f85149"))
                    self.tbl.setItem(ri, ci, item)
            if hasattr(self, 'count_lbl') and self.count_lbl is not None:
                self.count_lbl.setText(f"Toplam: {len(rows)} stok")
        except Exception as e:
            print(f"Stok refresh error: {e}")

    def _yeni(self):
        dlg = StokDialog(self.db, parent=self)
        if dlg.exec():
            self.refresh()

    def _duzenle(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Lütfen bir stok seçin.")
            return
        stok_id = int(self.tbl.item(row, 0).text())
        dlg = StokDialog(self.db, stok_id, parent=self)
        if dlg.exec():
            self.refresh()

    def _sil(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        stok_id = int(self.tbl.item(row, 0).text())
        stok_adi = self.tbl.item(row, 2).text()
        reply = QMessageBox.question(
            self, "Silme Onayı", f"'{stok_adi}' stokunu silmek istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db.get_conn() as conn:
                    conn.execute("DELETE FROM stoklar WHERE id=?", (stok_id,))
                self.refresh()
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Hata", "Bu stoka ait fatura satırları var, silinemez!")

    def _excel_export(self):
        try:
            import pandas as pd
            with self.db.get_conn() as conn:
                rows = conn.execute("SELECT * FROM stoklar ORDER BY stok_adi").fetchall()
            data = [dict(r) for r in rows]
            if not data:
                QMessageBox.information(self, "Bilgi", "Dışa aktarılacak veri yok.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Excel Kaydet", "stoklar.xlsx", "Excel (*.xlsx)")
            if path:
                df = pd.DataFrame(data)
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Başarılı", f"Excel kaydedildi:\n{path}")
        except ImportError:
            QMessageBox.critical(self, "Hata", "pandas kurulu değil.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    def excel_yukle(self):
        # Dosya seçme penceresini açar
        path, _ = QFileDialog.getOpenFileName(self, "Excel Seç", "", "Excel Dosyası (*.xlsx)")
        if not path:
            return

        try:
            # Excel'i oku (Sütun isimleri: Malzeme No, Malzeme Adı, Miktar olmalı)
            df = pd.read_excel(path)
            
            with self.db.get_conn() as conn:
                for _, row in df.iterrows():
                    # Veritabanına ekle veya miktar güncelle
                    conn.execute('''
                        INSERT INTO stoklar (stok_kodu, stok_adi, miktar, birim)
                        VALUES (?, ?, ?, 'Adet')
                        ON CONFLICT(stok_kodu) DO UPDATE SET
                            miktar = miktar + EXCLUDED.miktar
                    ''', (str(row['Malzeme No']), str(row['Malzeme Adı']), float(row['Miktar'])))
                conn.commit()
            
            self.refresh() # Tabloyu anında günceller
            QMessageBox.information(self, "Başarılı", "Excel verileri stoğa eklendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yükleme sırasında hata oluştu:\n{str(e)}")


# ─────────────────────────────────────────────
#  FATURA MODÜLÜ
# ─────────────────────────────────────────────
class FaturaDialog(QDialog):
    # Tablo sütun indeksleri (gizli Stok ID dahil)
    COL_STOK_ID   = 0   # gizli
    COL_MAL_KODU  = 1
    COL_ACIKLAMA  = 2
    COL_BIRIM     = 3
    COL_MIKTAR    = 4
    COL_FIYAT_TL  = 5
    COL_KDV_ORAN  = 6
    COL_KDV_TL    = 7
    COL_TOPLAM_TL = 8
    COL_FIYAT_DOV = 9
    COL_TOPLAM_DOV= 10

    def __init__(self, db: DatabaseManager, usd_kur: float, eur_kur: float,
                fatura_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.usd_kur = usd_kur
        self.eur_kur = eur_kur
        self.fatura_id = fatura_id
        self.setWindowTitle("Yeni Fatura")
        self.setMinimumSize(1150, 700)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        self._load_cariler()
        self._load_stoklar()

    # ── UI İnşası ──────────────────────────────────────────────────────────
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(14, 14, 14, 14)

        # ── BAŞLIK GRUBU ──────────────────────────────────────────────────
        hg = QGroupBox("Fatura Bilgileri")
        hf = QGridLayout(hg)
        hf.setSpacing(8)
        hf.setColumnStretch(1, 2)
        hf.setColumnStretch(3, 2)

        self.fatura_no   = QLineEdit(f"FTR-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.cari_combo  = QComboBox(); self.cari_combo.setMinimumWidth(260)
        self.tarih       = QDateEdit(QDate.currentDate()); self.tarih.setCalendarPopup(True)
        self.fatura_tipi = QComboBox(); self.fatura_tipi.addItems(["SATIS", "ALIS"])
        self.fatura_tipi.currentTextChanged.connect(self._tip_degisti)
        self.doviz_birimi = QComboBox(); self.doviz_birimi.addItems(["TL", "USD", "EUR"])
        self.doviz_birimi.currentTextChanged.connect(self._doviz_degisti)
        self.doviz_kuru   = QDoubleSpinBox()
        self.doviz_kuru.setRange(0.0001, 999999); self.doviz_kuru.setDecimals(4)
        self.doviz_kuru.setValue(1.0)
        self.doviz_kuru.valueChanged.connect(self._kur_degisti)
        self.notlar = QLineEdit(); self.notlar.setPlaceholderText("Opsiyonel not...")

        hf.addWidget(QLabel("Fatura No:"),    0, 0); hf.addWidget(self.fatura_no,    0, 1)
        hf.addWidget(QLabel("Cari:"),         0, 2); hf.addWidget(self.cari_combo,   0, 3)
        hf.addWidget(QLabel("Tarih:"),        1, 0); hf.addWidget(self.tarih,        1, 1)
        hf.addWidget(QLabel("Fatura Tipi:"),  1, 2); hf.addWidget(self.fatura_tipi,  1, 3)
        hf.addWidget(QLabel("Döviz:"),        2, 0); hf.addWidget(self.doviz_birimi, 2, 1)
        hf.addWidget(QLabel("Döviz Kuru (₺):"),2, 2); hf.addWidget(self.doviz_kuru, 2, 3)
        hf.addWidget(QLabel("Not:"),          3, 0); hf.addWidget(self.notlar,       3, 1, 1, 3)
        self.stok_etkile_cb = QCheckBox("Bu faturadaki ürünleri stok miktarlarından düş/ekle")
        self.stok_etkile_cb.setChecked(True) # Varsayılan olarak işaretli
        hf.addWidget(self.stok_etkile_cb, 4, 0, 1, 4) # 4. satıra ekliyoruz
        main.addWidget(hg)

        # ── SATIR EKLEME BÖLÜMÜ ───────────────────────────────────────────
        sg = QGroupBox("Satır Ekle")
        sl = QGridLayout(sg)
        sl.setSpacing(8)
        sl.setColumnStretch(1, 2)
        sl.setColumnStretch(3, 3)

        # Satır 1: Malzeme kodu + Açıklama + Birim
        self.satir_mal_kodu = QLineEdit()
        self.satir_mal_kodu.setPlaceholderText("Malzeme Kodu (ör: STK001)")
        self.satir_mal_kodu.setMinimumWidth(130)
        self.satir_mal_kodu.textChanged.connect(self._kodu_ile_stok_bul)

        self.satir_aciklama = QLineEdit()
        self.satir_aciklama.setPlaceholderText("Malzeme Açıklaması")
        self.satir_aciklama.setMinimumWidth(220)

        self.satir_birim = QComboBox()
        self.satir_birim.addItems(["Adet", "KG", "LT", "MT", "M2", "M3", "Paket", "Kutu", "Ton"])
        self.satir_birim.setFixedWidth(80)

        sl.addWidget(QLabel("Mal. Kodu:"),   0, 0)
        sl.addWidget(self.satir_mal_kodu,    0, 1)
        sl.addWidget(QLabel("Açıklama:"),    0, 2)
        sl.addWidget(self.satir_aciklama,    0, 3)
        sl.addWidget(QLabel("Birim:"),       0, 4)
        sl.addWidget(self.satir_birim,       0, 5)

        # Satır 2: Miktar + Fiyat + KDV + Ekle butonu
        self.satir_miktar = QDoubleSpinBox()
        self.satir_miktar.setRange(0.001, 9999999)
        self.satir_miktar.setDecimals(3)
        self.satir_miktar.setValue(1)
        self.satir_miktar.setMinimumWidth(110)

        self.satir_fiyat = QDoubleSpinBox()
        self.satir_fiyat.setRange(0, 99999999)
        self.satir_fiyat.setDecimals(4)
        self.satir_fiyat.setMinimumWidth(130)

        self.satir_kdv = QComboBox()
        self.satir_kdv.addItems(["0", "1", "8", "10", "18", "20"])
        self.satir_kdv.setCurrentText("20")
        self.satir_kdv.setFixedWidth(70)

        ekle_btn = QPushButton("➕ Satır Ekle")
        ekle_btn.setFixedHeight(34)
        ekle_btn.clicked.connect(self._satir_ekle)

        sl.addWidget(QLabel("Miktar:"),          1, 0)
        sl.addWidget(self.satir_miktar,          1, 1)
        sl.addWidget(QLabel("Birim Fiyat (₺):"), 1, 2)
        sl.addWidget(self.satir_fiyat,           1, 3)
        sl.addWidget(QLabel("KDV %:"),           1, 4)
        sl.addWidget(self.satir_kdv,             1, 5)
        sl.addWidget(ekle_btn,                   1, 6)

        # Stok arama ipucu
        self.stok_ipucu = QLabel("💡 Malzeme kodunu yazınca stoktaki ürün otomatik bulunur. Yeni ürün yazabilirsiniz.")
        self.stok_ipucu.setStyleSheet("color: #8b949e; font-size: 11px; padding: 2px 0;")
        sl.addWidget(self.stok_ipucu, 2, 0, 1, 7)

        main.addWidget(sg)

        # Gizli: eşleşen stok id'si (None = yeni stok)
        self._satir_stok_id: Optional[int] = None

        # ── SATIR TABLOSU ─────────────────────────────────────────────────
        tg = QGroupBox("Fatura Satırları")
        tl = QVBoxLayout(tg)

        self.satirlar_tbl = QTableWidget(0, 11)
        self.satirlar_tbl.setHorizontalHeaderLabels([
            "Stok ID",          # 0 gizli
            "Malzeme Kodu",     # 1
            "Malzeme Açıklaması",# 2
            "Birim",            # 3
            "Miktar",           # 4
            "Birim Fiyat TL",   # 5
            "KDV %",            # 6
            "KDV Tutarı TL",    # 7
            "Toplam TL",        # 8
            "Birim Fiyat Döviz",# 9
            "Toplam Döviz",     # 10
        ])
        self.satirlar_tbl.setColumnHidden(0, True)
        hdr = self.satirlar_tbl.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [1, 3, 4, 5, 6, 7, 8, 9, 10]:
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.satirlar_tbl.setMinimumHeight(220)
        self.satirlar_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.satirlar_tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tl.addWidget(self.satirlar_tbl)

        # Satır sil + toplamlar
        bot = QHBoxLayout()
        sil_btn = QPushButton("🗑️ Seçili Satırı Sil")
        sil_btn.setObjectName("dangerBtn")
        sil_btn.clicked.connect(self._satir_sil)
        bot.addWidget(sil_btn)
        bot.addStretch()

        # Özet sağ taraf
        ozet = QGridLayout()
        ozet.setHorizontalSpacing(16)
        ozet.setVerticalSpacing(4)
        lbl_style  = "color: #8b949e; font-size: 12px;"
        val_style  = "color: #e0e0e0; font-weight: bold; font-size: 13px;"
        vat_style  = "color: #d29922; font-weight: bold; font-size: 13px;"
        tot_style  = "color: #2ea043; font-weight: bold; font-size: 15px;"
        dov_style  = "color: #1f6feb; font-weight: bold; font-size: 13px;"

        def _lbl(txt, style):
            l = QLabel(txt); l.setStyleSheet(style); return l

        self.lbl_ara    = _lbl("₺0,00", val_style)
        self.lbl_kdv    = _lbl("₺0,00", vat_style)
        self.lbl_genel  = _lbl("₺0,00", tot_style)
        self.lbl_doviz  = _lbl("",      dov_style)

        ozet.addWidget(_lbl("Mal/Hizmet Toplam:", lbl_style), 0, 0)
        ozet.addWidget(self.lbl_ara,   0, 1)
        ozet.addWidget(_lbl("Hesaplanan KDV:",    lbl_style), 1, 0)
        ozet.addWidget(self.lbl_kdv,   1, 1)
        ozet.addWidget(_lbl("Ödenecek Tutar:",    lbl_style), 2, 0)
        ozet.addWidget(self.lbl_genel, 2, 1)
        ozet.addWidget(_lbl("Döviz Tutarı:",      lbl_style), 3, 0)
        ozet.addWidget(self.lbl_doviz, 3, 1)
        bot.addLayout(ozet)
        tl.addLayout(bot)
        main.addWidget(tg)

        # ── ALT BUTONLAR ──────────────────────────────────────────────────
        btnrow = QHBoxLayout()
        btnrow.addStretch()
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("secondaryBtn")
        iptal_btn.clicked.connect(self.reject)
        kaydet_btn = QPushButton("💾 Faturayı Kaydet")
        kaydet_btn.setMinimumWidth(160)
        kaydet_btn.clicked.connect(self._build_ui)
        btnrow.addWidget(iptal_btn)
        btnrow.addWidget(kaydet_btn)
        main.addLayout(btnrow)

    # ── Yardımcı Yükleyiciler ─────────────────────────────────────────────
    def _load_cariler(self):
        self.cari_combo.clear()
        with self.db.get_conn() as conn:
            rows = conn.execute("SELECT id, unvan FROM cariler ORDER BY unvan").fetchall()
        for r in rows:
            self.cari_combo.addItem(r["unvan"], r["id"])

    def _load_stoklar(self):
        """Stok listesini hafızaya al — combo yok artık, kod ile aranıyor."""
        with self.db.get_conn() as conn:
            rows = conn.execute("SELECT * FROM stoklar ORDER BY stok_kodu").fetchall()
        self.stok_rows = list(rows)
        # kod → stok satırı eşlemesi (hızlı arama için)
        self.stok_by_kod = {r["stok_kodu"].upper(): r for r in rows}

    def _kodu_ile_stok_bul(self, kod: str):
        """Malzeme kodu yazılınca stoktaki eşleşmeyi otomatik doldur."""
        kod = kod.strip().upper()
        stok = self.stok_by_kod.get(kod)
        if stok:
            self.satir_aciklama.setText(stok["stok_adi"] or "")
            idx = self.satir_birim.findText(stok["birim"] or "Adet")
            if idx >= 0:
                self.satir_birim.setCurrentIndex(idx)
            tip = self.fatura_tipi.currentText()
            fiyat = stok["alis_fiyati"] if tip == "ALIS" else stok["satis_fiyati"]
            self.satir_fiyat.setValue(float(fiyat or 0))
            self._satir_stok_id = stok["id"]
            self.stok_ipucu.setText(
                f"✅ Stok bulundu: {stok['stok_adi']}  |  Mevcut: {stok['miktar']:,.3f} {stok['birim'] or 'Adet'}"
            )
            self.stok_ipucu.setStyleSheet("color: #2ea043; font-size: 11px; padding: 2px 0;")
        else:
            self._satir_stok_id = None
            if kod:
                self.stok_ipucu.setText("🆕 Stokta bulunamadı — alış faturasında yeni stok olarak eklenecek.")
                self.stok_ipucu.setStyleSheet("color: #d29922; font-size: 11px; padding: 2px 0;")
            else:
                self.stok_ipucu.setText("💡 Malzeme kodunu yazınca stoktaki ürün otomatik bulunur. Yeni ürün yazabilirsiniz.")
                self.stok_ipucu.setStyleSheet("color: #8b949e; font-size: 11px; padding: 2px 0;")

    def _tip_degisti(self, tip: str):
        """Fatura tipi değişince fiyatı yenile."""
        self._kodu_ile_stok_bul(self.satir_mal_kodu.text())

    def _doviz_degisti(self, doviz: str):
        kur_map = {"TL": 1.0, "USD": self.usd_kur, "EUR": self.eur_kur}
        self.doviz_kuru.setValue(kur_map.get(doviz, 1.0))
        self._doviz_kolonlari_goster(doviz != "TL")
        self._update_toplam()

    def _kur_degisti(self):
        self._update_toplam()

    def _doviz_kolonlari_goster(self, goster: bool):
        self.satirlar_tbl.setColumnHidden(self.COL_FIYAT_DOV,  not goster)
        self.satirlar_tbl.setColumnHidden(self.COL_TOPLAM_DOV, not goster)

    # ── Satır Ekleme ──────────────────────────────────────────────────────
    def _satir_ekle(self):
        mal_kodu   = self.satir_mal_kodu.text().strip()
        aciklama   = self.satir_aciklama.text().strip()
        birim      = self.satir_birim.currentText()
        miktar     = self.satir_miktar.value()
        fiyat      = self.satir_fiyat.value()
        kdv_oran   = float(self.satir_kdv.currentText())
        kur        = self.doviz_kuru.value() or 1.0
        doviz      = self.doviz_birimi.currentText()
        fatura_tip = self.fatura_tipi.currentText()

        # Zorunlu alan kontrolü
        if not mal_kodu:
            QMessageBox.warning(self, "Eksik Bilgi", "Malzeme kodu zorunludur!")
            self.satir_mal_kodu.setFocus()
            return
        if not aciklama:
            QMessageBox.warning(self, "Eksik Bilgi", "Açıklama zorunludur!")
            self.satir_aciklama.setFocus()
            return

        stok_id = self._satir_stok_id  # None = stokta yok

        # SATIS: stokta olmayan ürün satılamaz
        if fatura_tip == "SATIS" and stok_id is None:
            QMessageBox.critical(
                self, "Stok Bulunamadı",
                f"'{mal_kodu}' kodu stokta kayıtlı değil.\n"
                "Satış faturasına yalnızca kayıtlı stoklar eklenebilir.\n\n"
                "Önce Stoklar menüsünden bu ürünü ekleyin."
            )
            return

        # SATIS: stok miktarı kontrolü
        if fatura_tip == "SATIS" and stok_id is not None:
            stok = next((s for s in self.stok_rows if s["id"] == stok_id), None)
            if stok:
                mevcut = float(stok["miktar"] or 0)
                zaten_eklenen = 0.0
                for ri in range(self.satirlar_tbl.rowCount()):
                    sid_item = self.satirlar_tbl.item(ri, self.COL_STOK_ID)
                    if sid_item and sid_item.text() == str(stok_id):
                        try:
                            zaten_eklenen += float(
                                self.satirlar_tbl.item(ri, self.COL_MIKTAR)
                                .text().replace(",", "")
                            )
                        except Exception:
                            pass
                kalan = mevcut - zaten_eklenen
                if miktar > kalan:
                    cevap = QMessageBox.question(
                        self, "Stok Yetersiz",
                        f"'{aciklama}' için mevcut stok: {kalan:,.3f} {birim}\n"
                        f"Girilen miktar: {miktar:,.3f}\n\n"
                        f"Stok eksiye düşecek. Yine de eklemek istiyor musunuz?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if cevap == QMessageBox.StandardButton.No:
                        return

        # Hesaplamalar
        ara_toplam  = miktar * fiyat
        kdv_tutari  = ara_toplam * kdv_oran / 100
        genel_satir = ara_toplam + kdv_tutari
        dov_sym     = {"USD": "$", "EUR": "€"}.get(doviz, "")
        doviz_fiyat = fiyat / kur if doviz != "TL" else 0.0
        doviz_top   = genel_satir / kur if doviz != "TL" else 0.0

        # Tabloya ekle
        ri = self.satirlar_tbl.rowCount()
        self.satirlar_tbl.insertRow(ri)

        def _item(val, align=Qt.AlignmentFlag.AlignCenter):
            it = QTableWidgetItem(str(val))
            it.setTextAlignment(align)
            return it

        # stok_id yerine "YENİ" yazacak — kayıtta oluşturulacak
        self.satirlar_tbl.setItem(ri, self.COL_STOK_ID,
                                _item(str(stok_id) if stok_id is not None else "YENİ"))
        self.satirlar_tbl.setItem(ri, self.COL_MAL_KODU,  _item(mal_kodu))
        self.satirlar_tbl.setItem(ri, self.COL_ACIKLAMA,
                                _item(aciklama, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
        self.satirlar_tbl.setItem(ri, self.COL_BIRIM,     _item(birim))
        self.satirlar_tbl.setItem(ri, self.COL_MIKTAR,    _item(f"{miktar:,.3f}"))
        self.satirlar_tbl.setItem(ri, self.COL_FIYAT_TL,  _item(f"₺{fiyat:,.4f}"))
        self.satirlar_tbl.setItem(ri, self.COL_KDV_ORAN,  _item(f"%{kdv_oran:.0f}"))

        it_kdv = _item(f"₺{kdv_tutari:,.2f}")
        it_kdv.setForeground(QColor("#d29922"))
        self.satirlar_tbl.setItem(ri, self.COL_KDV_TL, it_kdv)

        it_top = _item(f"₺{genel_satir:,.2f}")
        it_top.setForeground(QColor("#2ea043"))
        self.satirlar_tbl.setItem(ri, self.COL_TOPLAM_TL, it_top)

        self.satirlar_tbl.setItem(ri, self.COL_FIYAT_DOV,
                                _item(f"{dov_sym}{doviz_fiyat:,.4f}" if doviz != "TL" else ""))
        self.satirlar_tbl.setItem(ri, self.COL_TOPLAM_DOV,
                                _item(f"{dov_sym}{doviz_top:,.2f}" if doviz != "TL" else ""))

        # YENİ satıra sarı arka plan ver (bilgi amaçlı)
        if stok_id is None:
            for c in range(1, 11):
                item = self.satirlar_tbl.item(ri, c)
                if item:
                    item.setBackground(QColor("#2d2500"))

        # Alanları temizle
        self.satir_mal_kodu.clear()
        self.satir_aciklama.clear()
        self.satir_fiyat.setValue(0)
        self.satir_miktar.setValue(1)
        self._satir_stok_id = None
        self.stok_ipucu.setText("💡 Malzeme kodunu yazınca stoktaki ürün otomatik bulunur. Yeni ürün yazabilirsiniz.")
        self.stok_ipucu.setStyleSheet("color: #8b949e; font-size: 11px; padding: 2px 0;")
        self.satir_mal_kodu.setFocus()

        self._update_toplam()

    def _satir_sil(self):
        row = self.satirlar_tbl.currentRow()
        if row >= 0:
            self.satirlar_tbl.removeRow(row)
            self._update_toplam()

    # ── Toplam Hesaplama ──────────────────────────────────────────────────
    def _parse_tl(self, item) -> float:
        if not item:
            return 0.0
        try:
            return float(item.text().replace("₺", "").replace(",", "").strip())
        except ValueError:
            return 0.0

    def _update_toplam(self):
        ara = 0.0
        kdv = 0.0
        for ri in range(self.satirlar_tbl.rowCount()):
            kdv_item = self.satirlar_tbl.item(ri, self.COL_KDV_TL)
            top_item = self.satirlar_tbl.item(ri, self.COL_TOPLAM_TL)
            top_val  = self._parse_tl(top_item)
            kdv_val  = self._parse_tl(kdv_item)
            kdv += kdv_val
            ara += (top_val - kdv_val)

        genel = ara + kdv
        kur   = self.doviz_kuru.value() or 1.0
        doviz = self.doviz_birimi.currentText()
        dov_sym = {"USD": "$", "EUR": "€"}.get(doviz, "")

        self.lbl_ara.setText(f"₺{ara:,.2f}")
        self.lbl_kdv.setText(f"₺{kdv:,.2f}")
        self.lbl_genel.setText(f"₺{genel:,.2f}")
        if doviz != "TL":
            self.lbl_doviz.setText(f"{dov_sym}{genel / kur:,.2f}  (Kur: {kur:.4f})")
        else:
            self.lbl_doviz.setText("—")

    # ── Kaydet ────────────────────────────────────────────────────────────
def _kaydet(self):
        if self.satirlar_tbl.rowCount() == 0:
            QMessageBox.warning(self, "Hata", "En az bir fatura satırı ekleyin!")
            return
        cari_id = self.cari_combo.currentData()
        if not cari_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir cari seçin!")
            return

        fatura_no    = self.fatura_no.text().strip()
        tarih        = self.tarih.date().toString("yyyy-MM-dd")
        fatura_tipi  = self.fatura_tipi.currentText()
        doviz_birimi = self.doviz_birimi.currentText()
        doviz_kuru   = self.doviz_kuru.value() or 1.0
        notlar       = self.notlar.text().strip()

        # Satır verilerini topla
        satirlar   = []
        ara_toplam = 0.0
        kdv_toplam = 0.0

        for ri in range(self.satirlar_tbl.rowCount()):
            stok_id_raw = self.satirlar_tbl.item(ri, self.COL_STOK_ID).text()
            stok_id     = None if stok_id_raw == "YENİ" else int(stok_id_raw)
            mal_kodu    = self.satirlar_tbl.item(ri, self.COL_MAL_KODU).text()
            aciklama    = self.satirlar_tbl.item(ri, self.COL_ACIKLAMA).text()
            birim       = self.satirlar_tbl.item(ri, self.COL_BIRIM).text()
            miktar      = float(self.satirlar_tbl.item(ri, self.COL_MIKTAR).text().replace(",", ""))
            birim_fiyat = self._parse_tl(self.satirlar_tbl.item(ri, self.COL_FIYAT_TL))
            kdv_oran    = float(self.satirlar_tbl.item(ri, self.COL_KDV_ORAN).text().replace("%", ""))
            kdv_tutar   = self._parse_tl(self.satirlar_tbl.item(ri, self.COL_KDV_TL))
            satir_top   = self._parse_tl(self.satirlar_tbl.item(ri, self.COL_TOPLAM_TL))
            ara_t       = satir_top - kdv_tutar

            ara_toplam += ara_t
            kdv_toplam += kdv_tutar

            doviz_tutari = satir_top / doviz_kuru if doviz_birimi != "TL" else satir_top
            satirlar.append({
                "stok_id":         stok_id,
                "mal_kodu":        mal_kodu,
                "aciklama":        aciklama,
                "birim":           birim,
                "miktar":          miktar,
                "birim_fiyat":     birim_fiyat,
                "kdv_orani":       kdv_oran,
                "kdv_tutari":      kdv_tutar,
                "satir_top":       ara_t,
                "satir_kdv_dahil": satir_top,
                "doviz_tutari":    doviz_tutari,
            })

        genel_toplam    = ara_toplam + kdv_toplam
        doviz_tut_genel = genel_toplam / doviz_kuru if doviz_birimi != "TL" else genel_toplam

        try:
            with self.db.get_conn() as conn:
                conn.execute("BEGIN")

                # 1. Fatura başlığı kaydı
                cur = conn.execute("""
                    INSERT INTO faturalar
                        (fatura_no, cari_id, tarih, fatura_tipi, genel_toplam,
                        doviz_birimi, doviz_kuru, doviz_tutari, notlar, kdv_toplam)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (fatura_no, cari_id, tarih, fatura_tipi, genel_toplam,
                    doviz_birimi, doviz_kuru, doviz_tut_genel, notlar, kdv_toplam))
                fatura_id = cur.lastrowid

                for s in satirlar:
                    sid = s["stok_id"]

                    # 2. Yeni stok kartı oluşturma (Eğer stokta yoksa ve ALIŞ ise)
                    if sid is None:
                        if fatura_tipi != "ALIS":
                            raise Exception(f"'{s['mal_kodu']}' stokta kayıtlı değil, satış yapılamaz!")
                        
                        cur2 = conn.execute("""
                            INSERT INTO stoklar
                                (stok_kodu, stok_adi, birim, miktar, alis_fiyati, satis_fiyati, kategori)
                            VALUES (?, ?, ?, 0, ?, ?, 'Genel')
                        """, (s["mal_kodu"], s["aciklama"], s["birim"], s["birim_fiyat"], s["birim_fiyat"]))
                        sid = cur2.lastrowid

                    # 3. Fatura satırı kaydı
                    conn.execute("""
                        INSERT INTO fatura_satirlari
                            (fatura_id, stok_id, malzeme_kodu, miktar, birim_fiyat,
                            kdv_orani, kdv_tutari, satir_toplami, satir_kdv_dahil,
                            doviz_birimi, doviz_kuru, doviz_tutari)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (fatura_id, sid, s["mal_kodu"], s["miktar"], s["birim_fiyat"],
                        s["kdv_orani"], s["kdv_tutari"], s["satir_top"], s["satir_kdv_dahil"],
                        doviz_birimi, doviz_kuru, s["doviz_tutari"]))

                    # 4. STOK MİKTARI GÜNCELLEME (Checkbox Kontrolü)
                    if self.stok_etkile_cb.isChecked():
                        if fatura_tipi == "ALIS":
                            conn.execute(
                                "UPDATE stoklar SET miktar = miktar + ? WHERE id=?",
                                (s["miktar"], sid)
                            )
                        else:
                            conn.execute(
                                "UPDATE stoklar SET miktar = miktar - ? WHERE id=?",
                                (s["miktar"], sid)
                            )

                # 5. Cari bakiye güncelleme (Bu işlem her zaman yapılır)
                tl_degisim  = genel_toplam if fatura_tipi == "SATIS" else -genel_toplam
                usd_degisim = (doviz_tut_genel if doviz_birimi == "USD" else 0.0)
                eur_degisim = (doviz_tut_genel if doviz_birimi == "EUR" else 0.0)
                if fatura_tipi == "ALIS":
                    usd_degisim = -usd_degisim
                    eur_degisim = -eur_degisim

                conn.execute("""
                    UPDATE cariler
                    SET bakiye_tl   = bakiye_tl   + ?,
                        bakiye_usd  = bakiye_usd  + ?,
                        bakiye_eur  = COALESCE(bakiye_eur, 0) + ?
                    WHERE id = ?
                """, (tl_degisim, usd_degisim, eur_degisim, cari_id))

                # 6. Kur geçmişi
                conn.execute(
                    "INSERT INTO kur_gecmisi (tarih, usd_kur, eur_kur) VALUES (?,?,?)",
                    (tarih, self.usd_kur, self.eur_kur)
                )

                conn.execute("COMMIT")

            QMessageBox.information(self, "✅ Başarılı", f"Fatura '{fatura_no}' kaydedildi.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "İşlem Hatası", f"Fatura kaydedilemedi:\n{str(e)}")
# ─────────────────────────────────────────────
#  ÖDEME DİALOGU
# ─────────────────────────────────────────────
class OdemeDialog(QDialog):
    def __init__(self, db: DatabaseManager, fatura_id: int, usd_kur: float, eur_kur: float, parent=None):
        super().__init__(parent)
        self.db       = db
        self.fatura_id = fatura_id
        self.usd_kur  = usd_kur
        self.eur_kur  = eur_kur
        self.setWindowTitle("Ödeme Ekle")
        self.setMinimumWidth(520)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        self._load_fatura_bilgi()
        self._load_odemeler()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Fatura özet bilgisi
        self.ozet_lbl = QLabel("")
        self.ozet_lbl.setStyleSheet(
            "background-color: #161b22; border: 1px solid #30363d; "
            "border-radius: 6px; padding: 10px; color: #c9d1d9; font-size: 13px;"
        )
        self.ozet_lbl.setWordWrap(True)
        layout.addWidget(self.ozet_lbl)

        # Ödeme giriş formu
        form_group = QGroupBox("Yeni Ödeme")
        form = QGridLayout(form_group)
        form.setSpacing(10)

        self.odeme_tarih = QDateEdit(QDate.currentDate())
        self.odeme_tarih.setCalendarPopup(True)

        self.odeme_tutar = QDoubleSpinBox()
        self.odeme_tutar.setRange(0.01, 99999999)
        self.odeme_tutar.setDecimals(2)
        self.odeme_tutar.setMinimumWidth(150)
        self.odeme_tutar.valueChanged.connect(self._tutar_degisti)

        self.odeme_doviz = QComboBox()
        self.odeme_doviz.addItems(["TL", "USD", "EUR"])
        self.odeme_doviz.currentTextChanged.connect(self._doviz_degisti)

        self.odeme_kuru = QDoubleSpinBox()
        self.odeme_kuru.setRange(0.0001, 999999)
        self.odeme_kuru.setDecimals(4)
        self.odeme_kuru.setValue(1.0)
        self.odeme_kuru.valueChanged.connect(self._tutar_degisti)

        self.odeme_yontemi = QComboBox()
        self.odeme_yontemi.addItems(["Nakit", "Banka Transferi", "Çek", "Senet", "Kredi Kartı", "Diğer"])

        self.odeme_aciklama = QLineEdit()
        self.odeme_aciklama.setPlaceholderText("Opsiyonel açıklama...")

        self.tl_karsilik_lbl = QLabel("TL Karşılığı: ₺0,00")
        self.tl_karsilik_lbl.setStyleSheet("color: #2ea043; font-weight: bold;")

        form.addWidget(QLabel("Tarih:"),        0, 0); form.addWidget(self.odeme_tarih,   0, 1)
        form.addWidget(QLabel("Tutar:"),        0, 2); form.addWidget(self.odeme_tutar,   0, 3)
        form.addWidget(QLabel("Döviz:"),        1, 0); form.addWidget(self.odeme_doviz,   1, 1)
        form.addWidget(QLabel("Kur (₺):"),      1, 2); form.addWidget(self.odeme_kuru,    1, 3)
        form.addWidget(QLabel("Yöntem:"),       2, 0); form.addWidget(self.odeme_yontemi, 2, 1)
        form.addWidget(QLabel("Açıklama:"),     2, 2); form.addWidget(self.odeme_aciklama,2, 3)
        form.addWidget(self.tl_karsilik_lbl,    3, 0, 1, 4)
        layout.addWidget(form_group)

        ekle_btn = QPushButton("💳 Ödeme Ekle")
        ekle_btn.clicked.connect(self._odeme_ekle)
        layout.addWidget(ekle_btn)

        # Geçmiş ödemeler
        gecmis_lbl = QLabel("📋 Ödeme Geçmişi")
        gecmis_lbl.setStyleSheet("color: #c9d1d9; font-weight: bold; font-size: 14px;")
        layout.addWidget(gecmis_lbl)

        self.odeme_tbl = QTableWidget(0, 6)
        self.odeme_tbl.setHorizontalHeaderLabels([
            "Tarih", "Tutar TL", "Döviz", "Kur", "Yöntem", "Açıklama"
        ])
        self.odeme_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.odeme_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.odeme_tbl.setMaximumHeight(180)
        layout.addWidget(self.odeme_tbl)

        # Alt butonlar
        btn_row = QHBoxLayout()
        self.odeme_sil_btn = QPushButton("🗑️ Seçili Ödemeyi Sil")
        self.odeme_sil_btn.setObjectName("dangerBtn")
        self.odeme_sil_btn.clicked.connect(self._odeme_sil)
        btn_row.addWidget(self.odeme_sil_btn)
        btn_row.addStretch()
        kapat_btn = QPushButton("Kapat")
        kapat_btn.setObjectName("secondaryBtn")
        kapat_btn.clicked.connect(self.accept)
        btn_row.addWidget(kapat_btn)
        layout.addLayout(btn_row)

    def _load_fatura_bilgi(self):
        with self.db.get_conn() as conn:
            row = conn.execute("""
                SELECT f.*, c.unvan, c.cari_tipi
                FROM faturalar f JOIN cariler c ON f.cari_id = c.id
                WHERE f.id = ?
            """, (self.fatura_id,)).fetchone()
        if not row:
            return
        self._fatura = dict(row)
        genel   = row["genel_toplam"] or 0
        odenen  = row["odenen_toplam"] if "odenen_toplam" in row.keys() else 0
        kalan   = genel - (odenen or 0)
        durum   = row["odeme_durumu"] if "odeme_durumu" in row.keys() else "BEKLIYOR"

        # Ödeme yönü: SATIS → müşteriden alacak, ALIS → tedarikçiye borç
        yon = "Müşteriden Alacak" if row["fatura_tipi"] == "SATIS" else "Tedarikçiye Borç"

        self.ozet_lbl.setText(
            f"<b>Fatura No:</b> {row['fatura_no']}  |  "
            f"<b>Cari:</b> {row['unvan']}  |  "
            f"<b>Tip:</b> {row['fatura_tipi']}  ({yon})<br>"
            f"<b>Genel Toplam:</b> ₺{genel:,.2f}  |  "
            f"<b>Ödenen:</b> ₺{odenen or 0:,.2f}  |  "
            f"<b>Kalan:</b> <span style='color:#f85149;font-weight:bold;'>₺{kalan:,.2f}</span>  |  "
            f"<b>Durum:</b> {durum}"
        )
        # Kalan tutarı varsayılan olarak doldur
        self.odeme_tutar.setValue(max(0.01, kalan))

    def _load_odemeler(self):
        with self.db.get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM odemeler WHERE fatura_id=? ORDER BY tarih DESC
            """, (self.fatura_id,)).fetchall()
        self.odeme_tbl.setRowCount(0)
        for r in rows:
            ri = self.odeme_tbl.rowCount()
            self.odeme_tbl.insertRow(ri)
            dov = r["doviz_birimi"] or "TL"
            dov_sym = {"USD": "$", "EUR": "€"}.get(dov, "")
            dov_str = f"{dov_sym}{r['doviz_tutari']:,.2f}" if dov != "TL" else "TL"
            cells = [
                r["tarih"],
                f"₺{r['tutar_tl']:,.2f}",
                dov_str,
                f"₺{r['doviz_kuru']:,.4f}" if dov != "TL" else "—",
                r["odeme_yontemi"] or "Nakit",
                r["aciklama"] or ""
            ]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if ci == 1:
                    item.setForeground(QColor("#2ea043"))
                self.odeme_tbl.setItem(ri, ci, item)

    def _doviz_degisti(self, doviz: str):
        kur_map = {"TL": 1.0, "USD": self.usd_kur, "EUR": self.eur_kur}
        self.odeme_kuru.setValue(kur_map.get(doviz, 1.0))
        self.odeme_kuru.setEnabled(doviz != "TL")
        self._tutar_degisti()

    def _tutar_degisti(self):
        tutar  = self.odeme_tutar.value()
        doviz  = self.odeme_doviz.currentText()
        kur    = self.odeme_kuru.value() or 1.0
        if doviz == "TL":
            tl = tutar
        else:
            tl = tutar * kur
            dov_sym = {"USD": "$", "EUR": "€"}.get(doviz, "")
            self.tl_karsilik_lbl.setText(
                f"TL Karşılığı: ₺{tl:,.2f}  ({dov_sym}{tutar:,.2f} × {kur:.4f})"
            )
            return
        self.tl_karsilik_lbl.setText(f"TL Karşılığı: ₺{tl:,.2f}")

    def _odeme_ekle(self):
        tutar  = self.odeme_tutar.value()
        doviz  = self.odeme_doviz.currentText()
        kur    = self.odeme_kuru.value() or 1.0
        tarih  = self.odeme_tarih.date().toString("yyyy-MM-dd")
        yontem = self.odeme_yontemi.currentText()
        aciklama = self.odeme_aciklama.text().strip()

        tutar_tl     = tutar if doviz == "TL" else tutar * kur
        doviz_tutari = tutar if doviz != "TL" else 0.0

        try:
            with self.db.get_conn() as conn:
                conn.execute("BEGIN")

                # Ödeme kaydı
                conn.execute("""
                    INSERT INTO odemeler
                        (fatura_id, cari_id, tarih, tutar_tl, doviz_birimi,
                        doviz_kuru, doviz_tutari, odeme_yontemi, aciklama)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (self.fatura_id, self._fatura["cari_id"], tarih, tutar_tl,
                    doviz, kur, doviz_tutari, yontem, aciklama))

                # Fatura odenen_toplam güncelle
                conn.execute("""
                    UPDATE faturalar
                    SET odenen_toplam = COALESCE(odenen_toplam, 0) + ?
                    WHERE id = ?
                """, (tutar_tl, self.fatura_id))

                # Ödeme durumunu belirle
                row = conn.execute(
                    "SELECT genel_toplam, odenen_toplam FROM faturalar WHERE id=?",
                    (self.fatura_id,)
                ).fetchone()
                genel  = row["genel_toplam"] or 0
                odenen = row["odenen_toplam"] if "odenen_toplam" in row.keys() else \
                        conn.execute("SELECT odenen_toplam FROM faturalar WHERE id=?",
                                    (self.fatura_id,)).fetchone()["odenen_toplam"] or 0

                if odenen >= genel:
                    durum = "ODENDI"
                elif odenen > 0:
                    durum = "KISMI"
                else:
                    durum = "BEKLIYOR"

                conn.execute(
                    "UPDATE faturalar SET odeme_durumu=? WHERE id=?",
                    (durum, self.fatura_id)
                )

                # Cari bakiye düş (ödeme yapıldı → borç/alacak azalır)
                # SATIS faturası: müşteri ödedi → alacak azalır (-TL)
                # ALIS faturası:  biz ödedik    → borç azalır  (+TL, çünkü bakiye negatif)
                fatura_tipi = self._fatura["fatura_tipi"]
                tl_degisim  = -tutar_tl if fatura_tipi == "SATIS" else tutar_tl
                usd_deg     = -doviz_tutari if doviz == "USD" and fatura_tipi == "SATIS" \
                            else doviz_tutari if doviz == "USD" else 0.0
                eur_deg     = -doviz_tutari if doviz == "EUR" and fatura_tipi == "SATIS" \
                            else doviz_tutari if doviz == "EUR" else 0.0

                conn.execute("""
                    UPDATE cariler
                    SET bakiye_tl  = bakiye_tl  + ?,
                        bakiye_usd = bakiye_usd + ?,
                        bakiye_eur = COALESCE(bakiye_eur,0) + ?
                    WHERE id = ?
                """, (tl_degisim, usd_deg, eur_deg, self._fatura["cari_id"]))

                conn.execute("COMMIT")

            QMessageBox.information(self, "✅ Ödeme Eklendi",
                f"₺{tutar_tl:,.2f} ödeme başarıyla kaydedildi.")
            self._load_fatura_bilgi()
            self._load_odemeler()
            self.odeme_aciklama.clear()

        except Exception as e:
            try:
                with self.db.get_conn() as conn:
                    conn.execute("ROLLBACK")
            except Exception:
                pass
            QMessageBox.critical(self, "Hata", f"Ödeme kaydedilemedi:\n{e}")

    def _odeme_sil(self):
        row = self.odeme_tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Silmek için bir ödeme seçin.")
            return
        tutar_str = self.odeme_tbl.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"{tutar_str} tutarındaki ödemeyi silmek istiyor musunuz?\n"
            "Cari bakiye ve fatura durumu geri alınacak!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            # Silinecek ödemenin tutarını bul
            with self.db.get_conn() as conn:
                odeme_rows = conn.execute(
                    "SELECT * FROM odemeler WHERE fatura_id=? ORDER BY tarih DESC",
                    (self.fatura_id,)
                ).fetchall()
            if row >= len(odeme_rows):
                return
            odeme = odeme_rows[row]

            with self.db.get_conn() as conn:
                conn.execute("BEGIN")
                conn.execute("DELETE FROM odemeler WHERE id=?", (odeme["id"],))

                # odenen_toplam geri al
                conn.execute("""
                    UPDATE faturalar
                    SET odenen_toplam = MAX(0, COALESCE(odenen_toplam,0) - ?)
                    WHERE id=?
                """, (odeme["tutar_tl"], self.fatura_id))

                # Durum güncelle
                r2 = conn.execute(
                    "SELECT genel_toplam, odenen_toplam FROM faturalar WHERE id=?",
                    (self.fatura_id,)
                ).fetchone()
                # Güvenli okuma
                genel  = r2["genel_toplam"] or 0
                od_row = conn.execute(
                    "SELECT odenen_toplam FROM faturalar WHERE id=?",
                    (self.fatura_id,)
                ).fetchone()
                odenen2 = od_row["odenen_toplam"] if od_row and "odenen_toplam" in od_row.keys() else 0

                durum = "ODENDI" if odenen2 >= genel else ("KISMI" if odenen2 > 0 else "BEKLIYOR")
                conn.execute("UPDATE faturalar SET odeme_durumu=? WHERE id=?", (durum, self.fatura_id))

                # Cari bakiye ters çevir
                fatura_tipi = self._fatura["fatura_tipi"]
                tl_geri     = odeme["tutar_tl"] if fatura_tipi == "SATIS" else -odeme["tutar_tl"]
                dov         = odeme["doviz_birimi"] or "TL"
                dov_tut     = odeme["doviz_tutari"] or 0
                usd_geri    = dov_tut if dov == "USD" and fatura_tipi == "SATIS" \
                            else -dov_tut if dov == "USD" else 0.0
                eur_geri    = dov_tut if dov == "EUR" and fatura_tipi == "SATIS" \
                            else -dov_tut if dov == "EUR" else 0.0
                conn.execute("""
                    UPDATE cariler
                    SET bakiye_tl  = bakiye_tl  + ?,
                        bakiye_usd = bakiye_usd + ?,
                        bakiye_eur = COALESCE(bakiye_eur,0) + ?
                    WHERE id=?
                """, (tl_geri, usd_geri, eur_geri, self._fatura["cari_id"]))

                conn.execute("COMMIT")

            self._load_fatura_bilgi()
            self._load_odemeler()
        except Exception as e:
            try:
                with self.db.get_conn() as conn:
                    conn.execute("ROLLBACK")
            except Exception:
                pass
            QMessageBox.critical(self, "Hata", f"Ödeme silinemedi:\n{e}")


class FaturaWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.usd_kur = 32.50
        self.eur_kur = 35.20
        self._build_ui()
        self.refresh()

    def set_kurlar(self, usd: float, eur: float):
        self.usd_kur = usd
        self.eur_kur = eur

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        title = QLabel("🧾 Faturalar")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.arama = QLineEdit()
        self.arama.setPlaceholderText("🔍 Fatura no / cari ara...")
        self.arama.setFixedWidth(220)
        self.arama.textChanged.connect(self.refresh)
        header.addWidget(self.arama)

        self.tip_filter = QComboBox()
        self.tip_filter.addItems(["Tümü", "SATIS", "ALIS"])
        self.tip_filter.setFixedWidth(100)
        self.tip_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.tip_filter)

        yeni_btn = QPushButton("➕ Yeni Fatura")
        yeni_btn.clicked.connect(self._yeni_fatura)
        header.addWidget(yeni_btn)

        excel_btn = QPushButton("📊 Excel")
        excel_btn.setObjectName("infoBtn")
        excel_btn.clicked.connect(self._excel_export)
        header.addWidget(excel_btn)
        layout.addLayout(header)

        self.tbl = QTableWidget(0, 10)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Fatura No", "Cari", "Tarih", "Tip",
            "Genel Toplam", "Ödenen", "Kalan", "Durum", "Döviz"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.doubleClicked.connect(self._odeme_ekle)
        layout.addWidget(self.tbl)

        btn_row = QHBoxLayout()
        detay_btn = QPushButton("🔍 Detay")
        detay_btn.setObjectName("secondaryBtn")
        detay_btn.clicked.connect(self._detay_goster)
        odeme_btn = QPushButton("💳 Ödeme Ekle")
        odeme_btn.setObjectName("infoBtn")
        odeme_btn.clicked.connect(self._odeme_ekle)
        sil_btn = QPushButton("🗑️ Sil")
        sil_btn.setObjectName("dangerBtn")
        sil_btn.clicked.connect(self._sil)
        btn_row.addWidget(detay_btn)
        btn_row.addWidget(odeme_btn)
        btn_row.addWidget(sil_btn)
        btn_row.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #8b949e;")
        btn_row.addWidget(self.count_lbl)
        layout.addLayout(btn_row)

    def refresh(self):
        try:
            arama = self.arama.text().strip()
            tip = self.tip_filter.currentText()
            with self.db.get_conn() as conn:
                query = """
                    SELECT f.*, c.unvan FROM faturalar f
                    JOIN cariler c ON f.cari_id = c.id
                    WHERE (f.fatura_no LIKE ? OR c.unvan LIKE ?)
                """
                params = [f"%{arama}%", f"%{arama}%"]
                if tip != "Tümü":
                    query += " AND f.fatura_tipi=?"
                    params.append(tip)
                query += " ORDER BY f.id DESC"
                rows = conn.execute(query, params).fetchall()

            durum_renk = {
                "ODENDI":   "#2ea043",
                "KISMI":    "#d29922",
                "BEKLIYOR": "#f85149",
            }
            self.tbl.setRowCount(0)
            for r in rows:
                ri = self.tbl.rowCount()
                self.tbl.insertRow(ri)
                genel   = r["genel_toplam"] or 0
                odenen  = r["odenen_toplam"] if "odenen_toplam" in r.keys() else 0
                odenen  = odenen if odenen else 0
                kalan   = genel - odenen
                durum   = r["odeme_durumu"] if "odeme_durumu" in r.keys() else "BEKLIYOR"
                durum   = durum or "BEKLIYOR"
                doviz_str = (
                    f"{r['doviz_birimi']} {r['doviz_tutari']:,.2f} @ {r['doviz_kuru']:,.4f}"
                    if r["doviz_birimi"] != "TL" else "TL"
                )
                tip_color   = "#2ea043" if r["fatura_tipi"] == "SATIS" else "#1f6feb"
                durum_color = durum_renk.get(durum, "#8b949e")

                cells = [
                    (str(r["id"]),          None),
                    (r["fatura_no"],        None),
                    (r["unvan"],            None),
                    (r["tarih"],            None),
                    (r["fatura_tipi"],      tip_color),
                    (f"₺{genel:,.2f}",     None),
                    (f"₺{odenen:,.2f}",    "#2ea043"),
                    (f"₺{kalan:,.2f}",     "#f85149" if kalan > 0.01 else "#2ea043"),
                    (durum,                 durum_color),
                    (doviz_str,             None),
                ]
                for ci, (val, color) in enumerate(cells):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if color:
                        item.setForeground(QColor(color))
                    self.tbl.setItem(ri, ci, item)
            self.count_lbl.setText(f"Toplam: {len(rows)} fatura")
        except Exception as e:
            print(f"Fatura refresh error: {e}")

    def _yeni_fatura(self):
        dlg = FaturaDialog(self.db, self.usd_kur, self.eur_kur, parent=self)
        if dlg.exec():
            self.refresh()

    def _odeme_ekle(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Lütfen bir fatura seçin.")
            return
        fatura_id = int(self.tbl.item(row, 0).text())
        durum = self.tbl.item(row, 8).text() if self.tbl.item(row, 8) else "BEKLIYOR"
        if durum == "ODENDI":
            reply = QMessageBox.question(
                self, "Fatura Ödenmiş",
                "Bu fatura zaten ödenmiş olarak işaretli.\nYine de ödeme eklemek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        dlg = OdemeDialog(self.db, fatura_id, self.usd_kur, self.eur_kur, parent=self)
        dlg.exec()
        self.refresh()

    def _detay_goster(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Lütfen bir fatura seçin.")
            return
        fatura_id = int(self.tbl.item(row, 0).text())
        fatura_no = self.tbl.item(row, 1).text()
        try:
            with self.db.get_conn() as conn:
                fatura = conn.execute("SELECT * FROM faturalar WHERE id=?", (fatura_id,)).fetchone()
                satirlar = conn.execute("""
                    SELECT fs.*, s.stok_kodu, s.stok_adi, s.birim
                    FROM fatura_satirlari fs
                    JOIN stoklar s ON fs.stok_id = s.id
                    WHERE fs.fatura_id=?
                """, (fatura_id,)).fetchall()

            dlg = QDialog(self)
            dlg.setWindowTitle(f"Fatura Detayı — {fatura_no}")
            dlg.setMinimumSize(900, 480)
            dlg.setStyleSheet(DARK_STYLE)
            vl = QVBoxLayout(dlg)

            # Özet bilgiler
            info = QLabel(
                f"<b>Fatura No:</b> {fatura['fatura_no']}  |  "
                f"<b>Tarih:</b> {fatura['tarih']}  |  "
                f"<b>Tip:</b> {fatura['fatura_tipi']}  |  "
                f"<b>Döviz:</b> {fatura['doviz_birimi']}  |  "
                f"<b>Kur:</b> ₺{fatura['doviz_kuru']:.4f}"
            )
            info.setStyleSheet("color: #c9d1d9; padding: 6px;")
            vl.addWidget(info)

            tbl = QTableWidget(len(satirlar), 10)
            tbl.setHorizontalHeaderLabels([
                "Malzeme Kodu", "Açıklama", "Birim", "Miktar",
                "Birim Fiyat TL", "KDV %", "KDV Tutarı TL",
                "Toplam TL", "Birim Fiyat Döviz", "Toplam Döviz"
            ])
            tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            dov = fatura["doviz_birimi"]
            dov_sym = {"USD": "$", "EUR": "€"}.get(dov, "")

            for ri, s in enumerate(satirlar):
                kdv_orani  = s["kdv_orani"]  if "kdv_orani"  in s.keys() else 0
                kdv_tutari = s["kdv_tutari"] if "kdv_tutari" in s.keys() else 0
                kdv_dahil  = s["satir_kdv_dahil"] if "satir_kdv_dahil" in s.keys() else s["satir_toplami"]
                dov_fiyat  = (s["birim_fiyat"] / fatura["doviz_kuru"]) if dov != "TL" else 0
                dov_top    = s["doviz_tutari"] if "doviz_tutari" in s.keys() else 0
                mal_kodu   = s["malzeme_kodu"] if "malzeme_kodu" in s.keys() else (s["stok_kodu"] or "")

                cells = [
                    mal_kodu or s["stok_kodu"] or "",
                    s["stok_adi"],
                    s["birim"] or "Adet",
                    f"{s['miktar']:,.3f}",
                    f"₺{s['birim_fiyat']:,.4f}",
                    f"%{kdv_orani:.0f}",
                    f"₺{kdv_tutari:,.2f}",
                    f"₺{kdv_dahil:,.2f}",
                    f"{dov_sym}{dov_fiyat:,.4f}" if dov != "TL" else "—",
                    f"{dov_sym}{dov_top:,.2f}"   if dov != "TL" else "—",
                ]
                for ci, val in enumerate(cells):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(ri, ci, item)

            vl.addWidget(tbl)

            # Toplam özeti
            kdv_top = fatura["kdv_toplam"] if "kdv_toplam" in fatura.keys() else 0
            ara_top = fatura["genel_toplam"] - (kdv_top or 0)
            ozet = QLabel(
                f"<b>Mal/Hizmet Toplam:</b> ₺{ara_top:,.2f}  |  "
                f"<b>KDV Toplam:</b> ₺{kdv_top:,.2f}  |  "
                f"<b>Ödenecek Tutar:</b> ₺{fatura['genel_toplam']:,.2f}"
            )
            ozet.setStyleSheet("color: #2ea043; font-weight: bold; padding: 8px;")
            vl.addWidget(ozet)

            kapat = QPushButton("Kapat")
            kapat.setObjectName("secondaryBtn")
            kapat.clicked.connect(dlg.accept)
            hl = QHBoxLayout(); hl.addStretch(); hl.addWidget(kapat)
            vl.addLayout(hl)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _sil(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        fatura_id = int(self.tbl.item(row, 0).text())
        fatura_no = self.tbl.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{fatura_no}' faturasını silmek istiyor musunuz?\n"
            "Stok ve cari bakiyeler GERİ ALINMAYACAKTIR!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db.get_conn() as conn:
                    conn.execute("DELETE FROM faturalar WHERE id=?", (fatura_id,))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _excel_export(self):
        try:
            import pandas as pd
            with self.db.get_conn() as conn:
                rows = conn.execute("""
                    SELECT f.*, c.unvan as cari_unvan FROM faturalar f
                    JOIN cariler c ON f.cari_id = c.id ORDER BY f.id DESC
                """).fetchall()
            data = [dict(r) for r in rows]
            if not data:
                QMessageBox.information(self, "Bilgi", "Dışa aktarılacak veri yok.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Excel Kaydet", "faturalar.xlsx", "Excel (*.xlsx)")
            if path:
                df = pd.DataFrame(data)
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Başarılı", f"Excel kaydedildi:\n{path}")
        except ImportError:
            QMessageBox.critical(self, "Hata", "pandas kurulu değil.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ─────────────────────────────────────────────
#  KUR FARKI ANALİZİ MODÜLÜ
# ─────────────────────────────────────────────
class KurFarkiWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.guncel_usd = 32.50
        self.guncel_eur = 35.20
        self._build_ui()

    def set_kurlar(self, usd: float, eur: float):
        self.guncel_usd = usd
        self.guncel_eur = eur
        self.usd_lbl.setText(f"Güncel USD: ₺{usd:.4f}")
        self.eur_lbl.setText(f"Güncel EUR: ₺{eur:.4f}")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        title = QLabel("💱 Kur Farkı Analizi")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.usd_lbl = QLabel(f"Güncel USD: ₺{self.guncel_usd:.4f}")
        self.usd_lbl.setStyleSheet("color: #d29922; font-weight: bold;")
        self.eur_lbl = QLabel(f"Güncel EUR: ₺{self.guncel_eur:.4f}")
        self.eur_lbl.setStyleSheet("color: #8957e5; font-weight: bold;")
        header.addWidget(self.usd_lbl)
        header.addWidget(QLabel("  "))
        header.addWidget(self.eur_lbl)

        hesapla_btn = QPushButton("🔄 Hesapla")
        hesapla_btn.clicked.connect(self._hesapla)
        header.addWidget(hesapla_btn)

        excel_btn = QPushButton("📊 Excel")
        excel_btn.setObjectName("infoBtn")
        excel_btn.clicked.connect(self._excel_export)
        header.addWidget(excel_btn)
        layout.addLayout(header)

        # Filtre
        filtre_row = QHBoxLayout()
        filtre_row.addWidget(QLabel("Döviz:"))
        self.doviz_filter = QComboBox()
        self.doviz_filter.addItems(["USD ve EUR", "USD", "EUR"])
        self.doviz_filter.setFixedWidth(150)
        filtre_row.addWidget(self.doviz_filter)
        filtre_row.addWidget(QLabel("Fatura Tipi:"))
        self.tip_filter = QComboBox()
        self.tip_filter.addItems(["Tümü", "SATIS", "ALIS"])
        self.tip_filter.setFixedWidth(100)
        filtre_row.addWidget(self.tip_filter)
        filtre_row.addStretch()
        layout.addLayout(filtre_row)

        # Özet kartlar
        ozet_row = QHBoxLayout()
        self.kart_usd_kf = OzetKart("USD Kur Farkı (₺)", "₺0", "💵", "cardGold")
        self.kart_eur_kf = OzetKart("EUR Kur Farkı (₺)", "₺0", "💶", "cardPurple")
        self.kart_toplam_kf = OzetKart("Toplam Kur Farkı (₺)", "₺0", "📊", "cardBlue")
        ozet_row.addWidget(self.kart_usd_kf)
        ozet_row.addWidget(self.kart_eur_kf)
        ozet_row.addWidget(self.kart_toplam_kf)
        layout.addLayout(ozet_row)

        # Ana tablo
        self.tbl = QTableWidget(0, 10)
        self.tbl.setHorizontalHeaderLabels([
            "Fatura No", "Cari", "Tarih", "Tip", "Döviz",
            "Fatura Kuru", "Güncel Kur", "Döviz Tutarı",
            "Fatura TL", "Kur Farkı (₺)"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tbl)

        # Açıklama
        aciklama = QLabel(
            "ℹ️  Kur Farkı = (Güncel Kur − Fatura Kuru) × Döviz Tutarı  |  "
            "Pozitif = Kâr (Alacaklarınız değerlendi / Borçlarınız ucuzladı)"
        )
        aciklama.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(aciklama)

    def _hesapla(self):
        try:
            doviz_sec = self.doviz_filter.currentText()
            tip_sec = self.tip_filter.currentText()

            with self.db.get_conn() as conn:
                query = """
                    SELECT f.fatura_no, c.unvan, f.tarih, f.fatura_tipi,
                        f.doviz_birimi, f.doviz_kuru, f.doviz_tutari, f.genel_toplam
                    FROM faturalar f
                    JOIN cariler c ON f.cari_id = c.id
                    WHERE f.doviz_birimi != 'TL'
                """
                params = []
                if doviz_sec == "USD":
                    query += " AND f.doviz_birimi = 'USD'"
                elif doviz_sec == "EUR":
                    query += " AND f.doviz_birimi = 'EUR'"
                if tip_sec != "Tümü":
                    query += " AND f.fatura_tipi = ?"
                    params.append(tip_sec)
                query += " ORDER BY f.tarih DESC"
                rows = conn.execute(query, params).fetchall()

            self.tbl.setRowCount(0)
            toplam_usd_kf = toplam_eur_kf = 0.0

            for r in rows:
                doviz = r["doviz_birimi"]
                fatura_kuru = r["doviz_kuru"] or 1
                doviz_tutari = r["doviz_tutari"] or 0
                guncel_kur = self.guncel_usd if doviz == "USD" else self.guncel_eur

                # Kur farkı hesabı: SATIS faturasında alacak (pozitif kur farkı kârdır)
                # ALIS faturasında borç (negatif kur farkı kârdır)
                if r["fatura_tipi"] == "SATIS":
                    kur_farki = (guncel_kur - fatura_kuru) * doviz_tutari
                else:
                    kur_farki = (fatura_kuru - guncel_kur) * doviz_tutari

                if doviz == "USD":
                    toplam_usd_kf += kur_farki
                else:
                    toplam_eur_kf += kur_farki

                ri = self.tbl.rowCount()
                self.tbl.insertRow(ri)
                cells = [
                    r["fatura_no"], r["unvan"], r["tarih"], r["fatura_tipi"],
                    doviz, f"₺{fatura_kuru:.4f}", f"₺{guncel_kur:.4f}",
                    f"{doviz} {doviz_tutari:,.2f}",
                    f"₺{r['genel_toplam']:,.2f}", f"₺{kur_farki:,.2f}"
                ]
                for ci, val in enumerate(cells):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if ci == 9:
                        item.setForeground(
                            QColor("#2ea043") if kur_farki >= 0 else QColor("#f85149")
                        )
                    if ci == 3:
                        item.setForeground(
                            QColor("#2ea043") if r["fatura_tipi"] == "SATIS" else QColor("#1f6feb")
                        )
                    self.tbl.setItem(ri, ci, item)

            toplam = toplam_usd_kf + toplam_eur_kf
            usd_str = f"₺{toplam_usd_kf:+,.2f}"
            eur_str = f"₺{toplam_eur_kf:+,.2f}"
            top_str = f"₺{toplam:+,.2f}"
            self.kart_usd_kf.set_deger(usd_str)
            self.kart_eur_kf.set_deger(eur_str)
            self.kart_toplam_kf.set_deger(top_str)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kur farkı hesaplama hatası:\n{e}")

    def _excel_export(self):
        try:
            import pandas as pd
            rows_data = []
            for ri in range(self.tbl.rowCount()):
                row = {}
                headers = [
                    "Fatura No", "Cari", "Tarih", "Tip", "Döviz",
                    "Fatura Kuru", "Güncel Kur", "Döviz Tutarı", "Fatura TL", "Kur Farkı (₺)"
                ]
                for ci, h in enumerate(headers):
                    item = self.tbl.item(ri, ci)
                    row[h] = item.text() if item else ""
                rows_data.append(row)
            if not rows_data:
                QMessageBox.information(self, "Bilgi", "Önce hesapla butonuna basın.")
                return
            path, _ = QFileDialog.getSaveFileName(
                self, "Excel Kaydet", "kur_farki_analizi.xlsx", "Excel (*.xlsx)"
            )
            if path:
                df = pd.DataFrame(rows_data)
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Başarılı", f"Excel kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ─────────────────────────────────────────────
#  KUR GEÇMİŞİ MODÜLÜ
# ─────────────────────────────────────────────
class KurGecmisiWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        title = QLabel("📈 Kur Geçmişi (TCMB)")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.setObjectName("secondaryBtn")
        yenile_btn.clicked.connect(self.refresh)
        header.addWidget(yenile_btn)
        layout.addLayout(header)

        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["ID", "Tarih", "USD (₺)", "EUR (₺)"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tbl)

    def refresh(self):
        try:
            with self.db.get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM kur_gecmisi ORDER BY id DESC LIMIT 100"
                ).fetchall()
            self.tbl.setRowCount(0)
            for r in rows:
                ri = self.tbl.rowCount()
                self.tbl.insertRow(ri)
                cells = [str(r["id"]), r["tarih"],
                        f"₺{r['usd_kur']:.4f}", f"₺{r['eur_kur']:.4f}"]
                for ci, val in enumerate(cells):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl.setItem(ri, ci, item)
        except Exception as e:
            print(f"Kur geçmişi error: {e}")


# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager(DB_PATH)
        self.usd_kur = 32.50
        self.eur_kur = 35.20
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        self._start_kur_thread()

        # Auto-refresh dashboard every 5 min
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(300_000)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("⚡ ERP")
        logo.setStyleSheet(
            "color: #1f6feb; font-size: 18px; font-weight: bold; padding: 8px 0;"
        )
        sidebar_layout.addWidget(logo)
        sub = QLabel("ERP Lite v2.0")
        sub.setStyleSheet("color: #8b949e; font-size: 11px; padding-bottom: 16px;")
        sidebar_layout.addWidget(sub)

        # Nav buttons
        self.nav_btns = []
        nav_items = [
            ("🏠 Dashboard", 0),
            ("👥 Cariler", 1),
            ("📦 Stoklar", 2),
            ("🧾 Faturalar", 3),
            ("💱 Kur Farkı", 4),
            ("📈 Kur Geçmişi", 5),
        ]
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_btns.append(btn)

        sidebar_layout.addStretch()

        # Status
        self.status_lbl = QLabel("🔄 Kurlar alınıyor...")
        self.status_lbl.setStyleSheet(
            "color: #8b949e; font-size: 10px; padding: 4px;"
        )
        self.status_lbl.setWordWrap(True)
        sidebar_layout.addWidget(self.status_lbl)

        main_layout.addWidget(sidebar)

        # Content stack
        self.stack = QStackedWidget()

        self.dashboard = DashboardWidget(self.db)
        self.cari_widget = CariWidget(self.db)
        self.stok_widget = StokWidget(self.db)
        self.fatura_widget = FaturaWidget(self.db)
        self.kur_farki_widget = KurFarkiWidget(self.db)
        self.kur_gecmisi_widget = KurGecmisiWidget(self.db)

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.cari_widget)
        self.stack.addWidget(self.stok_widget)
        self.stack.addWidget(self.fatura_widget)
        self.stack.addWidget(self.kur_farki_widget)
        self.stack.addWidget(self.kur_gecmisi_widget)

        main_layout.addWidget(self.stack)

        # Default
        self._switch_page(0)
        self.dashboard.refresh()

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
        # Refresh active widget
        if idx == 0:
            self.dashboard.refresh()
        elif idx == 1:
            self.cari_widget.refresh()
        elif idx == 2:
            self.stok_widget.refresh()
        elif idx == 3:
            self.fatura_widget.refresh()
        elif idx == 5:
            self.kur_gecmisi_widget.refresh()

    def _start_kur_thread(self):
        self.kur_thread = KurCekiciThread()
        self.kur_thread.kur_yuklendi.connect(self._kurlar_yuklendi)
        self.kur_thread.hata_olustu.connect(self._kur_hatasi)
        self.kur_thread.start()

    def _kurlar_yuklendi(self, usd: float, eur: float):
        self.usd_kur = usd
        self.eur_kur = eur
        self.status_lbl.setText(
            f"✅ TCMB\nUSD: ₺{usd:.4f}\nEUR: ₺{eur:.4f}\n"
            f"{datetime.now().strftime('%H:%M')}"
        )
        self.status_lbl.setStyleSheet("color: #2ea043; font-size: 10px; padding: 4px;")

        # Propagate to widgets
        self.dashboard.set_kurlar(usd, eur)
        self.dashboard.refresh()
        self.fatura_widget.set_kurlar(usd, eur)
        self.kur_farki_widget.set_kurlar(usd, eur)

    def _kur_hatasi(self, hata: str):
        self.status_lbl.setText(f"⚠️ {hata[:60]}")
        self.status_lbl.setStyleSheet("color: #d29922; font-size: 10px; padding: 4px;")

    def _refresh_all(self):
        self._start_kur_thread()
        self.dashboard.refresh()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    # Global dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0f1117"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()