# 🧩 Proiect SASPS — Stiluri Arhitecturale și Șabloane de Proiectare Software  

## 📰 Sistem de Agregare și Analiză a Știrilor Românești  
**Arhitectură bazată pe design patterns**

---

### 👥 Componența echipei
- **COLĂCEL Anca-Maria** — SSA1-A  
- **ZECHERU Andreea-Corina** — EGOV2  
- **FUIOREA Florina-Daniela** — EGOV2  
- **TOEA Valentin Daniel** — EGOV2

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

### 🤝 Împărțire taskuri
1.	Colectează articolele din sursele selectate - **Zecheru Andreea-Corina** 
2.	Procesează textele (normalizare, curățare) - **Zecheru Andreea-Corina + Toea Valentin Daniel**
3.	Extrage entități, cuvinte-cheie și subiecte principale - **Fuiorea Florina-Daniela + Toea Valentin Daniel**
4.	Analizează tonul și sentimentele articolelor - **Fuiorea Florina-Daniela**
5.	Generează rapoarte în format Markdown - **Colăcel Anca-Maria**
6.	Testare și validare rapoarte finale - **Colăcel Anca-Maria**
7.	Implementare variantă cu design patterns - **Zecheru + Fuiorea + Colăcel + Toea**
8.	Realizare comparații + articol final - **Zecheru + Fuiorea + Colăcel + Toea**

---

## 📌 Sprint-uri și versiuni

| **Sprint** | **Obiectiv principal** | **Ce se face** | **Rezultat** |
|-----------|-------------------------|-----------------|---------------|
| **Sprint 1** | Documentație proiect | - Întocmire documentație<br>- Configurare repo pentru proiect | Mediu de lucru propice pentru începerea proiectului |
| **Sprint 2** | Implementare variantă simplă | - Pipeline fără design patterns<br>- Salvare JSON + normalizare text + extragere topicuri și entități | Fișiere în format JSON cu informații despre știrile colectate |
| **Sprint 3** | Implementare variantă finală, fără design patterns | - Adăugare surse noi de știri<br>- Analiză pe ton și sentiment<br>- Generare rapoarte finale<br>- Testare sistem | Rapoarte finale în format Markdown despre principalele știri apărute într-o anumită perioadă |
| **Sprint 4** | Implementare cu design patterns + comparații | - Refactorizare pipeline folosind Strategy, Factory, Builder, Chain of Responsibility, Template Method<br>- Comparații între variante | Varianta finală cu design patterns și rapoarte comparative |

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

