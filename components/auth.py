"""
인증 컴포넌트 (소셜 로그인 - 스텁)
"""
import streamlit as st
from typing import Optional, Dict, Any
from config import GOOGLE_CLIENT_ID, NAVER_CLIENT_ID


def render_login_button():
    """로그인 버튼 (헤더용)"""

    if st.session_state.get('user'):
        user = st.session_state.user
        nickname = user.get('nickname', user.get('email', '').split('@')[0])

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"👤 **{nickname}**님")
        with col2:
            if st.button("로그아웃", key="logout_btn"):
                st.session_state.user = None
                st.session_state.user_id = None
                st.rerun()
    else:
        if st.button("🔐 로그인", key="login_btn", use_container_width=True):
            st.session_state.show_login_modal = True
            st.rerun()


def render_login_modal():
    """로그인 모달 (스텁)"""

    if not st.session_state.get('show_login_modal'):
        return

    # 모달 오버레이
    st.markdown("""
    <style>
    .login-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("---")
        st.markdown("### 🔐 로그인")
        st.markdown("관심 물건 저장 및 입찰일 알림을 받으시려면 로그인하세요.")

        col1, col2 = st.columns(2)

        with col1:
            # 구글 로그인 버튼
            if st.button("🔵 Google로 로그인", key="google_login", use_container_width=True):
                if GOOGLE_CLIENT_ID:
                    # TODO: 실제 Google OAuth 구현
                    st.warning("Google OAuth 연동 예정")
                else:
                    # 스텁: 테스트 유저로 로그인
                    _stub_login("google", "test@gmail.com", "테스트유저")

        with col2:
            # 네이버 로그인 버튼
            if st.button("🟢 Naver로 로그인", key="naver_login", use_container_width=True):
                if NAVER_CLIENT_ID:
                    # TODO: 실제 Naver OAuth 구현
                    st.warning("Naver OAuth 연동 예정")
                else:
                    # 스텁: 테스트 유저로 로그인
                    _stub_login("naver", "test@naver.com", "네이버유저")

        st.markdown("---")

        # 테스트 로그인 (개발용)
        st.markdown("##### 🧪 테스트 로그인 (개발용)")

        test_email = st.text_input("이메일", value="demo@test.com", key="test_email")
        test_nickname = st.text_input("닉네임", value="데모유저", key="test_nickname")

        if st.button("테스트 로그인", key="test_login"):
            _stub_login("test", test_email, test_nickname)

        if st.button("❌ 닫기", key="close_modal"):
            st.session_state.show_login_modal = False
            st.rerun()


def _stub_login(provider: str, email: str, nickname: str):
    """스텁 로그인 처리"""
    from database import get_or_create_user

    user = get_or_create_user(
        email=email,
        provider=provider,
        nickname=nickname
    )

    st.session_state.user = {
        'id': user.id,
        'email': user.email,
        'nickname': user.nickname,
        'provider': user.provider
    }
    st.session_state.user_id = user.id
    st.session_state.show_login_modal = False

    st.success(f"환영합니다, {nickname}님!")
    st.rerun()


def get_current_user() -> Optional[Dict[str, Any]]:
    """현재 로그인된 유저 반환"""
    return st.session_state.get('user')


def get_current_user_id() -> Optional[int]:
    """현재 로그인된 유저 ID 반환"""
    return st.session_state.get('user_id')


def require_login(message: str = "이 기능을 사용하려면 로그인이 필요합니다."):
    """로그인 필수 데코레이터/함수"""
    if not get_current_user():
        st.warning(message)
        if st.button("🔐 로그인하기"):
            st.session_state.show_login_modal = True
            st.rerun()
        return False
    return True
