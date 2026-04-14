# -*- coding: utf-8 -*-
import cv2
import os
import tempfile
from flask import Flask, request, jsonify
from deepface import DeepFace
from hogar_inteligente import ejecutar_acciones, PERFILES
from bdatos import inicializar_db, registrar_evento, obtener_ultimos_eventos


app = Flask(__name__)

CONOCIDOS_DIR = "known_faces"
MODELO = "VGG-Face"
DETECTOR = "opencv"
UMBRAL_CONFIANZA = 0.6


with app.app_context():
    inicializar_db()


@app.get("/")
def raiz():
    return jsonify({"mensaje": "API de hogar inteligente activa.", "version": "1.0.0"})


@app.get("/perfiles")
def listar_perfiles():
    """Lista todos los perfiles registrados en el sistema."""
    return jsonify({"perfiles": list(PERFILES.keys())})


@app.get("/eventos")
def listar_eventos():
    """Retorna los ultimos eventos de reconocimiento registrados."""
    limite = request.args.get("limite", 20, type=int)
    return jsonify({"eventos": obtener_ultimos_eventos(limite)})


@app.post("/identificar")
def identificar():
    """
    Recibe una imagen y retorna la persona identificada con las acciones ejecutadas.
    """
    if "imagen" not in request.files:
        return jsonify({"error": "No se envio ninguna imagen."}), 400

    imagen = request.files["imagen"]

    if not imagen.content_type.startswith("image/"):
        return jsonify({"error": "El archivo debe ser una imagen."}), 400

    contenido = imagen.read()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(contenido)
        tmp_path = tmp.name

    try:
        mejor_nombre = "desconocido"
        mejor_distancia = float("inf")

        personas = [
            d for d in os.listdir(CONOCIDOS_DIR)
            if os.path.isdir(os.path.join(CONOCIDOS_DIR, d))
        ] if os.path.exists(CONOCIDOS_DIR) else []

        for persona in personas:
            ruta_persona = os.path.join(CONOCIDOS_DIR, persona)
            try:
                resultado = DeepFace.find(
                    img_path=tmp_path,
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

        if mejor_distancia > UMBRAL_CONFIANZA:
            mejor_nombre = "desconocido"

        acciones = ejecutar_acciones(mejor_nombre)
        registrar_evento(
            nombre=mejor_nombre,
            tipo=acciones["perfil"]["tipo"],
            confianza=float(mejor_distancia) if mejor_distancia != float("inf") else None,
        )

        return jsonify({
            "nombre": mejor_nombre,
            "distancia": float(mejor_distancia) if mejor_distancia != float("inf") else None,
            "acciones": acciones["perfil"],
            "timestamp": acciones["timestamp"],
        })

    finally:
        os.unlink(tmp_path)


@app.post("/agregar_perfil/<nombre>")
def agregar_perfil(nombre):
    """
    Agrega una imagen de referencia para un nuevo usuario o usuario existente.
    """
    if "imagen" not in request.files:
        return jsonify({"error": "No se envio ninguna imagen."}), 400

    imagen = request.files["imagen"]

    ruta_usuario = os.path.join(CONOCIDOS_DIR, nombre)
    os.makedirs(ruta_usuario, exist_ok=True)

    fotos_existentes = len(os.listdir(ruta_usuario))
    nombre_archivo = f"{nombre}_{fotos_existentes + 1}.jpg"
    ruta_foto = os.path.join(ruta_usuario, nombre_archivo)

    imagen.save(ruta_foto)

    return jsonify({
        "mensaje": f"Imagen registrada para {nombre}.",
        "archivo": nombre_archivo,
        "total_fotos": fotos_existentes + 1,
    })


if __name__ == "__main__":
    app.run(debug=True)
