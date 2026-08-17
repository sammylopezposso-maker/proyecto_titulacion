import sys
import json

from paddleocr import PaddleOCR


# ============================================================
# CONFIGURACIÓN
# ============================================================

DEVICE = "cpu"


# ============================================================
# EXTRAER RESULTADOS
# ============================================================

def extraer_resultados(resultado):

    lecturas = []

    for item in resultado:

        datos = None

        try:
            datos = item.json
        except Exception:
            pass

        if callable(datos):
            try:
                datos = datos()
            except Exception:
                datos = None

        if datos is None:
            try:
                datos = item.to_dict()
            except Exception:
                datos = None

        if not isinstance(datos, dict):
            continue

        if (
            "res" in datos
            and isinstance(datos["res"], dict)
        ):
            datos = datos["res"]

        rec_texts = datos.get(
            "rec_texts",
            []
        )

        rec_scores = datos.get(
            "rec_scores",
            []
        )

        for indice, texto in enumerate(rec_texts):

            confianza = 0.0

            if indice < len(rec_scores):
                try:
                    confianza = float(
                        rec_scores[indice]
                    )
                except Exception:
                    confianza = 0.0

            lecturas.append(
                {
                    "texto_bruto": str(texto),
                    "confianza": confianza
                }
            )

    return lecturas


# ============================================================
# MAIN
# ============================================================

def main():

    ocr = PaddleOCR(
        lang="en",
        device=DEVICE,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False
    )

    print(
        "__PADDLE_READY__",
        flush=True
    )

    for linea in sys.stdin:

        linea = linea.strip()

        if not linea:
            continue

        try:
            peticion = json.loads(linea)

        except Exception as error:

            respuesta = {
                "ok": False,
                "error": str(error),
                "lecturas": []
            }

            print(
                "__PADDLE_RESULT__"
                + json.dumps(
                    respuesta,
                    ensure_ascii=False
                ),
                flush=True
            )

            continue


        comando = peticion.get(
            "command",
            "ocr"
        )


        if comando == "quit":

            print(
                "__PADDLE_BYE__",
                flush=True
            )

            break


        ruta = peticion.get(
            "image"
        )


        try:

            resultado = ocr.predict(
                ruta
            )

            lecturas = extraer_resultados(
                resultado
            )

            respuesta = {
                "ok": True,
                "device": DEVICE,
                "lecturas": lecturas
            }

        except Exception as error:

            respuesta = {
                "ok": False,
                "device": DEVICE,
                "error": str(error),
                "lecturas": []
            }


        print(
            "__PADDLE_RESULT__"
            + json.dumps(
                respuesta,
                ensure_ascii=False
            ),
            flush=True
        )


if __name__ == "__main__":
    main()