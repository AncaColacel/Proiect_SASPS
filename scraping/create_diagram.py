from graphviz import Digraph

def create_simple_diagram():
    # Configurare vizuală curată
    dot = Digraph(comment='Arhitectura High-Level', format='png')
    dot.attr(rankdir='TB') # De sus în jos
    dot.attr('node', shape='rect', style='rounded,filled', fontname='Arial', fontsize='12', height='0.6')
    
    # --- ACTORII PRINCIPALI ---
    dot.node('User', 'Utilizator', shape='circle', fillcolor='#E3F2FD', width='1.2')
    dot.node('App', 'Aplicație Web\n(Frontend + Server)', fillcolor='#BBDEFB')

    # --- RAMURA 1: SINCRON (Monolit) ---
    # Reprezentăm procesarea grea care blochează
    dot.node('Process', 'Procesare Clasificare & Clusterizare în Timp Real\n', fillcolor='#FFCDD2', color='#C62828')

    # --- RAMURA 2: ASINCRON (Optimizat) ---
    # Reprezentăm stocarea inteligentă și worker-ul din spate
    dot.node('DB', 'Date Gata Procesate\n(Bază de Date)', shape='cylinder', fillcolor='#DCEDC8', color='#2E7D32')
    dot.node('Worker', 'Procesare în Background\n(Scraping + NLP analysis)', shape='hexagon', fillcolor='#FFF9C4', style='dashed,filled')

    # --- CONEXIUNI (FLUXUL) ---

    # 1. Interacțiunea de bază
    dot.edge('User', 'App', label=' Cere Raport')

    # 2. Fluxul ROȘU (Lent)
    dot.edge('App', 'Process', label=' 1. Mod Sincron', color='red', penwidth='2.0')
    dot.edge('Process', 'App', label=' Așteptare (Lent)', color='red', style='dashed')

    # 3. Fluxul VERDE (Rapid)
    dot.edge('App', 'DB', label=' 2. Mod Asincron', color='darkgreen', penwidth='2.0')
    dot.edge('DB', 'App', label=' Răspuns Instant', color='darkgreen', style='dashed')

    # 4. Fluxul din Umbră (Pregătirea datelor)
    dot.edge('Worker', 'DB', label=' Salvează Datele', color='gray', style='dotted')

    # Randare
    file_path = dot.render('diagrama_arhitectura_simpla', view=True)
    print(f"Diagrama simplificată salvată: {file_path}")

if __name__ == '__main__':
    create_simple_diagram()