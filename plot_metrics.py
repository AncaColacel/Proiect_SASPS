import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurare vizuală
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

def generate_plots():
    try:
        df = pd.read_csv("metrics_log.csv")
    except:
        print("Nu găsesc metrics_log.csv! Rulează benchmark-ul întâi.")
        return

    # Dacă fișierul e gol sau are puține date, ieșim
    if len(df) < 2:
        print("Prea puține date pentru grafice.")
        return

    # 1. GRAFIC: TIMP DE RĂSPUNS (Bar Chart)
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="Mode", y="Latency_Sec", data=df, palette=["#e74c3c", "#2ecc71"], errorbar=None)
    
    # Adăugăm valorile pe bare
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2fs', padding=3, fontsize=12, fontweight='bold')
        
    plt.title("Comparație Latență: Sincron vs Asincron", fontsize=16, pad=20)
    plt.ylabel("Secunde (mai puțin e mai bine)")
    plt.xlabel("")
    plt.savefig("grafice/grafic_latenta.png", dpi=300, bbox_inches='tight')
    print("✅ Generat: grafic_latenta.png")

    # 2. GRAFIC: MEMORIE RAM (Line Chart sau Bar)
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Mode", y="Memory_MB", data=df, palette=["#e74c3c", "#2ecc71"], errorbar=None)
    plt.title("Consum Mediu de Memorie RAM", fontsize=16, pad=20)
    plt.ylabel("Memorie (MB)")
    plt.xlabel("")
    plt.savefig("grafice/grafic_memorie.png", dpi=300, bbox_inches='tight')
    print("✅ Generat: grafic_memorie.png")
    
    # 3. GRAFIC: CPU (Box Plot - arată efortul)
    plt.figure(figsize=(8, 6))
    sns.boxplot(x="Mode", y="CPU_Percent", data=df, palette=["#e74c3c", "#2ecc71"])
    plt.title("Încărcarea Procesorului (CPU Load)", fontsize=16)
    plt.ylabel("Utilizare CPU (%)")
    plt.savefig("grafice/grafic_cpu.png", dpi=300, bbox_inches='tight')
    print("✅ Generat: grafic_cpu.png")

if __name__ == "__main__":
    generate_plots()