from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
import os
import sys
import psutil
import csv
from datetime import datetime

# --- IMPORTURI DIN PROIECT ---
from raport_generation import ReportEngine

# 2. Importăm funcția SINCRONĂ din folderul nlp_processing
sys.path.append(os.path.join(os.path.dirname(__file__), 'nlp_processing'))
try:
    from nlp_processing.category_extractor_sincron import classify_on_demand 
except ImportError:
    print("⚠️ Nu am găsit 'category_extractor_sincron.py' în folderul nlp_processing.")

app = Flask(__name__)
CORS(app)

# --- CONFIGURARE FIȘIERE ---
FILE_ASINCRON = "jsons/final/BAZA_DATE_FINALA.json" 
FILE_TEMP_SINCRON = "temp_sincron_result.json"
METRICS_FILE = "metrics_log.csv"

# --- INITIALIZARE MONITORIZARE ---
if not os.path.exists(METRICS_FILE):
    with open(METRICS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        # Header simplificat (Fără Disk_Read_MB)
        writer.writerow(["Timestamp", "Mode", "Latency_Sec", "CPU_Percent", "Memory_MB"])

proc = psutil.Process(os.getpid())

def log_metrics(mode, duration, cpu_val):
    """ Măsoară doar CPU, RAM și Timp """
    try:
        # 1. Memorie (RSS)
        mem_mb = proc.memory_info().rss / 1024 / 1024

        # 2. Scriere în CSV
        with open(METRICS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            ts = datetime.now().strftime("%H:%M:%S")
            # Scriem doar datele relevante
            writer.writerow([ts, mode, round(duration, 4), round(cpu_val, 2), round(mem_mb, 1)])
            
    except Exception as e:
        print(f"Eroare logare metrics: {e}")

# --- ENDPOINTS ---

@app.route('/api/v1/sincron', methods=['POST'])
def endpoint_sincron():
    # 1. RESET CPU
    proc.cpu_percent(interval=None)
    start_time = time.time()
    
    req_data = request.json
    start_str = req_data.get('start_date')
    end_str = req_data.get('end_date')
    print(f"🐌 [V1] Cerere Sincronă: {start_str} -> {end_str}")

    try:
        result_data = classify_on_demand(start_str, end_str)
        
        if "error" in result_data: return jsonify(result_data), 400
        
        count = result_data.get('count', 0)
        if count == 0:
            cpu_usage = proc.cpu_percent(interval=None)
            log_metrics("Sincron (V1)", time.time() - start_time, cpu_usage)
            return jsonify({"status": "empty", "report": "Nu au fost găsite articole."})

        temp_structure = {"source": "Sincron", "articles": result_data['articles']}
        with open(FILE_TEMP_SINCRON, "w", encoding="utf-8") as f:
            json.dump(temp_structure, f, ensure_ascii=False)

        s_date = datetime.strptime(start_str, "%Y-%m-%d")
        e_date = datetime.strptime(end_str, "%Y-%m-%d")
        engine = ReportEngine(s_date, e_date)
        engine.load_data(FILE_TEMP_SINCRON)
        markdown_report = engine.generate_curated_markdown() 
        
        duration = time.time() - start_time
        
        # 2. READ CPU
        cpu_usage = proc.cpu_percent(interval=None)
        print(f"⏱️ [V1] Gata în {duration:.2f}s | CPU: {cpu_usage}%")

        log_metrics("Sincron (V1)", duration, cpu_usage)

        return jsonify({
            "status": "success", "report": markdown_report, 
            "processing_time": duration, "articles_count": count, "type": "sincron"
        })

    except Exception as e:
        print(f"Eroare V1: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v2/asincron', methods=['POST'])
def endpoint_asincron():
    # 1. RESET CPU
    proc.cpu_percent(interval=None)
    start_time = time.time()
    
    req_data = request.json
    start_str = req_data.get('start_date')
    end_str = req_data.get('end_date')
    print(f"🚀 [V2] Cerere Asincronă: {start_str} -> {end_str}")

    try:
        s_date = datetime.strptime(start_str, "%Y-%m-%d")
        e_date = datetime.strptime(end_str, "%Y-%m-%d")
        engine = ReportEngine(s_date, e_date)
        
        if not os.path.exists(FILE_ASINCRON):
            return jsonify({"error": "Lipsă fișier procesat"}), 500
            
        engine.load_data(FILE_ASINCRON)
        markdown_report = engine.generate_curated_markdown()

        duration = time.time() - start_time
        processed_count = engine.stats.get('total', 0)
        
        # 2. READ CPU
        cpu_usage = proc.cpu_percent(interval=None)
        print(f"⚡ [V2] Gata în {duration:.2f}s | CPU: {cpu_usage}%")

        log_metrics("Asincron (V2)", duration, cpu_usage)

        return jsonify({
            "status": "success", "report": markdown_report, 
            "processing_time": duration, "articles_count": processed_count, "type": "asincron"
        })

    except Exception as e:
        print(f"Eroare V2: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Inițializare CPU Gauge (primul apel returnează 0, dar "armează" contorul)
    psutil.cpu_percent(interval=None) 
    print("🌍 Server pornit pe http://localhost:5000. Monitorizare activă.")
    app.run(port=5000, debug=True)