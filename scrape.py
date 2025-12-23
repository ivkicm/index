import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz

def get_news():
    url = "https://www.index.hr/sport"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    news_data = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Versuch: JSON-LD (Sehr genau)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    for element in data.get('itemListElement', []):
                        item = element.get('item', {})
                        headline = item.get('name') or item.get('headline')
                        image_url = item.get('image')
                        pub_date = item.get('datePublished')
                        
                        if headline and pub_date:
                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            tz = pytz.timezone('Europe/Zagreb')
                            dt_local = dt.astimezone(tz)
                            news_data.append({
                                'title': headline, 'image': image_url,
                                'time_obj': dt_local, 'time_str': dt_local.strftime("%H:%M")
                            })
            except: continue
        
        # 2. Versuch: HTML-Fallback (Falls JSON-LD fehlt)
        if not news_data:
            articles = soup.select('.grid-item, .first-news-holder')
            for art in articles:
                try:
                    title_el = art.select_one('.title')
                    img_el = art.select_one('img')
                    if title_el and img_el:
                        news_data.append({
                            'title': title_el.get_text(strip=True),
                            'image': img_el['src'],
                            'time_obj': datetime.now(), 'time_str': "--:--"
                        })
                except: continue

        news_data.sort(key=lambda x: x.get('time_obj', 0), reverse=True)
        return news_data[:8]
    except Exception as e:
        print(f"Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    # Falls keine News da sind, eine Info-Seite bauen
    if not news:
        news = [{'title': 'Aktuell keine News verfügbar (Scraping-Check)', 'image': '', 'time_str': '--:--', 'date': ''}]

    slides_html = ""
    for i, item in enumerate(news):
        active_class = "active" if i == 0 else ""
        img_url = item.get('image', '')
        if img_url and '?' in img_url:
            img_url = img_url.split('?')[0] + "?width=1200&height=630&mode=crop"

        slides_html += f"""
        <div class="slide {active_class}">
            <div class="image-container">
                <img src="{img_url}" onerror="this.style.display='none'">
                <div class="img-overlay"></div>
            </div>
            <div class="content-box">
                <div class="meta-line">
                    <span class="source">INDEX SPORT</span>
                    <span class="pub-time">{item.get('time_str', '--:--')} UHR</span>
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
    <title>Index Sport Radar</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@800;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; background: black; color: white; font-family: 'Inter', sans-serif; overflow: hidden; }}
        .header-info {{ position: fixed; top: 15px; right: 20px; z-index: 100; background: rgba(0, 180, 216, 0.9); padding: 5px 15px; border-radius: 8px; font-family: 'JetBrains Mono'; font-size: 1.2rem; font-weight: 800; }}
        .slide {{ position: absolute; width: 100%; height: 100%; display: none; flex-direction: column; }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}
        .image-container {{ width: 100%; height: 55vh; position: relative; overflow: hidden; background: #111; }}
        .image-container img {{ width: 100%; height: 100%; object-fit: cover; border-bottom: 6px solid #00b4d8; }}
        .content-box {{ flex: 1; padding: 25px 60px; background: #000; display: flex; flex-direction: column; }}
        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #00b4d8; font-weight: 900; font-size: 2.5rem; letter-spacing: 2px; }}
        .pub-time {{ font-family: 'JetBrains Mono'; font-size: 2.5rem; opacity: 0.8; }}
        .title {{ font-size: 4rem; font-weight: 900; line-height: 1.1; text-transform: uppercase; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
</head>
<body>
    <div class="header-info">STAND: {now}</div>
    {slides_html}
    <script>
        let current = 0;
        const slides = document.querySelectorAll('.slide');
        function next() {{
            if(slides.length < 2) return;
            slides[current].classList.remove('active');
            current = (current + 1) % slides.length;
            slides[current].classList.add('active');
        }}
        setInterval(next, 12000);
    </script>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    news = get_news()
    generate_html(news) # Erstellt IMMER eine Datei
