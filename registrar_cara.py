# -*- coding: utf-8 -*-
"""
registrar_cara.py — Herramienta para registrar nuevos usuarios en el sistema.

Abre la camara, muestra el video en tiempo real y permite capturar fotos
del nuevo usuario. Solo acepta la captura cuando detecta un rostro en el
frame, lo que garantiza que las imagenes de referencia sean utiles para
DeepFace.

Uso:
    python registrar_cara.py <nombre_usuario> [num_fotos]

Ejemplo:
    python registrar_cara.py carlos 5
"""

import cv2
import os
import sys


# Ruta donde se almacenan las imagenes de referencia por persona
CONOCIDOS_DIR = "known_faces"

# Clasificador Haar para deteccion de rostros antes de capturar
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def hay_rostro(frame) -> bool:
    """
    Verifica si hay al menos un rostro visible en el frame.

    Usa el clasificador Haar de OpenCV para una deteccion rapida.
    Retorna True si se detecta al menos un rostro, False en caso contrario.
    """
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = face_cascade.detectMultiScale(
        gris,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    return len(rostros) > 0


def dibujar_overlay(frame, contador: int, num_fotos: int, rostro_detectado: bool):
    """
    Dibuja indicaciones y estado sobre el frame de la camara.

    Muestra:
      - Barra de progreso de fotos capturadas.
      - Indicador verde/rojo segun si hay rostro en frame.
      - Instrucciones de control.

    Args:
        frame:            Frame actual de la camara (modificado en sitio).
        contador:         Numero de fotos ya capturadas.
        num_fotos:        Total de fotos a capturar.
        rostro_detectado: True si hay un rostro visible en este frame.
    """
    color_estado = (0, 255, 0) if rostro_detectado else (0, 0, 255)
    estado_texto = "Rostro detectado" if rostro_detectado else "Sin rostro — acercate a la camara"

    cv2.putText(frame, estado_texto, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_estado, 2)
    cv2.putText(frame, f"Fotos: {contador}/{num_fotos}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    instrucciones = "ESPACIO: capturar  |  Q: salir"
    h = frame.shape[0]
    cv2.putText(frame, instrucciones, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    return frame


def registrar_usuario(nombre: str, num_fotos: int = 5):
    """
    Registra un nuevo usuario capturando sus fotos de referencia.

    Guarda las imagenes en known_faces/<nombre>/ con el formato
    <nombre>_<n>.jpg. Solo permite capturar cuando hay un rostro visible
    en el frame.

    Args:
        nombre:    Identificador del usuario (nombre de carpeta y prefijo de archivo).
        num_fotos: Cantidad de fotos a capturar (por defecto 5).
    """
    ruta = os.path.join(CONOCIDOS_DIR, nombre)
    os.makedirs(ruta, exist_ok=True)

    # Fotos ya existentes para no sobreescribir
    fotos_previas = len([
        f for f in os.listdir(ruta)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo abrir la camara.")
        sys.exit(1)

    print(f"\nRegistrando a: {nombre.upper()}")
    print(f"Se tomaran {num_fotos} fotos.")
    print("Coloca tu cara frente a la camara.")
    print("ESPACIO para capturar  |  Q para salir\n")

    contador = 0
    while contador < num_fotos:
        ret, frame = cap.read()
        if not ret:
            break

        rostro_ok = hay_rostro(frame)
        frame = dibujar_overlay(frame, contador, num_fotos, rostro_ok)
        cv2.imshow(f"Registro — {nombre}", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord(" "):
            if not rostro_ok:
                print("No se detecto ningun rostro. Acercate a la camara e intentalo de nuevo.")
                continue
            indice = fotos_previas + contador + 1
            ruta_foto = os.path.join(ruta, f"{nombre}_{indice}.jpg")
            cv2.imwrite(ruta_foto, frame)
            contador += 1
            print(f"  [{contador}/{num_fotos}] Foto guardada: {ruta_foto}")

        elif tecla == ord("q"):
            print("Registro cancelado por el usuario.")
            break

    cap.release()
    cv2.destroyAllWindows()

    total = fotos_previas + contador
    print(f"\nRegistro completado. {contador} fotos nuevas guardadas.")
    print(f"Total de fotos para '{nombre}': {total}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python registrar_cara.py <nombre_usuario> [num_fotos]")
        sys.exit(1)

    nombre_arg = sys.argv[1].strip().lower()
    fotos_arg = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
    registrar_usuario(nombre_arg, fotos_arg)
