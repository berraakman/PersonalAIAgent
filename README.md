# 🤖 BerrAI – Kişisel Yapay Zeka Asistanınız

BerrAI, günlük dijital hayatınızı kolaylaştırmak için tasarlanmış; Google ekosistemi (Drive, Docs, Sheets, Slides, Calendar, Gmail) ile **tam entegre** çalışan, hem sesli hem de yazılı komutlarla yönetilebilen akıllı bir kişisel yapay zeka asistanıdır.

Gelişmiş AI mantığı ve şık, kullanıcı dostu arayüzü sayesinde tek bir ekrandan tüm Google dijital çalışma alanınıza hükmedebilir, karmaşık görevleri yapay zekaya devredebilirsiniz.

---

## 🎯 BerrAI Neler Yapabilir? (Temel Özellikler)

BerrAI, Google hizmetleriyle doğrudan konuşmanızı sağlar. İşte yapabildiği bazı sihirli şeyler:

| Servis | Yapabildikleri | Örnek Komut |
|---------|----------|-------------|
| 📁 **Google Drive** | İçindeki dosyaları bulma, listeleme, klasör oluşturma, indirme işlemleri. | *"Drive'ımda Machine Learning ile ilgili PDF'leri bulur musun?"* |
| 📄 **Google Docs** | Sıfırdan belge oluşturma, belge okuma, belirli bir metni ekleme veya bulup değiştirme. | *"Yeni bir doküman oluştur, adını 'Proje Notları' koy ve içine 'Tasarım toplantısı yarın yapılacak' yaz."* |
| 📊 **Google Sheets** | Tablo (E-Tablo) oluşturma, sayfaları (sheet) okuma/yazma, yeni veri satırları ekleme. | *"Bütçe Excel'imi bul ve son satıra 'Market Alışverişi - 500 TL' ekle."* |
| 🎞️ **Google Slides** | Sunum başlatma, slayt sayfası ekleme ve asistanla birlikte slayt içeriklerini şekillendirme. | *"Yeni bir slayt oluştur ve ilk sayfaya 'BerrAI Tanıtım Sunumu' yaz."* |
| 📅 **Google Calendar** | Randevu defterinize bakma, yeni etkinlik, toplantı ayarlama ve mevcut etkinlikleri güncelleme veya silme. | *"Yarın saat 14:00'te 'Yazılım Ekip Toplantısı' adında 1 saatlik etkinlik oluştur."* |
| ✉️ **Gmail** | Gelen kutunuzdaki son mailleri okuma, bir e-posta taslağı oluşturma veya doğrudan mail atma. | *"ali@veli.com adresine 'Proje Durumu' konulu, projenin bittiğini haber veren bir e-posta gönder."* |

**Ekstra Özellikler:**
- 🎤 **Kusursuz Ses Algılama (Web Speech API):** Klavye kullanmanıza gerek yok. Dinleme butonuna basın, mikrofonunuzla doğrudan Türkçe komut verin. Duraklatma, devam etme ve anında iptal destekleri bulunur.
- 💬 **Gelişmiş Sohbetsel Hafıza:** OpenAI / DeepSeek vb. AI modellerine bağlı olduğu için, ona sorduğunuz kod sorularını, teknik konseptleri profesyonelce açıklar veya günlük sohbetlerinizi cevaplar.

---

## 🏗️ Kullanılan Teknolojiler (Teknik Yapı)

BerrAI, hızlı ve hafif bir yapı üzerine inşa edilmiştir. Veritabanı (DB) bağımlılığı yoktur, doğrudan Google API'leri ile iletişim kurarak çalışır.

- **Backend (Sunucu):** Python `FastAPI` (Yüksek hızlı, asenkron web framework)
- **Frontend (Arayüz):** Sadece `HTML5`, `CSS3` (Modern Cam Efekti tasarımı) ve `Vanilla JavaScript` (Hiçbir JS framework'ü, React/Vue vs. kullanılmamıştır, dolayısıyla çok hızlı ve hafiftir).
- **Yapay Zeka (AI):** `OpenRouter` aracılığıyla *DeepSeek*, *OpenAI* veya lokal kullanım için `Ollama` entegrasyonu (Ayarlardan değiştirilebilir).
- **Kimlik Doğrulama:** Google OAuth 2.0 (Kullanıcı girişleri doğrudan Google üzerinden gerçekleşir).

---

## 👩‍💻 Kurulum ve Çalıştırma Rehberi

Eğer bir yazılımcı değilseniz bile aşağıdaki adımları sırayla takip ederek BerrAI'ı kendi bilgisayarınızda çalıştırabilirsiniz.

### Adım 1: Kurulum İçin Bilgisayarınızı Hazırlayın
1. Bilgisayarınızda **Python**'un yüklü olduğundan emin olun. Değilse [python.org](https://www.python.org/downloads/)'dan indirip kurun (Python 3.10 veya üzeri önerilir).
2. Proje dosyalarını bilgisayarınıza indirin veya `git clone` komutu ile kopyalayın.
3. Terminal'i (Windows için Komut İstemi / Mac için Terminal) açın ve proje klasörünün (`PersonalAIAgent`) içine girin.
4. Gerekli kütüphaneleri indirmek için şu komutu çalıştırın:
   ```bash
   pip install -r requirements.txt
   ```

### Adım 2: Google ve Yapay Zeka Kimlik Bilgilerini Ayarlayın
BerrAI'ın Google hesabınızla işlem yapabilmesi için Google tarafında "Bu uygulamaya güveniyorum" ayarı yapılması gerekir.

1. `.env.example` dosyasının adını sadece `.env` olarak değiştirin veya kopyalayarak yeni bir `.env` oluşturun.
2. [Google Cloud Console](https://console.cloud.google.com/)'a gidin.
3. Yeni bir proje oluşturun. Arama barından şunları bulup **Etkinleştirin (Enable)**: 
   *Google Drive API, Google Docs/Sheets/Slides API, Google Calendar API, Gmail API.*
4. **"APIs & Services" -> "Credentials (Kimlik Bilgileri)"** menüsüne gidin.
5. "Create Credentials" (Kimlik Bilgisi Oluştur) butonuna tıklayıp **OAuth client ID**'yi seçin. "Web application" tipini seçin. *"Authorized redirect URIs"* kısmına şunu tam olarak kopyalayıp ekleyin: `http://localhost:8000/auth/callback`
6. Karşınıza çıkan **Client ID** ve **Client Secret** şifrelerini kopyalayın ve `.env` dosyanızdaki `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` kısımlarına yapıştırın.
7. Son olarak, bir yapay zeka modelinin zekasını kullanmalıyız. OpenRouter (veya Ollama vb.) sitesinden aldığınız API Key'i `.env` dosyasındaki `AI_API_KEY` kısmına yapıştırın.

### Adım 3: Asistanı Çalıştırın!
Her şey hazır. Aynı terminal ekranında aşağıdaki sihirli komutu yazın:
```bash
python -m app.main
```

Terminalde uygulamanın başladığını gördükten sonra favori web tarayıcınızı (Chrome vb.) açın ve adres çubuğuna şunu yazıp Enter'a basın: **`http://localhost:8000`**

### Adım 4: Bağlanın ve Konuşmaya Başlayın
1. Sol menüden **"Google ile Bağlan"** tuşuna basarak Google hesabınızla giriş yapın (Eğer Google bir güvenlik uyarısı verirse, kendi projeniz olduğu için 'Gelişmiş' butonuna tıklayarak devam edebilirsiniz).
2. Artık arayüzdesiniz! Aşağıdaki metin kutucuğuna gidip *"Drive'ımda bugün oluşturduğum dosyaları göster"* yazabilir veya mikrofon ikonuna 🎤 tıklayarak konuşabilirsiniz!

---

## 🔒 Gizlilik, Güvenlik ve Veri Yönetimi

BerrAI tamamen sizin bilgisayarınızda (*localhost*) çalışır. 
- Google'a giriş yapmak için kullandığınız özel Token dosyası (`token.json`), bilgisayarınızın dışına çıkmaz.
- Yapay Zeka API şifreniz (`.env` dosyasındaki), GitHub'a veya internete yüklenmesini engelleyen `.gitignore` sayesinde maksimum koruma altındadır.
- Asistan, sadece sizin Google hesabınızın içindeki verilere "siz bir komut verdiğiniz zaman" ulaşır, kendi kendine hesaplarınızı okuyan bir arka plan servisi çalıştırmaz.

---

## 📁 Proje Klasör Yapısı (Geliştiriciler İçin)

Projenin iç mimarisi düzenli olması için bileşenlere ayrılmıştır:

```text
PersonalAIAgent/
├── app/
│   ├── main.py                # Sunucunun çalıştığı ve tüm servisleri ayaklandırdığı başlangıç noktası
│   ├── config.py              # Klasör yolları, .env dosyası ve ayarların içe aktarıldığı yer
│   ├── routers/
│   │   ├── auth.py            # Kullanıcının Google girişi ve Çıkış yapmasını yöneten uç noktalar (Endpoints)
│   │   └── chat.py            # UI ile Yapay zeka servislerini bağlayan Ana Sohbet API'leri
│   ├── services/
│   │   ├── ai_agent.py        # 🧠 ASİSTANIN BEYNİ: Anlama, planlama ve Tool(Araç) kullanımı burada döner
│   │   ├── google_auth.py     # OAuth2 ile Token canlandırma ve yetki denetimi yapan fonksiyonlar
│   │   └── google_*.py        # Google'ın her uygulamasının kendine özel kodları (Drive, Docs, Gmail vs.)
│   └── static/
│       ├── app.js             # 🎨 Arayüzün tüm zeki mantığı (Ses animasyonları, mesaj gösterme, API ping)
│       ├── styles.css         # Modern renk paleti, animasyonlar ve flex/grid CSS dosyamız
│       └── index.html         # Uygulamanın iskeleti
├── .env.example               # Örnek güvenlik dosyamız
├── .gitignore                 # GitHub'ın zararlı/gizli dosyaları yüklemesini önleyen kalkan
└── requirements.txt           # Python için gerekli eklenti paketi listemiz
```

---

📝 **Geliştirici:** *Berra Akman*  
📜 **Lisans:** MIT License (Açık kaynak ve kişisel kullanıma açık)
