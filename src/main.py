import psutil
import platform
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import List
import re
import os

#IMPORTAMOS LIBRERIAS.

app = FastAPI()
uname = platform.uname()
svmem = psutil.virtual_memory()

media = 'df -BG | grep 2351bf86 || echo "null: 0 0 0 0% null"'
backup = 'df -BG | grep d3682f49 || echo "null: 0 0 0 0% null"'

def get_cpu_temperature():
    cpu_temperature = psutil.sensors_temperatures().get('cpu_thermal', [])
    if cpu_temperature:
        return cpu_temperature[0].current
    else:
        return None
        
# Ruta al directorio donde están los archivos
DIRECTORY_PATH = "/mnt/d3682f49/dump"

# Expresión regular para capturar la fecha en formato "vzdump-qemu-200-YYYY-MM-DD_hh_mm_ss.zst"

def get_latest_date_from_files(directory: str, pattern: str) -> str:
    files = os.listdir(directory)
    date_pattern = re.compile(pattern)
        
    # Inicializar variables para almacenar la fecha y el archivo más reciente
    latest_date = None
    latest_file = None    
    
    # Filtrar los archivos que coincidan con el patrón
    for file in files:
        match = date_pattern.search(file)
        if match:
            date_str = match.group(1)  # Extraer solo la parte de la fecha "YYYY_MM_DD"
            try:
                # Convertir la fecha al formato datetime
                date = datetime.strptime(date_str, "%Y_%m_%d")
                # Comparar la fecha actual con la más reciente encontrada
                if latest_date is None or date > latest_date:
                   latest_date = date
                   latest_file = file
            except ValueError:
                continue  # Ignorar archivos con fechas inválidas
    
    if not latest_date:
        raise ValueError("No se encontraron archivos válidos con el formato requerido.")
    
    # Obtener el tamaño del archivo más reciente
    file_path = os.path.join(directory, latest_file)
    file_size = os.path.getsize(file_path)
    
    # Devolver la fecha en formato string
    return latest_date.strftime("%Y-%m-%d"), file_size


@app.get("/v1")
def read_root():
    print("Inicio fastapi")
    
    try:
        result_media = subprocess.run(media, shell=True, check=True, capture_output=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing media command: {e}")
        raise HTTPException(status_code=500, detail="Error executing media command")

    
    try:
        result_backup = subprocess.run(backup, shell=True, check=True, capture_output=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing backup command: {e}")
        raise HTTPException(status_code=500, detail="Error executing backup command")
        

    pattern_ha = re.compile(r'vzdump-qemu-200-(\d{4}_\d{2}_\d{2})-\d{2}_\d{2}_\d{2}\.vma\.zst$')    
    latest_date_ha, file_size_ha = get_latest_date_from_files(DIRECTORY_PATH, pattern_ha )            
    
    pattern_ub = re.compile(r'vzdump-qemu-2000-(\d{4}_\d{2}_\d{2})-\d{2}_\d{2}_\d{2}\.vma\.zst$')    
    latest_date_ub, file_size_ub = get_latest_date_from_files(DIRECTORY_PATH, pattern_ub )            

    logging.info(datetime.now())     
    
    return {"System": uname.system,
            "Release": uname.release,
            "Version": uname.version,
            "Machine": uname.machine,
            "Physical_cores": psutil.cpu_count(logical=False),
            "Total_cores": psutil.cpu_count(logical=True),
            "Total_CPU_Usage": psutil.cpu_percent(),
            "Total_memory": round(svmem.total / ( 1024 * 1024)),
            "Available_memory": round(svmem.available / ( 1024 * 1024)),
            "Used_memory": round(svmem.used / ( 1024 * 1024)),
            "Percentage_memory": svmem.percent,
            "media_total": result_media.stdout.split()[1][:-1],
            "media_used": result_media.stdout.split()[2][:-1],
            "media_available": result_media.stdout.split()[3][:-1],
            "media_use": result_media.stdout.split()[4][:-1],             
            "backup_total": result_backup.stdout.split()[1][:-1],
            "backup_used": result_backup.stdout.split()[2][:-1],
            "backup_available": result_backup.stdout.split()[3][:-1],
            "backup_use": result_backup.stdout.split()[4][:-1],
            "temperature": round(get_cpu_temperature(),1),
            "latest_date_ha": latest_date_ha,
            "file_size_ha": round ( file_size_ha / 1024/ 1024 / 1024 ,1),
            "latest_date_ub": latest_date_ub,
            "file_size_ub": round ( file_size_ub / 1024/ 1024 / 1024 ,1)
           }

