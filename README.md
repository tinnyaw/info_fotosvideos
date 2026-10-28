# 📊 Informador Multimedia y Metadatos para Nemo (Linux Mint / Cinnamon)

Herramienta ligera y modular de análisis técnico para archivos de vídeo, audio e imágenes. Está integrada nativamente en el gestor de archivos **Nemo** mediante el menú contextual y utiliza `ffprobe` y `Zenity` para extraer y desplegar metadatos y etiquetas EXIF de forma visual, segura y sin consumo persistente de recursos.

---

## 🛠️ Arquitectura y Compatibilidad

Este proyecto consta de dos componentes desacoplados:
1. **Script de Procesamiento en Python (`info_fotosvideos.py`):** Encargado del parseo de metadatos mediante `ffprobe`, manejo de excepciones, formateo de datos y renderizado de la interfaz gráfica modal vía `Zenity`.
2. **Archivo de Acción de Nemo (`info_fotosvideos.nemo_action`):** Define el punto de entrada en el menú contextual de Linux Mint Cinnamon.

### Compatibilidad de Plataformas
* **Linux Mint (Cinnamon):** Integración nativa completa mediante GUI.
* **Ubuntu Studio / Ubuntu Server:** Operativo mediante ejecución CLI directa desde la terminal o integrado en gestores de archivos compatibles con acciones FreeDesktop/Nemo.

---

## ⚙️ Requisitos del Sistema

El script utiliza exclusivamente la **librería estándar de Python 3** para mantener la máxima ligereza en hardware limitado (ej. Celeron N5000 / 8GB RAM). 

Requiere la presencia de las siguientes utilidades del sistema:

* **Python 3.x**
* **ffmpeg** (provee el binario `ffprobe`)
* **zenity** (provee los cuadros de diálogo gráficos)

### Instalación de dependencias en Debian/Ubuntu/Mint:

```bash
sudo apt update
sudo apt install -y python3 ffmpeg zenity