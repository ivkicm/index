import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz
import re

def get_article_time(url, headers):
    """Besucht den einzelnen Artikel und extrahiert die genaue Uhrzeit."""
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Index.hr hat die Zeit meistens in einem span innerhalb von .publish-date
        # Format oft: "23.12.2025. u 13:47"
        time_el = soup.select_one('.publish-date span')
        if time_el:
            text = time_el.get_text(strip=True)
            # Extrahiere nur die Uhrzeit (HH:MM) mit Regex
            match = re.search(r'(\d{1,2}:\d{2})', text)
            if match:
                return match.group(1)
    except:
        pass
    return "--:--"

def get_news():
    base_url = "https://www.index.hr"
    url = "https://www.index.hr/sport"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_data = []

        # Wir sammeln die Top-Artikel von der Startseite
        # Wir nehmen den Hauptartikel und die Grid-Items
        articles = soup.select('.first-news-holder, .grid-item')
        
        # Wir limitieren auf die Top 8, damit die GitHub Action nicht zu lange braucht
        for art in articles[:8]:
            try:
                title_el = art.select_one('.title')
                link_el = art.select_one('a')
                img_el = art.select_one('img')
                
                if title_el and link_el and img_el:
                    title = title_el.get_text(strip=True)
                    link = link_el['href']
                    if not link.startswith('http'):
                        link = base_url + link
                    
                    img = img_el['src']
                    
                    # JETZT: Eine Stufe tiefer gehen und die Uhrzeit aus dem Artikel holen
                    print(f"Scrape Uhrzeit für: {title[:30]}...")
                    uhrzeit = get_article_time(link, headers)
                    
                    news_data.append({
                        'title': title,
                        'image': img,
                        'time_str': uhrzeit,
                        # Wir speichern ein Zeit-Objekt für die Sortierung
                        # Da wir nur HH:MM haben, nutzen wir das heutige Datum
                        'sort_key': uhrzeit if uhrzeit != "--:--" else "00:00"
                    })
            except Exception as e:
                print(f"Fehler bei Einzelartikel: {e}")
                continue

        # Chronologisch sortieren (Neueste zuerst)
        news_data.sort(key=lambda x: x['sort_key'], reverse=True)
        return news_data
    except Exception as e:
        print(f"Scraping Hauptseite Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    slides_html = ""
    for i, item in enumerate(news):
        active_class = "active" if i == 0 else ""
        # Bild-URL für XXL optimieren
        img_url = item['image']
        if '?' in img_url:
            img_url = img_url.split('?')[0] + "?width=1200&height=630&mode=crop"

        slides_html += f"""
        <div class="slide {active_class}">
            <div class="image-container">
                <img src="{img_url}" alt="News Image">
                <div class="img-overlay"></div>
            </div>
            <div class="content-box">
                <div class="meta-line">
                    <span class="source">INDEX SPORT</span>
                    <span class="pub-time">{item['time_str']} UHR</span>
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
        body, html {{ 
            margin: 0; padding: 0; width: 100%; height: 100%; 
            background-color: black; color: white; font-family: 'Inter', sans-serif;
            overflow: hidden;
        }}
        .header-info {{
            position: fixed; top: 15px; right: 20px; z-index: 100;
            background: rgba(0, 180, 216, 0.9); color: white;
            padding: 5px 15px; border-radius: 8px;
            font-family: 'JetBrains Mono'; font-size: 1.2rem;
            font-weight: 800; box-shadow: 0 0 15px rgba(0,0,0,0.5);
        }}
        .slide {{
            position: absolute; width: 100%; height: 100%;
            display: none; flex-direction: column;
        }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}
        .image-container {{ width: 100%; height: 55vh; position: relative; overflow: hidden; }}
        .image-container img {{ width: 100%; height: 100%; object-fit: cover; border-bottom: 6px solid #00b4d8; }}
        .img-overlay {{ position: absolute; bottom: 0; left: 0; width: 100%; height: 25%; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); }}
        .content-box {{ flex: 1; padding: 30px 60px; background: #000; display: flex; flex-direction: column; justify-content: flex-start; padding-top: 35px; }}
        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #00b4d8; font-weight: 900; font-size: 3rem; letter-spacing: 3px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 3rem; font-weight: 800; }}
        .title {{ font-size: 4.2rem; font-weight: 900; line-height: 1.1; text-transform: uppercase; letter-spacing: -1px; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; color: #ffffff; }}
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
        setInterval(nextSlide, 12000); 
        setTimeout(() => {{ location.reload(); }}, 1800000);
    </script>
</body>
</html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    data = get_news()
    generate_html(data)
