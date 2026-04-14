# -*- coding: utf-8 -*-
"""
hogar_inteligente.py — Perfiles y automatizacion del hogar inteligente.

Define los perfiles de usuario conocidos (PERFILES) y la logica de
acciones simuladas que se ejecutan al detectar una persona:
  - Musica personalizada
  - Temperatura
  - Iluminacion
  - Modos especiales (infantil, alerta, etc.)

Para personas desconocidas tambien se adaptan las acciones segun la
edad y genero estimados por DeepFace.analyze().
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Perfiles de usuarios registrados
# ---------------------------------------------------------------------------
# Cada clave es el nombre del directorio en known_faces/.
# 'tipo' puede ser: 'adulto', 'nino', 'desconocido'.

PERFILES = {
    "juan": {
        "tipo": "adulto",
        "musica": "rock clasico",
        "temperatura": 22,
        "iluminacion": "tenue",
        "bienvenida": "Bienvenido a casa, Juan.",
    },
    "maria": {
        "tipo": "adulto",
        "musica": "jazz",
        "temperatura": 24,
        "iluminacion": "calida",
        "bienvenida": "Hola Maria, que tengas una tarde tranquila.",
    },
    "nino_luis": {
        "tipo": "nino",
        "musica": "canciones infantiles",
        "temperatura": 23,
        "iluminacion": "brillante",
        "bienvenida": "Hola Luis, a jugar!",
    },
    "desconocido": {
        "tipo": "desconocido",
        "musica": None,
        "temperatura": None,
        "iluminacion": "alerta",
        "bienvenida": "Persona no reconocida detectada.",
    },
}


# ---------------------------------------------------------------------------
# Logica de acciones
# ---------------------------------------------------------------------------

def _adaptar_perfil_desconocido(analisis: dict | None) -> dict:
    """
    Genera un perfil adaptado para una persona desconocida usando los datos
    de DeepFace.analyze() (edad estimada y genero).

    Si la edad estimada es menor a 18 se activan acciones de modo infantil;
    de lo contrario se usa el perfil de alerta estandar.

    Args:
        analisis: dict con claves 'edad', 'genero', 'emocion' o None.

    Retorna:
        dict de perfil adaptado.
    """
    perfil_base = dict(PERFILES["desconocido"])

    if not analisis:
        return perfil_base

    edad = analisis.get("edad")
    genero = analisis.get("genero", "desconocido")

    if edad is not None and edad < 18:
        # Menor de edad detectado: activar modo infantil de seguridad
        perfil_base.update({
            "tipo": "nino_desconocido",
            "musica": "musica infantil neutral",
            "iluminacion": "brillante",
            "bienvenida": f"Menor detectado (~{edad} años). Activando modo seguro.",
        })
    else:
        desc_edad = f"~{edad} años" if edad else "edad desconocida"
        perfil_base["bienvenida"] = (
            f"Adulto no reconocido detectado ({genero}, {desc_edad})."
        )

    return perfil_base


def ejecutar_acciones(nombre: str, analisis: dict | None = None) -> dict:
    """
    Ejecuta las acciones del hogar para la persona detectada.

    Si el nombre esta en PERFILES se usa su configuracion directamente.
    Si es 'desconocido', se adaptan las acciones segun el analisis de
    DeepFace (edad, genero).

    Las acciones son simuladas con print() para representar la integracion
    con dispositivos reales (luces, termostato, altavoces, etc.).

    Args:
        nombre:   Nombre de la persona identificada o 'desconocido'.
        analisis: Resultado de DeepFace.analyze() con edad, genero y emocion.

    Retorna:
        dict con claves 'nombre', 'perfil' y 'timestamp'.
    """
    hora = datetime.now().strftime("%H:%M:%S")

    if nombre in PERFILES and nombre != "desconocido":
        perfil = PERFILES[nombre]
    else:
        perfil = _adaptar_perfil_desconocido(analisis)

    # --- Cabecera ---
    print(f"\n[{hora}] Persona detectada: {nombre.upper()}")
    print(f"  Tipo            : {perfil['tipo']}")
    print(f"  Mensaje         : {perfil['bienvenida']}")

    # --- Analisis biometrico (si esta disponible) ---
    if analisis:
        print(
            f"  Analisis IA     : "
            f"edad~{analisis.get('edad')}  "
            f"genero={analisis.get('genero')}  "
            f"emocion={analisis.get('emocion')}"
        )

    # --- Acciones simuladas ---
    if perfil["musica"]:
        print(f"  [SIMULADO] Poniendo musica     : {perfil['musica']}")
    else:
        print("  [SIMULADO] Musica no configurada para este perfil.")

    if perfil["temperatura"]:
        print(f"  [SIMULADO] Ajustando temperatura: {perfil['temperatura']} °C")
    else:
        print("  [SIMULADO] Temperatura no modificada.")

    print(f"  [SIMULADO] Ajustando iluminacion: {perfil['iluminacion']}")

    # --- Acciones especiales segun tipo ---
    tipo = perfil["tipo"]
    if tipo in ("nino", "nino_desconocido"):
        print("  [SIMULADO] Activando modo entretenimiento infantil.")
        print("  [SIMULADO] Activando control parental en pantallas.")
        if analisis and analisis.get("emocion") == "sad":
            print("  [SIMULADO] Emocion triste detectada. Activando modo confort infantil.")
    elif tipo == "desconocido":
        print("  [ALERTA]   Enviando notificacion al propietario.")
        print("  [ALERTA]   Grabando secuencia de video de seguridad.")
    elif tipo == "adulto":
        emocion = analisis.get("emocion") if analisis else None
        if emocion == "happy":
            print("  [SIMULADO] Emocion positiva detectada. Aumentando brillo.")
        elif emocion in ("sad", "fear", "angry"):
            print(f"  [SIMULADO] Emocion '{emocion}' detectada. Activando modo relax.")

    return {
        "nombre": nombre,
        "perfil": perfil,
        "timestamp": hora,
    }
