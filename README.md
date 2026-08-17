# Sistema ALPR – Reconocimiento Automático de Placas Vehiculares

## Mecánica Automotriz Mundial – Ibarra

Prototipo de **Reconocimiento Automático de Placas Vehiculares (ALPR)** desarrollado como parte del proyecto de titulación de la **Maestría en Inteligencia Artificial Aplicada – Universidad de Las Américas (UDLA)**.

El sistema utiliza técnicas de **visión por computadora, detección de objetos y reconocimiento óptico de caracteres (OCR)** para detectar placas vehiculares dentro de videos, extraer la región correspondiente a la placa, reconocer sus caracteres y generar resultados estructurados.

---

# 1. Tecnologías utilizadas

El proyecto utiliza las siguientes tecnologías principales:

* **Python 3.12.10**
* **OpenCV** – procesamiento de imágenes y videos.
* **Ultralytics YOLO** – detección de placas vehiculares.
* **PaddleOCR** – reconocimiento óptico de caracteres.
* **PaddlePaddle** – motor utilizado por PaddleOCR.
* **NumPy** – procesamiento matricial.
* **JSON** – almacenamiento de resultados estructurados.
* **CSV** – exportación de resultados.
* **Git** – control de versiones.

> **Importante:** el entorno de desarrollo recomendado para este proyecto es **Python 3.12.10**.

---

# 2. Flujo general del sistema

El pipeline del sistema es:

```text
Video de entrada
       ↓
Extracción de frames
       ↓
Detección de placa con YOLO
       ↓
Extracción de la región de interés (ROI)
       ↓
Preprocesamiento de imagen
       ↓
Reconocimiento mediante OCR
       ↓
Normalización de caracteres
       ↓
Validación del formato de placa
       ↓
Consolidación de resultados
       ↓
Generación de JSON / CSV
       ↓
Almacenamiento de evidencias
```

---

# 3. Requisitos del sistema

## 3.1 Requisitos mínimos

Para ejecutar el prototipo se recomienda:

| Componente        | Requisito mínimo                                |
| ----------------- | ----------------------------------------------- |
| Sistema operativo | Windows 10/11, Linux o macOS                    |
| Python            | 3.12.10                                         |
| Procesador        | Intel Core i5 / AMD Ryzen 5 o equivalente       |
| Memoria RAM       | 8 GB                                            |
| Almacenamiento    | 5 GB libres                                     |
| GPU               | No obligatoria                                  |
| Internet          | Requerido principalmente durante la instalación |

## 3.2 Configuración recomendada

Para procesamiento de video con mejor rendimiento:

| Componente     | Recomendado                          |
| -------------- | ------------------------------------ |
| Procesador     | Intel Core i7/i9 o AMD Ryzen 7/9     |
| Memoria RAM    | 16 GB o superior                     |
| Almacenamiento | SSD                                  |
| GPU            | NVIDIA compatible con CUDA, opcional |
| VRAM           | 4 GB o superior                      |
| Python         | 3.12.10                              |

El proyecto puede ejecutarse utilizando únicamente **CPU**, por lo que una GPU dedicada no es un requisito obligatorio.

---

# 4. Estructura general del proyecto

La estructura esperada del repositorio es similar a:

```text
proyecto_alpr/
│
├── main.py
├── paddle_worker.py
├── train_yolo.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── models/
│   └── license_plate_detector.pt
│
├── videos/
│   └── video_ejemplo.mp4
│
├── results/
│   ├── debug_placas/
│   └── debug_timestamp/
│
├── evidencias/
│
├── datasets/
│   └── placas_ecuador/
│       ├── train/
│       ├── valid/
│       ├── test/
│       └── data.yaml
│
└── runs/
```

---

# 5. Instalación desde cero

Esta sección explica cómo preparar el proyecto en un computador nuevo.

## PASO 1 – Instalar Git

Git es necesario para clonar el repositorio.

### Windows

Abrir PowerShell y comprobar:

```powershell
git --version
```

Si Git está instalado se mostrará una versión similar a:

```text
git version 2.x.x
```

Si no está instalado, puede instalarse mediante `winget`:

```powershell
winget install --id Git.Git -e
```

Cerrar y volver a abrir PowerShell después de la instalación.

Comprobar nuevamente:

```powershell
git --version
```

### Linux

En Ubuntu/Debian:

```bash
sudo apt update
sudo apt install git
```

Verificar:

```bash
git --version
```

### macOS

Verificar:

```bash
git --version
```

Si no está disponible, macOS puede solicitar automáticamente la instalación de las Command Line Tools.

---

# 6. Instalar Python 3.12.10

El proyecto está preparado para trabajar con:

```text
Python 3.12.10
```

## Windows

Después de instalar Python 3.12.10, abrir una nueva terminal PowerShell y ejecutar:

```powershell
py -3.12 --version
```

Resultado esperado:

```text
Python 3.12.10
```

También puede comprobarse con:

```powershell
python --version
```

Si `python` apunta correctamente a la instalación, deberá mostrar:

```text
Python 3.12.10
```

> Durante la instalación de Python en Windows es recomendable habilitar la opción **Add Python to PATH**.

---

## Linux

Comprobar:

```bash
python3.12 --version
```

Resultado esperado:

```text
Python 3.12.10
```

También debe estar disponible el módulo para creación de entornos virtuales.

En distribuciones Debian/Ubuntu puede ser necesario instalar:

```bash
sudo apt install python3.12-venv
```

---

## macOS

Comprobar la instalación mediante:

```bash
python3.12 --version
```

Resultado esperado:

```text
Python 3.12.10
```

---

# 7. Clonar el repositorio

Ubicarse en la carpeta donde se desea almacenar el proyecto.

Ejemplo:

```bash
git clone URL_DEL_REPOSITORIO.git
```

Posteriormente:

```bash
cd proyecto_alpr
```

Ejemplo en Windows:

```powershell
cd D:\Dev\Maestria
git clone URL_DEL_REPOSITORIO.git
cd proyecto_alpr
```

> Sustituir `URL_DEL_REPOSITORIO.git` por la dirección real del repositorio GitHub del proyecto.

---

# 8. Crear el entorno virtual `.venv`

Todas las dependencias deben instalarse dentro de un entorno virtual.

Esto evita modificar la instalación global de Python y permite mantener un ambiente reproducible para el proyecto.

## Windows – PowerShell

Desde la carpeta raíz del proyecto:

```powershell
py -3.12 -m venv .venv
```

La estructura será:

```text
proyecto_alpr/
│
├── .venv/
├── main.py
├── requirements.txt
└── ...
```

---

# 9. Activar `.venv`

## Windows – PowerShell

Ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si se activó correctamente, la terminal mostrará:

```text
(.venv) PS D:\Dev\Maestria\proyecto_alpr>
```

---

## Windows – CMD

Ejecutar:

```cmd
.venv\Scripts\activate.bat
```

---

## Linux

Crear el entorno:

```bash
python3.12 -m venv .venv
```

Activarlo:

```bash
source .venv/bin/activate
```

---

## macOS

Crear:

```bash
python3.12 -m venv .venv
```

Activar:

```bash
source .venv/bin/activate
```

---

# 10. Verificar que `.venv` utiliza Python 3.12.10

Después de activar `.venv`, ejecutar:

```bash
python --version
```

El resultado debe ser exactamente:

```text
Python 3.12.10
```

También:

```bash
python -m pip --version
```

En Windows puede verificarse la ubicación del ejecutable mediante:

```powershell
where.exe python
```

La primera ruta debería apuntar al entorno virtual:

```text
...\proyecto_alpr\.venv\Scripts\python.exe
```

En Linux/macOS:

```bash
which python
```

Debe apuntar a:

```text
.../proyecto_alpr/.venv/bin/python
```

---

# 11. Problema de ejecución de scripts en PowerShell

En algunos computadores Windows, PowerShell puede mostrar un error al ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

relacionado con la política de ejecución.

Para habilitar scripts únicamente durante la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después ejecutar nuevamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Esta configuración aplica únicamente a la sesión actual de PowerShell.

---

# 12. Actualizar pip

Con `.venv` activado:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Comprobar:

```bash
pip --version
```

---

# 13. Instalar las dependencias

Con el entorno virtual activo ejecutar:

```bash
pip install -r requirements.txt
```

También puede utilizarse:

```bash
python -m pip install -r requirements.txt
```

Se recomienda la segunda opción porque garantiza que `pip` pertenece al mismo intérprete Python activo:

```bash
python -m pip install -r requirements.txt
```

La instalación puede tardar varios minutos debido a librerías como:

* OpenCV
* Ultralytics
* PaddleOCR
* PaddlePaddle

---

# 14. Verificar las dependencias

## OpenCV

Ejecutar:

```bash
python -c "import cv2; print('OpenCV:', cv2.__version__)"
```

Si funciona correctamente mostrará:

```text
OpenCV: x.x.x
```

## Ultralytics

Ejecutar:

```bash
python -c "import ultralytics; print('Ultralytics OK')"
```

Resultado:

```text
Ultralytics OK
```

## PaddlePaddle

Ejecutar:

```bash
python -c "import paddle; print('PaddlePaddle:', paddle.__version__)"
```

## PaddleOCR

Ejecutar:

```bash
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

Resultado:

```text
PaddleOCR OK
```

---

# 15. Verificar todas las dependencias instaladas

Para visualizar los paquetes:

```bash
pip list
```

Para obtener las versiones exactas:

```bash
pip freeze
```

---

# 16. Verificar el modelo de detección

El sistema necesita el modelo entrenado para detección de placas.

Debe existir:

```text
models/license_plate_detector.pt
```

La estructura debe ser:

```text
proyecto_alpr/
│
├── models/
│   └── license_plate_detector.pt
│
├── main.py
└── ...
```

Si el archivo no está presente, el sistema no podrá realizar la detección mediante YOLO.

---

# 17. Preparar los videos

Los videos a procesar deben colocarse dentro de:

```text
videos/
```

Ejemplo:

```text
proyecto_alpr/
│
├── videos/
│   ├── vehiculo_001.mp4
│   ├── vehiculo_002.mp4
│   └── vehiculo_003.mp4
│
└── main.py
```

Entre los formatos de video utilizados por el proyecto se encuentran:

```text
.mp4
.MP4
.avi
.mov
.mkv
```

---

# 18. Ejecutar el proyecto

Verificar primero que `.venv` esté activo.

Windows:

```text
(.venv) PS D:\Dev\Maestria\proyecto_alpr>
```

Ejecutar:

```bash
python main.py
```

En Windows:

```powershell
(.venv) PS D:\Dev\Maestria\proyecto_alpr> python main.py
```

El programa realizará:

```text
Carga del modelo YOLO
        ↓
Inicialización del OCR
        ↓
Lectura del video
        ↓
Análisis de frames
        ↓
Detección de placas
        ↓
OCR
        ↓
Validación
        ↓
Generación de resultados
        ↓
Generación de evidencias
```

---

# 19. Resultados

Los resultados del procesamiento se almacenan principalmente en:

```text
results/
```

Dependiendo de la ejecución pueden generarse archivos como:

```text
results/
├── video_resultados.csv
├── video_resultados_final.json
├── video_resultados_match.json
├── video_resultados_tecnico.json
├── debug_placas/
└── debug_timestamp/
```

---

# 20. Evidencias

Las capturas utilizadas como evidencia pueden almacenarse en:

```text
evidencias/
```

Ejemplo:

```text
evidencias/
├── vehiculo_001_placa_frame_01.jpg
├── vehiculo_002_placa_frame_01.jpg
└── ...
```

---

# 21. Configuración principal

Los parámetros del pipeline pueden encontrarse dentro del código principal.

Entre los parámetros utilizados se encuentran configuraciones relacionadas con:

```text
Confianza mínima de detección YOLO
Confianza de aceptación
Resolución de inferencia
Intervalo de análisis de frames
Dispositivo CPU/GPU
Visualización del video
Modo debug
Almacenamiento de imágenes de depuración
```

Estos valores deben modificarse de manera controlada para conservar la reproducibilidad de los experimentos.

---

# 22. Ejecución mediante CPU

El prototipo puede configurarse para trabajar mediante:

```python
YOLO_DEVICE = "cpu"
```

Esta configuración permite ejecutar el sistema sin una tarjeta gráfica NVIDIA dedicada.

La velocidad de procesamiento dependerá principalmente de:

* procesador;
* resolución del video;
* resolución utilizada por YOLO;
* cantidad de frames analizados;
* cantidad de detecciones;
* procesamiento OCR.

---

# 23. PaddleOCR

El proyecto utiliza PaddleOCR para el reconocimiento de caracteres.

Si existe:

```text
paddle_worker.py
```

y este es iniciado automáticamente desde `main.py`, no es necesario ejecutar manualmente el worker.

La ejecución normal debe realizarse mediante:

```bash
python main.py
```

---

# 24. Entrenamiento del modelo YOLO

Si se desea volver a entrenar el detector y el repositorio contiene:

```text
train_yolo.py
```

ejecutar:

```bash
python train_yolo.py
```

El dataset debe encontrarse correctamente configurado antes de ejecutar el entrenamiento.

Una estructura habitual es:

```text
datasets/
└── placas_ecuador/
    ├── train/
    │   ├── images/
    │   └── labels/
    │
    ├── valid/
    │   ├── images/
    │   └── labels/
    │
    ├── test/
    │   ├── images/
    │   └── labels/
    │
    └── data.yaml
```

---

# 25. Desactivar `.venv`

Cuando se termine de trabajar con el proyecto:

```bash
deactivate
```

La terminal dejará de mostrar:

```text
(.venv)
```

---

# 26. Volver a trabajar en el proyecto

No es necesario crear `.venv` cada vez.

Después de reiniciar el computador:

## Windows

Entrar al proyecto:

```powershell
cd D:\Dev\Maestria\proyecto_alpr
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Ejecutar:

```powershell
python main.py
```

## Linux/macOS

```bash
cd proyecto_alpr
source .venv/bin/activate
python main.py
```

---

# 27. Reconstruir `.venv`

Si el entorno presenta problemas graves, puede eliminarse y crearse nuevamente.

## Windows PowerShell

Desactivar:

```powershell
deactivate
```

Eliminar:

```powershell
Remove-Item -Recurse -Force .venv
```

Crear nuevamente:

```powershell
py -3.12 -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar herramientas:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Verificar:

```powershell
python --version
```

Resultado esperado:

```text
Python 3.12.10
```

---

## Linux/macOS

```bash
deactivate
rm -rf .venv

python3.12 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel

python -m pip install -r requirements.txt
```

---

# 28. `.gitignore`

El directorio `.venv` **NO debe subirse al repositorio Git**.

El `.gitignore` debe contener como mínimo:

```gitignore
# Entornos virtuales
.venv/
.venv*/
venv/
venv*/
env/

# Python
__pycache__/
*.py[cod]
*$py.class

# IDE
.vscode/
.idea/

# Sistema operativo
.DS_Store
Thumbs.db

# Archivos temporales
*.tmp
*.log
```

---

# 29. Verificar que `.venv` está siendo ignorado

Ejecutar:

```bash
git status
```

La carpeta:

```text
.venv/
```

no debe aparecer entre los archivos pendientes para subir.

También puede verificarse mediante:

```bash
git check-ignore -v .venv/
```

---

# 30. Instalación rápida en Windows

Para un computador que ya tenga **Git y Python 3.12.10**, el proceso completo es:

```powershell
git clone URL_DEL_REPOSITORIO.git

cd proyecto_alpr

py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1

python --version

python -m pip install --upgrade pip setuptools wheel

python -m pip install -r requirements.txt

python main.py
```

La comprobación:

```powershell
python --version
```

debe devolver:

```text
Python 3.12.10
```

---

# 31. Instalación rápida en Linux/macOS

```bash
git clone URL_DEL_REPOSITORIO.git

cd proyecto_alpr

python3.12 -m venv .venv

source .venv/bin/activate

python --version

python -m pip install --upgrade pip setuptools wheel

python -m pip install -r requirements.txt

python main.py
```

---

# 32. Solución de problemas

## Error: `python` no se reconoce

En Windows probar:

```powershell
py -3.12 --version
```

Si devuelve:

```text
Python 3.12.10
```

crear el entorno mediante:

```powershell
py -3.12 -m venv .venv
```

---

## Error al activar `.venv` en PowerShell

Ejecutar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Error: `No module named cv2`

Con `.venv` activo:

```bash
python -m pip install opencv-python
```

---

## Error: `No module named ultralytics`

Ejecutar:

```bash
python -m pip install ultralytics
```

---

## Error relacionado con PaddleOCR

Comprobar primero:

```bash
python -c "import paddle; print(paddle.__version__)"
```

Después:

```bash
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

Si una dependencia no está instalada, volver a ejecutar:

```bash
python -m pip install -r requirements.txt
```

---

## El programa no encuentra videos

Comprobar que los videos estén dentro de:

```text
videos/
```

---

## El programa no encuentra el modelo

Comprobar que exista:

```text
models/license_plate_detector.pt
```

---

# 33. Reproducibilidad

Para asegurar que otro integrante pueda reproducir los resultados deben mantenerse controlados:

* versión de Python;
* versiones de dependencias;
* versión del modelo YOLO;
* dataset utilizado;
* parámetros de inferencia;
* videos de prueba;
* configuración experimental;
* resultados obtenidos;
* commit de Git correspondiente.

La versión de Python utilizada debe comprobarse mediante:

```bash
python --version
```

Resultado esperado:

```text
Python 3.12.10
```

Las dependencias pueden comprobarse mediante:

```bash
pip freeze
```

El commit utilizado puede obtenerse mediante:

```bash
git rev-parse HEAD
```

---

# 34. Generar `requirements.txt`

Cuando el entorno `.venv` haya sido completamente probado y funcione correctamente, se pueden congelar las versiones instaladas mediante:

```bash
python -m pip freeze > requirements.txt
```

Después verificar:

```bash
cat requirements.txt
```

En Windows PowerShell:

```powershell
Get-Content requirements.txt
```

> Se recomienda generar `requirements.txt` únicamente desde un entorno limpio y funcional del proyecto.

---

# 35. Consideraciones de privacidad

El prototipo procesa placas vehiculares para el propósito académico y operativo definido para Mecánica Automotriz Mundial.

El alcance del sistema no contempla:

* reconocimiento facial;
* identificación biométrica;
* identificación automática del propietario;
* consulta automática a registros gubernamentales;
* vigilancia externa al establecimiento.

Las imágenes, videos, placas y resultados utilizados durante las pruebas deben mantenerse con acceso restringido y conservarse únicamente durante el período necesario para la evaluación académica y operativa.

---

# 36. Proyecto académico

**Universidad de Las Américas – UDLA**

**Facultad de Ingeniería y Ciencias Aplicadas**

**Maestría en Inteligencia Artificial Aplicada**

### Tema

**Desarrollo de un prototipo de reconocimiento automático de placas vehiculares mediante visión por computadora para automatizar el registro de vehículos para Mecánica Automotriz Mundial de Ibarra.**

---

# 37. Estado del proyecto

**Prototipo académico en desarrollo y validación.**

El sistema no debe considerarse un mecanismo de control de acceso crítico. Las lecturas con baja confianza, formato inválido o resultados ambiguos deben ser sometidas a revisión antes de considerarse registros válidos.

---

# 38. Resumen de instalación

### Windows

```powershell
# 1. Clonar
git clone URL_DEL_REPOSITORIO.git
cd proyecto_alpr

# 2. Crear entorno virtual con Python 3.12
py -3.12 -m venv .venv

# 3. Activar
.\.venv\Scripts\Activate.ps1

# 4. Verificar Python
python --version

# 5. Actualizar pip
python -m pip install --upgrade pip setuptools wheel

# 6. Instalar dependencias
python -m pip install -r requirements.txt

# 7. Ejecutar
python main.py
```

### Linux/macOS

```bash
# 1. Clonar
git clone URL_DEL_REPOSITORIO.git
cd proyecto_alpr

# 2. Crear entorno
python3.12 -m venv .venv

# 3. Activar
source .venv/bin/activate

# 4. Verificar
python --version

# 5. Actualizar pip
python -m pip install --upgrade pip setuptools wheel

# 6. Instalar dependencias
python -m pip install -r requirements.txt
python -m pip install paddlepaddle==3.2.2
python -m pip install paddleocr
 
# 7. Ejecutar
python main.py
```

La instalación se considera correcta cuando:

```bash
python --version
```

muestra:

```text
Python 3.12.10
```

y:

```bash
python main.py
```

inicia correctamente el pipeline de detección y reconocimiento de placas.
