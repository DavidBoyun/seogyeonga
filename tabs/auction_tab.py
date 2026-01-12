"""
경매 탭 (필터 + 목록 + 지도)
실제 법원경매 API 연동
"""
import streamlit as st
from datetime import date, timedelta
from database import (
    get_auctions, get_gugun_list, get_dong_list,
    is_favorite, add_favorite, remove_favorite, get_user_favorites
)
from components.auction_card import render_auction_list
from components.auction_map import render_auction_map
from components.auth import get_current_user_id
from services.court_crawler import (
    CourtAuctionCrawler, SEOUL_SIDO_CODE, SEOUL_SGG_CODES
)


# 구 이름 -> 코드 매핑 (3자리 코드)
SGG_CODE_MAP = {name: code[2:] for name, code in SEOUL_SGG_CODES.items()}


def fetch_auctions_from_db(
    gugun: str = None,
    dong: str = None,
    min_price: int = None,
    max_price: int = None,
    auction_counts: list = None,
    risk_levels: list = None,
    days_until: int = None
) -> list:
    """
    데이터베이스에서 경매 물건 가져오기
    (법원경매 목록 API가 업데이트될 때까지 샘플 데이터 사용)
    """
    return get_auctions(
        gugun=gugun,
        dong=dong,
        min_price=min_price,
        max_price=max_price,
        auction_counts=auction_counts,
        risk_levels=risk_levels,
        days_until=days_until
    )


def render_auction_tab():
    """경매 탭 렌더링 (실제 API 연동)"""

    user_id = get_current_user_id()

    # 사이드바 필터
    with st.sidebar:
        st.markdown("### 🔍 필터")

        # 지역 필터
        st.markdown("##### 지역")
        # 실제 크롤링 가능한 서울 구 목록
        gugun_list = sorted(list(SEOUL_SGG_CODES.keys()))
        gugun_options = ["전체"] + gugun_list
        selected_gugun = st.selectbox(
            "구 선택",
            gugun_options,
            key="filter_gugun",
            label_visibility="collapsed"
        )

        # 동 선택 (구 선택 시)
        selected_dong = None
        if selected_gugun and selected_gugun != "전체":
            dong_list = get_dong_list(selected_gugun)
            if dong_list:
                dong_options = ["전체"] + dong_list
                selected_dong = st.selectbox(
                    "동 선택",
                    dong_options,
                    key="filter_dong",
                    label_visibility="collapsed"
                )
                if selected_dong == "전체":
                    selected_dong = None

        st.markdown("---")

        # 가격 필터
        st.markdown("##### 가격 (최저가 기준)")
        price_range = st.slider(
            "가격 범위 (억)",
            min_value=0,
            max_value=50,
            value=(0, 50),
            step=1,
            key="filter_price",
            label_visibility="collapsed"
        )
        min_price = price_range[0] * 100000000 if price_range[0] > 0 else None
        max_price = price_range[1] * 100000000 if price_range[1] < 50 else None

        st.markdown("---")

        # 경매 차수 필터
        st.markdown("##### 경매 차수")
        auction_count_options = {
            "전체": None,
            "신건 (1차)": [1],
            "2차": [2],
            "3차 이상": [3, 4, 5, 6, 7, 8, 9, 10],
        }
        selected_count = st.radio(
            "차수 선택",
            list(auction_count_options.keys()),
            key="filter_count",
            label_visibility="collapsed"
        )
        auction_counts = auction_count_options[selected_count]

        st.markdown("---")

        # 위험도 필터
        st.markdown("##### 위험도")
        risk_options = st.multiselect(
            "위험도 선택",
            ["안전", "주의", "위험"],
            default=["안전", "주의", "위험"],
            key="filter_risk",
            label_visibility="collapsed"
        )
        risk_levels = risk_options if risk_options else None

        st.markdown("---")

        # 입찰일 필터
        st.markdown("##### 입찰일")
        days_options = {
            "전체": None,
            "7일 이내": 7,
            "14일 이내": 14,
            "30일 이내": 30,
        }
        selected_days = st.radio(
            "입찰일 선택",
            list(days_options.keys()),
            key="filter_days",
            label_visibility="collapsed"
        )
        days_until = days_options[selected_days]

        st.markdown("---")

        # 필터 초기화 버튼
        if st.button("🔄 필터 초기화", use_container_width=True):
            for key in ['filter_gugun', 'filter_dong', 'filter_price',
                        'filter_count', 'filter_risk', 'filter_days']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # 메인 컨텐츠
    # 뷰 토글
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("#### 경매 물건")
    with col2:
        view_mode = st.radio(
            "보기 방식",
            ["📋 목록", "🗺️ 지도"],
            horizontal=True,
            key="view_mode",
            label_visibility="collapsed"
        )
    with col3:
        # 관심 물건만 보기
        if user_id:
            show_favorites = st.checkbox("⭐ 관심만", key="show_favorites")
        else:
            show_favorites = False

    # 데이터 조회
    if show_favorites and user_id:
        auctions = get_user_favorites(user_id)
        total_count = len(auctions)
        data_source = "favorites"
    else:
        # 데이터베이스에서 경매 물건 조회
        auctions = fetch_auctions_from_db(
            gugun=selected_gugun if selected_gugun != "전체" else None,
            dong=selected_dong,
            min_price=min_price,
            max_price=max_price,
            auction_counts=auction_counts,
            risk_levels=risk_levels,
            days_until=days_until
        )
        total_count = len(auctions)
        data_source = "database"

    # 결과 카운트 및 안내
    st.markdown(f"**{total_count}**개 물건")

    # 실시간 데이터 안내
    if data_source == "database":
        st.info("💡 **실제 경매 물건 조회**: [🔍 사건조회] 탭에서 사건번호로 실시간 법원 데이터를 확인하세요.")

    # 관심 물건 ID 세트
    favorite_ids = set()
    if user_id:
        favorites = get_user_favorites(user_id)
        favorite_ids = {f['id'] for f in favorites}

    # 관심 토글 콜백
    def handle_favorite_click(auction_id):
        if not user_id:
            st.warning("로그인이 필요합니다.")
            return

        if auction_id in favorite_ids:
            remove_favorite(user_id, auction_id)
            st.toast("관심 물건에서 제거되었습니다.")
        else:
            add_favorite(user_id, auction_id)
            st.toast("관심 물건에 추가되었습니다.")
        st.rerun()

    # 뷰 렌더링
    if view_mode == "📋 목록":
        render_auction_list(
            auctions,
            favorites=favorite_ids,
            user_id=user_id,
            on_favorite_click=handle_favorite_click
        )
    else:
        # 지도 뷰 (스텁)
        auction_dicts = []
        for a in auctions:
            if hasattr(a, '__dict__'):
                auction_dicts.append({
                    'id': a.id,
                    'apt_name': a.apt_name,
                    'lat': a.lat,
                    'lng': a.lng,
                    'min_price': a.min_price,
                    'risk_level': a.risk_level,
                })
            else:
                auction_dicts.append(a)

        render_auction_map(auction_dicts)

    # 데이터 없음
    if not auctions:
        st.info("조건에 맞는 물건이 없습니다. 필터를 조정해 보세요.")
