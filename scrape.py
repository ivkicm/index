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
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Wir suchen nach den JSON-Metadaten für die exakten Uhrzeiten
        scripts = soup.find_all('script', type='application/ld+json')
        news_data = []
        
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
                            # Zeit umwandeln in Zagreb-Lokalzeit
                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            tz = pytz.timezone('Europe/Zagreb')
                            dt_local = dt.astimezone(tz)
                            
                            news_data.append({
                                'title': headline,
                                'image': image_url,
                                'time_obj': dt_local,
                                'time_str': dt_local.strftime("%H:%M")
                            })
            except: continue
        
        # Sortieren: Neueste zuerst
        news_data.sort(key=lambda x: x['time_obj'], reverse=True)
        return news_data[:8] 
    except Exception as e:
        print(f"Scraping Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    slides_html = ""
    for i, item in enumerate(news):
        active_class = "active" if i == 0 else ""
        # Bild-URL säubern (erzwingt große Auflösung bei Index.hr)
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
    <!-- GOOGLE SCHUTZ: Verhindert Indizierung -->
    <meta name="robots" content="noindex, nofollow">
    <meta name="googlebot" content="noindex">
    
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
            font-family: 'JetBrains Mono'; font-size: 1.3rem;
            font-weight: 800; box-shadow: 0 0 15px rgba(0,0,0,0.5);
        }}

        .slide {{
            position: absolute; width: 100%; height: 100%;
            display: none; flex-direction: column;
        }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}

        .image-container {{ 
            width: 100%; height: 55vh; position: relative; overflow: hidden; 
        }}
        
        .image-container img {{ 
            width: 100%; height: 100%; 
            object-fit: cover; 
            object-position: center center; 
            border-bottom: 6px solid #00b4d8;
        }}

        .img-overlay {{
            position: absolute; bottom: 0; left: 0; width: 100%; height: 25%;
            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
        }}

        .content-box {{ 
            flex: 1; padding: 25px 60px; 
            background: linear-gradient(to bottom, #050505, #000);
            display: flex; flex-direction: column; justify-content: flex-start;
            padding-top: 35px;
        }}

        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #00b4d8; font-weight: 900; font-size: 3rem; letter-spacing: 3px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 3rem; font-weight: 800; }}

        .title {{ 
            font-size: 4.2rem; font-weight: 900; line-height: 1.1; 
            text-transform: uppercase; letter-spacing: -1px;
            display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
            color: #ffffff;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }}

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
    if data:
        generate_html(data)
