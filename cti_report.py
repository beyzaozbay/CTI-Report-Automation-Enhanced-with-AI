# coding: utf-8
import feedparser
import datetime
import os
import openai
from fpdf import FPDF
# 1. OpenAI API Ayarı
openai_api_key = "KENDİ API Key'inizi giriniz"
client = openai.OpenAI(api_key=openai_api_key)

# 2. Anahtar Kelimeler
KEYWORDS_VIETNAM = [
    "vietnam", "hanoi", "ho chi minh", "viettel", "vinaphone", "mobifone", "vnpt"
]
KEYWORDS_TELECOM = [
    "telecom", "telecommunication", "telco", "gsm", "mobile operator", "mobile carrier",
    "cellular", "5g", "lte", "fiber", "isp", "msp", "carrier", "provider", "bts",
    "mms", "satellite", "voice", "internet service", "network outage"
]
KEYWORDS_AVIATION = [
    "aviation", "airline", "airport", "icao", "iata", "flight", "airplane", "pilot",
    "aircraft", "air traffic", "airspace", "faa", "atc", "hijack", "ground handling",
    "terminal", "check-in", "boarding"
]

#  3. RSS Feed Listesi (güncel kaynaklarla) 
RSS_FEEDS = [
    # Global siber güvenlik kaynakları
    "https://krebsonsecurity.com/feed/",
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://feeds.feedburner.com/Securityweek",
    "https://databreaches.net/feed/",
    "https://thecyberwire.com/rss/news.xml",
    "https://threatpost.com/feed/",
    "https://www.infosecurity-magazine.com/rss/news/",
    "https://www.darkreading.com/rss.xml",

    # Vietnam ile ilgili İngilizce kaynaklar
    "https://vietnamnews.vn/rss/society.rss",
    "https://tuoitrenews.vn/rss/home.rss",
    "https://vietnaminsider.vn/feed/",
    "https://english.vov.vn/en.rss",

    # Global telekom ve havacılık kaynakları
    "https://www.totaltele.com/rss/rss.xml",
    "https://www.fiercetelecom.com/rss.xml",
    "https://developingtelecoms.com/feed",
    "https://www.lightreading.com/rss.xml",
    "https://blog.telegeography.com/rss.xml",
    "https://www.telecomlead.com/feed",
    "https://www.globaltelecomsbusiness.com/feed",
    "https://www.aero-news.net/index.cfm?do=main.rss",
    "https://www.aviation-news.co.uk/feed/",
    "https://airlinegeeks.com/feed/",
    "https://www.nycaviation.com/feed/",
    "https://www.easa.europa.eu/en/newsroom-press-releases/rss.xml",
]

# 4. Dosya yolları - archive klasörü 
ARCHIVE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "archive"))

#  5. AI ile içerik uygunluk ve özet üretimi

def ai_content_check_and_summary(title: str, link: str, desc: str, category: str):
    """
    Başlığı ve açıklaması verilen haberi istenen kategoriye göre kontrol eder
    ve OpenAI ile Türkçe özet üretir. Eğer haber uygun değilse None döner.
    """
    cat_prompt_map = {
        "VIETNAM": "Bu haber Vietnam'a yapılan bir siber saldırı veya Vietnam merkezli büyük bir siber saldırı ile ilgili mi? (Evet/Hayır, kısaca neden)",
        "TELECOM": "Bu haber globalde telekomünikasyon sektörünü etkileyen, bir telekom şirketine/altyapısına yapılan bir siber saldırı ile ilgili mi? (Evet/Hayır, kısaca neden)",
        "AVIATION": "Bu haber globalde havacılık sektörünü etkileyen, bir havayolu şirketi, havalimanı, uçak üreticisi, hava trafik/yer kontrolüne yapılan bir siber saldırı ile ilgili mi? (Evet/Hayır, kısaca neden)",
    }

    prompt_check = (
        f"Başlık: {title}\n"
        f"Haber linki: {link}\n"
        f"Özet: {desc}\n\n"
        f"{cat_prompt_map[category]}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_check}],
            max_tokens=100,
            temperature=0,
        )
        answer = response.choices[0].message.content.lower()
        if not answer.startswith("evet"):
            return None
    except Exception as e:
        print(f"Kapsam kontrol hatası: {e}")
        return None

    prompt_summary = (
        f"Başlık: {title}\n"
        f"Haber linki: {link}\n"
        f"Özet: {desc}\n"
        "Lütfen bu haber için profesyonel düzeyde, etkileyici bir başlık ve ardından tam olarak 5 cümlelik Türkçe özet oluştur. "
        "Özet yalnızca gerçekleri, saldırının niteliğini, hedefini, etkisini ve sektöre olan yansımalarını içersin. "
        "Yanıtı şu biçimde ver: Başlık: <yeni başlık> ardından 5 cümlelik özet."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_summary}],
            max_tokens=300,
            temperature=0.4,
        )
        answer = response.choices[0].message.content.strip()
        lines = [line.strip() for line in answer.split("\n") if line.strip()]
        if lines[0].lower().startswith("başlık:"):
            new_title = lines[0][8:].strip()
            new_summary = " ".join(lines[1:]).strip()
        else:
            new_title = lines[0]
            new_summary = " ".join(lines[1:]).strip()
        return new_title, new_summary
    except Exception as e:
        print(f"Özet hatası: {e}")
        return None

# 6. AI ile Benzer Haber Kontrolü 

def ai_is_duplicate(title1: str, summary1: str, title2: str, summary2: str) -> bool:
    """İki haberin aynı olayı anlatıp anlatmadığını AI ile kontrol eder."""
    prompt = (
        f"Birinci haber:\nBaşlık: {title1}\nÖzet: {summary1}\n\n"
        f"İkinci haber:\nBaşlık: {title2}\nÖzet: {summary2}\n\n"
        "Bu iki haber aynı siber saldırı olayını mı anlatıyor? Sadece 'Evet' ya da 'Hayır' diye yanıtla."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "evet"
    except Exception as e:
        print(f"Duplicate check hatası: {e}")
        return False

def merge_similar_entries_ai(entries):
    """
    Benzer haberleri gruplayarak linklerini birleştirir.
    """
    merged = []
    used = set()

    for i, (pub1, title1, summary1, link1) in enumerate(entries):
        if i in used:
            continue

        group_links = [link1]
        used.add(i)

        for j in range(i + 1, len(entries)):
            pub2, title2, summary2, link2 = entries[j]
            if ai_is_duplicate(title1, summary1, title2, summary2):
                group_links.append(link2)
                used.add(j)

        merged.append((pub1, title1, summary1, group_links))

    return merged

# 7. Ana script fonksiyonu 

def fetch_recent_entries(days: int = 1):
    """
    Son 'days' gün içindeki uygun haberleri toplar, özetler ve
    txt, md, html ve pdf formatlarında raporlar oluşturur.
    """
    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(days=days)

    results = {"VIETNAM": [], "TELECOM": [], "AVIATION": []}

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            # Yayın tarihi
            published = None
            if entry.get("published_parsed"):
                published = datetime.datetime(*entry.published_parsed[:6])
            elif entry.get("updated_parsed"):
                published = datetime.datetime(*entry.updated_parsed[:6])

            if not published or published <= since:
                continue

            title = entry.title
            desc = entry.get("summary", "") or entry.get("description", "")
            content = f"{title.lower()} {desc.lower()}"

            for cat, keywords in [
                ("VIETNAM", KEYWORDS_VIETNAM),
                ("TELECOM", KEYWORDS_TELECOM),
                ("AVIATION", KEYWORDS_AVIATION),
            ]:
                if any(kw in content for kw in keywords):
                    summary_tuple = ai_content_check_and_summary(
                        title, entry.link, desc, cat
                    )
                    if summary_tuple:
                        new_title, new_summary = summary_tuple
                        results[cat].append(
                            (published, new_title, new_summary, entry.link)
                        )

    today_str = now.strftime("%Y-%m-%d")

    # Çıktı klasörlerini oluştur
    for fmt in ["txt", "md", "html", "pdf"]:
        os.makedirs(os.path.join(ARCHIVE_ROOT, fmt), exist_ok=True)

    # Kronolojik sırala ve benzerleri birleştir
    for cat in results:
        results[cat].sort(key=lambda x: x[0], reverse=True)
        results[cat] = merge_similar_entries_ai(results[cat])

    # --- TXT ---
    txt_lines = []
    for cat, entries in results.items():
        txt_lines.append(f"--- {cat} ---")
        if not entries:
            txt_lines.append(f"Son {days} günde haber yok.\n")
        else:
            for published, title, summary, links in entries:
                txt_lines.append(
                    f"- Tarih: {published.strftime('%Y-%m-%d %H:%M')}\n"
                    f"  Başlık: {title}\n"
                    f"  {summary}\n"
                    f"  Kaynaklar:\n" + "\n".join([f"    - {l}" for l in links]) + "\n"
                )

    with open(
        os.path.join(ARCHIVE_ROOT, "txt", f"{today_str}.txt"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(txt_lines))

    # --- MD ---
    md_lines = []
    for cat, entries in results.items():
        md_lines.append(f"## {cat}")
        if not entries:
            md_lines.append(f"_Son {days} günde haber yok._\n")
        else:
            for published, title, summary, links in entries:
                md_lines.append(
                    f"- **{title}**\n"
                    f"  - Tarih: {published.strftime('%Y-%m-%d %H:%M')}\n"
                    f"  - {summary}\n"
                    f"  - Kaynaklar:\n" + "\n".join([f"    - {l}" for l in links]) + "\n"
                )

    with open(
        os.path.join(ARCHIVE_ROOT, "md", f"{today_str}.md"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(md_lines))

    # --- HTML ---
    html_lines = ["<html><head><meta charset='utf-8'></head><body>"]
    for cat, entries in results.items():
        html_lines.append(f"<h2>{cat}</h2>")
        if not entries:
            html_lines.append(f"<p><em>Son {days} günde haber yok.</em></p>")
        else:
            html_lines.append("<ul>")
            for published, title, summary, links in entries:
                html_lines.append(
                    f"<li><b>{title}</b><br>"
                    f"Tarih: {published.strftime('%Y-%m-%d %H:%M')}<br>"
                    f"{summary}<br>"
                    f"Kaynaklar:<br>"
                    + "<br>".join([f'<a href=\"{l}\">{l}</a>' for l in links])
                    + "</li>"
                )
            html_lines.append("</ul>")
    html_lines.append("</body></html>")

    with open(
        os.path.join(ARCHIVE_ROOT, "html", f"{today_str}.html"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(html_lines))


# TXT içeriğini PDF'e yazdırma
def txt_to_pdf(txt_path, pdf_path,
               font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    """
    TXT dosyasındaki tüm içeriği UTF-8 uyumlu olarak PDF’e yazdırır.
    Başka hiçbir yeri etkilemez.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    # Unicode destekli bir font ekleyelim
    if font_path and os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=11)
    else:
        pdf.set_font("Arial", size=11)

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            pdf.multi_cell(0, 8, line.rstrip())

    pdf.output(pdf_path)


if __name__ == "__main__":
    # Önce raporları oluştur
    fetch_recent_entries(days=2)

    # --- PDF ---
    # TXT dosyasının adını üretmek için gerekli tarih
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    txt_file = os.path.join(ARCHIVE_ROOT, "txt", f"{today_str}.txt")
    pdf_file = os.path.join(ARCHIVE_ROOT, "pdf", f"{today_str}.pdf")
    txt_to_pdf(txt_file, pdf_file)


