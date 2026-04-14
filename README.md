# Sistema de Reconocimiento Facial para Hogar Inteligente

Sistema de visión por computadora que identifica personas a través de la cámara y automatiza características del hogar (música, iluminación, temperatura) según el perfil detectado. Desarrollado con **DeepFace**, **OpenCV** y **Flask**.

## Arquitectura del proyecto

```
VisionXcomputadora/
├── main.py               # Loop principal de cámara + detección en tiempo real
├── api.py                # API REST con Flask
├── hogar_inteligente.py  # Perfiles y acciones simuladas del hogar
├── bdatos.py             # Registro de eventos en SQLite
├── registrar_cara.py     # Herramienta para registrar nuevos usuarios
├── requirements.txt      # Dependencias Python
└── known_faces/          # Imágenes de referencia por persona (se crea al registrar)
    └── <nombre>/
        ├── <nombre>_1.jpg
        └── <nombre>_2.jpg
```

## Flujo del sistema

```
registrar_cara.py  →  known_faces/<nombre>/
       ↓
   main.py  (loop de cámara)
       ├── OpenCV Haar cascade  → bounding boxes (cada frame)
       ├── DeepFace.find()      → identidad (cada 5s)
       └── DeepFace.analyze()   → edad / género / emoción (cada 5s)
               ↓
       hogar_inteligente.py  → acciones simuladas por consola
               ↓
          bdatos.py  → log en SQLite (logs/events.db)
               ↓
          api.py (Flask)  → consulta de eventos y perfiles vía HTTP
```

***

## Instalación y ejecución e

### Requisitos previos

* Probado en Windows 11 (64 bits)(solo se probo en windows)

* Python 3.11 (64 bits) — [descargar aquí](https://www.python.org/downloads/release/python-3119/)
  * Durante la instalación marcar **"Add python.exe to PATH"**
  
* Cámara web conectada

### 1. Clonar o descargar el proyecto

```bat
cd C:\ruta\donde\quieras\el\proyecto
```

### 2. Crear el entorno virtual con Python 3.11

```bat
py -3.11 -m venv venv
venv\Scripts\activate
```

> El prompt cambiará a `(venv)` cuando esté activo.

### 3. Instalar dependencias

```bat
pip install -r requirements.txt
```

### 4. Registrar un usuario

En `hogar_inteligente.py` hay una lista estática de perfiles. Si quieres que el sistema reconozca a alguien con su nombre, agrégalo ahí; de lo contrario aparecerá como desconocido aunque sea identificado por la cara.

```bat
python registrar_cara.py juan 5
```

Se recomiendan 5 fotos para mejorar la precisión. Abrirá la cámara — presiona **ESPACIO** para capturar cada foto (solo funciona cuando detecta un rostro). Presiona **Q** para salir.

### 5. Ejecutar el sistema en tiempo real

```bat
python main.py
```

Abre la ventana de cámara con detección en vivo. Presiona **Q** para salir.

### 6. Ejecutar la API Flask (opcional)

```bat
python api.py
```

La API queda disponible en `http://127.0.0.1:5000`.

> **Importante:** abre esa URL en la **barra de direcciones** del navegador (donde aparece la dirección del sitio actual), no en el buscador de Google. Si la escribes en Google, lo tratará como una búsqueda y no encontrará nada.

Endpoints disponibles:

| Método | Endpoint                   | Descripción                       |
| ------ | -------------------------- | --------------------------------- |
| GET    | `/`                        | Estado de la API                  |
| GET    | `/perfiles`                | Lista perfiles registrados        |
| GET    | `/eventos?limite=20`       | Últimos eventos de reconocimiento |
| POST   | `/identificar`             | Identificar persona desde imagen  |
| POST   | `/agregar_perfil/<nombre>` | Agregar foto de referencia        |

Los endpoints GET se pueden abrir directamente en el navegador. Los endpoints POST requieren enviar datos, por lo que se usan con **curl** o herramientas como Postman.

### Ejemplos con curl (Windows)

**Consultar estado:**

```bat
curl http://127.0.0.1:5000/
```

**Listar perfiles registrados:**

```bat
curl http://127.0.0.1:5000/perfiles
```

**Ver últimos eventos:**

```bat
curl http://127.0.0.1:5000/eventos?limite=10
```

**Identificar persona enviando una imagen:**

> **Importante (Windows):** curl no acepta barras invertidas `\` en rutas de archivo. Usa barras normales `/` o ejecuta el comando desde la carpeta donde está la imagen.

Opción A — barras `/` en la ruta:

```bat
curl -X POST http://127.0.0.1:5000/identificar -F "imagen=@D:/HIBRYDGE/Anio2/Tetra4/Ai/VisionXcomputadora/foto.jpg"
```

Opción B — pararse en la carpeta del proyecto y usar solo el nombre del archivo:

```bat
cd D:\HIBRYDGE\Anio2\Tetra4\Ai\VisionXcomputadora
curl -X POST http://127.0.0.1:5000/identificar -F "imagen=@known_faces/hector/hector_1.jpg"
```

**Agregar foto de referencia para un usuario:**

```bat
curl -X POST http://127.0.0.1:5000/agregar_perfil/juan -F "imagen=@foto.jpg"
```

***

## Ver la base de datos de eventos en VS Code

Los eventos de reconocimiento se guardan en `logs/events.db` (SQLite). Para consultarlos visualmente desde VS Code:

### 1. Instalar la extensión SQLite Viewer

1. Abre VS Code
2. Ve a Extensiones con `Ctrl+Shift+X`
3. Busca: `SQLite Viewer`
4. Instala la extensión de **Florian Klampfer**

### 2. Abrir la base de datos

1. En el explorador de VS Code (panel izquierdo) navega a `logs/events.db`
2. Haz doble click sobre el archivo
3. Se abre una vista de tabla con todos los eventos registrados

Verás las siguientes columnas:

| Columna     | Descripción                                      |
| ----------- | ------------------------------------------------ |
| `id`        | Identificador único del evento                   |
| `nombre`    | Persona detectada                                |
| `tipo`      | Tipo de perfil (`adulto`, `nino`, `desconocido`) |
| `timestamp` | Fecha y hora del evento                          |
| `confianza` | Distancia de reconocimiento (menor = más seguro) |

***

## Agregar un nuevo perfil al hogar

Los perfiles se definen en `hogar_inteligente.py` dentro del diccionario `PERFILES`. Para agregar un usuario:

1. Registra sus fotos con `registrar_cara.py` usando el mismo nombre que usarás en el perfil.
2. Agrega una entrada al diccionario:

```Python
"carlos": {
    "tipo": "adulto",
    "musica": "electronica",
    "temperatura": 21,
    "iluminacion": "tenue",
    "bienvenida": "Bienvenido, Carlos.",
},
```

***

## Notas

* Las acciones del hogar (música, temperatura, luces) son **simuladas** con mensajes en consola. En un entorno real se integrarían con APIs de dispositivos inteligentes (Home Assistant, Google Home, etc.).
* El reconocimiento se ejecuta cada 5 segundos (configurable con `INTERVALO_SEGUNDOS` en `main.py`) para no saturar la CPU.
* Los eventos quedan registrados en `logs/events.db` (SQLite).

