# CTI-Report-Automation-Enhanced-with-AI
Kısaca Ne Yapıyor?
Bu Python betiği, günlük Siber Tehdit İstihbaratı (CTI) raporunu tamamen otomatik üretmek için dört adımlı bir boru hattı kurar:
Haber Toplama (Ingest)
Ön Eleme & Doğrulama (Filter + AI Relevance)
Birleştirme (Deduplication)
Çıktı Üretimi (Reporting) – TXT, Markdown, HTML, PDF
1. Haber Toplama
Bileşen	Açıklama
RSS_FEEDS	20-den fazla küresel / sektörel RSS kaynağı (siber güvenlik, Vietnam, telekom, havacılık).
feedparser.parse(url)	Her feed’i indirir, entry listesi üretir.
Zaman Filtresi	since = now – timedelta(days) ile “son N gün” sınırı koyar.
Neden: Bir CTI analisti olarak “güncel” kalmak istiyorsunuz; eski haberler otomatikman atılır.
2. Ön Eleme & AI Doğrulama
2.1 Anahtar-Kelime Taraması
Üç kategori: VIETNAM, TELECOM, AVIATION
Her kategoriye özel KEYWORDS_* listesi.
Başlık + özet string’inde (lower-case) any(kw in content for kw in keywords).
Bu kaba tarama, “gürültüyü” hızlıca azaltır.
2.2 “Gerçekten İlgili mi?” – OpenAI Kontrolü
Fonksiyon: ai_content_check_and_summary
Prompt 1 (Relevance Check)
Örneğin TELECOM için:
“Bu haber global telekom sektörünü etkileyen bir siber saldırı ile ilgili mi? (Evet/Hayır, kısaca neden).”
“Evet” cevabı gelmezse haber elenir.
Prompt 2 (Türkçe Özet)
5 cümlelik profesyonel Türkçe özet + yeni, vurucu başlık.
Neden AI?
• Anahtar-kelime eşleşmesi tek başına yeterli değil (ör. “5G” geçen teknoloji haberi, siber saldırı olmayabilir).
• Türkçe özet, raporun okunabilirliğini artırır.
3. Birleştirme (Deduplication)
Fonksiyon: merge_similar_entries_ai
Her kategori, tarih sırasıyla gezilir.
Her çift için ai_is_duplicate
Prompt: “Bu iki haber aynı siber saldırı olayını mı anlatıyor? Sadece ‘Evet’ / ‘Hayır’.”
Aynı olay ise link’ler tek madde altında gruplanır.
Kazanç:
Rapor şişmez, analist aynı olayı iki kere incelemek zorunda kalmaz.
4. Raporlama Katmanı
Format	Yöntem	Kullanım
TXT	Düz satırlar, kolay diff & arşiv.	
Markdown	GitHub veya wiki’ye doğrudan yapıştırılabilir, link’ler tıklanabilir.	
HTML	E-posta gövdesi veya intranet sayfası için.	
PDF	Dosya bütünlüğü, offline paylaşım; txt_to_pdf() fonksiyonu ile TXT aynen PDF’e aktarılıyor.	
Her format aynı dizin ağacına yazılır:
archive/
  txt/2025-06-27.txt
  md/  2025-06-27.md
  html/2025-06-27.html
  pdf/ 2025-06-27.pdf
