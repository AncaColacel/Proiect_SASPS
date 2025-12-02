import json
from datetime import datetime
from collections import Counter
import difflib
import os

# --- CONFIGURARE ---
INPUT_FILE = "jsons/final/BAZA_DATE.json"
TOP_STORIES_PER_CATEGORY = 5 

class Topic:
    def __init__(self, main_article):
        self.title = main_article.get("title")
        self.articles = [main_article]
        self.sources = {self._get_source_name(main_article)}
        self.entities = self._extract_entities(main_article)
        self.score = 0

    def _get_source_name(self, article):
        url = article.get("url", "")
        if "hotnews" in url: return "HotNews"
        if "digi24" in url: return "Digi24"
        if "mediafax" in url: return "Mediafax"
        if "a1.ro" in url: return "Antena1"
        return "Alte Surse"

    def _extract_entities(self, article):
        ents = article.get("entities", {})
        all_e = []
        if isinstance(ents, dict):
            for k in ["PER", "PERSON", "ORG", "GPE", "LOC"]:
                all_e.extend(ents.get(k, []))
        return set(all_e)

    def add_article(self, article):
        self.articles.append(article)
        self.sources.add(self._get_source_name(article))
        self.entities.update(self._extract_entities(article))
        if len(article.get("title", "")) > len(self.title):
            self.title = article.get("title")

    def calculate_importance(self):
        # Formula de scor
        score_volume = len(self.articles) * 10
        score_diversity = len(self.sources) * 30
        score_info = len(self.entities) * 1
        self.score = score_volume + score_diversity + score_info

class ReportEngine:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.topics_by_category = {} 
        self.stats = {"total": 0}

    def load_data(self, source_input):
        raw_list = []
        
        # 1. Încărcare din Fișier (V2) sau Memorie (V1)
        if isinstance(source_input, str):
            print(f"📖 Citire din fișier: {source_input}")
            try:
                with open(source_input, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict): 
                        raw_list = data.get("articles", [])
                    else:
                        for src in data: raw_list.extend(src.get("articles", []))
            except: return
        elif isinstance(source_input, list):
            raw_list = source_input

        # 2. Procesare
        print("Clustering topics...")
        seen_urls = set()
        
        # Mapare rapidă pentru V2 (Clustering pre-calculat)
        cluster_map = {} 

        for art in raw_list:
            if art.get('url') in seen_urls: continue
            
            try:
                d_str = art.get("date", "").split("T")[0]
                d = datetime.strptime(d_str, "%Y-%m-%d")
                if not (self.start_date <= d <= self.end_date): continue
            except: continue

            seen_urls.add(art.get('url'))
            
            # Categorie
            cat = art.get("auto_category") or art.get("category") or "DIVERSE"
            if cat not in self.topics_by_category:
                self.topics_by_category[cat] = []

            # --- LOGICA HIBRIDĂ ---
            
            # CAZ A: Avem Cluster ID (V2 - Asincron)
            if "cluster_id" in art:
                cid = art["cluster_id"]
                if cid == -1: continue # Ignorăm zgomotul

                if cid in cluster_map:
                    cluster_map[cid].add_article(art)
                else:
                    new_topic = Topic(art)
                    cluster_map[cid] = new_topic
                    self.topics_by_category[cat].append(new_topic)
            
            # CAZ B: Nu avem ID (V1 - Sincron) - Facem difflib
            else:
                found_topic = False
                for topic in self.topics_by_category[cat]:
                    # Comparație lentă de text
                    sim = difflib.SequenceMatcher(None, topic.title, art.get("title")).ratio()
                    if sim > 0.60:
                        topic.add_article(art)
                        found_topic = True
                        break
                
                if not found_topic:
                    self.topics_by_category[cat].append(Topic(art))

        self.stats['total'] = len(seen_urls)

    def generate_curated_markdown(self):
            lines = []
            
            # --- HEADER ---
            lines.append(f"# 📰 Raport de Sinteză Media")
            
            # Dacă nu sunt date, afișăm doar mesajul de eroare
            if self.stats['total'] == 0:
                return "### ⚠️ Nu au fost găsite știri în această perioadă."

            priority_cats = ["POLITIC", "ECONOMIC", "EXTERNE", "JUSTIȚIE", "SOCIAL", "SPORT", "IT"]
            sorted_keys = sorted(self.topics_by_category.keys(), 
                                key=lambda k: next((i for i, p in enumerate(priority_cats) if p in k.upper()), 99))

            for cat in sorted_keys:
                topics = self.topics_by_category[cat]
                if not topics: continue

                # Calculăm scoruri
                for t in topics: t.calculate_importance()
                topics.sort(key=lambda t: t.score, reverse=True)
                
                top_topics = topics[:TOP_STORIES_PER_CATEGORY]
                
                if top_topics[0].score < 10: continue 

                # --- CONȚINUTUL EFECTIV ---
                
                # Titlul Categoriei (cu spațiu înainte)
                lines.append(f"## {cat}")
                lines.append("") 
                
                for idx, topic in enumerate(top_topics, 1):
                    # Sentiment
                    sents = [a.get("sentiment", {}).get("label", "neutral") for a in topic.articles]
                    main_sent = Counter(sents).most_common(1)[0][0]
                    
                    emoji = "⚪"
                    sent_text = "Neutru"
                    if main_sent == "negative": 
                        emoji = "🔴"
                        sent_text = "Negativ / Critic"
                    if main_sent == "positive": 
                        emoji = "🟢"
                        sent_text = "Pozitiv"

                    # 1. Titlu
                    lines.append(f"### {idx}. {topic.title}")
                    
                    # 2. Impact
                    surse_count = len(topic.sources)
                    text_surse = "sursă" if surse_count == 1 else "surse"
                    lines.append(f"- **Impact:** {surse_count} {text_surse}")
                    
                    # 3. Sentiment
                    lines.append(f"- **Sentiment:** {emoji} {sent_text}")
                    
                    # 4. Mențiuni
                    if topic.entities:
                        top_ents = [e[0] for e in Counter(list(topic.entities)).most_common(4)]
                        lines.append(f"- **Mențiuni cheie:** {', '.join(top_ents)}")

                    # 5. Link-uri
                    links = []
                    seen_src = set()
                    for a in topic.articles:
                        src = topic._get_source_name(a)
                        if src not in seen_src:
                            links.append(f"[🔗 **{src}**]({a.get('url')})")
                            seen_src.add(src)
                    
                    lines.append(f"- **Citește pe:** {', '.join(links)}")
                    lines.append("") 

                lines.append("---\n")

            return "\n".join(lines)

    def save(self, filename):
        content = self.generate_curated_markdown()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Raport salvat: {os.path.abspath(filename)}")

if __name__ == "__main__":
    # Test local
    s = datetime(2025, 10, 1)
    e = datetime(2025, 10, 6)
    start_str = s.strftime("%Y-%m-%d")
    end_str = e.strftime("%Y-%m-%d")
    dynamic_filename = f"Raport_Sinteza_{start_str}_{end_str}.md"
    
    engine = ReportEngine(s, e)
    engine.load_data(INPUT_FILE)
    engine.save(dynamic_filename)