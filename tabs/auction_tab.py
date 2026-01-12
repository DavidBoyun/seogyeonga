"""
경매 탭 (필터 + 목록 + 지도)
실제 법원경매 API 연동 (v2 - 신규 API)
"""
import streamlit as st
from datetime import date, timedelta, datetime
from database import (
    get_auctions, get_gugun_list, get_dong_list,
    is_favorite, add_favorite, remove_favorite, get_user_favorites
)
from components.auction_card import render_auction_list
from components.auction_map import render_auction_map
from components.auth import get_current_user_id

# 신규 API 크롤러 (v2)
try:
    from services.court_crawler_v2 import (
        CourtAuctionCrawlerV2,
        COURT_CODES,
    )
    API_CRAWLER_AVAILABLE = True
except ImportError:
    API_CRAWLER_AVAILABLE = False

# 기존 크롤러 (폴백용)
from services.court_crawler import SEOUL_SGG_CODES


# 서울 구 목록
SEOUL_GU_LIST = [
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구"
]


def crawl_auctions_api(
    gu_name: str = None,
    page: int = 1,
    page_size: int = 50,
    property_type: str = "아파트"
) -> tuple:
    """
    신규 API로 실시간 경매 물건 크롤링

    Args:
        gu_name: 특정 구 (None이면 서울 전체)
        page: 페이지 번호
        page_size: 페이지 크기
        property_type: 물건 종류 (아파트, 전체)

    Returns:
        (물건 목록, 총 건수)
    """
    if not API_CRAWLER_AVAILABLE:
        return [], 0

    try:
        crawler = CourtAuctionCrawlerV2()

        # 서울 전체 검색
        result = crawler.search_auctions(
            sido_code="11",  # 서울
            page=page,
            page_size=page_size,
        )

        items = result.get("items", [])
        total = result.get("total", 0)

        # 구 필터링
        if gu_name and gu_name != "전체":
            items = [
                item for item in items
                if gu_name in item.get("sigu", "") or gu_name in item.get("address", "")
            ]

        # 아파트 필터링
        if property_type == "아파트":
            items = [
                item for item in items
                if any(t in item.get("usage_name", "") for t in ["아파트", "주상복합", "오피스텔"])
            ]

        # 표준 형식으로 변환
        formatted_items = []
        for item in items:
            formatted = {
                "id": item.get("id", ""),
                "case_no": item.get("case_no", ""),
                "court": item.get("court_name", ""),
                "apt_name": item.get("building_name") or extract_apt_name(item.get("address", "")),
                "address": item.get("address", ""),
                "addr1": item.get("sigu", ""),
                "area": item.get("area_max", 0),
                "appraisal_price": item.get("appraisal_price", 0),
                "min_price": item.get("min_price", 0),
                "auction_date": item.get("auction_date", ""),
                "auction_count": item.get("bid_count", 1) + 1,  # 유찰+1 = 차수
                "item_type": item.get("usage_name", ""),
                "status": "진행",
                "risk_level": calculate_risk(item),
                "risk_reason": get_risk_reason(item),
                "note": item.get("note", ""),
            }
            formatted_items.append(formatted)

        return formatted_items, total

    except Exception as e:
        st.error(f"크롤링 오류: {e}")
        return [], 0


def extract_apt_name(address: str) -> str:
    """주소에서 아파트명 추출"""
    if not address:
        return "경매물건"

    # 아파트명 패턴
    import re
    patterns = [
        r'([가-힣A-Za-z0-9]+아파트)',
        r'([가-힣A-Za-z0-9]+타워)',
        r'([가-힣A-Za-z0-9]+파크)',
        r'([가-힣A-Za-z0-9]+빌라)',
    ]

    for pattern in patterns:
        match = re.search(pattern, address)
        if match:
            return match.group(1)

    # 못 찾으면 주소의 마지막 부분
    parts = address.split()
    return parts[-1] if parts else "경매물건"


def calculate_risk(item: dict) -> str:
    """위험도 계산"""
    bid_count = item.get("bid_count", 0)

    if bid_count >= 4:
        return "위험"
    elif bid_count >= 2:
        return "주의"
    return "안전"


def get_risk_reason(item: dict) -> str:
    """위험 사유"""
    reasons = []
    bid_count = item.get("bid_count", 0)

    if bid_count >= 2:
        reasons.append(f"{bid_count + 1}회차 (유찰 {bid_count}회)")

    return ", ".join(reasons)


def apply_filters(auctions: list, filters: dict) -> list:
    """크롤링 결과에 필터 적용"""
    result = auctions

    # 가격 필터
    if filters.get("min_price"):
        result = [a for a in result if a.get("min_price", 0) >= filters["min_price"]]
    if filters.get("max_price"):
        result = [a for a in result if a.get("min_price", 0) <= filters["max_price"]]

    # 경매 차수 필터
    if filters.get("auction_counts"):
        result = [a for a in result if a.get("auction_count", 1) in filters["auction_counts"]]

    # 위험도 필터
    if filters.get("risk_levels"):
        result = [a for a in result if a.get("risk_level", "안전") in filters["risk_levels"]]

    # 동 필터
    if filters.get("dong"):
        result = [a for a in result if filters["dong"] in a.get("address", "")]

    # 물건 종류 필터
    if filters.get("property_type") == "아파트":
        result = [
            a for a in result
            if any(t in a.get("item_type", "") for t in ["아파트", "주상복합", "오피스텔"])
        ]

    return result


def render_auction_tab():
    """경매 탭 렌더링 (신규 API 연동)"""

    user_id = get_current_user_id()

    # 사이드바 필터
    with st.sidebar:
        st.markdown("### 🔍 필터")

        # 지역 필터
        st.markdown("##### 지역")
        gugun_options = ["전체"] + SEOUL_GU_LIST
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

        # 물건 종류 필터
        st.markdown("##### 물건 종류")
        property_type = st.radio(
            "종류 선택",
            ["아파트", "전체"],
            key="filter_property",
            label_visibility="collapsed"
        )

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

        # 필터 초기화 버튼
        if st.button("🔄 필터 초기화", use_container_width=True):
            for key in ['filter_gugun', 'filter_dong', 'filter_price',
                        'filter_count', 'filter_risk', 'filter_property']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # 메인 컨텐츠
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("#### 🏠 서울 경매 물건")
    with col2:
        view_mode = st.radio(
            "보기 방식",
            ["📋 목록", "🗺️ 지도"],
            horizontal=True,
            key="view_mode",
            label_visibility="collapsed"
        )
    with col3:
        if user_id:
            show_favorites = st.checkbox("⭐ 관심만", key="show_favorites")
        else:
            show_favorites = False

    # 크롤링 섹션
    st.markdown("---")
    crawl_col1, crawl_col2 = st.columns([3, 1])

    with crawl_col1:
        if API_CRAWLER_AVAILABLE:
            st.markdown("**🔥 실시간 API 연동** - 법원경매 사이트에서 직접 데이터를 가져옵니다.")
        else:
            st.markdown("**⚠️ 크롤러 초기화 실패** - 샘플 데이터를 표시합니다.")

    with crawl_col2:
        crawl_button = st.button(
            "🔄 실시간 검색",
            use_container_width=True,
            disabled=not API_CRAWLER_AVAILABLE,
            key="crawl_button"
        )

    # 크롤링 실행
    if crawl_button and API_CRAWLER_AVAILABLE:
        target_gu = selected_gugun if selected_gugun != "전체" else None

        with st.spinner(f"서울 경매 물건을 검색 중입니다..."):
            crawled_items, total = crawl_auctions_api(
                gu_name=target_gu,
                page=1,
                page_size=100,
                property_type=property_type
            )

            if crawled_items:
                st.session_state["crawled_auctions"] = crawled_items
                st.session_state["crawled_total"] = total
                st.session_state["crawled_time"] = datetime.now()
                st.session_state["crawled_gu"] = target_gu or "서울 전체"
                st.success(f"**{len(crawled_items)}**개 물건 검색 완료! (전체 {total:,}건)")
            else:
                st.warning("검색 결과가 없습니다.")

    st.markdown("---")

    # 데이터 조회
    if show_favorites and user_id:
        auctions = get_user_favorites(user_id)
        total_count = len(auctions)
        data_source = "favorites"
    elif "crawled_auctions" in st.session_state and st.session_state.get("crawled_auctions"):
        auctions = st.session_state["crawled_auctions"]

        # 필터 적용
        filters = {
            "min_price": min_price,
            "max_price": max_price,
            "auction_counts": auction_counts,
            "risk_levels": risk_levels,
            "dong": selected_dong,
            "property_type": property_type,
        }
        auctions = apply_filters(auctions, filters)

        total_count = len(auctions)
        data_source = "crawled"
    else:
        # 샘플 데이터
        auctions = get_auctions(
            gugun=selected_gugun if selected_gugun != "전체" else None,
            dong=selected_dong,
            min_price=min_price,
            max_price=max_price,
            auction_counts=auction_counts,
            risk_levels=risk_levels,
        )
        total_count = len(auctions)
        data_source = "database"

    # 결과 카운트
    st.markdown(f"**{total_count}**개 물건")

    # 데이터 소스 표시
    if data_source == "crawled":
        crawled_time = st.session_state.get("crawled_time", datetime.now())
        crawled_gu = st.session_state.get("crawled_gu", "")
        crawled_total = st.session_state.get("crawled_total", 0)
        time_str = crawled_time.strftime("%H:%M")
        st.success(f"🔥 실시간 데이터 ({crawled_gu}, {time_str} 기준) - 전체 {crawled_total:,}건 중 {total_count}건 표시")
    elif data_source == "database":
        st.info("💡 샘플 데이터입니다. **[🔄 실시간 검색]** 버튼을 눌러 실제 데이터를 가져오세요.")

    # 관심 물건 ID
    favorite_ids = set()
    if user_id:
        favorites = get_user_favorites(user_id)
        favorite_ids = {f['id'] for f in favorites}

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

    if not auctions:
        st.info("조건에 맞는 물건이 없습니다. 필터를 조정하거나 **[🔄 실시간 검색]**을 눌러보세요.")
