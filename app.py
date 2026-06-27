import streamlit as st
import os
from dotenv import load_dotenv

# Database and Models
from database import SessionLocal, init_db, hash_password, verify_password
import models
import ai_service

# Load env variables if they exist
load_dotenv()

# Initialize DB on first run in Streamlit
@st.cache_resource
def setup_database():
    init_db()
    return True

setup_database()

# DB Helper
def get_session():
    return SessionLocal()

# Page configuration
st.set_page_config(
    page_title="EduAI - Akıllı LMS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            placeholder="Anahtar girilmezse .env veya Mock AI kullanılır"
        )
        st.session_state.api_key = custom_key
        
        st.divider()
        if st.button("Çıkış Yap", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
            
    else:
        st.info("Devam etmek için giriş yapın veya yeni bir hesap oluşturun.")

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
                    db = get_session()
                    try:
                        db_user = db.query(models.User).filter(models.User.username == l_username).first()
                        if not db_user or not verify_password(l_password, db_user.password_hash):
                            st.error("Geçersiz kullanıcı adı veya şifre.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = {
                                "id": db_user.id,
                                "username": db_user.username,
                                "role": db_user.role
                            }
                            st.success("Giriş başarılı!")
                            st.rerun()
                    finally:
                        db.close()
                        
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
                    db = get_session()
                    try:
                        existing = db.query(models.User).filter(models.User.username == r_username).first()
                        if existing:
                            st.error("Bu kullanıcı adı zaten alınmış.")
                        else:
                            hashed_pwd = hash_password(r_password)
                            new_user = models.User(username=r_username, password_hash=hashed_pwd, role=r_role)
                            db.add(new_user)
                            db.commit()
                            st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                    finally:
                        db.close()

# ==========================================
# STUDENT DASHBOARD
# ==========================================
elif st.session_state.user["role"] == "student":
    student_id = st.session_state.user["id"]
    
    st.markdown(f'<div class="hero-banner"><h1 class="hero-title">Öğrenci Paneli</h1><p class="hero-subtitle">Hoş geldin, {st.session_state.user["username"]}! Derslerini ve ödevlerini buradan takip edebilirsin.</p></div>', unsafe_allow_html=True)
    
    tab_my_courses, tab_all_courses = st.tabs(["📚 Kayıtlı Derslerim", "🔍 Tüm Kursları Keşfet"])
    
    # 1. MY COURSES TAB
    with tab_my_courses:
        db = get_session()
        try:
            my_courses_db = db.query(models.Course).join(models.Enrollment).filter(models.Enrollment.student_id == student_id).all()
            my_courses = [{"id": c.id, "title": c.title, "description": c.description} for c in my_courses_db]
            
            if not my_courses:
                st.info("Henüz hiçbir kursa kayıtlı değilsiniz. 'Tüm Kursları Keşfet' sekmesinden kaydolabilirsiniz.")
            else:
                course_options = {c["title"]: c for c in my_courses}
                selected_course_title = st.selectbox("Detayları görüntülemek için bir ders seçin:", list(course_options.keys()))
                selected_course = course_options[selected_course_title]
                
                st.divider()
                st.subheader(selected_course["title"])
                st.write(selected_course["description"])
                
                subtab_materials, subtab_assignments = st.tabs(["📖 Ders Materyalleri", "📝 Ödev Gönderimi"])
                
                # Subtab: Materials
                with subtab_materials:
                    materials_db = db.query(models.Material).filter(models.Material.course_id == selected_course["id"]).all()
                    materials = [{"id": m.id, "title": m.title, "content": m.content} for m in materials_db]
                    
                    if not materials:
                        st.info("Bu ders için henüz materyal yüklenmemiş.")
                    else:
                        for mat in materials:
                            with st.expander(f"📄 {mat['title']}"):
                                st.write(mat['content'])
                                
                                st.markdown("---")
                                if st.button("🤖 Yapay Zekâ ile Özetle", key=f"sum_{mat['id']}"):
                                    with st.spinner("Özet hazırlanıyor..."):
                                        summary = ai_service.summarize_text(
                                            text=mat['content'],
                                            provider=st.session_state.api_provider,
                                            api_key=st.session_state.api_key
                                        )
                                        st.info("### Yapay Zekâ Özeti")
                                        st.markdown(summary)
                                            
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
                                    analysis = ai_service.analyze_submission(
                                        text_content=essay_text,
                                        course_title=selected_course["title"],
                                        provider=st.session_state.api_provider,
                                        api_key=st.session_state.api_key
                                    )
                                    
                                    new_sub = models.Submission(
                                        student_id=student_id,
                                        course_id=selected_course["id"],
                                        text_content=essay_text,
                                        ai_feedback=analysis.get("feedback"),
                                        grade=analysis.get("grade")
                                    )
                                    db.add(new_sub)
                                    db.commit()
                                    db.refresh(new_sub)
                                    
                                    st.success("Ödeviniz başarıyla teslim edildi ve analiz edildi!")
                                    st.session_state.last_submission = {
                                        "grade": new_sub.grade,
                                        "ai_feedback": new_sub.ai_feedback
                                    }
                                        
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
                    submissions_db = db.query(models.Submission).filter(
                        models.Submission.course_id == selected_course["id"],
                        models.Submission.student_id == student_id
                    ).order_by(models.Submission.submitted_at.desc()).all()
                    
                    if not submissions_db:
                        st.info("Bu ders için geçmiş bir ödev gönderiniz bulunmamaktadır.")
                    else:
                        for i, sub in enumerate(submissions_db):
                            date_str = str(sub.submitted_at).split(" ")[0]
                            with st.expander(f"📅 Teslim Tarihi: {date_str} - Not: {sub.grade}"):
                                st.text_area("Gönderilen Metin", sub.text_content, height=100, disabled=True, key=f"hist_txt_{i}")
                                st.markdown("#### AI Değerlendirmesi ve Geribildirim")
                                st.markdown(sub.ai_feedback)
        finally:
            db.close()

    # 2. ALL COURSES TAB
    with tab_all_courses:
        db = get_session()
        try:
            all_courses_db = db.query(models.Course).all()
            my_course_ids = [c.id for c in db.query(models.Enrollment).filter(models.Enrollment.student_id == student_id).all()]
            
            if not all_courses_db:
                st.info("Sistemde henüz kurs bulunmamaktadır.")
            else:
                for course in all_courses_db:
                    st.markdown(f"""
                    <div class="course-card">
                        <h3>{course.title}</h3>
                        <p>{course.description or 'Açıklama bulunmuyor.'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if course.id in my_course_ids:
                        st.button("Zaten Kayıtlısınız", key=f"enroll_btn_{course.id}", disabled=True)
                    else:
                        if st.button("Kursa Kaydol", key=f"enroll_btn_{course.id}"):
                            new_enrollment = models.Enrollment(student_id=student_id, course_id=course.id)
                            db.add(new_enrollment)
                            db.commit()
                            st.success(f"'{course.title}' kursuna başarıyla kaydoldunuz!")
                            st.rerun()
        finally:
            db.close()


# ==========================================
# TEACHER DASHBOARD
# ==========================================
elif st.session_state.user["role"] == "teacher":
    teacher_id = st.session_state.user["id"]
    
    st.markdown(f'<div class="hero-banner"><h1 class="hero-title">Eğitmen Yönetim Paneli</h1><p class="hero-subtitle">Hoş geldiniz, {st.session_state.user["username"]}. Kurslarınızı, materyallerinizi yönetebilir ve öğrenci ödevlerini değerlendirebilirsiniz.</p></div>', unsafe_allow_html=True)
    
    tab_my_courses, tab_create_course = st.tabs(["🛠️ Derslerim & Yönetim", "➕ Yeni Ders Oluştur"])
    
    # 1. TEACHER'S COURSES MANAGEMENT
    with tab_my_courses:
        db = get_session()
        try:
            teacher_courses_db = db.query(models.Course).filter(models.Course.teacher_id == teacher_id).all()
            teacher_courses = [{"id": c.id, "title": c.title, "description": c.description} for c in teacher_courses_db]
            
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
                                new_mat = models.Material(course_id=selected_course["id"], title=m_title, content=m_content)
                                db.add(new_mat)
                                db.commit()
                                st.success("Ders materyali başarıyla yayınlandı!")
                                    
                    st.subheader("Mevcut Materyaller")
                    existing_mats = db.query(models.Material).filter(models.Material.course_id == selected_course["id"]).all()
                    if not existing_mats:
                        st.info("Bu derse henüz materyal eklenmemiş.")
                    else:
                        for emat in existing_mats:
                            date_str = str(emat.created_at).split(" ")[0]
                            st.text(f"• {emat.title} ({date_str})")
                
                # Subtab: Evaluate Student Submissions
                with subtab_evaluate_submissions:
                    st.subheader("Ödev Değerlendirme & AI Analizleri")
                    
                    submissions_db = db.query(models.Submission).filter(models.Submission.course_id == selected_course["id"]).all()
                    
                    if not submissions_db:
                        st.info("Bu derse henüz ödev gönderimi yapılmamış.")
                    else:
                        for i, sub in enumerate(submissions_db):
                            student_db = db.query(models.User).filter(models.User.id == sub.student_id).first()
                            student_name = student_db.username if student_db else f"Öğrenci #{sub.student_id}"
                            submitted_date = str(sub.submitted_at).split(" ")[0]
                            
                            with st.expander(f"👤 Öğrenci: {student_name} | Tarih: {submitted_date} | Not: {sub.grade}"):
                                st.markdown("**Öğrencinin Gönderdiği Metin:**")
                                st.text_area("İçerik", sub.text_content, height=150, disabled=True, key=f"t_sub_txt_{i}")
                                
                                st.divider()
                                st.markdown("#### Yapay Zekâ Analiz Raporu")
                                st.markdown(sub.ai_feedback)
                                
                                st.divider()
                                st.markdown("##### ⚙️ Yapay Zekâyı Yeniden Çalıştır")
                                if st.button("Yeniden Analiz Et", key=f"re_eval_{sub.id}"):
                                    with st.spinner("Yapay zekâ analizi yenileniyor..."):
                                        analysis = ai_service.analyze_submission(
                                            text_content=sub.text_content,
                                            course_title=selected_course["title"],
                                            provider=st.session_state.api_provider,
                                            api_key=st.session_state.api_key
                                        )
                                        sub.ai_feedback = analysis.get("feedback")
                                        sub.grade = analysis.get("grade")
                                        db.commit()
                                        st.success("Yapay zekâ analizi başarıyla yenilendi!")
                                        st.rerun()
        finally:
            db.close()
                                        
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
                    db = get_session()
                    try:
                        new_course = models.Course(title=c_title, description=c_desc, teacher_id=teacher_id)
                        db.add(new_course)
                        db.commit()
                        st.success(f"'{c_title}' dersi başarıyla oluşturuldu!")
                        st.rerun()
                    finally:
                        db.close()
