from ultralytics import YOLO


def main():

    print("=" * 60)
    print("ENTRENAMIENTO YOLO - PLACAS ECUADOR")
    print("=" * 60)

    # Modelo base preentrenado
    model = YOLO("yolo11n.pt")

    # Entrenamiento
    results = model.train(

        # Archivo descargado con el dataset
        data="datasets/placas_ecuador/data.yaml",

        # Número de épocas
        epochs=100,

        # Resolución
        imgsz=640,

        # Batch inicial
        batch=8,

        # Early stopping
        patience=20,

        # Nombre del experimento
        project="runs_alpr",

        name="placas_ecuador",

        # Utilizar pesos preentrenados
        pretrained=True,

        # Guardar resultados
        save=True,

        # Gráficos de entrenamiento
        plots=True
    )

    print()
    print("=" * 60)
    print("ENTRENAMIENTO FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":
    main()