import cv2
import re
import csv
import json
import os
import sys
import subprocess
import tempfile

from collections import Counter
from datetime import datetime

from ultralytics import YOLO


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

VIDEO_FOLDER = "videos"

MODEL_PATH = "models/license_plate_detector.pt"

PADDLE_WORKER_SCRIPT = "paddle_worker.py"


# ============================================================
# CARPETAS PRINCIPALES
# ============================================================

RESULTS_DIR = "results"

# Evidencias FUERA de results
EVIDENCE_DIR = "evidencias"

# Debug dentro de results solamente si se activa
DEBUG_PLATE_DIR = os.path.join(
    RESULTS_DIR,
    "debug_placas"
)

DEBUG_TIMESTAMP_DIR = os.path.join(
    RESULTS_DIR,
    "debug_timestamp"
)


# ============================================================
# DEBUG / RENDIMIENTO
# ============================================================

DEBUG = False

SAVE_DEBUG_IMAGES = False

SHOW_VIDEO = True

DISPLAY_WIDTH = 960


# ============================================================
# INTERVALO DE ANÁLISIS
# ============================================================

# 1.0 = analizar aproximadamente un frame por segundo
ANALYSIS_INTERVAL_SECONDS = 1.0


# ============================================================
# YOLO
# ============================================================

YOLO_DETECTION_CONF = 0.05

YOLO_ACCEPT_CONF = 0.15

YOLO_IMAGE_SIZE = 1280

YOLO_DEVICE = "cpu"


# ============================================================
# CONFIRMACIÓN DIRECTA
# ============================================================

OCR_DIRECT_CONFIRM_THRESHOLD = 0.95

YOLO_DIRECT_CONFIRM_THRESHOLD = 0.15


# ============================================================
# VIDEO
# ============================================================

VIDEO_EXTENSIONS = (
    ".mp4",
    ".avi",
    ".mov",
    ".mkv"
)


# ============================================================
# TIMESTAMP SUPERIOR IZQUIERDO
# ============================================================

TIMESTAMP_X1_RATIO = 0.00
TIMESTAMP_Y1_RATIO = 0.00

TIMESTAMP_X2_RATIO = 0.32
TIMESTAMP_Y2_RATIO = 0.10


# ============================================================
# RECORTE SUPERIOR DE PLACA
# ============================================================

CROP_PLATE_TOP = True

PLATE_TOP_CROP_RATIO = 0.28

ADAPTIVE_CROP_MIN_WIDTH = 120

ADAPTIVE_CROP_MIN_HEIGHT = 50


# ============================================================
# PLACA PEQUEÑA
# ============================================================

SMALL_PLATE_WIDTH = 120

SMALL_PLATE_HEIGHT = 50


# ============================================================
# TRACKING
# ============================================================

TRACK_IOU_THRESHOLD = 0.25

TRACK_TIMEOUT_SECONDS = 4

CONSENSUS_WINDOW_SECONDS = 10


# ============================================================
# CONSENSO DE RESPALDO
# ============================================================

HIGH_CONF_THRESHOLD = 0.50
HIGH_CONF_MIN_OBSERVATIONS = 3

MEDIUM_CONF_THRESHOLD = 0.15
MEDIUM_CONF_MIN_OBSERVATIONS = 2

LOW_CONF_MIN_OBSERVATIONS = 2

MIN_CONSENSUS_RATIO = 0.60

MIN_STABILITY_COUNT = 2


# ============================================================
# DUPLICADOS
# ============================================================

DUPLICATE_SECONDS = 20


# ============================================================
# GEOMETRÍA
# ============================================================

MIN_PLATE_WIDTH = 35

MIN_PLATE_HEIGHT = 12


# ============================================================
# CREAR CARPETAS
# ============================================================

os.makedirs(
    RESULTS_DIR,
    exist_ok=True
)

os.makedirs(
    EVIDENCE_DIR,
    exist_ok=True
)

if SAVE_DEBUG_IMAGES:

    os.makedirs(
        DEBUG_PLATE_DIR,
        exist_ok=True
    )

    os.makedirs(
        DEBUG_TIMESTAMP_DIR,
        exist_ok=True
    )


# ============================================================
# NOMBRES DE SALIDA POR VIDEO
# ============================================================

def obtener_nombres_salida(video_name):

    base_video = os.path.splitext(
        video_name
    )[0]

    return {

        "json_tecnico":
            os.path.join(
                RESULTS_DIR,
                f"{base_video}_resultados_tecnico.json"
            ),

        "json_final":
            os.path.join(
                RESULTS_DIR,
                f"{base_video}_resultados_final.json"
            ),

        "json_match":
            os.path.join(
                RESULTS_DIR,
                f"{base_video}_resultados_match.json"
            ),

        "csv":
            os.path.join(
                RESULTS_DIR,
                f"{base_video}_resultados.csv"
            )
    }


# ============================================================
# PADDLE WORKER
# ============================================================

class PaddleWorker:

    def __init__(self):

        self.proceso = None

        self.iniciar()


    def iniciar(self):

        print()
        print("=" * 70)
        print("INICIANDO PADDLEOCR WORKER")
        print("=" * 70)

        self.proceso = subprocess.Popen(
            [
                sys.executable,
                PADDLE_WORKER_SCRIPT
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        while True:

            linea = (
                self.proceso
                .stdout
                .readline()
            )

            if not linea:

                raise RuntimeError(
                    "PaddleOCR Worker terminó antes de inicializar."
                )

            linea = linea.strip()

            if DEBUG:

                print(
                    f"[PADDLE WORKER] {linea}"
                )

            if linea == "__PADDLE_READY__":

                break

        print(
            "PaddleOCR Worker listo."
        )


    def reconocer(
        self,
        ruta_imagen
    ):

        if (
            self.proceso is None
            or
            self.proceso.poll() is not None
        ):

            raise RuntimeError(
                "PaddleOCR Worker no está disponible."
            )

        peticion = {
            "command":
                "ocr",

            "image":
                os.path.abspath(
                    ruta_imagen
                )
        }

        self.proceso.stdin.write(
            json.dumps(
                peticion,
                ensure_ascii=False
            )
            + "\n"
        )

        self.proceso.stdin.flush()

        while True:

            linea = (
                self.proceso
                .stdout
                .readline()
            )

            if not linea:

                raise RuntimeError(
                    "PaddleOCR Worker terminó inesperadamente."
                )

            linea = linea.strip()

            if linea.startswith(
                "__PADDLE_RESULT__"
            ):

                contenido = linea[
                    len(
                        "__PADDLE_RESULT__"
                    ):
                ]

                respuesta = json.loads(
                    contenido
                )

                if not respuesta.get(
                    "ok",
                    False
                ):

                    print(
                        "[PADDLE ERROR] "
                        + respuesta.get(
                            "error",
                            "Error desconocido"
                        )
                    )

                    return []

                return respuesta.get(
                    "lecturas",
                    []
                )

            if DEBUG:

                print(
                    f"[PADDLE LOG] "
                    f"{linea}"
                )


    def cerrar(self):

        if (
            self.proceso is None
            or
            self.proceso.poll() is not None
        ):

            return

        try:

            self.proceso.stdin.write(
                json.dumps(
                    {
                        "command":
                            "quit"
                    }
                )
                + "\n"
            )

            self.proceso.stdin.flush()

            self.proceso.wait(
                timeout=5
            )

        except Exception:

            try:

                self.proceso.kill()

            except Exception:

                pass

        finally:

            self.proceso = None


# ============================================================
# ARCHIVO TEMPORAL PARA OCR
# ============================================================

def crear_imagen_temporal(
    imagen,
    prefijo
):

    fd, ruta = tempfile.mkstemp(
        prefix=prefijo,
        suffix=".jpg"
    )

    os.close(fd)

    cv2.imwrite(
        ruta,
        imagen
    )

    return ruta


# ============================================================
# NORMALIZAR PLACA
# ============================================================

def normalizar_placa(texto):

    if not texto:
        return ""

    texto = str(
        texto
    ).upper()

    texto = texto.replace(
        "ECUADOR",
        ""
    )

    texto = re.sub(
        r"[^A-Z0-9]",
        "",
        texto
    )

    return texto


# ============================================================
# CORRECCIÓN POSICIONAL
# ============================================================

def corregir_placa(texto):

    texto = normalizar_placa(
        texto
    )

    if len(texto) not in (
        6,
        7
    ):
        return texto

    caracteres = list(
        texto
    )

    numero_a_letra = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "8": "B"
    }

    letra_a_numero = {
        "O": "0",
        "Q": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8"
    }

    # Primeras tres posiciones deben ser letras
    for i in range(3):

        if caracteres[i] in numero_a_letra:

            caracteres[i] = (
                numero_a_letra[
                    caracteres[i]
                ]
            )

    # El resto deben ser números
    for i in range(
        3,
        len(caracteres)
    ):

        if caracteres[i] in letra_a_numero:

            caracteres[i] = (
                letra_a_numero[
                    caracteres[i]
                ]
            )

    return "".join(
        caracteres
    )


# ============================================================
# VALIDAR PLACA
# ============================================================

def validar_placa(placa):

    return bool(
        re.fullmatch(
            r"^[A-Z]{3}[0-9]{3,4}$",
            placa
        )
    )


# ============================================================
# PLACA PEQUEÑA
# ============================================================

def es_placa_pequena(roi):

    alto, ancho = (
        roi.shape[:2]
    )

    return (
        ancho < SMALL_PLATE_WIDTH
        or
        alto < SMALL_PLATE_HEIGHT
    )


# ============================================================
# ROI TIMESTAMP
# ============================================================

def extraer_roi_timestamp(frame):

    alto, ancho = (
        frame.shape[:2]
    )

    x1 = int(
        ancho
        * TIMESTAMP_X1_RATIO
    )

    y1 = int(
        alto
        * TIMESTAMP_Y1_RATIO
    )

    x2 = int(
        ancho
        * TIMESTAMP_X2_RATIO
    )

    y2 = int(
        alto
        * TIMESTAMP_Y2_RATIO
    )

    return frame[
        y1:y2,
        x1:x2
    ]


# ============================================================
# NORMALIZAR TIMESTAMP
# ============================================================

def normalizar_timestamp_ocr(texto):

    texto = str(
        texto
    ).upper()

    texto = texto.replace(
        "O",
        "0"
    )

    texto = texto.replace(
        "I",
        "1"
    )

    texto = texto.replace(
        "L",
        "1"
    )

    texto = texto.replace(
        "\\",
        "/"
    )

    return texto


# ============================================================
# PARSEAR TIMESTAMP
# ============================================================

def parsear_timestamp(
    lecturas
):

    textos = []

    for lectura in lecturas:

        bruto = lectura.get(
            "texto_bruto",
            ""
        )

        if bruto:

            textos.append(
                normalizar_timestamp_ocr(
                    bruto
                )
            )

    texto_total = " ".join(
        textos
    )

    # Formato esperado:
    # 2026/07/31 08:41:44

    patron = (
        r"(\d{4})"
        r"[\s/\-\.]*"
        r"(\d{2})"
        r"[\s/\-\.]*"
        r"(\d{2})"
        r"\s+"
        r"(\d{2})"
        r"[\s:\.]*"
        r"(\d{2})"
        r"[\s:\.]*"
        r"(\d{2})"
    )

    match = re.search(
        patron,
        texto_total
    )

    if match:

        grupos = match.groups()

        try:

            momento = datetime(
                int(grupos[0]),
                int(grupos[1]),
                int(grupos[2]),
                int(grupos[3]),
                int(grupos[4]),
                int(grupos[5])
            )

            return {
                "ok":
                    True,

                "texto_ocr":
                    texto_total,

                "fecha":
                    momento.strftime(
                        "%Y-%m-%d"
                    ),

                "hora":
                    momento.strftime(
                        "%H:%M:%S"
                    ),

                "captured_at":
                    momento.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
            }

        except ValueError:

            pass

    # ========================================================
    # FALLBACK SOLO DÍGITOS
    # ========================================================

    solo_digitos = re.sub(
        r"\D",
        "",
        texto_total
    )

    match = re.search(
        r"(\d{4})"
        r"(\d{2})"
        r"(\d{2})"
        r"(\d{2})"
        r"(\d{2})"
        r"(\d{2})",
        solo_digitos
    )

    if match:

        grupos = match.groups()

        try:

            momento = datetime(
                int(grupos[0]),
                int(grupos[1]),
                int(grupos[2]),
                int(grupos[3]),
                int(grupos[4]),
                int(grupos[5])
            )

            return {
                "ok":
                    True,

                "texto_ocr":
                    texto_total,

                "fecha":
                    momento.strftime(
                        "%Y-%m-%d"
                    ),

                "hora":
                    momento.strftime(
                        "%H:%M:%S"
                    ),

                "captured_at":
                    momento.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
            }

        except ValueError:

            pass

    return {
        "ok":
            False,

        "texto_ocr":
            texto_total,

        "fecha":
            "",

        "hora":
            "",

        "captured_at":
            ""
    }


# ============================================================
# LEER TIMESTAMP
# ============================================================

def leer_timestamp_frame(
    paddle_worker,
    frame,
    frame_number
):

    roi = extraer_roi_timestamp(
        frame
    )

    if (
        roi is None
        or
        roi.size == 0
    ):

        return {
            "ok":
                False,

            "texto_ocr":
                "",

            "fecha":
                "",

            "hora":
                "",

            "captured_at":
                ""
        }

    roi_grande = cv2.resize(
        roi,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC
    )

    if SAVE_DEBUG_IMAGES:

        ruta = os.path.abspath(
            os.path.join(
                DEBUG_TIMESTAMP_DIR,
                (
                    f"timestamp_frame_"
                    f"{frame_number}.jpg"
                )
            )
        )

        cv2.imwrite(
            ruta,
            roi_grande
        )

        borrar_despues = False

    else:

        ruta = crear_imagen_temporal(
            roi_grande,
            "alpr_timestamp_"
        )

        borrar_despues = True

    try:

        lecturas = (
            paddle_worker.reconocer(
                ruta
            )
        )

    finally:

        if borrar_despues:

            try:

                os.remove(
                    ruta
                )

            except OSError:

                pass

    resultado = parsear_timestamp(
        lecturas
    )

    if DEBUG:

        print(
            f"[TIMESTAMP] "
            f"{resultado['texto_ocr']} "
            f"-> "
            f"{resultado['captured_at']}"
        )

    return resultado


# ============================================================
# IoU
# ============================================================

def calcular_iou(
    bbox_a,
    bbox_b
):

    ax1, ay1, ax2, ay2 = bbox_a

    bx1, by1, bx2, by2 = bbox_b

    ix1 = max(
        ax1,
        bx1
    )

    iy1 = max(
        ay1,
        by1
    )

    ix2 = min(
        ax2,
        bx2
    )

    iy2 = min(
        ay2,
        by2
    )

    iw = max(
        0,
        ix2 - ix1
    )

    ih = max(
        0,
        iy2 - iy1
    )

    inter = (
        iw
        * ih
    )

    area_a = (
        (ax2 - ax1)
        * (ay2 - ay1)
    )

    area_b = (
        (bx2 - bx1)
        * (by2 - by1)
    )

    union = (
        area_a
        + area_b
        - inter
    )

    if union <= 0:
        return 0.0

    return (
        inter
        / union
    )


# ============================================================
# YOLO
# ============================================================

def detectar_placas(
    modelo,
    frame
):

    resultados = modelo.predict(
        source=frame,
        conf=YOLO_DETECTION_CONF,
        imgsz=YOLO_IMAGE_SIZE,
        device=YOLO_DEVICE,
        verbose=False
    )

    detecciones = []

    for resultado in resultados:

        if resultado.boxes is None:
            continue

        for box in resultado.boxes:

            confianza = float(
                box.conf[0]
            )

            if (
                confianza
                < YOLO_ACCEPT_CONF
            ):

                if DEBUG:

                    print(
                        f"[YOLO IGNORADO] "
                        f"{confianza:.1%}"
                    )

                continue

            coordenadas = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )

            x1, y1, x2, y2 = (
                coordenadas.tolist()
            )

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                frame.shape[1],
                x2
            )

            y2 = min(
                frame.shape[0],
                y2
            )

            if (
                x2 <= x1
                or
                y2 <= y1
            ):
                continue

            ancho = (
                x2 - x1
            )

            alto = (
                y2 - y1
            )

            if (
                ancho
                < MIN_PLATE_WIDTH
                or
                alto
                < MIN_PLATE_HEIGHT
            ):
                continue

            detecciones.append(
                {
                    "confidence":
                        confianza,

                    "bbox":
                        (
                            x1,
                            y1,
                            x2,
                            y2
                        )
                }
            )

    detecciones.sort(
        key=lambda x:
            x[
                "confidence"
            ],
        reverse=True
    )

    return detecciones


# ============================================================
# OCR PLACA
# ============================================================

def reconocer_placa(
    paddle_worker,
    frame,
    bbox,
    frame_number,
    segundo,
    track_id
):

    x1, y1, x2, y2 = bbox

    ancho = (
        x2 - x1
    )

    alto = (
        y2 - y1
    )

    margen_x = int(
        ancho
        * 0.08
    )

    margen_y = int(
        alto
        * 0.10
    )

    px1 = max(
        0,
        x1 - margen_x
    )

    py1 = max(
        0,
        y1 - margen_y
    )

    px2 = min(
        frame.shape[1],
        x2 + margen_x
    )

    py2 = min(
        frame.shape[0],
        y2 + margen_y
    )

    roi = frame[
        py1:py2,
        px1:px2
    ]

    if (
        roi is None
        or
        roi.size == 0
    ):

        return {
            "candidatos":
                [],

            "lecturas":
                []
        }

    pequena = es_placa_pequena(
        roi
    )

    # ========================================================
    # QUITAR ECUADOR SOLO SI LA PLACA ES GRANDE
    # ========================================================

    if (
        CROP_PLATE_TOP
        and
        not pequena
    ):

        alto_roi, ancho_roi = (
            roi.shape[:2]
        )

        if (
            ancho_roi
            >= ADAPTIVE_CROP_MIN_WIDTH
            and
            alto_roi
            >= ADAPTIVE_CROP_MIN_HEIGHT
        ):

            corte = int(
                alto_roi
                * PLATE_TOP_CROP_RATIO
            )

            corte = min(
                max(
                    corte,
                    0
                ),
                alto_roi - 1
            )

            roi = roi[
                corte:,
                :
            ]

    # ========================================================
    # DEBUG O TEMPORAL
    # ========================================================

    if SAVE_DEBUG_IMAGES:

        ruta = os.path.abspath(
            os.path.join(
                DEBUG_PLATE_DIR,
                (
                    f"track_{track_id:03d}_"
                    f"segundo_{int(segundo):04d}_"
                    f"frame_{frame_number}_"
                    f"roi_ocr.jpg"
                )
            )
        )

        cv2.imwrite(
            ruta,
            roi
        )

        borrar_despues = False

    else:

        ruta = crear_imagen_temporal(
            roi,
            "alpr_plate_"
        )

        borrar_despues = True

    try:

        paddle_lecturas = (
            paddle_worker.reconocer(
                ruta
            )
        )

    finally:

        if borrar_despues:

            try:

                os.remove(
                    ruta
                )

            except OSError:

                pass

    candidatos = []

    lecturas_tecnicas = []

    for lectura in paddle_lecturas:

        bruto = lectura.get(
            "texto_bruto",
            ""
        )

        confianza = float(
            lectura.get(
                "confianza",
                0.0
            )
        )

        normalizada = normalizar_placa(
            bruto
        )

        corregida = corregir_placa(
            normalizada
        )

        valida = validar_placa(
            corregida
        )

        lecturas_tecnicas.append(
            {
                "ocr":
                    bruto,

                "normalizada":
                    normalizada,

                "corregida":
                    corregida,

                "confianza":
                    round(
                        confianza,
                        4
                    ),

                "valida":
                    valida
            }
        )

        if valida:

            candidatos.append(
                {
                    "placa":
                        corregida,

                    "confianza":
                        confianza
                }
            )

            print(
                f"[PLACA] "
                f"T{track_id} | "
                f"{corregida} | "
                f"OCR {confianza:.1%}"
            )

    return {
        "candidatos":
            candidatos,

        "lecturas":
            lecturas_tecnicas
    }


# ============================================================
# TRACKING
# ============================================================

def asignar_track(
    tracks,
    bbox,
    segundo,
    siguiente_id
):

    mejor_track = None

    mejor_iou = 0.0

    for (
        track_id,
        track
    ) in tracks.items():

        if (
            segundo
            - track[
                "last_seen"
            ]
            > TRACK_TIMEOUT_SECONDS
        ):
            continue

        iou = calcular_iou(
            bbox,
            track[
                "bbox"
            ]
        )

        if iou > mejor_iou:

            mejor_iou = iou

            mejor_track = track_id

    if (
        mejor_track is not None
        and
        mejor_iou
        >= TRACK_IOU_THRESHOLD
    ):

        return (
            mejor_track,
            siguiente_id
        )

    track_id = siguiente_id

    tracks[
        track_id
    ] = {
        "bbox":
            bbox,

        "first_seen":
            segundo,

        "last_seen":
            segundo,

        "observaciones":
            [],

        "yolo_confidences":
            [],

        "confirmado":
            False,

        "placa_confirmada":
            None
    }

    return (
        track_id,
        siguiente_id + 1
    )


# ============================================================
# CONSENSO
# ============================================================

def obtener_consenso_track(
    observaciones
):

    placas = [
        obs[
            "placa"
        ]

        for obs
        in observaciones

        if validar_placa(
            obs[
                "placa"
            ]
        )
    ]

    if not placas:

        return (
            None,
            0,
            0.0
        )

    conteo = Counter(
        placas
    )

    placa, cantidad = (
        conteo
        .most_common(1)[0]
    )

    ratio = (
        cantidad
        /
        len(
            placas
        )
    )

    return (
        placa,
        cantidad,
        ratio
    )


# ============================================================
# EVIDENCIA FINAL
# ============================================================

def guardar_evidencia(
    frame,
    video_name,
    placa,
    frame_number,
    bbox,
    captured_at
):

    imagen = frame.copy()

    x1, y1, x2, y2 = bbox

    cv2.rectangle(
        imagen,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        4
    )

    texto = placa

    if captured_at:

        texto += (
            f" | {captured_at}"
        )

    cv2.putText(
        imagen,
        texto,
        (
            x1,
            max(
                y1 - 15,
                30
            )
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2
    )

    base_video = os.path.splitext(
        video_name
    )[0]

    nombre = (
        f"{base_video}_"
        f"{placa}_"
        f"frame_{frame_number}.jpg"
    )

    ruta = os.path.join(
        EVIDENCE_DIR,
        nombre
    )

    cv2.imwrite(
        ruta,
        imagen
    )

    return ruta


# ============================================================
# REDIMENSIONAR SOLO PARA GUI
# ============================================================

def preparar_frame_display(
    frame
):

    if (
        frame is None
        or
        frame.size == 0
    ):
        return frame

    alto, ancho = (
        frame.shape[:2]
    )

    if ancho <= DISPLAY_WIDTH:
        return frame

    escala = (
        DISPLAY_WIDTH
        / ancho
    )

    nuevo_alto = int(
        alto
        * escala
    )

    return cv2.resize(
        frame,
        (
            DISPLAY_WIDTH,
            nuevo_alto
        ),
        interpolation=cv2.INTER_AREA
    )


# ============================================================
# CREAR REGISTRO FINAL
# ============================================================

def crear_registro_match(
    video_name,
    track_id,
    placa,
    frame_number,
    segundo,
    yolo_conf,
    ocr_conf,
    timestamp,
    metodo,
    evidencia
):

    return {
        "video":
            video_name,

        "track_id":
            track_id,

        "placa":
            placa,

        "fecha":
            timestamp.get(
                "fecha",
                ""
            ),

        "hora":
            timestamp.get(
                "hora",
                ""
            ),

        "captured_at":
            timestamp.get(
                "captured_at",
                ""
            ),

        "frame":
            frame_number,

        "segundo_video":
            round(
                segundo,
                2
            ),

        "yolo_confidence":
            round(
                yolo_conf,
                4
            ),

        "ocr_confidence":
            round(
                ocr_conf,
                4
            ),

        "ocr_engine":
            "PaddleOCR",

        "timestamp_source":
            (
                "VIDEO_OVERLAY_OCR"

                if timestamp.get(
                    "ok"
                )

                else

                "NO_DISPONIBLE"
            ),

        "metodo_confirmacion":
            metodo,

        "estado":
            "MATCH_CONFIRMADO",

        "evidencia":
            evidencia
    }


# ============================================================
# PROCESAR VIDEO
# ============================================================

def procesar_video(
    modelo,
    paddle_worker,
    video_path
):

    video_name = os.path.basename(
        video_path
    )

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():

        print(
            f"ERROR abriendo "
            f"{video_name}"
        )

        return (
            [],
            [],
            []
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duracion = (
        total_frames
        / fps

        if fps > 0

        else 0
    )

    print()
    print("=" * 70)

    print(
        f"Procesando: "
        f"{video_name}"
    )

    print(
        f"FPS: "
        f"{fps:.2f}"
    )

    print(
        f"Frames: "
        f"{total_frames}"
    )

    print(
        f"Duracion: "
        f"{duracion:.2f}s"
    )

    print(
        f"Intervalo análisis: "
        f"{ANALYSIS_INTERVAL_SECONDS:.1f}s"
    )

    print("=" * 70)

    resultados_tecnicos = []

    resultados_finales = []

    resultados_match = []

    tracks = {}

    siguiente_track = 1

    placas_guardadas = {}

    frame_number = 0

    ultimo_analisis = (
        -ANALYSIS_INTERVAL_SECONDS
    )

    window_name = (
        "ALPR - YOLO + PaddleOCR"
    )

    if SHOW_VIDEO:

        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.resizeWindow(
            window_name,
            DISPLAY_WIDTH,
            int(
                DISPLAY_WIDTH
                * 9
                / 16
            )
        )

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1

        segundo = (
            (frame_number - 1)
            / fps

            if fps > 0

            else 0
        )

        frame_visual = frame.copy()

        # ====================================================
        # CONTROL DE FRECUENCIA DE ANÁLISIS
        # ====================================================

        analizar = (
            segundo
            - ultimo_analisis
            >= ANALYSIS_INTERVAL_SECONDS
        )

        if analizar:

            ultimo_analisis = (
                segundo
            )

            detecciones = detectar_placas(
                modelo,
                frame
            )

            print(
                f"[{segundo:05.2f}s] "
                f"YOLO: "
                f"{len(detecciones)}"
            )

            for deteccion in detecciones:

                bbox = (
                    deteccion[
                        "bbox"
                    ]
                )

                yolo_conf = (
                    deteccion[
                        "confidence"
                    ]
                )

                (
                    track_id,
                    siguiente_track
                ) = asignar_track(
                    tracks,
                    bbox,
                    segundo,
                    siguiente_track
                )

                track = tracks[
                    track_id
                ]

                track[
                    "bbox"
                ] = bbox

                track[
                    "last_seen"
                ] = segundo

                track[
                    "yolo_confidences"
                ].append(
                    yolo_conf
                )

                # =================================================
                # OCR DE PLACA
                # =================================================

                resultado_ocr = reconocer_placa(
                    paddle_worker,
                    frame,
                    bbox,
                    frame_number,
                    segundo,
                    track_id
                )

                candidatos = (
                    resultado_ocr[
                        "candidatos"
                    ]
                )

                if not candidatos:

                    resultados_tecnicos.append(
                        {
                            "video":
                                video_name,

                            "frame":
                                frame_number,

                            "segundo_video":
                                round(
                                    segundo,
                                    2
                                ),

                            "track_id":
                                track_id,

                            "yolo_confidence":
                                round(
                                    yolo_conf,
                                    4
                                ),

                            "ocr_lecturas":
                                resultado_ocr[
                                    "lecturas"
                                ],

                            "placa":
                                None,

                            "estado":
                                "YOLO_SIN_OCR_VALIDO"
                        }
                    )

                    continue

                candidato = max(
                    candidatos,
                    key=lambda x:
                        x[
                            "confianza"
                        ]
                )

                placa = (
                    candidato[
                        "placa"
                    ]
                )

                ocr_conf = (
                    candidato[
                        "confianza"
                    ]
                )

                track[
                    "observaciones"
                ].append(
                    {
                        "placa":
                            placa,

                        "confianza":
                            ocr_conf,

                        "segundo":
                            segundo
                    }
                )

                track[
                    "observaciones"
                ] = [
                    obs

                    for obs
                    in track[
                        "observaciones"
                    ]

                    if (
                        segundo
                        - obs[
                            "segundo"
                        ]
                    )
                    <= CONSENSUS_WINDOW_SECONDS
                ]

                (
                    placa_consenso,
                    cantidad_consenso,
                    ratio_consenso
                ) = obtener_consenso_track(
                    track[
                        "observaciones"
                    ]
                )

                # =================================================
                # CONFIRMACIÓN DIRECTA
                # =================================================

                confirmacion_directa = (
                    validar_placa(
                        placa
                    )

                    and

                    ocr_conf
                    >= OCR_DIRECT_CONFIRM_THRESHOLD

                    and

                    yolo_conf
                    >= YOLO_DIRECT_CONFIRM_THRESHOLD
                )

                resultados_tecnicos.append(
                    {
                        "video":
                            video_name,

                        "frame":
                            frame_number,

                        "segundo_video":
                            round(
                                segundo,
                                2
                            ),

                        "track_id":
                            track_id,

                        "yolo_confidence":
                            round(
                                yolo_conf,
                                4
                            ),

                        "ocr_lecturas":
                            resultado_ocr[
                                "lecturas"
                            ],

                        "placa":
                            placa,

                        "ocr_confidence":
                            round(
                                ocr_conf,
                                4
                            ),

                        "placa_consenso":
                            placa_consenso,

                        "observaciones_consenso":
                            cantidad_consenso,

                        "ratio_consenso":
                            round(
                                ratio_consenso,
                                4
                            ),

                        "confirmacion_directa":
                            confirmacion_directa
                    }
                )

                # =================================================
                # MATCH
                # =================================================

                if (
                    confirmacion_directa
                    and
                    not track[
                        "confirmado"
                    ]
                ):

                    ultima = (
                        placas_guardadas.get(
                            placa,
                            -999999
                        )
                    )

                    if (
                        segundo
                        - ultima
                        >= DUPLICATE_SECONDS
                    ):

                        # ==========================================
                        # LEER TIMESTAMP SOLO AL CONFIRMAR
                        # ==========================================

                        timestamp = leer_timestamp_frame(
                            paddle_worker,
                            frame,
                            frame_number
                        )

                        # ==========================================
                        # GUARDAR EVIDENCIA FUERA DE results
                        # ==========================================

                        evidencia = guardar_evidencia(
                            frame,
                            video_name,
                            placa,
                            frame_number,
                            bbox,
                            timestamp.get(
                                "captured_at",
                                ""
                            )
                        )

                        track[
                            "confirmado"
                        ] = True

                        track[
                            "placa_confirmada"
                        ] = placa

                        placas_guardadas[
                            placa
                        ] = segundo

                        registro = crear_registro_match(
                            video_name=
                                video_name,

                            track_id=
                                track_id,

                            placa=
                                placa,

                            frame_number=
                                frame_number,

                            segundo=
                                segundo,

                            yolo_conf=
                                yolo_conf,

                            ocr_conf=
                                ocr_conf,

                            timestamp=
                                timestamp,

                            metodo=
                                "OCR_ALTA_CONFIANZA",

                            evidencia=
                                evidencia
                        )

                        resultados_finales.append(
                            registro
                        )

                        resultados_match.append(
                            {
                                "video":
                                    video_name,

                                "placa":
                                    placa,

                                "fecha":
                                    timestamp.get(
                                        "fecha",
                                        ""
                                    ),

                                "hora":
                                    timestamp.get(
                                        "hora",
                                        ""
                                    ),

                                "captured_at":
                                    timestamp.get(
                                        "captured_at",
                                        ""
                                    ),

                                "frame":
                                    frame_number,

                                "segundo_video":
                                    round(
                                        segundo,
                                        2
                                    )
                            }
                        )

                        print()
                        print("=" * 60)

                        print(
                            "MATCH CONFIRMADO"
                        )

                        print(
                            f"Placa: "
                            f"{placa}"
                        )

                        print(
                            f"YOLO: "
                            f"{yolo_conf:.1%}"
                        )

                        print(
                            f"OCR: "
                            f"{ocr_conf:.1%}"
                        )

                        print(
                            f"Timestamp: "
                            f"{timestamp.get('captured_at', '')}"
                        )

                        print(
                            f"Evidencia: "
                            f"{evidencia}"
                        )

                        print("=" * 60)

                # =================================================
                # DIBUJAR EN GUI
                # =================================================

                x1, y1, x2, y2 = bbox

                color = (
                    (0, 255, 0)

                    if track[
                        "confirmado"
                    ]

                    else

                    (0, 255, 255)
                )

                cv2.rectangle(
                    frame_visual,
                    (x1, y1),
                    (x2, y2),
                    color,
                    3
                )

                texto_gui = (
                    track[
                        "placa_confirmada"
                    ]

                    if track[
                        "confirmado"
                    ]

                    else

                    placa
                )

                cv2.putText(
                    frame_visual,
                    texto_gui,
                    (
                        x1,
                        max(
                            y1 - 10,
                            30
                        )
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

        # ====================================================
        # GUI
        # ====================================================

        if SHOW_VIDEO:

            cv2.putText(
                frame_visual,
                (
                    f"{segundo:.1f}s | "
                    f"Frame "
                    f"{frame_number}/"
                    f"{total_frames}"
                ),
                (
                    30,
                    frame_visual.shape[0] - 30
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            frame_display = preparar_frame_display(
                frame_visual
            )

            cv2.imshow(
                window_name,
                frame_display
            )

            tecla = (
                cv2.waitKey(1)
                & 0xFF
            )

            if tecla == 27:

                print(
                    "Proceso detenido."
                )

                break

    cap.release()

    if SHOW_VIDEO:

        cv2.destroyAllWindows()

    return (
        resultados_tecnicos,
        resultados_finales,
        resultados_match
    )


# ============================================================
# GUARDAR JSON
# ============================================================

def guardar_json(
    ruta,
    datos
):

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# GUARDAR CSV
# ============================================================

def guardar_csv_video(
    ruta,
    datos
):

    campos = [
        "video",
        "track_id",
        "placa",
        "fecha",
        "hora",
        "captured_at",
        "frame",
        "segundo_video",
        "yolo_confidence",
        "ocr_confidence",
        "ocr_engine",
        "timestamp_source",
        "metodo_confirmacion",
        "estado",
        "evidencia"
    ]

    with open(
        ruta,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        writer = csv.DictWriter(
            archivo,
            fieldnames=campos
        )

        writer.writeheader()

        if datos:

            writer.writerows(
                datos
            )


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not os.path.exists(
        MODEL_PATH
    ):

        print(
            f"No existe modelo: "
            f"{MODEL_PATH}"
        )

        return


    if not os.path.exists(
        VIDEO_FOLDER
    ):

        print(
            f"No existe carpeta: "
            f"{VIDEO_FOLDER}"
        )

        return


    if not os.path.exists(
        PADDLE_WORKER_SCRIPT
    ):

        print(
            f"No existe worker: "
            f"{PADDLE_WORKER_SCRIPT}"
        )

        return


    # ========================================================
    # CARGAR YOLO
    # ========================================================

    print()
    print(
        "Cargando YOLO..."
    )

    modelo = YOLO(
        MODEL_PATH
    )

    print(
        "YOLO cargado."
    )


    # ========================================================
    # INICIAR PADDLEOCR
    # ========================================================

    paddle_worker = (
        PaddleWorker()
    )


    try:

        videos = [
            archivo

            for archivo
            in os.listdir(
                VIDEO_FOLDER
            )

            if archivo.lower().endswith(
                VIDEO_EXTENSIONS
            )
        ]

        videos.sort()

        if not videos:

            print(
                "No existen videos."
            )

            return


        # ====================================================
        # PROCESAR CADA VIDEO
        # ====================================================

        for numero, video in enumerate(
            videos,
            start=1
        ):

            print()
            print("=" * 70)

            print(
                f"VIDEO "
                f"{numero}/"
                f"{len(videos)}"
            )

            print(
                f"Archivo: "
                f"{video}"
            )

            print("=" * 70)


            ruta_video = os.path.join(
                VIDEO_FOLDER,
                video
            )


            (
                tecnicos,
                finales,
                matches
            ) = procesar_video(
                modelo,
                paddle_worker,
                ruta_video
            )


            # =================================================
            # ARCHIVOS DE SALIDA
            # =================================================

            salidas = obtener_nombres_salida(
                video
            )


            guardar_json(
                salidas[
                    "json_tecnico"
                ],
                tecnicos
            )


            guardar_json(
                salidas[
                    "json_final"
                ],
                finales
            )


            guardar_json(
                salidas[
                    "json_match"
                ],
                matches
            )


            guardar_csv_video(
                salidas[
                    "csv"
                ],
                finales
            )


            # =================================================
            # RESUMEN
            # =================================================

            print()
            print("-" * 70)

            print(
                f"VIDEO FINALIZADO: "
                f"{video}"
            )

            print(
                f"Registros técnicos: "
                f"{len(tecnicos)}"
            )

            print(
                f"Matches: "
                f"{len(finales)}"
            )

            print()
            print(
                "Resultados:"
            )

            print(
                f"  {salidas['json_tecnico']}"
            )

            print(
                f"  {salidas['json_final']}"
            )

            print(
                f"  {salidas['json_match']}"
            )

            print(
                f"  {salidas['csv']}"
            )

            print()

            print(
                f"Evidencias: "
                f"{os.path.abspath(EVIDENCE_DIR)}"
            )

            print("-" * 70)


    finally:

        paddle_worker.cerrar()


    print()
    print("=" * 70)

    print(
        "TODOS LOS VIDEOS PROCESADOS"
    )

    print()

    print(
        f"Resultados JSON/CSV:"
    )

    print(
        os.path.abspath(
            RESULTS_DIR
        )
    )

    print()

    print(
        f"Evidencias:"
    )

    print(
        os.path.abspath(
            EVIDENCE_DIR
        )
    )

    print("=" * 70)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()