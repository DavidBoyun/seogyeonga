"""
서경아 (Seogyeonga) - 서울 아파트 경매 서비스
메인 앱
"""
import streamlit as st
from database import init_db, get_auctions
from components.auth import render_login_button, render_login_modal

# 페이지 설정
st.set_page_config(
    page_title="서경아 - 서울 아파트 경매",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DB 초기화
init_db()

# 샘플 데이터 로드 (DB가 비어있을 때)
if 'data_loaded' not in st.session_state:
    existing = get_auctions()
    if not existing:
        from data import load_sample_data
        load_sample_data()
    st.session_state.data_loaded = True

# 세션 상태 초기화
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'show_login_modal' not in st.session_state:
    st.session_state.show_login_modal = False

# 커스텀 CSS
st.markdown("""
<style>
    /* 전체 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 헤더 스타일 */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 24px;
    }

    .logo {
        font-size: 28px;
        font-weight: 700;
        color: #1e40af;
    }

    .logo span {
        color: #6b7280;
        font-weight: 400;
        font-size: 14px;
        margin-left: 8px;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
    }

    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* 사이드바 */
    .css-1d391kg {
        padding-top: 2rem;
    }

    /* 카드 컨테이너 */
    .auction-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        background: white;
    }

    /* 히든 Streamlit 요소 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 헤더
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("""
    <div class="logo">
        🏠 서경아 <span>서울 아파트 경매</span>
    </div>
    """, unsafe_allow_html=True)
with col2:
    render_login_button()

# 로그인 모달
render_login_modal()

# 메인 탭
tab1, tab2, tab3 = st.tabs(["🏠 경매", "🔍 사건조회", "📰 뉴스"])

with tab1:
    # 경매 탭 내용을 여기에 인라인으로 렌더링
    from tabs.auction_tab import render_auction_tab
    render_auction_tab()

with tab2:
    # 사건번호 조회 탭 (실제 API 연동)
    from tabs.case_lookup import render_case_lookup
    render_case_lookup()

with tab3:
    # 뉴스 탭 내용을 여기에 인라인으로 렌더링
    from tabs.news_tab import render_news_tab
    render_news_tab()

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #9ca3af; font-size: 12px; padding: 16px 0;">
    © 2025 서경아 | 서울 아파트 경매 AI 분석 서비스<br>
    ⚠️ 본 서비스의 정보는 참고용이며, 실제 투자 결정 시 전문가 상담을 권장합니다.
</div>
""", unsafe_allow_html=True)
