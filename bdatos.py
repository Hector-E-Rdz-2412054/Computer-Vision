import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join("logs", "events.db")


def inicializar_db():
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT    NOT NULL,
            tipo      TEXT    NOT NULL,
            timestamp TEXT    NOT NULL,
            confianza REAL
        )
    """)
    conn.commit()
    conn.close()


def registrar_evento(nombre: str, tipo: str, confianza: float = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO eventos (nombre, tipo, timestamp, confianza) VALUES (?, ?, ?, ?)",
        (nombre, tipo, datetime.now().isoformat(), confianza),
    )
    conn.commit()
    conn.close()


def obtener_ultimos_eventos(limite: int = 20) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nombre, tipo, timestamp, confianza FROM eventos ORDER BY id DESC LIMIT ?",
        (limite,),
    )
    filas = cursor.fetchall()
    conn.close()
    return [
        {"nombre": f[0], "tipo": f[1], "timestamp": f[2], "confianza": f[3]}
        for f in filas
    ]