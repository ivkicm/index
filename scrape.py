import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import pytz
import re

def get_relative_time_string(dt):
    """Berechnet die vergangene Zeit seit Veröffentlichung."""
    try:
        tz = pytz.timezone('Europe/Zagreb')
        now = datetime.now(tz)
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 0: return "GERADE EBEN" # Falls Uhrzeit in der Zukunft liegt (Server-Sync)
        if seconds < 3600: # Weniger als 1 Stunde
            mins = int(seconds / 60)
            return f"VOR {max(1, mins)} MINUTEN"
        elif seconds < 86400: # Weniger als 24 Stunden
            hours = int(seconds / 3600)
            return f"VOR {hours} {'STUNDE' if hours == 1 else 'STUNDEN'}"
        else:
            return dt.strftime("%d.%m. %H:%M")
    except:
        return "AKTUELL"

def get_article_time(url, headers):
    """Versucht die Zeit aus dem Artikel zu lesen. Wenn es fehlschlägt, gibt es None zurück."""
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Suche nach ISO Zeitstempel in Meta-Tags
        meta_time = soup.find("meta", property="article:published_time")
        if meta_time and meta_time.get("content"):
            iso_date = meta_time.get("content")
            # Robustes Parsing
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.astimezone(pytz.timezone('Europe/Zagreb'))
    except:
        pass
    return None

def get_news():
    base_url = "https://www.index.hr"
    url = "https://www.index.hr/sport"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    news_data = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Wir suchen alle Artikelboxen
        articles = soup.select('.first-news-holder, .grid-item')
        print(f"Gefundene Artikel: {len(articles)}")

        for art in articles[:10]: # Top 10 prüfen
            try:
                title_el = art.select_one('.title')
                link_el = art.select_one('a')
                img_el = art.select_one('img')
                
                if title_el and link_el:
                    title = title_el.get_text(strip=True)
                    link = link_el['href']
                    if not link.startswith('http'): link = base_url + link
                    
                    # Bild finden (entweder src oder data-src)
                    img = ""
                    if img_el:
                        img = img_el.get('src') or img_el.get('data-src') or ""
                    
                    # Deep-Scraping Versuch für die Zeit
                    dt_obj = get_article_time(link, headers)
                    
                    # Zeit-String erstellen
                    if dt_obj:
                        rel_time = get_relative_time_string(dt_obj)
                        sort_val = dt_obj
                    else:
                        rel_time = "AKTUELL"
                        sort_val = datetime.now(pytz.timezone('Europe/Zagreb'))

                    news_data.append({
                        'title': title,
                        'image': img,
                        'time_obj': sort_val,
                        'rel_time': rel_time
                    })
            except Exception as e:
                print(f"Fehler bei Artikel-Extraktion: {e}")
                continue

        # Sortierung nach Zeit (nur wenn Zeit-Objekte da sind)
        news_data.sort(key=lambda x: x['time_obj'], reverse=True)
        return news_data
    except Exception as e:
        print(f"Haupt-Scraping Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz).strftime("%H:%M")
    
    # FALLBACK: Falls news leer ist, erstelle eine Info-Slide
    if not news:
        news = [{'title': 'Nachrichten werden aktualisiert...', 'image': '', 'rel_time': 'SYSTEM', 'time_obj': datetime.now()}]

    slides_html = ""
    for i, item in enumerate(news):
        active_class = "active" if i == 0 else ""
        img_url = item['image']
        
        # Bild-URL für Index.hr optimieren (Fallback zu Platzhalter falls leer)
        if img_url:
            if 'index.hr' in img_url and '?' in img_url:
                img_url = img_url.split('?')[0] + "?width=1200&height=630&mode=crop"
        else:
            img_url = "https://placehold.co/1200x630/000000/FFFFFF?text=INDEX+SPORT"

        slides_html += f"""
        <div class="slide {active_class}">
            <div class="image-container">
                <img src="{img_url}" alt="News Image">
                <div class="img-overlay"></div>
            </div>
            <div class="content-box">
                <div class="meta-line">
                    <span class="source">INDEX SPORT</span>
                    <span class="pub-time">{item['rel_time']}</span>
                </div>
                <div class="title">{item['title']}</div>
            </div>
        </div>
        """

    html_content = f"""
<!DOCTYPE html>
<html lang="hr">
<head>
    <meta charset="UTF-8">
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index Sport Radar XXL</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@800;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; background-color: black; color: white; font-family: 'Inter', sans-serif; overflow: hidden; }}
        .header-info {{ position: fixed; top: 15px; right: 20px; z-index: 100; background: rgba(0, 180, 216, 0.9); padding: 5px 15px; border-radius: 8px; font-family: 'JetBrains Mono'; font-size: 1.2rem; font-weight: 800; }}
        .slide {{ position: absolute; width: 100%; height: 100%; display: none; flex-direction: column; }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}
        .image-container {{ width: 100%; height: 55vh; position: relative; overflow: hidden; background: #111; }}
        .image-container img {{ width: 100%; height: 100%; object-fit: cover; border-bottom: 6px solid #00b4d8; }}
        .img-overlay {{ position: absolute; bottom: 0; left: 0; width: 100%; height: 25%; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); }}
        .content-box {{ flex: 1; padding: 30px 60px; background: #000; display: flex; flex-direction: column; justify-content: flex-start; padding-top: 35px; }}
        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #00b4d8; font-weight: 900; font-size: 3rem; letter-spacing: 3px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 3rem; font-weight: 800; }}
        .title {{ font-size: 4.5rem; font-weight: 900; line-height: 1.05; text-transform: uppercase; letter-spacing: -2px; color: #ffffff; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
</head>
<body>
    <div class="header-info">UPDATE: {now}</div>
    {slides_html}
    <script>
        const slides = document.querySelectorAll('.slide');
        let current = 0;
        function nextSlide() {{
            if (slides.length <= 1) return;
            slides[current].classList.remove('active');
            current = (current + 1) % slides.length;
            slides[current].classList.add('active');
        }}
        setInterval(nextSlide, 10000); 
    </script>
</body>
</html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    data = get_news()
    generate_html(data)
