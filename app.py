import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load env variables if they exist
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EduAI - Akıllı LMS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_URL = "http://127.0.0.1:8000"

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Global layout style adjustments */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(14, 17, 23, 1) 0%, rgba(20, 24, 33, 1) 90.1%);
    }
    
    /* Card Styles */
    .course-card {
        background-color: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .course-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    /* Header/Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
        border-radius: 20px;
        padding: 30px 40px;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(to right, #38bdf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .badge-teacher {
        background-color: rgba(13, 148, 136, 0.2);
        color: #2dd4bf;
        border: 1px solid rgba(13, 148, 136, 0.4);
    }
    .badge-student {
        background-color: rgba(79, 70, 229, 0.2);
        color: #818cf8;
        border: 1px solid rgba(79, 70, 229, 0.4);
    }
    
    /* Grade Circle */
    .grade-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%);
        color: white;
        font-size: 1.4rem;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "api_provider" not in st.session_state:
    st.session_state.api_provider = "gemini"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar logic
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=80)
    st.title("EduAI Kontrol")
    
    if st.session_state.logged_in:
        role_label = "Eğitmen" if st.session_state.user["role"] == "teacher" else "Öğrenci"
        badge_style = "badge-teacher" if st.session_state.user["role"] == "teacher" else "badge-student"
        
        st.markdown(f"**Kullanıcı:** {st.session_state.user['username']}")
        st.markdown(f'<span class="badge {badge_style}">{role_label}</span>', unsafe_allow_html=True)
        st.divider()
        
        # AI Config Panel
        st.subheader("🤖 Yapay Zekâ Ayarları")
        provider = st.selectbox(
            "AI Sağlayıcısı", 
            ["Gemini", "Groq"], 
            index=0 if st.session_state.api_provider == "gemini" else 1
        )
        st.session_state.api_provider = provider.lower()
        
        # Password/API key field
        custom_key = st.text_input(
            f"{provider} API Key", 
            type="password", 
            value=st.session_state.api_key, 
            placeholder="Anahtar girilmezse Mock AI kullanılır"
        )
        st.session_state.api_key = custom_key
        
        st.divider()
        if st.button("Çıkış Yap", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
            
    else:
        st.info("Devam etmek için giriş yapın veya yeni bir hesap oluşturun.")

# Check Backend Connection Helper
def check_backend():
    try:
        # Just simple test to API URL
        requests.get(f"{API_URL}/courses/all", timeout=2)
        return True
    except Exception:
        return False

# Main Render Flow
if not check_backend():
    st.error("⚠️ Backend API (FastAPI) sunucusuna bağlanılamadı.")
    st.warning("Lütfen komut satırından FastAPI sunucusunun çalıştığından emin olun:\n`uvicorn main:app --reload --port 8000`")
    st.info("Bu sırada verileri yükleyemez veya işlem yapamazsınız.")
    if st.button("Yeniden Bağlanmayı Dene"):
        st.rerun()
    st.stop()

# Helper API functions
def login_user(username, password):
    try:
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            return res.json(), None
        else:
            return None, res.json().get("detail", "Giriş başarısız.")
    except Exception as e:
        return None, f"Hata: {str(e)}"

def register_user(username, password, role):
    try:
        res = requests.post(f"{API_URL}/register", json={"username": username, "password": password, "role": role})
        if res.status_code == 201:
            return res.json(), None
        else:
            return None, res.json().get("detail", "Kayıt başarısız.")
    except Exception as e:
        return None, f"Hata: {str(e)}"


# ==========================================
# AUTHENTICATION PAGE
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="hero-banner"><h1 class="hero-title">🎓 EduAI LMS</h1><p class="hero-subtitle">Yapay Zekâ Destekli Öğrenme Yönetim Sistemine Hoş Geldiniz</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Giriş Yap")
        with st.form("login_form"):
            l_username = st.text_input("Kullanıcı Adı")
            l_password = st.text_input("Şifre", type="password")
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submitted:
                if not l_username or not l_password:
                    st.error("Lütfen tüm alanları doldurun.")
                else:
                    user, err = login_user(l_username, l_password)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success("Giriş başarılı!")
                        st.rerun()
                        
    with col2:
        st.subheader("Kayıt Ol")
        with st.form("register_form"):
            r_username = st.text_input("Yeni Kullanıcı Adı")
            r_password = st.text_input("Şifre", type="password")
            r_role = st.selectbox("Rol Seçin", ["student", "teacher"], format_func=lambda x: "Öğrenci" if x == "student" else "Eğitmen")
            submitted_reg = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            if submitted_reg:
                if not r_username or not r_password:
                    st.error("Lütfen tüm alanları doldurun.")
                else:
                    user, err = register_user(r_username, r_password, r_role)
                    if err:
                        st.error(err)
                    else:
                        st.success("Kayıt başarılı! Giriş yapabilirsiniz.")

# ==========================================
# STUDENT DASHBOARD
# ==========================================
elif st.session_state.user["role"] == "student":
    student_id = st.session_state.user["id"]
    
    st.markdown(f'<div class="hero-banner"><h1 class="hero-title">Öğrenci Paneli</h1><p class="hero-subtitle">Hoş geldin, {st.session_state.user["username"]}! Derslerini ve ödevlerini buradan takip edebilirsin.</p></div>', unsafe_allow_html=True)
    
    tab_my_courses, tab_all_courses = st.tabs(["📚 Kayıtlı Derslerim", "🔍 Tüm Kursları Keşfet"])
    
    # 1. MY COURSES TAB
    with tab_my_courses:
        res = requests.get(f"{API_URL}/courses?student_id={student_id}")
        my_courses = res.json() if res.status_code == 200 else []
        
        if not my_courses:
            st.info("Henüz hiçbir kursa kayıtlı değilsiniz. 'Tüm Kursları Keşfet' sekmesinden kaydolabilirsiniz.")
        else:
            # Dropdown to select active course
            course_options = {c["title"]: c for c in my_courses}
            selected_course_title = st.selectbox("Detayları görüntülemek için bir ders seçin:", list(course_options.keys()))
            selected_course = course_options[selected_course_title]
            
            st.divider()
            st.subheader(selected_course["title"])
            st.write(selected_course["description"])
            
            subtab_materials, subtab_assignments = st.tabs(["📖 Ders Materyalleri", "📝 Ödev Gönderimi"])
            
            # Subtab: Materials
            with subtab_materials:
                mat_res = requests.get(f"{API_URL}/courses/{selected_course['id']}/materials")
                materials = mat_res.json() if mat_res.status_code == 200 else []
                
                if not materials:
                    st.info("Bu ders için henüz materyal yüklenmemiş.")
                else:
                    for mat in materials:
                        with st.expander(f"📄 {mat['title']}"):
                            st.write(mat['content'])
                            
                            st.markdown("---")
                            # Summarization Trigger
                            if st.button("🤖 Yapay Zekâ ile Özetle", key=f"sum_{mat['id']}"):
                                with st.spinner("Özet hazırlanıyor..."):
                                    sum_res = requests.post(
                                        f"{API_URL}/ai/summarize",
                                        json={
                                            "content": mat['content'],
                                            "provider": st.session_state.api_provider,
                                            "api_key": st.session_state.api_key
                                        }
                                    )
                                    if sum_res.status_code == 200:
                                        st.info("### Yapay Zekâ Özeti")
                                        st.markdown(sum_res.json()["summary"])
                                    else:
                                        st.error("Özet oluşturulamadı.")
                                        
            # Subtab: Assignments & AI feedback
            with subtab_assignments:
                st.subheader("Ödev Teslim Et")
                st.write("Aşağıdaki alana ödevinizi veya makalenizi yazarak teslim edin. Yapay zekâ anında değerlendirme sunacaktır.")
                
                with st.form("submission_form"):
                    essay_text = st.text_area("Ödev İçeriği", height=250, placeholder="Konuyla ilgili analiz veya makalenizi buraya yazın...")
                    submit_essay = st.form_submit_button("Yapay Zekâ Analizi ile Ödevi Teslim Et")
                    
                    if submit_essay:
                        if not essay_text.strip():
                            st.error("Ödev metni boş bırakılamaz.")
                        else:
                            with st.spinner("Ödeviniz yapay zekâ tarafından analiz ediliyor..."):
                                sub_res = requests.post(
                                    f"{API_URL}/courses/{selected_course['id']}/submissions?student_id={student_id}&provider={st.session_state.api_provider}&api_key={st.session_state.api_key}",
                                    json={"text_content": essay_text}
                                )
                                if sub_res.status_code == 201:
                                    st.success("Ödeviniz başarıyla teslim edildi ve analiz edildi!")
                                    data = sub_res.json()
                                    st.session_state.last_submission = data
                                else:
                                    st.error("Ödev gönderilemedi veya yapay zekâ hatası oluştu.")
                                    
                # Show last feedback if available
                if "last_submission" in st.session_state:
                    sub = st.session_state.last_submission
                    st.markdown("### Son Ödev Değerlendirme Raporu")
                    col_grade, col_fb = st.columns([1, 4])
                    with col_grade:
                        st.markdown("**AI Öneri Notu**")
                        st.markdown(f'<div class="grade-badge">{sub["grade"]}</div>', unsafe_allow_html=True)
                    with col_fb:
                        st.markdown(sub["ai_feedback"])
                        
                st.divider()
                st.subheader("Geçmiş Gönderilerim")
                hist_res = requests.get(f"{API_URL}/courses/{selected_course['id']}/submissions?student_id={student_id}")
                submissions = hist_res.json() if hist_res.status_code == 200 else []
                
                if not submissions:
                    st.info("Bu ders için geçmiş bir ödev gönderiniz bulunmamaktadır.")
                else:
                    for i, sub in enumerate(reversed(submissions)):
                        date_str = sub["submitted_at"].split("T")[0]
                        with st.expander(f"📅 Teslim Tarihi: {date_str} - Not: {sub['grade']}"):
                            st.text_area("Gönderilen Metin", sub["text_content"], height=100, disabled=True, key=f"hist_txt_{i}")
                            st.markdown("#### AI Değerlendirmesi ve Geribildirim")
                            st.markdown(sub["ai_feedback"])

    # 2. ALL COURSES TAB
    with tab_all_courses:
        all_res = requests.get(f"{API_URL}/courses/all")
        all_courses = all_res.json() if all_res.status_code == 200 else []
        
        # Get list of enrolled course IDs
        my_course_ids = [c["id"] for c in my_courses]
        
        if not all_courses:
            st.info("Sistemde henüz kurs bulunmamaktadır.")
        else:
            for course in all_courses:
                st.markdown(f"""
                <div class="course-card">
                    <h3>{course['title']}</h3>
                    <p>{course['description'] or 'Açıklama bulunmuyor.'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Enroll button logic
                if course["id"] in my_course_ids:
                    st.button("Zaten Kayıtlısınız", key=f"enroll_btn_{course['id']}", disabled=True)
                else:
                    if st.button("Kursa Kaydol", key=f"enroll_btn_{course['id']}"):
                        enroll_res = requests.post(f"{API_URL}/courses/{course['id']}/enroll?student_id={student_id}")
                        if enroll_res.status_code == 201:
                            st.success(f"'{course['title']}' kursuna başarıyla kaydoldunuz!")
                            st.rerun()
                        else:
                            st.error("Kayıt sırasında hata oluştu.")


# ==========================================
# TEACHER DASHBOARD
# ==========================================
elif st.session_state.user["role"] == "teacher":
    teacher_id = st.session_state.user["id"]
    
    st.markdown(f'<div class="hero-banner"><h1 class="hero-title">Eğitmen Yönetim Paneli</h1><p class="hero-subtitle">Hoş geldiniz, {st.session_state.user["username"]}. Kurslarınızı, materyallerinizi yönetebilir ve öğrenci ödevlerini değerlendirebilirsiniz.</p></div>', unsafe_allow_html=True)
    
    tab_my_courses, tab_create_course = st.tabs(["🛠️ Derslerim & Yönetim", "➕ Yeni Ders Oluştur"])
    
    # 1. TEACHER'S COURSES MANAGEMENT
    with tab_my_courses:
        t_res = requests.get(f"{API_URL}/courses?teacher_id={teacher_id}")
        teacher_courses = t_res.json() if t_res.status_code == 200 else []
        
        if not teacher_courses:
            st.info("Henüz oluşturduğunuz bir ders yok. 'Yeni Ders Oluştur' sekmesini kullanabilirsiniz.")
        else:
            course_options = {c["title"]: c for c in teacher_courses}
            selected_course_title = st.selectbox("Yönetmek istediğiniz dersi seçin:", list(course_options.keys()))
            selected_course = course_options[selected_course_title]
            
            st.divider()
            st.subheader(f"Ders: {selected_course['title']}")
            st.write(selected_course["description"])
            
            subtab_add_material, subtab_evaluate_submissions = st.tabs(["📄 Materyal Ekle", "📝 Öğrenci Ödev Değerlendirmeleri"])
            
            # Subtab: Add Material
            with subtab_add_material:
                st.subheader("Yeni Materyal Ekle")
                with st.form("add_material_form"):
                    m_title = st.text_input("Materyal Başlığı", placeholder="Örn: Hafta 1 - Giriş Ders Notları")
                    m_content = st.text_area("Materyal Metni", height=200, placeholder="Öğrencilerin okuyacağı ve yapay zekânın özetleyebileceği ders içeriğini buraya girin...")
                    submit_material = st.form_submit_button("Materyali Yayınla")
                    
                    if submit_material:
                        if not m_title or not m_content:
                            st.error("Başlık ve içerik boş olamaz.")
                        else:
                            mat_post_res = requests.post(
                                f"{API_URL}/courses/{selected_course['id']}/materials?teacher_id={teacher_id}",
                                json={"title": m_title, "content": m_content}
                            )
                            if mat_post_res.status_code == 201:
                                st.success("Ders materyali başarıyla yayınlandı!")
                            else:
                                st.error("Materyal eklenirken hata oluştu.")
                                
                # List existing materials for reference
                st.subheader("Mevcut Materyaller")
                mat_list_res = requests.get(f"{API_URL}/courses/{selected_course['id']}/materials")
                existing_mats = mat_list_res.json() if mat_list_res.status_code == 200 else []
                if not existing_mats:
                    st.info("Bu derse henüz materyal eklenmemiş.")
                else:
                    for emat in existing_mats:
                        st.text(f"• {emat['title']} ({emat['created_at'].split('T')[0]})")
            
            # Subtab: Evaluate Student Submissions
            with subtab_evaluate_submissions:
                st.subheader("Ödev Değerlendirme & AI Analizleri")
                
                # Fetch submissions for this course
                sub_res = requests.get(f"{API_URL}/courses/{selected_course['id']}/submissions")
                submissions = sub_res.json() if sub_res.status_code == 200 else []
                
                if not submissions:
                    st.info("Bu derse henüz ödev gönderimi yapılmamış.")
                else:
                    for i, sub in enumerate(submissions):
                        # Fetch student username
                        std_res = requests.get(f"{API_URL}/users/{sub['student_id']}")
                        student_name = std_res.json()["username"] if std_res.status_code == 200 else f"Öğrenci #{sub['student_id']}"
                        
                        submitted_date = sub["submitted_at"].split("T")[0]
                        
                        with st.expander(f"👤 Öğrenci: {student_name} | Tarih: {submitted_date} | Not: {sub['grade']}"):
                            st.markdown("**Öğrencinin Gönderdiği Metin:**")
                            st.text_area("İçerik", sub["text_content"], height=150, disabled=True, key=f"t_sub_txt_{i}")
                            
                            st.divider()
                            st.markdown("#### Yapay Zekâ Analiz Raporu")
                            st.markdown(sub["ai_feedback"])
                            
                            # Option to re-trigger AI Analysis
                            st.divider()
                            st.markdown("##### ⚙️ Yapay Zekâyı Yeniden Çalıştır")
                            if st.button("Yeniden Analiz Et", key=f"re_eval_{sub['id']}"):
                                with st.spinner("Yapay zekâ analizi yenileniyor..."):
                                    re_res = requests.post(
                                        f"{API_URL}/submissions/{sub['id']}/reanalyze",
                                        json={
                                            "text_content": sub["text_content"],
                                            "course_title": selected_course["title"],
                                            "provider": st.session_state.api_provider,
                                            "api_key": st.session_state.api_key
                                        }
                                    )
                                    if re_res.status_code == 200:
                                        st.success("Yapay zekâ analizi başarıyla yenilendi!")
                                        st.rerun()
                                    else:
                                        st.error("Yeniden analiz yapılamadı.")
                                        
    # 2. CREATE NEW COURSE
    with tab_create_course:
        st.subheader("Yeni Ders Oluştur")
        with st.form("create_course_form"):
            c_title = st.text_input("Ders Başlığı", placeholder="Örn: Python Programlamaya Giriş")
            c_desc = st.text_area("Ders Açıklaması", placeholder="Bu dersin hedefleri ve müfredatı hakkında bilgi girin...")
            submit_course = st.form_submit_button("Dersi Kaydet ve Yayına Al")
            
            if submit_course:
                if not c_title:
                    st.error("Ders başlığı boş olamaz.")
                else:
                    course_post_res = requests.post(
                        f"{API_URL}/courses?teacher_id={teacher_id}",
                        json={"title": c_title, "description": c_desc}
                    )
                    if course_post_res.status_code == 201:
                        st.success(f"'{c_title}' dersi başarıyla oluşturuldu!")
                        st.rerun()
                    else:
                        st.error("Ders oluşturulurken hata oluştu.")
