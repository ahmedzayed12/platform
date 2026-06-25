
# -*- coding: utf-8 -*-
"""
منصة تتبع مخرجات الخريجين وقياس أثر التعليم
Streamlit + SQLite

تشغيل:
    streamlit run app.py
"""
from __future__ import annotations

import io
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# إعدادات عامة
# -----------------------------------------------------------------------------
APP_TITLE = "منصة تتبع مخرجات الخريجين وقياس أثر التعليم"
APP_SUBTITLE = "نظام مؤسسي لمتابعة الخريجين، قياس جودة البرامج، ودعم قرارات التطوير والاعتماد الأكاديمي"
DB_PATH = Path(__file__).with_name("graduates_platform.db")

STATUS_OPTIONS = ["موظف", "صاحب مشروع خاص", "باحث عن عمل", "طالب دراسات عليا", "متقاعد", "غير ذلك"]
GENDER_OPTIONS = ["غير محدد", "ذكر", "أنثى"]
GRADE_OPTIONS = ["ممتاز", "جيد جدًا", "جيد", "مقبول", "غير محدد"]
SECTOR_OPTIONS = ["غير محدد", "عام", "خاص", "أهلي/غير ربحي", "دولي", "عمل حر"]
RELATED_OPTIONS = ["نعم", "جزئيًا", "لا", "غير محدد"]
ROLE_OPTIONS = ["إدارة الجامعة", "مكتب الجودة والاعتماد", "رئيس قسم", "منسق خريجين", "باحث/صانع قرار"]
COUNTRIES = ["مصر", "السعودية", "الإمارات", "قطر", "الكويت", "ألمانيا", "المملكة المتحدة", "الولايات المتحدة", "أخرى"]
CITIES = ["القاهرة", "الإسكندرية", "الجيزة", "المنصورة", "طنطا", "أسيوط", "السويس", "دبي", "الرياض", "الدوحة", "برلين", "أخرى"]

COLLEGES = [
    "كلية الطب", "كلية الهندسة", "كلية الحاسبات والمعلومات", "كلية التجارة", "كلية العلوم",
    "كلية الآداب", "كلية التربية", "كلية الصيدلة", "كلية طب الأسنان", "كلية التمريض", "كلية الحقوق", "أخرى",
]

DEPARTMENTS_BY_COLLEGE = {
    "كلية الطب": ["باطنة", "جراحة", "أطفال", "نساء وتوليد", "صحة عامة", "أخرى"],
    "كلية الهندسة": ["معماري", "مدني", "كهرباء", "ميكانيكا", "اتصالات", "حاسبات", "أخرى"],
    "كلية الحاسبات والمعلومات": ["علوم حاسب", "نظم معلومات", "ذكاء اصطناعي", "هندسة برمجيات", "أخرى"],
    "كلية التجارة": ["محاسبة", "إدارة أعمال", "اقتصاد", "إحصاء", "تسويق", "أخرى"],
    "كلية العلوم": ["كيمياء", "فيزياء", "رياضيات", "جيولوجيا", "علوم حيوية", "أخرى"],
    "كلية الآداب": ["لغة عربية", "لغة إنجليزية", "تاريخ", "جغرافيا", "علم نفس", "أخرى"],
    "كلية التربية": ["تعليم أساسي", "مناهج وطرق تدريس", "تربية خاصة", "أخرى"],
    "كلية الصيدلة": ["صيدلة إكلينيكية", "كيمياء صيدلية", "فارماكولوجي", "أخرى"],
    "كلية طب الأسنان": ["علاج تحفظي", "جراحة فم", "تقويم", "أخرى"],
    "كلية التمريض": ["تمريض باطني وجراحي", "تمريض أطفال", "تمريض مسنين", "أخرى"],
    "كلية الحقوق": ["قانون عام", "قانون خاص", "شريعة", "أخرى"],
    "أخرى": ["أخرى"],
}

AR_COLS: Dict[str, str] = {
    "id": "رقم السجل",
    "national_id": "الرقم التعريفي",
    "full_name": "اسم الخريج",
    "email": "البريد الإلكتروني",
    "phone": "الهاتف",
    "gender": "النوع",
    "college": "الكلية",
    "department": "القسم",
    "major": "التخصص",
    "graduation_year": "سنة التخرج",
    "grade": "التقدير",
    "current_status": "الحالة الحالية",
    "employer": "جهة العمل",
    "job_title": "المسمى الوظيفي",
    "employment_sector": "قطاع العمل",
    "employment_start_date": "تاريخ بداية العمل",
    "job_related_to_major": "ارتباط العمل بالتخصص",
    "business_name": "اسم المشروع",
    "business_activity": "نشاط المشروع",
    "business_start_year": "سنة تأسيس المشروع",
    "business_employees": "عدد العاملين بالمشروع",
    "postgraduate_program": "برنامج الدراسات العليا",
    "first_job_months": "أشهر حتى أول وظيفة",
    "monthly_income": "الدخل الشهري",
    "country": "الدولة",
    "city": "المدينة",
    "last_update": "آخر تحديث",
    "notes": "ملاحظات",
    "created_at": "تاريخ الإدخال",
    "survey_date": "تاريخ الاستبيان",
    "scientific_knowledge": "المعرفة العلمية",
    "technical_skills": "المهارات التقنية",
    "communication_skills": "مهارات الاتصال",
    "leadership_skills": "مهارات القيادة",
    "problem_solving": "حل المشكلات",
    "overall_satisfaction": "الرضا العام",
    "curriculum_relevance": "ملاءمة المنهج",
    "missing_skills": "مهارات ناقصة",
    "comments": "تعليقات",
    "outcome_score": "مؤشر المخرجات",
    "risk_level": "مستوى المخاطر",
    "recommendation": "التوصية",
    "employment_rate": "معدل التوظيف",
    "related_rate": "معدل العمل داخل التخصص",
    "entrepreneurship_rate": "معدل ريادة الأعمال",
    "postgraduate_rate": "معدل الدراسات العليا",
    "avg_satisfaction": "متوسط الرضا",
    "avg_first_job_months": "متوسط مدة الحصول على أول وظيفة",
    "graduates_count": "عدد الخريجين",
}

# -----------------------------------------------------------------------------
# تهيئة الصفحة والاتجاه العربي
# -----------------------------------------------------------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

        :root {
            --primary: #1e3a8a;
            --primary-2: #0f766e;
            --ink: #0f172a;
            --muted: #64748b;
            --line: #e2e8f0;
            --soft: #f8fafc;
            --soft-blue: #eff6ff;
            --danger-soft: #fef2f2;
            --warning-soft: #fffbeb;
            --success-soft: #f0fdf4;
        }

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
        [data-testid="stMarkdownContainer"], [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {
            direction: rtl !important;
            text-align: right !important;
            font-family: 'Cairo', 'Tahoma', 'Arial', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6, p, li, label, span, div, button {
            font-family: 'Cairo', 'Tahoma', 'Arial', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6, p, li, label {
            direction: rtl !important;
            text-align: right !important;
        }

        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #1e3a8a 56%, #0f766e 100%);
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
            direction: rtl !important;
            text-align: right !important;
        }
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.12) !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-weight: 800 !important;
            opacity: 1 !important;
            visibility: visible !important;
            height: auto !important;
            display: block !important;
        }
        [data-testid="stSidebar"] .sidebar-label {
            color: #ffffff !important;
            font-weight: 900 !important;
            margin: 12px 0 6px 0;
            font-size: .92rem;
            line-height: 1.7;
        }
        [data-testid="stSidebar"] .sidebar-help {
            color: rgba(255,255,255,.82) !important;
            font-size: .78rem;
            line-height: 1.7;
            margin: -2px 0 8px 0;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #0f172a !important;
            background-color: #ffffff !important;
        }
        [data-testid="stSidebar"] [data-baseweb="checkbox"] * {
            color: #ffffff !important;
        }

        .hero {
            background: radial-gradient(circle at top left, rgba(56,189,248,.25), transparent 28%),
                        linear-gradient(135deg, #0f172a 0%, #1e3a8a 48%, #0f766e 100%);
            border-radius: 28px;
            padding: 30px 34px;
            color: white;
            margin-bottom: 18px;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.20);
            border: 1px solid rgba(255,255,255,0.12);
        }
        .hero h1 {font-size: 2.1rem; margin: 0 0 10px 0; font-weight: 900; color: white;}
        .hero p {font-size: 1.04rem; margin: 0; color: #e2e8f0; line-height: 1.95;}

        .mini-title {
            font-size: .82rem;
            color: #64748b;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .section-title {
            font-weight: 900;
            color: var(--ink);
            margin: 8px 0 4px;
            font-size: 1.28rem;
        }
        .section-subtitle {
            color: var(--muted);
            margin-bottom: 14px;
            line-height: 1.85;
        }
        .chart-title {
            display: block;
            width: 100%;
            background: #ffffff;
            border: 1px solid var(--line);
            border-bottom: 0;
            border-radius: 18px 18px 0 0;
            padding: 12px 16px 4px 16px;
            margin: 10px 0 0 0;
            font-weight: 900;
            font-size: 1.02rem;
            color: var(--ink);
            direction: rtl !important;
            text-align: right !important;
            line-height: 1.8;
            clear: both;
        }
        .chart-note {
            color: #64748b;
            font-size: .78rem;
            margin-top: 2px;
            font-weight: 600;
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 18px 18px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
            min-height: 126px;
        }
        .metric-label {font-size: 0.86rem; color: #64748b; font-weight: 800;}
        .metric-value {font-size: 1.85rem; color: var(--ink); font-weight: 900; margin-top: 6px; direction: ltr !important; text-align: right !important;}
        .metric-note {font-size: 0.78rem; color: #94a3b8; margin-top: 6px; line-height: 1.6;}
        .soft-box {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 18px 20px;
            line-height: 1.95;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        .info-box {background: #eff6ff; border-color:#bfdbfe;}
        .success-box {background: #f0fdf4; border-color:#bbf7d0;}
        .warning-box {background: #fffbeb; border-color:#fde68a;}
        .danger-box {background: #fef2f2; border-color:#fecaca;}
        .pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
            font-size: .82rem;
            font-weight: 800;
            margin: 3px 0 3px 6px;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            direction: rtl !important;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff;
            border-radius: 14px;
            padding: 10px 16px;
            border: 1px solid var(--line);
            font-weight: 800;
        }
        .stTabs [aria-selected="true"] {
            background: #dbeafe !important;
            border-color: #93c5fd !important;
            color: #1e3a8a !important;
        }

        .stTextInput input, .stNumberInput input, .stDateInput input, textarea,
        [data-baseweb="select"] div, [data-baseweb="input"] input {
            direction: rtl !important;
            text-align: right !important;
            unicode-bidi: plaintext !important;
        }
        input[type="text"], input[type="email"], input[type="tel"], textarea {
            direction: rtl !important;
            text-align: right !important;
        }
        .stButton button, .stDownloadButton button {
            border-radius: 12px !important;
            font-weight: 800 !important;
            direction: rtl !important;
        }
        .stDataFrame, [data-testid="stDataFrame"], [data-testid="stTable"] {
            direction: rtl !important;
            text-align: right !important;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border-radius: 16px;
            padding: 12px 14px;
            border: 1px solid var(--line);
            box-shadow: 0 8px 20px rgba(15,23,42,0.04);
        }
        div[data-testid="stMetricValue"] {direction:ltr !important; text-align:right !important; font-weight:900;}
        .js-plotly-plot, .plot-container, .svg-container {direction:ltr !important; overflow: visible !important;}
        .js-plotly-plot .svg-container {overflow: visible !important;}
        hr {border: 0; border-top: 1px solid #e2e8f0; margin: 22px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# قاعدة البيانات
# -----------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS graduates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            gender TEXT,
            college TEXT,
            department TEXT,
            major TEXT,
            graduation_year INTEGER,
            grade TEXT,
            current_status TEXT,
            employer TEXT,
            job_title TEXT,
            employment_sector TEXT,
            employment_start_date TEXT,
            job_related_to_major TEXT,
            business_name TEXT,
            business_activity TEXT,
            business_start_year INTEGER,
            business_employees INTEGER,
            postgraduate_program TEXT,
            first_job_months INTEGER,
            monthly_income REAL,
            country TEXT,
            city TEXT,
            last_update TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            graduate_id INTEGER NOT NULL,
            survey_date TEXT NOT NULL,
            scientific_knowledge INTEGER,
            technical_skills INTEGER,
            communication_skills INTEGER,
            leadership_skills INTEGER,
            problem_solving INTEGER,
            overall_satisfaction INTEGER,
            curriculum_relevance INTEGER,
            missing_skills TEXT,
            comments TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (graduate_id) REFERENCES graduates(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            entity TEXT,
            entity_id INTEGER,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def log_action(action: str, entity: str, entity_id: Optional[int] = None, details: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log(action, entity, entity_id, details) VALUES (?, ?, ?, ?)",
        (action, entity, entity_id, details),
    )
    conn.commit()
    conn.close()


def clear_cache() -> None:
    try:
        st.cache_data.clear()
    except Exception:
        pass


@st.cache_data(show_spinner=False)
def load_graduates() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM graduates ORDER BY id DESC", conn)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_surveys() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT s.*, g.full_name, g.college, g.department, g.major, g.graduation_year, g.current_status
        FROM surveys s
        LEFT JOIN graduates g ON s.graduate_id = g.id
        ORDER BY s.survey_date DESC, s.id DESC
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_audit_log(limit: int = 250) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM audit_log ORDER BY id DESC LIMIT {int(limit)}", conn)
    conn.close()
    return df


def insert_graduate(row: Dict) -> Tuple[bool, str]:
    conn = get_connection()
    fields = [
        "national_id", "full_name", "email", "phone", "gender", "college", "department", "major",
        "graduation_year", "grade", "current_status", "employer", "job_title", "employment_sector",
        "employment_start_date", "job_related_to_major", "business_name", "business_activity",
        "business_start_year", "business_employees", "postgraduate_program", "first_job_months",
        "monthly_income", "country", "city", "last_update", "notes",
    ]
    values = [row.get(f) for f in fields]
    placeholders = ",".join(["?"] * len(fields))
    try:
        cur = conn.execute(f"INSERT INTO graduates({','.join(fields)}) VALUES ({placeholders})", values)
        conn.commit()
        log_action("إضافة", "graduate", cur.lastrowid, row.get("full_name", ""))
        return True, "تم حفظ الخريج بنجاح."
    except sqlite3.IntegrityError:
        return False, "تعذر الحفظ: الرقم التعريفي موجود مسبقًا."
    except Exception as exc:
        return False, f"تعذر الحفظ: {exc}"
    finally:
        conn.close()


def update_graduate(graduate_id: int, row: Dict) -> Tuple[bool, str]:
    conn = get_connection()
    fields = [
        "national_id", "full_name", "email", "phone", "gender", "college", "department", "major",
        "graduation_year", "grade", "current_status", "employer", "job_title", "employment_sector",
        "employment_start_date", "job_related_to_major", "business_name", "business_activity",
        "business_start_year", "business_employees", "postgraduate_program", "first_job_months",
        "monthly_income", "country", "city", "last_update", "notes",
    ]
    assignments = ", ".join([f"{f}=?" for f in fields])
    values = [row.get(f) for f in fields] + [graduate_id]
    try:
        conn.execute(f"UPDATE graduates SET {assignments} WHERE id=?", values)
        conn.commit()
        log_action("تعديل", "graduate", graduate_id, row.get("full_name", ""))
        return True, "تم تحديث بيانات الخريج بنجاح."
    except sqlite3.IntegrityError:
        return False, "تعذر التحديث: الرقم التعريفي مستخدم في سجل آخر."
    except Exception as exc:
        return False, f"تعذر التحديث: {exc}"
    finally:
        conn.close()


def delete_graduate(graduate_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM graduates WHERE id=?", (graduate_id,))
    conn.commit()
    conn.close()
    log_action("حذف", "graduate", graduate_id, "حذف سجل خريج")


def insert_survey(row: Dict) -> Tuple[bool, str]:
    conn = get_connection()
    fields = [
        "graduate_id", "survey_date", "scientific_knowledge", "technical_skills", "communication_skills",
        "leadership_skills", "problem_solving", "overall_satisfaction", "curriculum_relevance",
        "missing_skills", "comments",
    ]
    values = [row.get(f) for f in fields]
    try:
        cur = conn.execute(
            f"INSERT INTO surveys({','.join(fields)}) VALUES ({','.join(['?'] * len(fields))})", values
        )
        conn.commit()
        log_action("إضافة", "survey", cur.lastrowid, f"graduate_id={row.get('graduate_id')}")
        return True, "تم حفظ الاستبيان بنجاح."
    except Exception as exc:
        return False, f"تعذر حفظ الاستبيان: {exc}"
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# بيانات تجريبية قوية
# -----------------------------------------------------------------------------
def demo_records() -> pd.DataFrame:
    names = [
        "أحمد محمد عبدالعزيز", "سارة محمود حسن", "محمود إبراهيم علي", "نورهان خالد السيد", "يوسف طارق فؤاد",
        "ريم أشرف منصور", "عمر سامي عبدالرحمن", "منة الله عادل", "كريم وليد مصطفى", "هاجر عمرو فهيم",
        "محمد إيهاب عبدالسلام", "دينا أحمد مرسي", "مصطفى حاتم جلال", "مريم شريف كامل", "علي حسن عثمان",
        "ندى ياسر عبدالغني", "عبدالله عماد الدين", "بسمة طارق نصر", "زياد أحمد لطفي", "إسراء محمد فوزي",
        "إياد هشام راضي", "ملك أيمن فرج", "رامي خالد زكي", "جنى سامح لطفي", "حسام عادل شوقي",
        "سلمى أحمد ربيع", "فارس محمد سمير", "آية مصطفى جمال", "شريف عمرو حسن", "نور أحمد السعيد",
        "أمنية وليد نافع", "خالد محمود صابر", "هبة علاء توفيق", "أنس محمد البنا", "رنا شادي كمال",
        "ياسين أحمد فتحي", "ليلى كريم مراد", "مازن إيهاب صبحي", "تقى سامي نبيل", "حبيبة محمد الشاذلي",
        "أدهم طارق خليل", "سارة أيمن عطية", "محمد وائل قاسم", "روان أحمد منصور", "عمر هشام توفيق",
        "ملك شريف عادل", "أحمد علاء جابر", "فرح محمود بدوي", "يوسف خالد ناصر", "مريم عماد زهران",
        "عبدالرحمن سامي فرج", "جاسمين أحمد لطيف", "مروان حاتم السيد", "إيمان محمد غنيم", "فاطمة أشرف جاد",
        "طارق وليد شوقي", "رغدة أحمد ماهر", "سيف محمود فؤاد", "أسماء ياسر قاسم", "هشام علاء حسن",
        "مها خالد علي", "وليد محمد رأفت", "رانيا أحمد عبدالقادر", "باسم شريف حلمي", "نهى سامي رشدي",
        "أحمد ياسر خيري", "منة خالد عبدالوهاب", "علياء محمد فتح الله", "مروان سامح جابر", "داليا أشرف صبري",
        "رامز طارق عبدالمجيد", "إنجي محمد سالم", "إسلام محمود عرفة", "سندس أحمد رمضان", "أيمن شريف نصر",
        "لوجين خالد نبيل", "محمد أشرف عمر", "شهد وليد مراد", "حمزة سامي عبدالعظيم", "يمنى أحمد صادق",
    ]
    college_cycle = [
        ("كلية الحاسبات والمعلومات", "علوم حاسب", "تحليل بيانات"),
        ("كلية الهندسة", "مدني", "إدارة مشروعات"),
        ("كلية التجارة", "محاسبة", "محاسبة ومراجعة"),
        ("كلية الطب", "صحة عامة", "وبائيات"),
        ("كلية العلوم", "كيمياء", "كيمياء تطبيقية"),
        ("كلية الصيدلة", "صيدلة إكلينيكية", "صيدلة إكلينيكية"),
        ("كلية الآداب", "لغة إنجليزية", "ترجمة"),
        ("كلية التمريض", "تمريض مسنين", "رعاية حرجة"),
        ("كلية الحقوق", "قانون خاص", "قانون تجاري"),
        ("كلية التربية", "مناهج وطرق تدريس", "تكنولوجيا تعليم"),
    ]
    employers = [
        "بنك مصر", "شركة فودافون مصر", "مستشفى جامعي", "شركة المقاولون العرب", "مكتب محاسبة دولي",
        "وزارة الصحة", "شركة برمجيات ناشئة", "مدرسة دولية", "شركة أدوية", "مكتب استشارات هندسية",
        "شركة اتصالات", "هيئة حكومية", "شركة تجارة إلكترونية", "مركز أبحاث", "جامعة خاصة",
    ]
    jobs = [
        "محلل بيانات", "مهندس موقع", "محاسب", "أخصائي جودة", "كيميائي", "صيدلي إكلينيكي",
        "مترجم", "ممرض رعاية مركزة", "محامٍ", "مصمم محتوى تعليمي", "مدير مشروع", "باحث مساعد",
        "أخصائي موارد بشرية", "مطور برمجيات", "مسؤول تسويق رقمي",
    ]
    statuses = ["موظف", "موظف", "موظف", "صاحب مشروع خاص", "باحث عن عمل", "طالب دراسات عليا", "موظف", "موظف", "صاحب مشروع خاص", "موظف"]
    rows = []
    for i, name in enumerate(names, start=1):
        college, dept, major = college_cycle[(i - 1) % len(college_cycle)]
        status = statuses[(i + (i // 7)) % len(statuses)]
        gender = "أنثى" if any(token in name for token in ["سارة", "نورهان", "ريم", "منة", "هاجر", "دينا", "مريم", "ندى", "بسمة", "إسراء", "ملك", "جنى", "سلمى", "آية", "نور", "أمنية", "هبة", "رنا", "ليلى", "تقى", "حبيبة", "روان", "فرح", "إيمان", "فاطمة", "رغدة", "أسماء", "مها", "رانيا", "نهى", "علياء", "داليا", "إنجي", "سندس", "لوجين", "شهد", "يمنى"]) else "ذكر"
        year = 2019 + (i % 6)
        related = ["نعم", "نعم", "جزئيًا", "لا", "نعم", "جزئيًا"][(i * 3) % 6]
        if status == "باحث عن عمل":
            employer, job_title, sector, related, start_date, months, income = "", "", "غير محدد", "غير محدد", "", None, None
        elif status == "طالب دراسات عليا":
            employer, job_title, sector, start_date, months, income = "جامعة أو مركز بحثي", "باحث دراسات عليا", "أكاديمي", f"{year+1}-10-01", 8 + (i % 9), 9000 + (i % 10) * 1200
        else:
            employer, job_title, sector = employers[i % len(employers)], jobs[i % len(jobs)], SECTOR_OPTIONS[(i % 5) + 1]
            start_date = f"{min(year + 1, 2025)}-{((i % 9)+1):02d}-15"
            months = 2 + ((i * 5) % 22)
            income = 6500 + (i % 18) * 1750
        business_name = business_activity = ""
        business_year = None
        business_employees = None
        if status == "صاحب مشروع خاص":
            business_name = f"مشروع {major} - {name.split()[0]}"
            business_activity = ["تطبيقات رقمية", "خدمات استشارية", "تجارة إلكترونية", "مستلزمات طبية", "تعليم وتدريب"][(i % 5)]
            business_year = year + 1
            business_employees = 2 + (i % 14)
            employer = "مشروع خاص"
            job_title = "مؤسس / مدير مشروع"
            sector = "عمل حر"
            months = 3 + (i % 12)
            income = 12000 + (i % 20) * 1400
        postgraduate_program = ""
        if status == "طالب دراسات عليا" or i % 9 == 0:
            postgraduate_program = ["ماجستير مهني", "دبلوم جودة", "ماجستير بحثي", "دكتوراه", "زمالة مهنية"][i % 5]
        rows.append({
            "national_id": f"GR-{2020 + (i % 6)}-{i:04d}",
            "full_name": name,
            "email": f"graduate{i:03d}@university.edu.eg",
            "phone": f"010{70000000+i:08d}"[:11],
            "gender": gender,
            "college": college,
            "department": dept,
            "major": major,
            "graduation_year": year,
            "grade": GRADE_OPTIONS[i % 4],
            "current_status": status,
            "employer": employer,
            "job_title": job_title,
            "employment_sector": sector,
            "employment_start_date": start_date,
            "job_related_to_major": related,
            "business_name": business_name,
            "business_activity": business_activity,
            "business_start_year": business_year,
            "business_employees": business_employees,
            "postgraduate_program": postgraduate_program,
            "first_job_months": months,
            "monthly_income": income,
            "country": COUNTRIES[i % 6],
            "city": CITIES[i % 11],
            "last_update": f"2026-{((i % 6)+1):02d}-{((i % 25)+1):02d}",
            "notes": "بيانات تجريبية لغرض العرض والتحليل" if i % 5 == 0 else "",
        })
    return pd.DataFrame(rows)


def demo_surveys_from_db() -> List[Dict]:
    df = load_graduates()
    surveys = []
    if df.empty:
        return surveys
    for _, row in df.iterrows():
        gid = int(row["id"])
        base = 3 + (gid % 3)
        if row.get("current_status") == "باحث عن عمل":
            base = max(2, base - 1)
        related = row.get("job_related_to_major")
        relevance = 5 if related == "نعم" else 3 if related == "جزئيًا" else 2
        surveys.append({
            "graduate_id": gid,
            "survey_date": f"2026-{((gid % 6)+1):02d}-{((gid % 24)+1):02d}",
            "scientific_knowledge": min(5, base),
            "technical_skills": min(5, base + (gid % 2)),
            "communication_skills": max(1, min(5, base + ((gid + 1) % 2))),
            "leadership_skills": max(1, min(5, base - 1 + (gid % 3))),
            "problem_solving": min(5, base + 1),
            "overall_satisfaction": max(1, min(5, base + (1 if related == "نعم" else 0))),
            "curriculum_relevance": relevance,
            "missing_skills": ["تحليل بيانات", "لغة إنجليزية", "مهارات سوق العمل", "إدارة مشاريع", "تدريب عملي"][gid % 5],
            "comments": "تحتاج المناهج إلى تدريب عملي أكثر" if gid % 4 == 0 else "تجربة تعليمية جيدة بوجه عام",
        })
    return surveys


def seed_demo_data(reset: bool = False) -> None:
    conn = get_connection()
    if reset:
        conn.execute("DELETE FROM surveys")
        conn.execute("DELETE FROM graduates")
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('graduates','surveys','audit_log')")
        conn.commit()
    current_count = conn.execute("SELECT COUNT(*) FROM graduates").fetchone()[0]
    conn.close()
    if current_count > 0 and not reset:
        return
    for row in demo_records().to_dict("records"):
        insert_graduate(row)
    for survey in demo_surveys_from_db():
        insert_survey(survey)
    log_action("تهيئة", "system", None, "إضافة بيانات تجريبية كاملة للمنصة")
    clear_cache()

# -----------------------------------------------------------------------------
# أدوات مساعدة للعرض والتحليل
# -----------------------------------------------------------------------------
def ar_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = {c: AR_COLS.get(c, c) for c in df.columns}
    return df.rename(columns=cols)


def pct(numerator: float, denominator: float) -> float:
    if denominator in [0, None] or pd.isna(denominator):
        return 0.0
    return round((float(numerator) / float(denominator)) * 100, 1)


def format_pct(value: float) -> str:
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def date_to_str(value) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if pd.isna(value):
        return ""
    return str(value)


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_sheet = sheet_name[:31]
            ar_df(df).to_excel(writer, index=False, sheet_name=safe_sheet)
            ws = writer.book[safe_sheet]
            ws.sheet_view.rightToLeft = True
            for col in ws.columns:
                max_len = 12
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, min(45, len(str(cell.value)) + 2))
                ws.column_dimensions[col_letter].width = max_len
    return output.getvalue()


def build_markdown_report(title: str, intro: str, metrics: Dict[str, str], recommendations: List[str]) -> str:
    lines = [f"# {title}", "", intro, "", "## المؤشرات الرئيسية"]
    for key, val in metrics.items():
        lines.append(f"- **{key}:** {val}")
    lines += ["", "## التوصيات"]
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append(f"\nتم إنشاء التقرير بتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def apply_plotly_layout(fig, title: str = "", height: int = 430):
    """تنسيق موحد للرسوم بدون عنوان Plotly داخلي حتى لا تتداخل النصوص العربية.

    يتم عرض العنوان كعنصر HTML مستقل أعلى الرسم، لأن Plotly قد يضع العنوان
    والـ legend والـ labels في نفس المساحة عند استخدام RTL أو الشاشات الضيقة.
    """
    if title:
        st.markdown(f"<div class='chart-title'>{title}</div>", unsafe_allow_html=True)
    fig.update_layout(
        title=None,
        font={"family": "Cairo, Tahoma, Arial", "size": 12},
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 11},
        },
        margin={"l": 15, "r": 25, "t": 18, "b": 86},
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def filtered_df(df: pd.DataFrame, college: str, department: str, year_range: Tuple[int, int], status: List[str], search: str) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out
    if college != "الكل":
        out = out[out["college"] == college]
    if department != "الكل":
        out = out[out["department"] == department]
    if year_range:
        out = out[(pd.to_numeric(out["graduation_year"], errors="coerce") >= year_range[0]) & (pd.to_numeric(out["graduation_year"], errors="coerce") <= year_range[1])]
    if status:
        out = out[out["current_status"].isin(status)]
    if search.strip():
        s = search.strip().lower()
        searchable_cols = ["full_name", "national_id", "email", "phone", "college", "department", "major", "employer", "job_title"]
        mask = pd.Series(False, index=out.index)
        for col in searchable_cols:
            if col in out.columns:
                mask = mask | out[col].fillna("").astype(str).str.lower().str.contains(s, regex=False)
        out = out[mask]
    return out


def compute_overview(df: pd.DataFrame, surveys: pd.DataFrame) -> Dict[str, float]:
    total = len(df)
    employed = int((df["current_status"] == "موظف").sum()) if not df.empty else 0
    business = int((df["current_status"] == "صاحب مشروع خاص").sum()) if not df.empty else 0
    job_seekers = int((df["current_status"] == "باحث عن عمل").sum()) if not df.empty else 0
    postgrad = int((df["current_status"] == "طالب دراسات عليا").sum()) if not df.empty else 0
    active_success = employed + business + postgrad
    related = int(df["job_related_to_major"].isin(["نعم", "جزئيًا"]).sum()) if not df.empty else 0
    avg_months = pd.to_numeric(df.get("first_job_months"), errors="coerce").dropna().mean() if not df.empty else 0
    avg_income = pd.to_numeric(df.get("monthly_income"), errors="coerce").dropna().mean() if not df.empty else 0
    avg_satisfaction = pd.to_numeric(surveys.get("overall_satisfaction"), errors="coerce").dropna().mean() if not surveys.empty else 0
    return {
        "total": total,
        "employed": employed,
        "business": business,
        "job_seekers": job_seekers,
        "postgrad": postgrad,
        "employment_rate": pct(active_success, total),
        "direct_employment_rate": pct(employed, total),
        "entrepreneurship_rate": pct(business, total),
        "postgraduate_rate": pct(postgrad, total),
        "related_rate": pct(related, total),
        "avg_months": round(avg_months if pd.notna(avg_months) else 0, 1),
        "avg_income": round(avg_income if pd.notna(avg_income) else 0, 0),
        "avg_satisfaction": round(avg_satisfaction if pd.notna(avg_satisfaction) else 0, 2),
    }


def program_performance(df: pd.DataFrame, surveys: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    d["is_success"] = d["current_status"].isin(["موظف", "صاحب مشروع خاص", "طالب دراسات عليا"]).astype(int)
    d["is_employed"] = (d["current_status"] == "موظف").astype(int)
    d["is_business"] = (d["current_status"] == "صاحب مشروع خاص").astype(int)
    d["is_postgrad"] = (d["current_status"] == "طالب دراسات عليا").astype(int)
    d["is_related"] = d["job_related_to_major"].isin(["نعم", "جزئيًا"]).astype(int)
    d["first_job_months_num"] = pd.to_numeric(d["first_job_months"], errors="coerce")

    grouped = d.groupby(group_cols, dropna=False).agg(
        graduates_count=("id", "count"),
        employment_rate=("is_success", "mean"),
        direct_employment_rate=("is_employed", "mean"),
        entrepreneurship_rate=("is_business", "mean"),
        postgraduate_rate=("is_postgrad", "mean"),
        related_rate=("is_related", "mean"),
        avg_first_job_months=("first_job_months_num", "mean"),
    ).reset_index()

    for col in ["employment_rate", "direct_employment_rate", "entrepreneurship_rate", "postgraduate_rate", "related_rate"]:
        grouped[col] = (grouped[col] * 100).round(1)
    grouped["avg_first_job_months"] = grouped["avg_first_job_months"].fillna(0).round(1)

    if not surveys.empty:
        s = surveys.copy()
        survey_cols = ["overall_satisfaction", "curriculum_relevance", "technical_skills", "communication_skills", "problem_solving"]
        for c in survey_cols:
            s[c] = pd.to_numeric(s[c], errors="coerce")
        s_group = s.groupby(group_cols, dropna=False)[survey_cols].mean().reset_index()
        s_group["avg_satisfaction"] = s_group["overall_satisfaction"].round(2)
        s_group["avg_curriculum_relevance"] = s_group["curriculum_relevance"].round(2)
        s_group["avg_skills"] = s_group[["technical_skills", "communication_skills", "problem_solving"]].mean(axis=1).round(2)
        grouped = grouped.merge(s_group[group_cols + ["avg_satisfaction", "avg_curriculum_relevance", "avg_skills"]], on=group_cols, how="left")
    else:
        grouped["avg_satisfaction"] = 0
        grouped["avg_curriculum_relevance"] = 0
        grouped["avg_skills"] = 0

    grouped[["avg_satisfaction", "avg_curriculum_relevance", "avg_skills"]] = grouped[["avg_satisfaction", "avg_curriculum_relevance", "avg_skills"]].fillna(0)

    speed_score = 100 - grouped["avg_first_job_months"].clip(0, 24) / 24 * 100
    satisfaction_score = grouped["avg_satisfaction"] / 5 * 100
    skills_score = grouped["avg_skills"] / 5 * 100
    grouped["outcome_score"] = (
        grouped["employment_rate"] * 0.35 +
        grouped["related_rate"] * 0.25 +
        satisfaction_score * 0.20 +
        speed_score * 0.10 +
        skills_score * 0.10
    ).round(1)

    def risk(score: float) -> str:
        if score >= 80:
            return "منخفض"
        if score >= 65:
            return "متوسط"
        if score >= 50:
            return "مرتفع"
        return "حرج"

    def rec(row) -> str:
        if row["outcome_score"] >= 80:
            return "الحفاظ على الأداء وتوثيق الممارسات الجيدة للاعتماد والتسويق الأكاديمي."
        if row["related_rate"] < 55:
            return "تحديث توصيف المقررات وربط التدريب العملي بفرص سوق العمل داخل التخصص."
        if row["employment_rate"] < 60:
            return "تفعيل شراكات توظيف وتدريب ميداني ومراجعة المهارات المهنية المطلوبة."
        if row["avg_satisfaction"] < 3.2:
            return "مراجعة تجربة الطالب والخريج وتحسين جودة التدريس والإرشاد المهني."
        return "برنامج قابل للتحسين عبر مؤشرات متابعة نصف سنوية ومقارنة معيارية."

    grouped["risk_level"] = grouped["outcome_score"].apply(risk)
    grouped["recommendation"] = grouped.apply(rec, axis=1)
    return grouped.sort_values("outcome_score", ascending=False)


def is_blank(value) -> bool:
    """يتعامل بأمان مع القيم الفارغة القادمة من SQLite/Pandas مثل None وNaN وNaT."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    if isinstance(value, str) and value.strip().lower() in ["", "nan", "nat", "none", "null"]:
        return True
    return False


def safe_str(value, default: str = "") -> str:
    return default if is_blank(value) else str(value)


def safe_int(value, default: int = 0, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    if is_blank(value):
        out = int(default)
    else:
        try:
            out = int(float(value))
        except Exception:
            out = int(default)
    if min_value is not None:
        out = max(out, int(min_value))
    if max_value is not None:
        out = min(out, int(max_value))
    return out


def safe_float(value, default: float = 0.0, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    if is_blank(value):
        out = float(default)
    else:
        try:
            out = float(value)
        except Exception:
            out = float(default)
    if min_value is not None:
        out = max(out, float(min_value))
    if max_value is not None:
        out = min(out, float(max_value))
    return out


def get_index(value, options: List[str], default: int = 0) -> int:
    try:
        value = safe_str(value, "")
        return options.index(value) if value in options else default
    except Exception:
        return default


def build_graduate_form(prefix: str, defaults: Optional[Dict] = None) -> Dict:
    defaults = defaults or {}
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("اسم الخريج", value=safe_str(defaults.get("full_name")), key=f"{prefix}_full_name")
        national_id = st.text_input("الرقم التعريفي / كود الخريج", value=safe_str(defaults.get("national_id")), key=f"{prefix}_national_id")
        gender = st.selectbox("النوع", GENDER_OPTIONS, index=get_index(defaults.get("gender", "غير محدد"), GENDER_OPTIONS), key=f"{prefix}_gender")
    with c2:
        email = st.text_input("البريد الإلكتروني", value=safe_str(defaults.get("email")), key=f"{prefix}_email")
        phone = st.text_input("الهاتف", value=safe_str(defaults.get("phone")), key=f"{prefix}_phone")
        grade = st.selectbox("التقدير", GRADE_OPTIONS, index=get_index(defaults.get("grade", "غير محدد"), GRADE_OPTIONS), key=f"{prefix}_grade")
    with c3:
        country = st.selectbox("الدولة", COUNTRIES, index=get_index(defaults.get("country", "مصر"), COUNTRIES), key=f"{prefix}_country")
        city = st.selectbox("المدينة", CITIES, index=get_index(defaults.get("city", "القاهرة"), CITIES), key=f"{prefix}_city")
        graduation_year = st.number_input("سنة التخرج", min_value=1980, max_value=2035, value=safe_int(defaults.get("graduation_year"), 2024, 1980, 2035), step=1, key=f"{prefix}_graduation_year")

    st.markdown("<hr>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        college = st.selectbox("الكلية", COLLEGES, index=get_index(defaults.get("college", "كلية الحاسبات والمعلومات"), COLLEGES), key=f"{prefix}_college")
    dept_options = DEPARTMENTS_BY_COLLEGE.get(college, ["أخرى"])
    with c5:
        department = st.selectbox("القسم", dept_options, index=get_index(defaults.get("department", dept_options[0]), dept_options), key=f"{prefix}_department")
    with c6:
        major = st.text_input("التخصص الدقيق", value=safe_str(defaults.get("major")), key=f"{prefix}_major")

    st.markdown("<hr>", unsafe_allow_html=True)
    c7, c8, c9 = st.columns(3)
    with c7:
        current_status = st.selectbox("الحالة الحالية", STATUS_OPTIONS, index=get_index(defaults.get("current_status", "موظف"), STATUS_OPTIONS), key=f"{prefix}_status")
    with c8:
        job_related_to_major = st.selectbox("هل العمل مرتبط بالتخصص؟", RELATED_OPTIONS, index=get_index(defaults.get("job_related_to_major", "غير محدد"), RELATED_OPTIONS), key=f"{prefix}_related")
    with c9:
        first_job_months = st.number_input("عدد الأشهر حتى أول وظيفة", min_value=0, max_value=120, value=safe_int(defaults.get("first_job_months"), 0, 0, 120), step=1, key=f"{prefix}_months")

    c10, c11, c12 = st.columns(3)
    with c10:
        employer = st.text_input("جهة العمل", value=safe_str(defaults.get("employer")), key=f"{prefix}_employer")
        job_title = st.text_input("المسمى الوظيفي", value=safe_str(defaults.get("job_title")), key=f"{prefix}_job_title")
    with c11:
        employment_sector = st.selectbox("قطاع العمل", SECTOR_OPTIONS, index=get_index(defaults.get("employment_sector", "غير محدد"), SECTOR_OPTIONS), key=f"{prefix}_sector")
        income_val = defaults.get("monthly_income")
        monthly_income = st.number_input("الدخل الشهري التقريبي", min_value=0.0, max_value=1000000.0, value=safe_float(income_val, 0.0, 0.0, 1000000.0), step=500.0, key=f"{prefix}_income")
    with c12:
        raw_date = defaults.get("employment_start_date")
        try:
            default_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date() if raw_date else date.today()
        except Exception:
            default_date = date.today()
        employment_start_date = st.date_input("تاريخ بداية العمل", value=default_date, key=f"{prefix}_emp_date")
        postgraduate_program = st.text_input("برنامج الدراسات العليا إن وجد", value=safe_str(defaults.get("postgraduate_program")), key=f"{prefix}_postgrad")

    st.markdown("<hr>", unsafe_allow_html=True)
    c13, c14, c15 = st.columns(3)
    with c13:
        business_name = st.text_input("اسم المشروع الخاص", value=safe_str(defaults.get("business_name")), key=f"{prefix}_business_name")
    with c14:
        business_activity = st.text_input("نوع نشاط المشروع", value=safe_str(defaults.get("business_activity")), key=f"{prefix}_business_activity")
    with c15:
        business_start_year = st.number_input("سنة تأسيس المشروع", min_value=0, max_value=2035, value=safe_int(defaults.get("business_start_year"), 0, 0, 2035), step=1, key=f"{prefix}_business_year")
        business_employees = st.number_input("عدد العاملين بالمشروع", min_value=0, max_value=100000, value=safe_int(defaults.get("business_employees"), 0, 0, 100000), step=1, key=f"{prefix}_business_employees")

    notes = st.text_area("ملاحظات", value=safe_str(defaults.get("notes")), key=f"{prefix}_notes", height=90)
    return {
        "national_id": national_id.strip(),
        "full_name": full_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "gender": gender,
        "college": college,
        "department": department,
        "major": major.strip(),
        "graduation_year": int(graduation_year),
        "grade": grade,
        "current_status": current_status,
        "employer": employer.strip(),
        "job_title": job_title.strip(),
        "employment_sector": employment_sector,
        "employment_start_date": date_to_str(employment_start_date) if current_status in ["موظف", "صاحب مشروع خاص", "طالب دراسات عليا"] else "",
        "job_related_to_major": job_related_to_major,
        "business_name": business_name.strip(),
        "business_activity": business_activity.strip(),
        "business_start_year": int(business_start_year) if business_start_year else None,
        "business_employees": int(business_employees) if business_employees else None,
        "postgraduate_program": postgraduate_program.strip(),
        "first_job_months": int(first_job_months) if first_job_months else None,
        "monthly_income": float(monthly_income) if monthly_income else None,
        "country": country,
        "city": city,
        "last_update": date.today().isoformat(),
        "notes": notes.strip(),
    }

# -----------------------------------------------------------------------------
# تبويبات المنصة
# -----------------------------------------------------------------------------
def render_dashboard(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("لوحة المؤشرات التنفيذية", "قراءة سريعة لأداء الخريجين، توافق العمل مع التخصص، وريادة الأعمال والدراسات العليا.")
    if df.empty:
        st.info("لا توجد بيانات حتى الآن. استخدم زر البيانات التجريبية من الشريط الجانبي أو أضف خريجين يدويًا.")
        return

    overview = compute_overview(df, surveys)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("إجمالي الخريجين", f"{overview['total']:,}", "عدد السجلات داخل قاعدة البيانات")
    with c2: metric_card("معدل المخرجات الإيجابية", format_pct(overview["employment_rate"]), "وظيفة + مشروع + دراسات عليا")
    with c3: metric_card("ارتباط العمل بالتخصص", format_pct(overview["related_rate"]), "نعم أو جزئيًا")
    with c4: metric_card("متوسط أول وظيفة", f"{overview['avg_months']} شهر", "متوسط الفترة بعد التخرج")
    with c5: metric_card("رضا الخريجين", f"{overview['avg_satisfaction']}/5", "متوسط الاستبيانات")

    st.markdown("<br>", unsafe_allow_html=True)
    c6, c7 = st.columns([1.05, 1])
    with c6:
        status_counts = df["current_status"].fillna("غير محدد").value_counts().reset_index()
        status_counts.columns = ["الحالة", "العدد"]
        fig = px.pie(status_counts, names="الحالة", values="العدد", hole=0.48)
        fig.update_traces(textinfo="percent", textposition="inside", insidetextorientation="radial")
        fig = apply_plotly_layout(fig, "توزيع حالات الخريجين", height=460)
        st.plotly_chart(fig, use_container_width=True)
    with c7:
        year_counts = df.groupby("graduation_year").size().reset_index(name="عدد الخريجين")
        fig = px.bar(year_counts, x="graduation_year", y="عدد الخريجين", text="عدد الخريجين")
        fig.update_traces(textposition="auto", cliponaxis=False)
        fig = apply_plotly_layout(fig, "توزيع الخريجين حسب سنة التخرج")
        st.plotly_chart(fig, use_container_width=True)

    c8, c9 = st.columns(2)
    with c8:
        by_college = program_performance(df, surveys, ["college"])
        if not by_college.empty:
            fig = px.bar(by_college.sort_values("employment_rate"), x="employment_rate", y="college", orientation="h", text="employment_rate")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
            fig = apply_plotly_layout(fig, "معدل المخرجات الإيجابية حسب الكلية")
            st.plotly_chart(fig, use_container_width=True)
    with c9:
        related = df["job_related_to_major"].fillna("غير محدد").value_counts().reset_index()
        related.columns = ["ارتباط العمل بالتخصص", "العدد"]
        fig = px.bar(related, x="ارتباط العمل بالتخصص", y="العدد", text="العدد")
        fig.update_traces(textposition="auto", cliponaxis=False)
        fig = apply_plotly_layout(fig, "مدى ارتباط الوظائف بالتخصص")
        st.plotly_chart(fig, use_container_width=True)

    c10, c11 = st.columns(2)
    with c10:
        sector = df["employment_sector"].replace("", "غير محدد").fillna("غير محدد").value_counts().reset_index()
        sector.columns = ["القطاع", "العدد"]
        fig = px.bar(sector, x="القطاع", y="العدد", text="العدد")
        fig.update_traces(textposition="auto", cliponaxis=False)
        fig = apply_plotly_layout(fig, "توزيع الخريجين حسب قطاع العمل")
        st.plotly_chart(fig, use_container_width=True)
    with c11:
        if not surveys.empty:
            skill_cols = ["scientific_knowledge", "technical_skills", "communication_skills", "leadership_skills", "problem_solving", "overall_satisfaction", "curriculum_relevance"]
            radar_df = pd.DataFrame({
                "المحور": [AR_COLS[c] for c in skill_cols],
                "المتوسط": [pd.to_numeric(surveys[c], errors="coerce").mean() for c in skill_cols],
            })
            fig = go.Figure(data=go.Scatterpolar(r=radar_df["المتوسط"], theta=radar_df["المحور"], fill="toself"))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
            fig = apply_plotly_layout(fig, "خريطة تقييم أثر التعليم")
            st.plotly_chart(fig, use_container_width=True)

    section_header("مؤشرات إنذار مبكر", "نقاط تحتاج انتباه الإدارة الأكاديمية ومكتب الجودة.")
    performance = program_performance(df, surveys, ["college", "department", "major"])
    if not performance.empty:
        risk_table = performance[performance["risk_level"].isin(["حرج", "مرتفع"])].head(8)
        if risk_table.empty:
            st.success("لا توجد برامج ضمن مستوى خطر حرج أو مرتفع حسب البيانات الحالية.")
        else:
            st.dataframe(ar_df(risk_table[["college", "department", "major", "graduates_count", "employment_rate", "related_rate", "avg_satisfaction", "outcome_score", "risk_level", "recommendation"]]), use_container_width=True, hide_index=True)


def render_graduates_management(df: pd.DataFrame) -> None:
    section_header("إدارة بيانات الخريجين", "إضافة، تحديث، حذف، والبحث داخل قاعدة بيانات الخريجين.")
    sub1, sub2, sub3 = st.tabs(["➕ إضافة خريج", "✏️ تعديل سجل", "🗑️ حذف سجل"])

    with sub1:
        st.markdown("<div class='soft-box info-box'>أدخل بيانات الخريج الأكاديمية والمهنية. الحقول الأساسية هي الاسم والكلية والقسم وسنة التخرج والحالة الحالية.</div>", unsafe_allow_html=True)
        with st.form("add_graduate_form", clear_on_submit=False):
            row = build_graduate_form("add")
            submitted = st.form_submit_button("حفظ الخريج")
            if submitted:
                if not row["full_name"]:
                    st.error("اسم الخريج مطلوب.")
                elif not row["national_id"]:
                    st.error("الرقم التعريفي مطلوب لتجنب تكرار السجلات.")
                else:
                    ok, msg = insert_graduate(row)
                    clear_cache()
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    with sub2:
        if df.empty:
            st.info("لا توجد سجلات للتعديل.")
        else:
            options = {f"{r.full_name} — {r.national_id} — سجل #{r.id}": int(r.id) for r in df.itertuples()}
            selected = st.selectbox("اختر الخريج المراد تعديله", list(options.keys()))
            selected_id = options[selected]
            selected_row = df[df["id"] == selected_id].iloc[0].to_dict()
            with st.form("update_graduate_form", clear_on_submit=False):
                row = build_graduate_form("update", selected_row)
                submitted = st.form_submit_button("تحديث البيانات")
                if submitted:
                    if not row["full_name"] or not row["national_id"]:
                        st.error("الاسم والرقم التعريفي مطلوبان.")
                    else:
                        ok, msg = update_graduate(selected_id, row)
                        clear_cache()
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()

    with sub3:
        if df.empty:
            st.info("لا توجد سجلات للحذف.")
        else:
            options = {f"{r.full_name} — {r.national_id} — سجل #{r.id}": int(r.id) for r in df.itertuples()}
            selected = st.selectbox("اختر السجل", list(options.keys()), key="delete_select")
            confirm = st.checkbox("أؤكد حذف هذا السجل وما يرتبط به من استبيانات", key="delete_confirm")
            if st.button("حذف نهائي", type="primary"):
                if confirm:
                    delete_graduate(options[selected])
                    clear_cache()
                    st.success("تم حذف السجل.")
                    st.rerun()
                else:
                    st.warning("يجب تأكيد الحذف أولًا.")


def render_database(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("قاعدة بيانات الخريجين", "بحث وفلاتر متقدمة، عرض الأعمدة، وتصدير البيانات.")
    if df.empty:
        st.info("لا توجد بيانات متاحة.")
        return
    min_year = int(pd.to_numeric(df["graduation_year"], errors="coerce").min())
    max_year = int(pd.to_numeric(df["graduation_year"], errors="coerce").max())
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.4])
    with f1:
        college = st.selectbox("فلترة حسب الكلية", ["الكل"] + sorted(df["college"].dropna().unique().tolist()))
    with f2:
        dept_values = sorted(df.loc[df["college"].eq(college) if college != "الكل" else df.index == df.index, "department"].dropna().unique().tolist())
        department = st.selectbox("فلترة حسب القسم", ["الكل"] + dept_values)
    with f3:
        year_range = st.slider("سنة التخرج", min_year, max_year, (min_year, max_year))
    with f4:
        status = st.multiselect("الحالة الحالية", STATUS_OPTIONS, default=[])
    search = st.text_input("بحث عام بالاسم، الكود، البريد، جهة العمل، التخصص...")

    out = filtered_df(df, college, department, year_range, status, search)
    c1, c2, c3 = st.columns(3)
    c1.metric("عدد النتائج", f"{len(out):,}")
    c2.metric("عدد الكليات", f"{out['college'].nunique():,}" if not out.empty else "0")
    c3.metric("نسبة التوظيف داخل النتائج", format_pct(compute_overview(out, surveys)["employment_rate"]) if not out.empty else "0%")

    default_cols = ["id", "national_id", "full_name", "college", "department", "major", "graduation_year", "current_status", "employer", "job_title", "job_related_to_major", "first_job_months", "last_update"]
    cols = st.multiselect("الأعمدة المعروضة", df.columns.tolist(), default=[c for c in default_cols if c in df.columns])
    st.dataframe(ar_df(out[cols] if cols else out), use_container_width=True, hide_index=True, height=440)

    st.download_button("تحميل النتائج CSV", out.to_csv(index=False).encode("utf-8-sig"), "graduates_filtered.csv", "text/csv")
    st.download_button("تحميل النتائج Excel", to_excel_bytes({"graduates": out}), "graduates_filtered.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_surveys(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("استبيانات أثر التعليم", "قياس استفادة الخريج من المعرفة والمهارات والمنهج ومدى الرضا العام.")
    sub1, sub2, sub3 = st.tabs(["إضافة استبيان", "تحليل الاستبيانات", "سجل الاستبيانات"])
    with sub1:
        if df.empty:
            st.info("أضف خريجين أولًا قبل تسجيل الاستبيانات.")
        else:
            options = {f"{r.full_name} — {r.college} — {r.national_id}": int(r.id) for r in df.itertuples()}
            with st.form("survey_form"):
                graduate_label = st.selectbox("اختر الخريج", list(options.keys()))
                c1, c2, c3 = st.columns(3)
                with c1:
                    scientific_knowledge = st.slider("المعرفة العلمية", 1, 5, 4)
                    technical_skills = st.slider("المهارات التقنية", 1, 5, 4)
                with c2:
                    communication_skills = st.slider("مهارات الاتصال", 1, 5, 4)
                    leadership_skills = st.slider("مهارات القيادة", 1, 5, 3)
                with c3:
                    problem_solving = st.slider("حل المشكلات", 1, 5, 4)
                    overall_satisfaction = st.slider("الرضا العام", 1, 5, 4)
                curriculum_relevance = st.slider("ملاءمة المنهج لسوق العمل", 1, 5, 4)
                missing_skills = st.text_area("ما المهارات الناقصة من وجهة نظر الخريج؟", height=80)
                comments = st.text_area("تعليقات إضافية", height=80)
                submitted = st.form_submit_button("حفظ الاستبيان")
                if submitted:
                    ok, msg = insert_survey({
                        "graduate_id": options[graduate_label],
                        "survey_date": date.today().isoformat(),
                        "scientific_knowledge": scientific_knowledge,
                        "technical_skills": technical_skills,
                        "communication_skills": communication_skills,
                        "leadership_skills": leadership_skills,
                        "problem_solving": problem_solving,
                        "overall_satisfaction": overall_satisfaction,
                        "curriculum_relevance": curriculum_relevance,
                        "missing_skills": missing_skills,
                        "comments": comments,
                    })
                    clear_cache()
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    with sub2:
        if surveys.empty:
            st.info("لا توجد استبيانات حتى الآن.")
        else:
            skill_cols = ["scientific_knowledge", "technical_skills", "communication_skills", "leadership_skills", "problem_solving", "overall_satisfaction", "curriculum_relevance"]
            summary = pd.DataFrame({
                "المحور": [AR_COLS[c] for c in skill_cols],
                "المتوسط من 5": [round(pd.to_numeric(surveys[c], errors="coerce").mean(), 2) for c in skill_cols],
            })
            c1, c2 = st.columns(2)
            with c1:
                fig = px.bar(summary, x="المحور", y="المتوسط من 5", text="المتوسط من 5")
                fig.update_traces(textposition="auto", cliponaxis=False)
                fig.update_yaxes(range=[0, 5])
                fig = apply_plotly_layout(fig, "متوسط تقييم محاور أثر التعليم")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                by_college = surveys.groupby("college")["overall_satisfaction"].mean().reset_index()
                by_college["overall_satisfaction"] = by_college["overall_satisfaction"].round(2)
                fig = px.bar(by_college.sort_values("overall_satisfaction"), x="overall_satisfaction", y="college", orientation="h", text="overall_satisfaction")
                fig.update_xaxes(range=[0, 5])
                fig = apply_plotly_layout(fig, "الرضا العام حسب الكلية")
                st.plotly_chart(fig, use_container_width=True)
            missing = surveys["missing_skills"].dropna().astype(str)
            common_terms = []
            for item in missing:
                common_terms += [x.strip() for x in item.replace("،", ",").split(",") if x.strip()]
            if common_terms:
                skill_freq = pd.Series(common_terms).value_counts().reset_index()
                skill_freq.columns = ["المهارة", "عدد مرات الذكر"]
                st.dataframe(skill_freq.head(20), use_container_width=True, hide_index=True)

    with sub3:
        st.dataframe(ar_df(surveys), use_container_width=True, hide_index=True, height=440)
        if not surveys.empty:
            st.download_button("تحميل الاستبيانات Excel", to_excel_bytes({"surveys": surveys}), "surveys.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_analytics(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("التحليلات المتقدمة ودعم القرار", "مقارنات معيارية بين الكليات والأقسام والتخصصات لتحديد نقاط القوة ومناطق التحسين.")
    if df.empty:
        st.info("لا توجد بيانات للتحليل.")
        return

    level = st.radio("مستوى التحليل", ["الكلية", "القسم", "التخصص"], horizontal=True)
    group_cols = {"الكلية": ["college"], "القسم": ["college", "department"], "التخصص": ["college", "department", "major"]}[level]
    perf = program_performance(df, surveys, group_cols)
    if perf.empty:
        return

    c1, c2 = st.columns([1.2, 1])
    with c1:
        label_col = group_cols[-1]
        fig = px.scatter(
            perf,
            x="employment_rate",
            y="related_rate",
            size="graduates_count",
            color="risk_level",
            hover_data=group_cols + ["outcome_score", "avg_satisfaction", "avg_first_job_months"],
            text=label_col,
        )
        fig.update_traces(textposition="top center", textfont={"size": 10}, cliponaxis=False)
        fig.update_xaxes(title="معدل المخرجات الإيجابية %", range=[0, 105])
        fig.update_yaxes(title="معدل العمل داخل/قريب من التخصص %", range=[0, 105])
        fig = apply_plotly_layout(fig, "مصفوفة الأداء: التوظيف مقابل ارتباط التخصص")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        risk_counts = perf["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["مستوى المخاطر", "عدد البرامج"]
        fig = px.pie(risk_counts, names="مستوى المخاطر", values="عدد البرامج", hole=.45)
        fig.update_traces(textinfo="percent", textposition="inside", insidetextorientation="radial")
        fig = apply_plotly_layout(fig, "توزيع مستويات المخاطر", height=430)
        st.plotly_chart(fig, use_container_width=True)

    section_header("جدول الأداء المؤسسي", "يحسب المؤشر المركب من: المخرجات الإيجابية، ارتباط التخصص، الرضا، سرعة الحصول على أول وظيفة، والمهارات.")
    show_cols = group_cols + ["graduates_count", "employment_rate", "related_rate", "entrepreneurship_rate", "postgraduate_rate", "avg_first_job_months", "avg_satisfaction", "outcome_score", "risk_level", "recommendation"]
    st.dataframe(ar_df(perf[show_cols]), use_container_width=True, hide_index=True, height=480)
    st.download_button("تحميل تحليل الأداء Excel", to_excel_bytes({"performance": perf}), "program_performance.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    section_header("أفضل البرامج والبرامج الأضعف", "مقارنة مباشرة بين أعلى وأدنى البرامج في مؤشر المخرجات.")
    top, bottom = st.columns(2)
    with top:
        st.markdown("<div class='soft-box success-box'><b>أفضل البرامج أداءً</b></div>", unsafe_allow_html=True)
        st.dataframe(ar_df(perf.head(5)[show_cols]), use_container_width=True, hide_index=True)
    with bottom:
        st.markdown("<div class='soft-box danger-box'><b>برامج تحتاج أولوية تطوير</b></div>", unsafe_allow_html=True)
        st.dataframe(ar_df(perf.tail(5).sort_values("outcome_score")[show_cols]), use_container_width=True, hide_index=True)


def render_reports(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("التقارير التنفيذية", "تقارير قابلة للتصدير للجامعة، الأقسام العلمية، الجودة والاعتماد.")
    if df.empty:
        st.info("لا توجد بيانات لإصدار التقارير.")
        return
    overview = compute_overview(df, surveys)
    perf_college = program_performance(df, surveys, ["college"])
    perf_program = program_performance(df, surveys, ["college", "department", "major"])

    sub1, sub2, sub3 = st.tabs(["تقرير الجامعة", "تقرير قسم/كلية", "تقرير الاعتماد والجودة"])

    with sub1:
        st.markdown("<div class='soft-box info-box'><b>ملخص تنفيذي:</b> يوضح التقرير الصورة العامة لمخرجات الخريجين على مستوى الجامعة بالكامل.</div>", unsafe_allow_html=True)
        metrics = {
            "إجمالي الخريجين": f"{overview['total']:,}",
            "معدل المخرجات الإيجابية": format_pct(overview["employment_rate"]),
            "معدل التوظيف المباشر": format_pct(overview["direct_employment_rate"]),
            "معدل ريادة الأعمال": format_pct(overview["entrepreneurship_rate"]),
            "معدل الدراسات العليا": format_pct(overview["postgraduate_rate"]),
            "ارتباط العمل بالتخصص": format_pct(overview["related_rate"]),
            "متوسط الرضا العام": f"{overview['avg_satisfaction']}/5",
            "متوسط مدة الحصول على أول وظيفة": f"{overview['avg_months']} شهر",
        }
        st.dataframe(pd.DataFrame(metrics.items(), columns=["المؤشر", "القيمة"]), use_container_width=True, hide_index=True)
        recommendations = [
            "تحديث البرامج ذات المخاطر المرتفعة بناءً على مؤشرات التوظيف وارتباط التخصص.",
            "إنشاء شراكات تدريب وتوظيف مع القطاعات الأكثر استيعابًا للخريجين.",
            "اعتماد استبيان نصف سنوي للخريجين وربط نتائجه بمراجعة المناهج.",
            "استخدام مؤشرات المنصة كأدلة داعمة في ملفات الجودة والاعتماد الأكاديمي.",
        ]
        report_text = build_markdown_report("تقرير مخرجات الخريجين على مستوى الجامعة", "هذا التقرير يلخص الوضع العام للخريجين ويعرض مؤشرات قابلة للاستخدام في التطوير المؤسسي.", metrics, recommendations)
        st.download_button("تحميل تقرير الجامعة Markdown", report_text.encode("utf-8-sig"), "university_report.md", "text/markdown")
        st.download_button("تحميل حزمة التقرير Excel", to_excel_bytes({"overview": pd.DataFrame(metrics.items(), columns=["metric", "value"]), "college_performance": perf_college, "program_performance": perf_program}), "university_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with sub2:
        college = st.selectbox("اختر الكلية", sorted(df["college"].dropna().unique().tolist()), key="report_college")
        dept_options = ["كل الأقسام"] + sorted(df.loc[df["college"] == college, "department"].dropna().unique().tolist())
        department = st.selectbox("اختر القسم", dept_options, key="report_department")
        subset = df[df["college"] == college].copy()
        if department != "كل الأقسام":
            subset = subset[subset["department"] == department]
        sub_surveys = surveys[surveys["college"].eq(college)] if not surveys.empty else pd.DataFrame()
        if department != "كل الأقسام" and not sub_surveys.empty:
            sub_surveys = sub_surveys[sub_surveys["department"] == department]
        metrics2 = compute_overview(subset, sub_surveys)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("عدد الخريجين", f"{metrics2['total']:,}")
        c2.metric("المخرجات الإيجابية", format_pct(metrics2["employment_rate"]))
        c3.metric("ارتباط التخصص", format_pct(metrics2["related_rate"]))
        c4.metric("الرضا العام", f"{metrics2['avg_satisfaction']}/5")
        if not subset.empty:
            perf = program_performance(subset, sub_surveys, ["college", "department", "major"])
            st.dataframe(ar_df(perf), use_container_width=True, hide_index=True)
            report_text = build_markdown_report(
                f"تقرير {college} - {department}",
                "تقرير تفصيلي لمتابعة مخرجات الخريجين على مستوى الكلية/القسم.",
                {
                    "عدد الخريجين": str(metrics2["total"]),
                    "معدل المخرجات الإيجابية": format_pct(metrics2["employment_rate"]),
                    "ارتباط العمل بالتخصص": format_pct(metrics2["related_rate"]),
                    "متوسط الرضا": f"{metrics2['avg_satisfaction']}/5",
                },
                ["تحليل البرامج ذات المعدل الأقل وإعداد خطة تحسين.", "توسيع التدريب العملي والتواصل مع أصحاب العمل.", "مقارنة نتائج القسم بالمتوسط العام للجامعة."],
            )
            st.download_button("تحميل تقرير القسم Markdown", report_text.encode("utf-8-sig"), "department_report.md", "text/markdown")
            st.download_button("تحميل تقرير القسم Excel", to_excel_bytes({"graduates": subset, "performance": perf}), "department_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with sub3:
        st.markdown("<div class='soft-box warning-box'><b>منطق الاعتماد:</b> كل مؤشر يمكن استخدامه كدليل Evidence في ملفات الجودة: مخرجات تعلم، توظيف، ملاءمة سوق العمل، رضا الخريجين، والتحسين المستمر.</div>", unsafe_allow_html=True)
        accreditation = perf_program.copy()
        accreditation["evidence_status"] = accreditation["outcome_score"].apply(lambda x: "دليل قوي" if x >= 80 else "دليل مقبول" if x >= 65 else "يتطلب خطة تحسين" if x >= 50 else "خطر اعتمادي")
        show = accreditation[["college", "department", "major", "graduates_count", "employment_rate", "related_rate", "avg_satisfaction", "outcome_score", "risk_level", "evidence_status", "recommendation"]]
        st.dataframe(ar_df(show), use_container_width=True, hide_index=True, height=480)
        st.download_button("تحميل تقرير الاعتماد Excel", to_excel_bytes({"accreditation": accreditation}), "accreditation_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_import_export(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("الاستيراد والتصدير والنسخ الاحتياطي", "إدارة البيانات بملفات CSV/Excel مع تحميل نسخة احتياطية من قاعدة البيانات.")
    st.markdown("<div class='soft-box info-box'>يمكن استيراد ملف يحتوي على أسماء الأعمدة الإنجليزية المستخدمة في قاعدة البيانات. يوجد ملف عينة داخل حزمة المشروع.</div>", unsafe_allow_html=True)
    sub1, sub2 = st.tabs(["استيراد بيانات", "تصدير ونسخة احتياطية"])
    with sub1:
        uploaded = st.file_uploader("ارفع ملف CSV أو Excel للخريجين", type=["csv", "xlsx", "xls"])
        if uploaded is not None:
            try:
                if uploaded.name.lower().endswith(".csv"):
                    imported = pd.read_csv(uploaded)
                else:
                    imported = pd.read_excel(uploaded)
                st.write("معاينة البيانات")
                st.dataframe(imported.head(20), use_container_width=True, hide_index=True)
                if st.button("استيراد السجلات المعروضة"):
                    required = {"national_id", "full_name", "college", "department", "major", "graduation_year", "current_status"}
                    missing = required - set(imported.columns)
                    if missing:
                        st.error("أعمدة مطلوبة غير موجودة: " + ", ".join(missing))
                    else:
                        count_ok = count_fail = 0
                        for rec in imported.to_dict("records"):
                            for col in ["gender", "grade", "employment_sector", "job_related_to_major", "country", "city"]:
                                rec.setdefault(col, "غير محدد")
                            rec.setdefault("last_update", date.today().isoformat())
                            ok, _ = insert_graduate(rec)
                            count_ok += int(ok)
                            count_fail += int(not ok)
                        clear_cache()
                        st.success(f"تم استيراد {count_ok} سجل. فشل/تكرر {count_fail} سجل.")
                        st.rerun()
            except Exception as exc:
                st.error(f"تعذر قراءة الملف: {exc}")
    with sub2:
        st.download_button("تحميل كل الخريجين CSV", df.to_csv(index=False).encode("utf-8-sig"), "all_graduates.csv", "text/csv", disabled=df.empty)
        st.download_button("تحميل كل البيانات Excel", to_excel_bytes({"graduates": df, "surveys": surveys}), "graduates_platform_export.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", disabled=df.empty)
        if DB_PATH.exists():
            st.download_button("تحميل نسخة احتياطية من قاعدة البيانات SQLite", DB_PATH.read_bytes(), "graduates_platform_backup.db", "application/octet-stream")
        sample = demo_records().head(20)
        st.download_button("تحميل ملف عينة للاستيراد CSV", sample.to_csv(index=False).encode("utf-8-sig"), "sample_graduates.csv", "text/csv")


def render_admin(df: pd.DataFrame, surveys: pd.DataFrame) -> None:
    section_header("الإعدادات وسجل التشغيل", "تعريفات النظام، القاموس البياني، وسجل العمليات.")
    sub1, sub2, sub3 = st.tabs(["تعريف المنصة", "قاموس البيانات", "سجل العمليات"])
    with sub1:
        st.markdown(
            """
            <div class='soft-box'>
            <b>الغرض المؤسسي:</b> تحويل متابعة الخريجين من ملفات منفصلة إلى نظام قياس مستمر يربط البرامج الأكاديمية بسوق العمل.<br>
            <b>الفئات المستخدمة:</b> إدارة الجامعة، الجودة والاعتماد، الأقسام العلمية، منسقو الخريجين، وصناع القرار.<br>
            <b>البيانات الأساسية:</b> بيانات أكاديمية، حالة مهنية، مشاريع خاصة، دراسات عليا، تقييم استفادة، ومؤشرات أداء.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<span class='pill'>Python</span><span class='pill'>Streamlit</span><span class='pill'>SQLite</span><span class='pill'>Plotly</span><span class='pill'>Pandas</span><span class='pill'>RTL Arabic UI</span>", unsafe_allow_html=True)
    with sub2:
        dictionary = pd.DataFrame([{"اسم الحقل التقني": k, "الاسم العربي": v} for k, v in AR_COLS.items()])
        st.dataframe(dictionary, use_container_width=True, hide_index=True)
    with sub3:
        log = load_audit_log()
        st.dataframe(ar_df(log), use_container_width=True, hide_index=True, height=420)

# -----------------------------------------------------------------------------
# التطبيق الرئيسي
# -----------------------------------------------------------------------------
def main() -> None:
    init_db()
    # بيانات تجريبية تلقائية عند أول تشغيل حتى تظهر المنصة جاهزة للعرض فورًا.
    conn = get_connection()
    initial_count = conn.execute("SELECT COUNT(*) FROM graduates").fetchone()[0]
    conn.close()
    if initial_count == 0:
        seed_demo_data(reset=False)

    df = load_graduates()
    surveys = load_surveys()

    st.sidebar.markdown("### 🎓 منصة مخرجات الخريجين")
    st.sidebar.caption("نسخة Streamlit مؤسسية تجريبية")

    st.sidebar.markdown("<div class='sidebar-label'>اختر دور المستخدم داخل النظام</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='sidebar-help'>يُستخدم لتوضيح منظور القراءة: إدارة الجامعة، الجودة، رئيس قسم، أو باحث.</div>", unsafe_allow_html=True)
    role = st.sidebar.selectbox(
        "اختر دور المستخدم داخل النظام",
        ROLE_OPTIONS,
        label_visibility="collapsed",
        help="هذا الاختيار يحدد الصفة التي تعرض بها المؤشرات والتقارير.",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-label'>ملخص سريع للبيانات</div>", unsafe_allow_html=True)
    st.sidebar.metric("عدد الخريجين", f"{len(df):,}")
    st.sidebar.metric("عدد الاستبيانات", f"{len(surveys):,}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-label'>أدوات التشغيل والاختبار</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='sidebar-help'>استخدم هذه الأزرار لإعادة التحميل أو إنشاء بيانات تجريبية للعرض.</div>", unsafe_allow_html=True)
    if st.sidebar.button("إعادة تحميل البيانات"):
        clear_cache()
        st.rerun()
    if st.sidebar.button("إعادة ملء بيانات تجريبية قوية"):
        seed_demo_data(reset=True)
        st.success("تم تجهيز البيانات التجريبية.")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-label'>منطقة خطرة: مسح قاعدة البيانات</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='sidebar-help'>فعّل مربع التأكيد أولًا، ثم اضغط زر المسح. هذا يحذف السجلات من قاعدة SQLite الحالية.</div>", unsafe_allow_html=True)
    reset_confirm = st.sidebar.checkbox("أؤكد أنني أريد مسح قاعدة البيانات الحالية")
    if st.sidebar.button("مسح قاعدة البيانات"):
        if reset_confirm:
            conn = get_connection()
            conn.execute("DELETE FROM surveys")
            conn.execute("DELETE FROM graduates")
            conn.execute("DELETE FROM audit_log")
            conn.commit()
            conn.close()
            clear_cache()
            st.rerun()
        else:
            st.sidebar.warning("فعّل مربع التأكيد أولًا قبل المسح.")

    st.markdown(
        f"""
        <div class="hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
            <p style="margin-top:10px;font-size:.92rem;color:#bfdbfe;">الدور الحالي: {role}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "🏠 لوحة المؤشرات",
        "👥 إدارة الخريجين",
        "🗃️ قاعدة البيانات",
        "📝 استبيانات الأثر",
        "📊 تحليلات متقدمة",
        "📑 التقارير",
        "📥 استيراد وتصدير",
        "⚙️ الإعدادات",
    ])
    with tabs[0]:
        render_dashboard(df, surveys)
    with tabs[1]:
        render_graduates_management(df)
    with tabs[2]:
        render_database(df, surveys)
    with tabs[3]:
        render_surveys(df, surveys)
    with tabs[4]:
        render_analytics(df, surveys)
    with tabs[5]:
        render_reports(df, surveys)
    with tabs[6]:
        render_import_export(df, surveys)
    with tabs[7]:
        render_admin(df, surveys)


if __name__ == "__main__":
    main()
