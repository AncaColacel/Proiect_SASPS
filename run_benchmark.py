import requests
import time

API_URL = "http://127.0.0.1:5000"
# Pune o perioadă unde știi că ai date (ex: 2025-10-01 -> 2025-10-05)
PAYLOAD = {"start_date": "2025-10-01", "end_date": "2025-10-05"} 

def run_test(mode, endpoint, iterations=5):
    print(f"\n🔥 Testare Modul {mode} ({iterations} iteratii)...")
    for i in range(iterations):
        print(f"   Iterația {i+1}...")
        try:
            requests.post(f"{API_URL}{endpoint}", json=PAYLOAD)
        except Exception as e:
            print(f"Eroare: {e}")
        
        # Pauză mică să lăsăm CPU să respire între teste (pt realism)
        time.sleep(1)

if __name__ == "__main__":
    # 1. Testăm Varianta Lentă (V1) - Facem 3-5 cereri că durează mult
    run_test("Sincron", "/api/v1/sincron", iterations=3)
    
    # 2. Testăm Varianta Rapidă (V2) - Facem 10 cereri că e rapid
    run_test("Asincron", "/api/v2/asincron", iterations=10)
    
    print("\n✅ Benchmark complet! Datele sunt în metrics_log.csv")