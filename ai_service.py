import os
import re
import json
import google.generativeai as genai
from groq import Groq

def summarize_text(text: str, provider: str = "gemini", api_key: str = None) -> str:
    """
    Summarize educational material using Gemini, Groq, or Mock API.
    """
    if not text.strip():
        return "Özetlenecek metin boş."

    # Standardize provider selection
    provider = provider.lower() if provider else "gemini"
    
    # Check if API key is present, if not fall back to mock
    if not api_key:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            
    if not api_key:
        return get_mock_summary(text)

    try:
        if provider == "gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "Sen profesyonel bir eğitimcisin. Lütfen aşağıdaki eğitim materyalini Türkçe olarak özetle.\n"
                "Özeti şu şekilde biçimlendir:\n"
                "1. **Ana Başlık**\n"
                "2. **Kısa Özet**: (Konuyu anlatan 2-3 cümle)\n"
                "3. **Önemli Noktalar**: (Maddeler halinde en önemli kavramlar)\n"
                "4. **Anahtar Terimler ve Tanımlar**: (Metindeki teknik kelimeler ve anlamları)\n\n"
                f"Materyal Metni:\n{text}"
            )
            response = model.generate_content(prompt)
            return response.text.strip()
            
        elif provider == "groq":
            client = Groq(api_key=api_key)
            prompt = (
                "Sen profesyonel bir eğitimcisin. Lütfen aşağıdaki eğitim materyalini Türkçe olarak özetle.\n"
                "Özeti şu şekilde biçimlendir:\n"
                "1. **Ana Başlık**\n"
                "2. **Kısa Özet**: (Konuyu anlatan 2-3 cümle)\n"
                "3. **Önemli Noktalar**: (Maddeler halinde en önemli kavramlar)\n"
                "4. **Anahtar Terimler ve Tanımlar**: (Metindeki teknik kelimeler ve anlamları)\n\n"
                f"Materyal Metni:\n{text}"
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.3,
            )
            return chat_completion.choices[0].message.content.strip()
            
    except Exception as e:
        print(f"AI Error ({provider}): {str(e)}")
        return f"AI Hatası Oluştu ({str(e)}). Lütfen API anahtarınızı kontrol edin veya daha sonra tekrar deneyin.\n\n--- MOCK ÖZET ---\n\n" + get_mock_summary(text)

    return get_mock_summary(text)


def analyze_submission(text_content: str, course_title: str, provider: str = "gemini", api_key: str = None) -> dict:
    """
    Analyze student essay submission using Gemini, Groq, or Mock API.
    Returns a dictionary with 'feedback' (markdown formatted) and 'grade' (A-F).
    """
    if not text_content.strip():
        return {
            "feedback": "Değerlendirilecek ödev metni boş.",
            "grade": "F"
        }

    provider = provider.lower() if provider else "gemini"
    
    # Check if API key is present, if not fall back to mock
    if not api_key:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            
    if not api_key:
        return get_mock_analysis(text_content, course_title)

    try:
        prompt = (
            f"Kurs/Ödev Konusu: {course_title}\n"
            "Bir öğrenci yukarıdaki konuyla ilgili aşağıdaki ödev metnini teslim etti.\n"
            "Bu metni bir eğitmen gözüyle analiz et. Dilbilgisi, içerik kalitesi, konuya bağlılık ve ifade gücünü değerlendir.\n"
            "Değerlendirmeyi Türkçe yapmalısın.\n\n"
            "Yanıtı kesinlikle aşağıdaki JSON formatında vermelisin. JSON dışında hiçbir şey yazma (açıklama, markdown kod blokları vb. ekleme):\n"
            "{\n"
            '  "feedback": "Buraya markdown formatında detaylı geribildirim yazılmalıdır. Değerlendirme kriterleri (Dilbilgisi, İçerik, Güçlü Yönler, Geliştirilebilir Noktalar) alt başlıklar halinde olmalıdır.",\n'
            '  "grade": "Öğrenciye verilecek öneri harf notu (A+, A, B+, B, C+, C, D, F şeklinde sadece bir harf notu)"\n'
            "}\n\n"
            f"Öğrencinin Ödev Metni:\n{text_content}"
        )

        if provider == "gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return parse_ai_response(response.text.strip(), text_content, course_title)
            
        elif provider == "groq":
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.2,
            )
            return parse_ai_response(chat_completion.choices[0].message.content.strip(), text_content, course_title)

    except Exception as e:
        print(f"AI Analysis Error ({provider}): {str(e)}")
        mock_res = get_mock_analysis(text_content, course_title)
        mock_res["feedback"] = f"AI Hatası ({str(e)}). API anahtarını kontrol ediniz. (Aşağıda sistem tarafından otomatik oluşturulan taslak analiz bulunmaktadır):\n\n" + mock_res["feedback"]
        return mock_res

    return get_mock_analysis(text_content, course_title)


def parse_ai_response(response_text: str, text_content: str, course_title: str) -> dict:
    """Helper to clean and parse JSON response from LLMs."""
    try:
        # Strip markdown json code block indicators if any
        cleaned = response_text
        if "```json" in cleaned:
            match = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        elif "```" in cleaned:
            match = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        
        # Clean any leading/trailing garbage
        match_json = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match_json:
            cleaned = match_json.group(0)

        data = json.loads(cleaned)
        if "feedback" in data and "grade" in data:
            return data
    except Exception as e:
        print(f"JSON Parsing failed: {str(e)}. Original response: {response_text}")
    
    # Fallback if parsing fails
    return {
        "feedback": f"### AI Analiz Raporu\n\n{response_text}",
        "grade": "B"
    }


def get_mock_summary(text: str) -> str:
    """Generates a structured, rich mock summary of text content."""
    word_count = len(text.split())
    # Try to extract potential keywords
    words = [w.strip(".,;:!?\"()").lower() for w in text.split() if len(w) > 5]
    common_words = sorted(list(set(words)), key=lambda x: words.count(x), reverse=True)[:4]
    keywords = ", ".join([w.capitalize() for w in common_words]) if common_words else "Eğitim, Öğrenim"

    summary = (
        "### 🤖 AI Özet (Demo Modu)\n\n"
        f"**Kısa Özet:** Bu materyal, temel eğitim kavramlarını ve konu bütünlüğünü içermektedir. "
        f"Toplam {word_count} kelimeden oluşan bu metin, konuya genel bir bakış sunarak ana hatları belirlemektedir.\n\n"
        "**Anahtar Çıkarımlar:**\n"
        "- **Temel Odak:** Metin, konuyla ilgili güncel akademik teorileri ve pratik uygulamaları ele almaktadır.\n"
        "- **Yapısal Analiz:** Yazar, kavramsal açıklamalar ve örneklerle konunun daha iyi kavranmasını hedeflemiştir.\n"
        "- **Sonuç:** Sunulan bilgiler, öğrencilerin konuya dair altyapısını güçlendirmeye yöneliktir.\n\n"
        f"**Anahtar Kelimeler:** {keywords}\n\n"
        "> [!NOTE]\n"
        "> Gerçek AI özetleri için lütfen ayarlar menüsünden geçerli bir Gemini veya Groq API anahtarı giriniz."
    )
    return summary


def get_mock_analysis(text: str, course_title: str) -> dict:
    """Generates a realistic mock evaluation report for essays."""
    word_count = len(text.split())
    
    # Calculate a mock grade based on word count and some keywords
    grade = "C+"
    feedback_intro = "Metin kısa veya içerik analizi sınırlı."
    
    if word_count > 100:
        grade = "B"
        feedback_intro = "Güzel bir giriş yapılmış, ancak argümanların daha fazla desteklenmesi gerekiyor."
    if word_count > 250:
        grade = "A"
        feedback_intro = "Oldukça detaylı, akıcı ve konuyla son derece uyumlu bir çalışma."
    if word_count < 30:
        grade = "D"
        feedback_intro = "Yetersiz içerik uzunluğu. Konuyu daha derinlemesine ele almalısınız."

    feedback = (
        f"### 🤖 AI Ödev Değerlendirme Raporu (Demo Modu)\n"
        f"**Ders:** {course_title}\n"
        f"**Analiz Edilen Kelime Sayısı:** {word_count}\n\n"
        f"#### 1. İçerik ve Konuya Uygunluk\n"
        f"{feedback_intro} Metin, ana tema ile doğrudan ilişkili terimler içeriyor ve kavramsal çerçeveyi doğru kuruyor.\n\n"
        f"#### 2. Dilbilgisi ve Anlatım Akıcılığı\n"
        f"Cümle yapıları genel olarak düzgün. İfade gücü yüksek. Bazı noktalama işaretlerine dikkat edilmesi metnin okunabilirliğini artıracaktır.\n\n"
        f"#### 3. Güçlü Yönler\n"
        f"- Konuya giriş yaparken net bir tez cümlesi kullanılmış.\n"
        f"- Temel kavramlar doğru bir terminoloji ile aktarılmış.\n\n"
        f"#### 4. Geliştirilebilecek Yönler\n"
        f"- İddialarınızı desteklemek için daha fazla örnek veya akademik referans ekleyebilirsiniz.\n"
        f"- Sonuç bölümü biraz aceleye getirilmiş görünüyor, ana fikri toparlayan güçlü bir kapanış yapılabilir.\n\n"
        f"> [!TIP]\n"
        f"> Gerçek AI tabanlı özelleştirilmiş geribildirim almak için lütfen geçerli bir API anahtarı tanımlayın."
    )

    return {
        "feedback": feedback,
        "grade": grade
    }
