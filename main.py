# -*- coding: utf-8 -*-
"""
main.py — Sistema de reconocimiento facial para hogar inteligente.

Flujo principal:
  1. Captura frames de la camara en tiempo real con OpenCV.
  2. Detecta rostros en cada frame usando el clasificador Haar de OpenCV
     y dibuja bounding boxes sobre ellos.
  3. Cada INTERVALO_SEGUNDOS ejecuta el reconocimiento completo:
       a. DeepFace.find()    → identifica a la persona (¿quién es?).
       b. DeepFace.analyze() → estima edad, genero y emocion dominante.
  4. Muestra la información sobre el frame en tiempo real.
  5. Ejecuta las acciones del hogar y registra el evento en la BD.

Controles:
  Q → salir
"""

import cv2
import os
import time
from deepface import DeepFace
from hogar_inteligente import ejecutar_acciones
from bdatos import inicializar_db, registrar_evento


# ---------------------------------------------------------------------------
# Configuracion global
# ---------------------------------------------------------------------------
CONOCIDOS_DIR = "known_faces"
MODELO = "VGG-Face"       # Opciones: VGG-Face, Facenet, ArcFace
DETECTOR = "opencv"        # Opciones: opencv, retinaface, mtcnn
UMBRAL_CONFIANZA = 0.6     # Distancia maxima para considerar coincidencia valida
INTERVALO_SEGUNDOS = 5     # Segundos entre reconocimientos consecutivos


# Clasificador Haar para deteccion rapida de rostros en cada frame.
# Se usa unicamente para dibujar bounding boxes; el reconocimiento pesado
# lo hace DeepFace cada INTERVALO_SEGUNDOS.
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


# ---------------------------------------------------------------------------
# Funciones de reconocimiento
# ---------------------------------------------------------------------------

def obtener_personas_conocidas() -> list:
    """Retorna la lista de nombres de personas registradas en known_faces/."""
    if not os.path.exists(CONOCIDOS_DIR):
        os.makedirs(CONOCIDOS_DIR)
        return []
    return [
        d for d in os.listdir(CONOCIDOS_DIR)
        if os.path.isdir(os.path.join(CONOCIDOS_DIR, d))
    ]


def identificar_persona(frame) -> tuple[str, float | None]:
    """
    Compara el frame contra las imagenes registradas en known_faces/.

    Guarda el frame como imagen temporal, ejecuta DeepFace.find() por cada
    persona registrada y selecciona la que tenga menor distancia.

    Retorna:
        (nombre, distancia) si hay coincidencia dentro del umbral.
        ("desconocido", distancia) si la distancia supera el umbral.
        ("desconocido", None) si no hay personas registradas.
    """
    personas = obtener_personas_conocidas()
    if not personas:
        return "desconocido", None

    temp_path = "temp_frame.jpg"
    cv2.imwrite(temp_path, frame)

    mejor_nombre = "desconocido"
    mejor_distancia = float("inf")

    for persona in personas:
        ruta_persona = os.path.join(CONOCIDOS_DIR, persona)
        try:
            resultado = DeepFace.find(
                img_path=temp_path,
                db_path=ruta_persona,
                model_name=MODELO,
                detector_backend=DETECTOR,
                enforce_detection=False,
                silent=True,
            )
            if resultado and len(resultado[0]) > 0:
                distancia = resultado[0]["distance"].iloc[0]
                if distancia < mejor_distancia:
                    mejor_distancia = distancia
                    mejor_nombre = persona
        except Exception:
            continue

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if mejor_distancia > UMBRAL_CONFIANZA:
        return "desconocido", mejor_distancia

    return mejor_nombre, mejor_distancia


def analizar_rostro(frame) -> dict | None:
    """
    Ejecuta DeepFace.analyze() sobre el frame para estimar:
      - edad aproximada
      - genero dominante
      - emocion dominante

    Retorna un dict con claves 'edad', 'genero', 'emocion',
    o None si no se detecta ningun rostro.
    """
    try:
        resultados = DeepFace.analyze(
            img_path=frame,
            actions=["age", "gender", "emotion"],
            enforce_detection=False,
            silent=True,
        )
        # DeepFace.analyze puede retornar una lista si hay varios rostros;
        # usamos el primero detectado.
        r = resultados[0] if isinstance(resultados, list) else resultados
        return {
            "edad": r.get("age"),
            "genero": r.get("dominant_gender"),
            "emocion": r.get("dominant_emotion"),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Funciones de visualizacion
# ---------------------------------------------------------------------------

def detectar_rostros(frame):
    """
    Detecta rostros con el clasificador Haar (rapido, cada frame).

    Retorna una lista de rectangulos (x, y, w, h) con la posicion de cada
    rostro encontrado en el frame en escala de grises.
    """
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = face_cascade.detectMultiScale(
        gris,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    return rostros


def dibujar_rostros(frame, rostros, nombre: str, distancia, analisis: dict | None):
    """
    Dibuja bounding boxes y etiquetas sobre los rostros detectados.

    - Verde  → persona identificada.
    - Rojo   → desconocido o sin coincidencia.
    - Muestra nombre, distancia, edad, genero y emocion si estan disponibles.
    """
    color = (0, 255, 0) if nombre != "desconocido" else (0, 0, 255)

    for (x, y, w, h) in rostros:
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    # Etiqueta principal: nombre + distancia
    etiqueta_nombre = nombre.upper()
    if distancia is not None:
        etiqueta_nombre += f"  [{distancia:.2f}]"
    cv2.putText(frame, etiqueta_nombre, (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # Informacion de analisis: edad, genero, emocion
    if analisis:
        edad   = analisis.get("edad", "?")
        genero = analisis.get("genero", "?")
        emocion = analisis.get("emocion", "?")
        linea_analisis = f"Edad: {edad}  Genero: {genero}  Emocion: {emocion}"
        cv2.putText(frame, linea_analisis, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return frame


def dibujar_estado(frame, segundos_restantes: float):
    """Muestra un indicador de tiempo hasta el proximo reconocimiento."""
    h_frame = frame.shape[0]
    texto = f"Proximo analisis en: {max(0, segundos_restantes):.1f}s  |  Q: salir"
    cv2.putText(frame, texto, (10, h_frame - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    return frame


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def main():
    """
    Inicializa la BD, abre la camara y ejecuta el loop de deteccion.

    Cada frame:
      - Detecta rostros con Haar cascade y dibuja bounding boxes.
      - Cada INTERVALO_SEGUNDOS lanza reconocimiento con DeepFace
        y analisis de edad/genero/emocion.
    """
    inicializar_db()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo abrir la camara.")
        return

    print("Sistema de hogar inteligente iniciado.")
    print("Presiona Q para salir.")

    # Estado del ultimo reconocimiento para reutilizarlo entre intervalos
    ultimo = {
        "nombre": "",
        "distancia": None,
        "analisis": None,
        "tiempo": 0.0,
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        ahora = time.time()
        tiempo_desde_ultimo = ahora - ultimo["tiempo"]

        # --- Reconocimiento periodico ---
        if tiempo_desde_ultimo >= INTERVALO_SEGUNDOS:
            nombre, distancia = identificar_persona(frame)
            analisis = analizar_rostro(frame)

            ultimo.update({
                "nombre": nombre,
                "distancia": distancia,
                "analisis": analisis,
                "tiempo": ahora,
            })

            # Ejecutar acciones del hogar y registrar evento
            resultado = ejecutar_acciones(nombre, analisis)
            registrar_evento(
                nombre=nombre,
                tipo=resultado["perfil"]["tipo"],
                confianza=distancia,
            )

        # --- Visualizacion (cada frame) ---
        rostros = detectar_rostros(frame)
        frame = dibujar_rostros(
            frame,
            rostros,
            ultimo["nombre"],
            ultimo["distancia"],
            ultimo["analisis"],
        )
        segundos_restantes = INTERVALO_SEGUNDOS - (ahora - ultimo["tiempo"])
        frame = dibujar_estado(frame, segundos_restantes)

        cv2.imshow("Hogar Inteligente - DeepFace", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Sistema detenido.")


if __name__ == "__main__":
    main()
