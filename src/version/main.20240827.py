import psutil
import platform
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from datetime import datetime
#IMPORTAMOS LIBRERIAS.

app = FastAPI()
uname = platform.uname()
svmem = psutil.virtual_memory()

media = 'df -BG | grep 2351bf86'
backup = 'df -BG | grep d3682f49'

def get_cpu_temperature():
    cpu_temperature = psutil.sensors_temperatures().get('cpu_thermal', [])
    if cpu_temperature:
        return cpu_temperature[0].current
    else:
        return None
        

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
            "temperature": round(get_cpu_temperature(),1)
           }

