from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
import os
import sys
import psutil
import csv
import traceback
from datetime import datetime

# --- IMPORTURI DIN PROIECT ---
from raport_generation import ReportBuilder

# 2. Importăm funcția SINCRONĂ din folderul nlp_processing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'nlp_processing'))
from category_extractor_sincron import classify_on_demand

app = Flask(__name__)
CORS(app)

# --- CONFIGURARE FIȘIERE ---
FILE_ASINCRON = "data/baza_date_final_nlp.json"  # Use final NLP output with topics, sentiments, entities
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
    
    try:
        # Extrage datele din request
        req_data = request.json
        start_str = req_data.get('start_date')
        end_str = req_data.get('end_date')
        # STEP 1: Clasificare
        if classify_on_demand is None:
            print("❌ [ERROR] Funcția classify_on_demand nu este disponibilă!")
            return jsonify({"error": "Funcția classify_on_demand nu a putut fi importată. Verifică nlp_processing/category_extractor_sincron.py."}), 500
        print("🔍 [DEBUG 1] Apelez classify_on_demand...")
        result_data = classify_on_demand(start_str, end_str)
        # Verificăm ce am primit (FOARTE IMPORTANT)
        print(f"📦 [DEBUG 2] Tip date primite: {type(result_data)}")
        if isinstance(result_data, dict):
            print(f"🔑 [DEBUG 2] Chei primite: {list(result_data.keys())}")
        else:
            print(f"❌ [DEBUG 2] ATENȚIE: result_data NU este dicționar! Este: {result_data}")

        if "error" in result_data: 
            print(f"⚠️ [DEBUG 3] Primit eroare din classifier: {result_data['error']}")
            return jsonify(result_data), 400

        count = result_data.get('count', 0)
        print(f"📊 [DEBUG 3] Count articole: {count}")

        if count == 0:
            print("Empty result, returning early.")
            cpu_usage = proc.cpu_percent(interval=None)
            log_metrics("Sincron (V1)", time.time() - start_time, cpu_usage)
            return jsonify({"status": "empty", "report": "Nu au fost găsite articole."})

        # STEP 2: Scriere fișier temp
        # Verificăm dacă cheia 'articles' există înainte să o accesăm
        if 'articles' not in result_data:
            raise KeyError("Cheia 'articles' lipsește din result_data! Verifică category_extractor_sincron.py")

        print(f"💾 [DEBUG 4] Scriu în fișier temporar: {FILE_TEMP_SINCRON}")

        # Write as a flat list for compatibility with new pipeline
        with open(FILE_TEMP_SINCRON, "w", encoding="utf-8") as f:
            json.dump(result_data['articles'], f, ensure_ascii=False)
        print("✅ [DEBUG 4] Scriere reușită.")

        # STEP 3: Report Engine
        print("⚙️ [DEBUG 5] Inițializez ReportEngine...")
        s_date = datetime.strptime(start_str, "%Y-%m-%d")
        e_date = datetime.strptime(end_str, "%Y-%m-%d")
        
        print(f"📂 [DEBUG 6] Încarc date în Engine din: {FILE_TEMP_SINCRON}")
        engine = (ReportBuilder()
            .set_date_range(s_date, e_date)
            .load_from_file(FILE_TEMP_SINCRON)
            .build())
        
        # Verificăm dacă engine-ul a încărcat ceva
        print(f"📈 [DEBUG 7] Stats Engine după încărcare: {engine.stats}")

        print("📝 [DEBUG 8] Generez Markdown...")
        markdown_report = engine.generate_curated_markdown() 
        print("✅ [DEBUG 9] Markdown generat.")
        
        duration = time.time() - start_time
        
        # 2. READ CPU
        cpu_usage = proc.cpu_percent(interval=None)
        print(f"⏱️ [V1] Gata în {duration:.2f}s | CPU: {cpu_usage}%")

        log_metrics("Sincron (V1)", duration, cpu_usage)

        return jsonify({
            "status": "success", "report": markdown_report, 
            "processing_time": duration, "articles_count": count, "type": "sincron"
        })
        log_metrics("Sincron (V1)", duration, cpu_usage)

        return jsonify({
            "status": "success", "report": markdown_report, 
            "processing_time": duration, "articles_count": count, "type": "sincron"
        })

    except Exception as e:
        print("\n❌ ❌ ❌ EROARE CRITICĂ ÎN ENDPOINT ❌ ❌ ❌")
        print(f"Mesaj eroare: {str(e)}")
        print("Traceback complet (Aici vezi linia exactă):")
        traceback.print_exc() # Asta îți arată exact linia cu problema
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
        print(f"s_date: {s_date}, e_date: {e_date}")
        
        if not os.path.exists(FILE_ASINCRON):
            return jsonify({"error": "Lipsă fișier procesat"}), 500
        
        engine = (ReportBuilder()
            .set_date_range(s_date, e_date)
            .load_from_file(FILE_ASINCRON)
            .build())
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