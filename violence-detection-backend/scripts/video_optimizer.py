#!/usr/bin/env python3
"""
Utilidad para optimizar y verificar videos de evidencia
Corrige problemas de FPS y mejora la calidad de reproducción
"""

import cv2
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import json
import subprocess
from typing import List, Dict, Any, Optional
import shutil


class VideoOptimizer:
    """Optimizador de videos de evidencia para corregir problemas de FPS"""

    def __init__(self, target_fps: int = 15, output_quality: str = "alta"):
        self.target_fps = target_fps
        self.output_quality = output_quality
        self.quality_settings = {
            "alta": {"crf": 20, "bitrate": "2000k", "scale": 1.0},
            "media": {"crf": 25, "bitrate": "1000k", "scale": 0.75},
            "baja": {"crf": 30, "bitrate": "500k", "scale": 0.5}
        }

    def analizar_video(self, video_path: Path) -> Dict[str, Any]:
        """Analiza un video y devuelve información detallada"""
        try:
            cap = cv2.VideoCapture(str(video_path))

            if not cap.isOpened():
                return {"error": "No se pudo abrir el video"}

            # Obtener propiedades del video
            fps_original = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Calcular duración real
            duracion_calculada = frame_count / fps_original if fps_original > 0 else 0

            # Verificar timestamps reales leyendo algunos frames
            timestamps = []
            frame_indices = [0, frame_count//4, frame_count //
                            2, 3*frame_count//4, frame_count-1]

            for frame_idx in frame_indices:
                if frame_idx >= frame_count:
                    continue
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                timestamps.append(timestamp_ms / 1000)  # Convertir a segundos

            cap.release()

            # Calcular FPS real basado en timestamps
            fps_real = 0
            if len(timestamps) > 1:
                tiempo_total = timestamps[-1] - timestamps[0]
                frames_analizados = len(timestamps) - 1
                fps_real = frames_analizados / tiempo_total if tiempo_total > 0 else 0

            # Obtener información del archivo
            file_size = video_path.stat().st_size / (1024 * 1024)  # MB

            analysis = {
                "archivo": str(video_path),
                "tamaño_mb": round(file_size, 2),
                "resolución": f"{width}x{height}",
                "fps_declarado": round(fps_original, 2),
                "fps_real_estimado": round(fps_real, 2),
                "total_frames": frame_count,
                "duración_calculada": round(duracion_calculada, 2),
                "timestamps_muestra": timestamps,
                "necesita_optimización": abs(fps_original - self.target_fps) > 1 or fps_real < fps_original * 0.8,
                "problema_detectado": None
            }

            # Detectar problemas comunes
            if fps_original > self.target_fps * 1.5:
                analysis["problema_detectado"] = "FPS demasiado alto - video se reproduce muy rápido"
            elif fps_original < self.target_fps * 0.5:
                analysis["problema_detectado"] = "FPS demasiado bajo - video se reproduce muy lento"
            elif abs(fps_real - fps_original) > fps_original * 0.2:
                analysis["problema_detectado"] = "Inconsistencia entre FPS declarado y real"
            elif duracion_calculada < 3:
                analysis["problema_detectado"] = "Video demasiado corto para evidencia"
            elif duracion_calculada > 20:
                analysis["problema_detectado"] = "Video demasiado largo - posible problema de buffer"

            return analysis

        except Exception as e:
            return {"error": f"Error analizando video: {str(e)}"}

    def optimizar_video_opencv(self, input_path: Path, output_path: Path) -> bool:
        """Optimiza un video usando OpenCV con FPS consistente"""
        try:
            print(f"🔧 Optimizando {input_path.name} con OpenCV...")

            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                print(f"❌ Error: No se pudo abrir {input_path}")
                return False

            # Obtener propiedades originales
            fps_original = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            print(
                f"📹 Video original: {width}x{height}, {fps_original:.2f}fps, {total_frames} frames")

            # Configurar codec y writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                self.target_fps,
                (width, height)
            )

            if not out.isOpened():
                print(f"❌ Error: No se pudo crear el archivo de salida")
                cap.release()
                return False

            # Calcular intervalo de frames para mantener FPS objetivo
            if fps_original > 0:
                frame_interval = fps_original / self.target_fps
            else:
                frame_interval = 1

            frame_counter = 0
            written_frames = 0
            next_frame_to_write = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Escribir frame si corresponde según el intervalo calculado
                if frame_counter >= next_frame_to_write:
                    # Agregar timestamp al frame
                    timestamp_text = f"Frame: {written_frames:04d} | {written_frames/self.target_fps:.2f}s"
                    cv2.putText(
                        frame, timestamp_text, (10, height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                    )

                    out.write(frame)
                    written_frames += 1
                    next_frame_to_write += frame_interval

                frame_counter += 1

                # Mostrar progreso
                if frame_counter % 30 == 0:
                    progress = (frame_counter / total_frames) * 100
                    print(
                        f"📊 Progreso: {progress:.1f}% ({written_frames} frames escritos)")

            cap.release()
            out.release()

            # Verificar el archivo de salida
            if output_path.exists():
                output_size = output_path.stat().st_size / (1024 * 1024)
                duration = written_frames / self.target_fps
                print(
                    f"✅ Video optimizado: {written_frames} frames, {duration:.2f}s, {output_size:.2f}MB")
                return True
            else:
                print(f"❌ Error: No se generó el archivo de salida")
                return False

        except Exception as e:
            print(f"❌ Error optimizando video: {e}")
            return False

    def optimizar_video_ffmpeg(self, input_path: Path, output_path: Path) -> bool:
        """Optimiza un video usando FFmpeg para mejor calidad"""
        try:
            print(f"🔧 Optimizando {input_path.name} con FFmpeg...")

            quality_config = self.quality_settings[self.output_quality]

            # Comando FFmpeg optimizado
            cmd = [
                'ffmpeg', '-y',  # Sobrescribir archivo de salida
                '-i', str(input_path),
                '-c:v', 'libx264',  # Codec de video
                '-preset', 'medium',  # Balance velocidad/calidad
                '-crf', str(quality_config['crf']),  # Calidad constante
                '-r', str(self.target_fps),  # FPS de salida
                '-vsync', '1',  # Sincronización de video
                '-avoid_negative_ts', 'make_zero',  # Evitar timestamps negativos
                '-fflags', '+genpts',  # Generar timestamps
                '-movflags', '+faststart',  # Optimizar para streaming
                '-pix_fmt', 'yuv420p',  # Formato de píxeles compatible
                str(output_path)
            ]

            # Ejecutar FFmpeg
            print(f"🔄 Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                output_size = output_path.stat().st_size / (1024 * 1024)
                print(f"✅ Video optimizado con FFmpeg: {output_size:.2f}MB")
                return True
            else:
                print(f"❌ Error FFmpeg: {result.stderr}")
                return False

        except FileNotFoundError:
            print("⚠️ FFmpeg no encontrado, usando OpenCV...")
            return self.optimizar_video_opencv(input_path, output_path)
        except Exception as e:
            print(f"❌ Error con FFmpeg: {e}")
            return False

    def procesar_directorio(self, input_dir: Path, output_dir: Path, backup: bool = True) -> Dict[str, Any]:
        """Procesa todos los videos en un directorio"""
        print(f"📁 Procesando directorio: {input_dir}")

        if not input_dir.exists():
            return {"error": f"Directorio no existe: {input_dir}"}

        # Crear directorio de salida
        output_dir.mkdir(parents=True, exist_ok=True)

        # Encontrar videos
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        videos = [f for f in input_dir.iterdir()
                  if f.suffix.lower() in video_extensions]

        if not videos:
            return {"error": "No se encontraron videos en el directorio"}

        print(f"📹 Encontrados {len(videos)} videos para procesar")

        resultados = {
            "total_videos": len(videos),
            "procesados": 0,
            "errores": 0,
            "optimizados": 0,
            "sin_cambios": 0,
            "detalles": []
        }

        for video_path in videos:
            print(f"\n🎬 Procesando: {video_path.name}")

            # Analizar video original
            analysis = self.analizar_video(video_path)

            if "error" in analysis:
                print(
                    f"❌ Error analizando {video_path.name}: {analysis['error']}")
                resultados["errores"] += 1
                resultados["detalles"].append({
                    "archivo": video_path.name,
                    "estado": "error",
                    "error": analysis["error"]
                })
                continue

            print(
                f"📊 FPS: {analysis['fps_declarado']} | Duración: {analysis['duración_calculada']}s")

            # Determinar si necesita optimización
            if not analysis["necesita_optimización"]:
                print(f"✅ {video_path.name} ya está optimizado")
                resultados["sin_cambios"] += 1
                resultados["detalles"].append({
                    "archivo": video_path.name,
                    "estado": "sin_cambios",
                    "analisis": analysis
                })
                continue

            # Crear backup si se solicita
            if backup:
                backup_path = video_path.parent / "backup" / video_path.name
                backup_path.parent.mkdir(exist_ok=True)
                if not backup_path.exists():
                    shutil.copy2(video_path, backup_path)
                    print(f"💾 Backup creado: {backup_path}")

            # Optimizar video
            output_path = output_dir / f"optimized_{video_path.name}"

            # Intentar con FFmpeg primero, luego OpenCV
            success = self.optimizar_video_ffmpeg(video_path, output_path)
            if not success:
                success = self.optimizar_video_opencv(video_path, output_path)

            if success:
                # Verificar resultado
                optimized_analysis = self.analizar_video(output_path)
                if "error" not in optimized_analysis:
                    print(f"✅ Optimización exitosa")
                    resultados["optimizados"] += 1
                    resultados["detalles"].append({
                        "archivo": video_path.name,
                        "archivo_optimizado": output_path.name,
                        "estado": "optimizado",
                        "original": analysis,
                        "optimizado": optimized_analysis
                    })
                else:
                    print(f"❌ Error verificando video optimizado")
                    resultados["errores"] += 1
            else:
                resultados["errores"] += 1
                resultados["detalles"].append({
                    "archivo": video_path.name,
                    "estado": "error_optimizacion"
                })

            resultados["procesados"] += 1

        return resultados

    def generar_reporte(self, resultados: Dict[str, Any], output_path: Path):
        """Genera un reporte detallado del procesamiento"""
        reporte = {
            "fecha_procesamiento": datetime.now().isoformat(),
            "configuracion": {
                "fps_objetivo": self.target_fps,
                "calidad": self.output_quality
            },
            "resumen": {
                "total_videos": resultados["total_videos"],
                "procesados": resultados["procesados"],
                "optimizados": resultados["optimizados"],
                "sin_cambios": resultados["sin_cambios"],
                "errores": resultados["errores"]
            },
            "detalles": resultados["detalles"]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)

        print(f"📄 Reporte generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Optimizador de videos de evidencia para corregir problemas de FPS"
    )
    parser.add_argument(
        "input", help="Archivo de video o directorio a procesar")
    parser.add_argument("-o", "--output", help="Directorio de salida")
    parser.add_argument("--fps", type=int, default=15,
                        help="FPS objetivo (default: 15)")
    parser.add_argument("--quality", choices=["alta", "media", "baja"], default="alta",
                        help="Calidad de salida")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Solo analizar, no optimizar")
    parser.add_argument("--no-backup", action="store_true",
                        help="No crear backup de archivos originales")
    parser.add_argument("--report", help="Archivo para guardar reporte JSON")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: {input_path} no existe")
        return 1

    optimizer = VideoOptimizer(
        target_fps=args.fps, output_quality=args.quality)

    if input_path.is_file():
        # Procesar un solo archivo
        print(f"🎬 Analizando archivo: {input_path}")
        analysis = optimizer.analizar_video(input_path)

        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return 1

        # Mostrar análisis
        print(f"\n📊 Análisis de {input_path.name}:")
        print(f"   Resolución: {analysis['resolución']}")
        print(f"   FPS declarado: {analysis['fps_declarado']}")
        print(f"   FPS real estimado: {analysis['fps_real_estimado']}")
        print(f"   Duración: {analysis['duración_calculada']}s")
        print(f"   Tamaño: {analysis['tamaño_mb']}MB")
        print(
            f"   Necesita optimización: {'Sí' if analysis['necesita_optimización'] else 'No'}")

        if analysis.get("problema_detectado"):
            print(f"   ⚠️ Problema: {analysis['problema_detectado']}")

        if not args.analyze_only and analysis["necesita_optimización"]:
            output_path = Path(
                args.output) if args.output else input_path.parent / f"optimized_{input_path.name}"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            success = optimizer.optimizar_video_ffmpeg(input_path, output_path)
            if not success:
                success = optimizer.optimizar_video_opencv(
                    input_path, output_path)

            if success:
                print(f"✅ Video optimizado guardado en: {output_path}")
            else:
                print(f"❌ Error optimizando video")
                return 1

    else:
        # Procesar directorio
        output_dir = Path(
            args.output) if args.output else input_path / "optimized"

        resultados = optimizer.procesar_directorio(
            input_path,
            output_dir,
            backup=not args.no_backup
        )

        if "error" in resultados:
            print(f"❌ Error: {resultados['error']}")
            return 1

        # Mostrar resumen
        print(f"\n📈 Resumen del procesamiento:")
        print(f"   Total de videos: {resultados['total_videos']}")
        print(f"   Procesados: {resultados['procesados']}")
        print(f"   Optimizados: {resultados['optimizados']}")
        print(f"   Sin cambios: {resultados['sin_cambios']}")
        print(f"   Errores: {resultados['errores']}")

        # Generar reporte si se solicita
        if args.report:
            report_path = Path(args.report)
            optimizer.generar_reporte(resultados, report_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
