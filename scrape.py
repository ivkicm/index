import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import pytz

def parse_relative_time(num_str, desc_str):
    """Wandelt '19' und 'min' oder '1' und 'h' in einen Zeitstempel um."""
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz)
    try:
        num = int(num_str)
        if 'min' in desc_str.lower():
            return now - timedelta(minutes=num), f"VOR {num} MINUTEN"
        elif 'h' in desc_str.lower():
            return now - timedelta(hours=num), f"VOR {num} {'STUNDE' if num == 1 else 'STUNDEN'}"
        elif 'd' in desc_str.lower():
            return now - timedelta(days=num), f"VOR {num} TAGEN"
    except:
        pass
    return now, "GERADE EBEN"

def get_news():
    url = "https://www.index.hr/najnovije?kategorija=150"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    news_data = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('ul.latest > li')
        
        for art in articles[:10]:
            try:
                num = art.select_one('.num').get_text(strip=True)
                desc = art.select_one('.desc').get_text(strip=True)
                dt_obj, rel_time_str = parse_relative_time(num, desc)
                
                title_el = art.select_one('.title')
                img_el = art.select_one('.img-holder img')
                
                if title_el and img_el:
                    title = title_el.get_text(strip=True)
                    img = img_el['src']
                    
                    if '?' in img:
                        img = img.split('?')[0] + "?width=1200&height=630&mode=crop"
                    
                    news_data.append({
                        'title': title,
                        'image': img,
                        'rel_time': rel_time_str,
                        'time_obj': dt_obj
                    })
            except: continue

        return news_data
    except Exception as e:
        print(f"Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Zagreb')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    if not news:
        news = [{'title': 'Tražim najnovije vijesti...', 'image': '', 'rel_time': 'INDEX', 'time_obj': datetime.now()}]

    slides_html = ""
    for i, item in enumerate(news):
        active_class = "active" if i == 0 else ""
        slides_html += f"""
        <div class="slide {active_class}">
            <div class="image-container">
                <img src="{item['image']}" alt="News Image">
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

        /* BILD-BEREICH EXAKT WIE IM GEWÜNSCHTEN CODE */
        .image-container {{ 
            width: 100%; height: 55vh; position: relative; overflow: hidden; 
        }}
        
        .image-container img {{ 
            width: 100%; height: 100%; 
            object-fit: cover; 
            object-position: center top; 
            border-bottom: 6px solid #00b4d8;
        }}

        .img-overlay {{
            position: absolute; bottom: 0; left: 0; width: 100%; height: 25%;
            background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
        }}

        /* TEXT-BEREICH EXAKT WIE IM GEWÜNSCHTEN CODE */
        .content-box {{ 
            flex: 1; padding: 25px 60px; 
            background: linear-gradient(to bottom, #0c0c0c, #000);
            display: flex; flex-direction: column; justify-content: flex-start;
            padding-top: 30px;
        }}

        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #00b4d8; font-weight: 900; font-size: 2.8rem; letter-spacing: 3px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 2.8rem; font-weight: 800; }}

        .title {{ 
            font-size: 4.5rem; font-weight: 900; line-height: 1.05; 
            text-transform: uppercase; letter-spacing: -2px;
            display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
            color: #f0f0f0;
        }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: scale(1.01); }} to {{ opacity: 1; transform: scale(1); }} }}
    </style>
</head>
<body>
    <div class="header-info">STAND: {now}</div>
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
