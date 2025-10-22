# 🧩 Proiect SASPS — Stiluri Arhitecturale și Șabloane de Proiectare Software  

## 📰 Sistem de Agregare și Analiză a Știrilor Românești  
**Arhitectură bazată pe design patterns**

---

### 👥 Componența echipei
- **COLĂCEL Anca-Maria** — SSA1-A  
- **ZECHERU Andreea-Corina** — EGOV2  
- **FUIOREA Florina-Daniela** — EGOV2  

---

### 🧠 Descrierea proiectului
Proiectul constă în dezvoltarea unei aplicații pentru **agregarea și analiza știrilor din presa românească** (ex: *Mediafax, Digi24, Libertatea*).  

Sistemul permite utilizatorului să introducă o perioadă de timp, iar aplicația:  
1. Colectează articolele din sursele selectate  
2. Procesează textele (normalizare, curățare)  
3. Extrage entități, cuvinte-cheie și subiecte principale  
4. Analizează tonul și sentimentele articolelor  
5. Generează rapoarte în format Markdown, care oferă o privire de ansamblu asupra:  
   - principalelor știri din perioada respectivă  
   - entităților menționate frecvent  
   - subiectelor dominante  
   - linkurilor și metadatelor asociate fiecărei știri  

Toate informațiile procesate vor fi salvate într-un format **JSON**, urmând ca ulterior să fie folosite pentru **generarea rapoartelor Markdown**.

---

### 🏗️ Design patterns utilizate

Ne propunem să aplicăm următoarele șabloane de proiectare:

- **Strategy Pattern** – pentru extractorii HTML  
- **Chain of Responsibility** – pentru pipeline-ul de procesare  
- **Factory Pattern** – pentru crearea dinamică a extractorilor pe baza URL-ului  
- **Builder Pattern** – pentru construirea pipeline-ului complex din surse, pași și output-uri  
- **Template Method Pattern** – pentru orchestrarea fluxului de execuție  

---

### 🧰 Tehnologii propuse

Implementarea va fi realizată în **Python**, folosind următoarele librării și tehnologii:  

- **BeautifulSoup** sau **Newspaper3k** — pentru parsarea și extragerea conținutului articolelor  
- **spaCy** (sau alt NER dedicat) — pentru recunoașterea entităților numite (persoane, organizații, locații etc.)  
- **BERT** — pentru analiza sentimentelor din text  
- **KeyBERT**, **YAKE** sau **Gensim** — pentru extragerea automată a cuvintelor-cheie și a topicurilor principale  
- **JSON** — pentru stocarea datelor procesate  
- **Markdown** — pentru generarea rapoartelor lizibile, cu sinteza principalelor știri, entități, subiecte și linkuri către surse  

---

### 📊 Etapa finală: Analiza comparativă

Proiectul se va încheia cu o **analiză comparativă**, sub forma unui articol tehnic, care va evidenția:  
- diferențele între implementarea fără design patterns și cea cu design patterns  
- analiza unor metrici de performanță, claritate și scalabilitate  

Printre metricele analizați se pot regăsi:  
- Timpul de execuție  
- Complexitatea codului  
- Ușurința extinderii sistemului  
- Nivelul de reutilizare a componentelor  

