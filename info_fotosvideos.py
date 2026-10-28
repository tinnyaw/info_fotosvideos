#!/usr/bin/env python3
"""
Analizador e Informador de Metadatos Multimedia para Nemo / Linux Mint.
Extrae información técnica (vídeo, audio, formato, rotación y Exif) mediante ffprobe
y la despliega en un cuadro de diálogo gráfico con Zenity.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys


def parsear_duracion(segundos_str: str) -> str:
    """Convierte segundos a formato legible HH:MM:SS."""
    try:
        total_sec = float(segundos_str)
        horas = int(total_sec // 3600)
        minutos = int((total_sec % 3600) // 60)
        segundos = int(total_sec % 60)
        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{segundos:02d} ({total_sec:.1f} s)"
        return f"{minutos:02d}:{segundos:02d} ({total_sec:.1f} s)"
    except (ValueError, TypeError):
        return "N/A"


def parsear_bitrate(bitrate_str: str) -> str:
    """Formatea la tasa de bits en Mbps o kbps."""
    try:
        bps = int(bitrate_str)
        if bps >= 1_000_000:
            return f"{bps / 1_000_000:.2f} Mbps"
        return f"{bps / 1_000:.0f} kbps"
    except (ValueError, TypeError):
        return "N/A"


def parsear_framerate(fps_str: str) -> str:
    """Convierte cadenas de tipo '30000/1001' o '30/1' a FPS decimales legibles."""
    if not fps_str or fps_str == "0/0":
        return "N/A"
    try:
        if "/" in fps_str:
            num, den = map(float, fps_str.split("/"))
            if den == 0:
                return "N/A"
            fps = num / den
        else:
            fps = float(fps_str)
        return f"{fps:.2f} fps"
    except (ValueError, TypeError):
        return str(fps_str)


def obtener_info_multimedia(ruta_archivo: pathlib.Path) -> dict:
    """Ejecuta ffprobe para extraer todos los datos del contenedor y de sus pistas."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(ruta_archivo)
    ]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
        datos = json.loads(resultado.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        return {"error": f"No se pudo analizar el archivo:\n{e}"}

    fmt = datos.get("format", {})
    streams = datos.get("streams", [])

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    # 1. Información General del Contenedor
    nombre = ruta_archivo.name
    formato = fmt.get("format_long_name") or fmt.get("format_name", "Desconocido")
    duracion = parsear_duracion(fmt.get("duration"))
    bitrate = parsear_bitrate(fmt.get("bit_rate"))

    # 2. Metadatos Exif / Fecha de creación (Stream o Format tags)
    tags_format = fmt.get("tags", {})
    tags_video = v_stream.get("tags", {}) if v_stream else {}
    creation_time = (
        tags_video.get("creation_time") or 
        tags_format.get("creation_time") or 
        "No disponible"
    )

    # 3. Datos de Vídeo
    if v_stream:
        codec_v = v_stream.get("codec_name", "N/A").upper()
        w = v_stream.get("width", 0)
        h = v_stream.get("height", 0)
        dimensiones = f"{w} × {h} px" if w and h else "N/A"
        
        fps_raw = v_stream.get("r_frame_rate") or v_stream.get("avg_frame_rate")
        framerate = parsear_framerate(fps_raw)

        # Rotación
        rotacion = 0
        for side_data in v_stream.get("side_data_list", []):
            if "rotation" in side_data:
                rotacion = abs(int(side_data["rotation"]))
        if not rotacion and "rotate" in tags_video:
            try:
                rotacion = abs(int(tags_video["rotate"]))
            except ValueError:
                pass
        rotation_str = f"{rotacion}°"
    else:
        codec_v = "Sin pista de vídeo"
        dimensiones = "N/A"
        framerate = "N/A"
        rotation_str = "N/A"

    # 4. Datos de Audio
    if a_stream:
        codec_a = a_stream.get("codec_name", "N/A").upper()
        sr = a_stream.get("sample_rate")
        sample_rate = f"{int(sr):,} Hz".replace(",", ".") if sr else "N/A"
    else:
        codec_a = "Sin pista de audio"
        sample_rate = "N/A"

    return {
        "nombre": nombre,
        "formato": formato,
        "length": duracion,
        "bitrate": bitrate,
        "video_codec": codec_v,
        "dimensiones": dimensiones,
        "framerate": framerate,
        "rotation": rotation_str,
        "audio_codec": codec_a,
        "samplerate": sample_rate,
        "creation_time": creation_time,
    }


def mostrar_dialogo_zenity(info: dict) -> None:
    """Genera la interfaz gráfica modal con Zenity con Pango Markup."""
    if "error" in info:
        cmd = [
            "zenity", "--error",
            "--title=❌ Error en Archivo Multimedia",
            f"--text={info['error']}",
            "--width=400"
        ]
        subprocess.run(cmd, check=False)
        return

    texto_html = f"""<b>📁 Archivo:</b> {info['nombre']}

<b>🎬 Vídeo y Contenedor:</b>
• <b>Formato:</b> {info['formato']}
• <b>Duración (Length):</b> {info['length']}
• <b>Bitrate Total:</b> {info['bitrate']}
• <b>Códec de Vídeo:</b> {info['video_codec']}
• <b>Dimensiones:</b> {info['dimensiones']}
• <b>Tasa de Fotogramas (Framerate):</b> {info['framerate']}
• <b>Rotación:</b> {info['rotation']}

<b>🎵 Audio:</b>
• <b>Códec de Audio:</b> {info['audio_codec']}
• <b>Frecuencia de Muestreo (Samplerate):</b> {info['samplerate']}

<b>📅 Metadatos EXIF / Fecha de Captura:</b>
• <b>creation_time:</b> {info['creation_time']}"""

    # Si se ejecuta sin GUI (terminal sin DISPLAY/Wayland), muestra salida por consola
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print(texto_html.replace("<b>", "").replace("</b>", ""))
        return

    if shutil.which("zenity"):
        subprocess.run([
            "zenity",
            "--info",
            "--title=📊 Informador Multimedia",
            f"--text={texto_html}",
            "--width=480",
            "--no-wrap"
        ], check=False)


def main():
    if len(sys.argv) < 2:
        print("Uso: info_multimedia.py <ruta_al_video>")
        sys.exit(1)

    archivo = pathlib.Path(sys.argv[1]).resolve()
    if not archivo.is_file():
        print(f"Error: El archivo {archivo} no existe.")
        sys.exit(1)

    info = obtener_info_multimedia(archivo)
    mostrar_dialogo_zenity(info)


if __name__ == "__main__":
    main()