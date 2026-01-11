"""
경매 물건 카드 컴포넌트 - Streamlit 네이티브 UI
"""
import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, Optional
from services import get_risk_emoji, get_risk_color


def calculate_days_until(auction_date) -> int:
    """입찰일까지 남은 일수"""
    if not auction_date:
        return 999
    if isinstance(auction_date, str):
        try:
            auction_date = datetime.strptime(auction_date, "%Y-%m-%d").date()
        except:
            return 999
    today = date.today()
    return (auction_date - today).days


def format_price(price: int) -> str:
    """가격 포맷 (억/만원)"""
    if not price:
        return "-"
    if price >= 100000000:
        억 = price // 100000000
        만 = (price % 100000000) // 10000
        if 만 > 0:
            return f"{억}억 {만:,}만"
        return f"{억}억"
    elif price >= 10000:
        return f"{price // 10000:,}만"
    return f"{price:,}"


def render_auction_card(
    auction: Dict[str, Any],
    is_favorite: bool = False,
    show_favorite_button: bool = True,
    on_favorite_click=None,
    user_id: Optional[int] = None
):
    """경매 물건 카드 렌더링 - Streamlit 네이티브"""

    # 데이터 추출
    apt_name = auction.get('apt_name', '아파트') or '아파트'
    address = auction.get('address', '')
    min_price = auction.get('min_price', 0)
    appraisal_price = auction.get('appraisal_price', 0)
    auction_date = auction.get('auction_date')
    auction_count = auction.get('auction_count', 1)
    risk_level = auction.get('risk_level', '주의')
    risk_reason = auction.get('risk_reason', '')
    area = auction.get('area', 0)
    court = auction.get('court', '')
    case_no = auction.get('case_no', '')
    auction_id = auction.get('id', apt_name)

    # 계산
    days_until = calculate_days_until(auction_date)
    risk_emoji = get_risk_emoji(risk_level)

    # 할인율
    if appraisal_price and min_price:
        discount = round((1 - min_price / appraisal_price) * 100)
    else:
        discount = 0

    # D-day 텍스트
    if days_until < 0:
        dday_text = "종료"
    else:
        dday_text = f"D-{days_until}"

    # 카드 컨테이너
    with st.container(border=True):
        # 이미지 + 기본정보
        col_img, col_info = st.columns([1, 2])

        with col_img:
            # 썸네일 이미지
            from services import get_sample_images
            images = get_sample_images(auction)
            if images:
                st.image(images[0], use_container_width=True)

        with col_info:
            # 헤더: 아파트명 + 차수 + 위험도
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown(f"**{apt_name}**")
                st.caption(f"{auction_count}차 경매")
            with header_col2:
                if risk_level == "안전":
                    st.success(f"{risk_emoji}")
                elif risk_level == "위험":
                    st.error(f"{risk_emoji}")
                else:
                    st.warning(f"{risk_emoji}")

            # 주소
            st.caption(address)

        # 가격 정보
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.metric("최저가", format_price(min_price))
        with col2:
            st.metric("감정가", format_price(appraisal_price))
        with col3:
            st.metric("할인율", f"-{discount}%")

        # 상세 정보
        st.markdown(f"📐 **{area}㎡** | 🏛️ {court} | 📋 {case_no}")

        # 입찰일 + D-day
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**입찰일:** {auction_date if auction_date else '-'}")
        with col2:
            if days_until <= 3 and days_until >= 0:
                st.error(dday_text)
            elif days_until < 0:
                st.text(dday_text)
            else:
                st.info(dday_text)

        # 위험 사유
        if risk_reason:
            st.warning(f"💡 {risk_reason}")

        # 버튼 영역
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔍 분석", key=f"analyze_{auction_id}", use_container_width=True):
                st.session_state[f"show_analysis_{auction_id}"] = True

        with col2:
            if st.button("📊 위험도", key=f"risk_{auction_id}", use_container_width=True):
                st.session_state[f"show_risk_{auction_id}"] = True

        with col3:
            if st.button("📋 감평서", key=f"appraisal_{auction_id}", use_container_width=True):
                st.session_state[f"show_appraisal_{auction_id}"] = True

        with col4:
            if show_favorite_button:
                icon = "⭐" if is_favorite else "☆"
                if st.button(icon, key=f"fav_{auction_id}", use_container_width=True):
                    if on_favorite_click:
                        on_favorite_click(auction_id)

        # 감정평가서 표시
        if st.session_state.get(f"show_appraisal_{auction_id}", False):
            st.divider()
            st.subheader("📋 감정평가서 요약")
            from services import get_sample_appraisal_data, summarize_appraisal_with_ai

            with st.spinner("감정평가서 분석 중..."):
                appraisal_data = get_sample_appraisal_data(auction)

            # 기본 정보
            info = appraisal_data.get("info", {})
            st.markdown(f"**{appraisal_data.get('summary', '')}**")

            # 권리사항
            if info.get("rights_analysis"):
                st.warning("⚠️ **권리사항**")
                for item in info["rights_analysis"]:
                    st.markdown(f"- {item}")

            # AI 요약 버튼
            if st.button("🤖 AI가 쉽게 설명해줘", key=f"ai_appraisal_{auction_id}"):
                with st.spinner("AI 분석 중..."):
                    ai_summary = summarize_appraisal_with_ai(appraisal_data)
                st.info(ai_summary)

            st.caption("*감정평가서 원본은 법원경매 사이트에서 확인하세요*")

            if st.button("닫기", key=f"close_appraisal_{auction_id}"):
                st.session_state[f"show_appraisal_{auction_id}"] = False
                st.rerun()

        # 위험도 차트 표시
        if st.session_state.get(f"show_risk_{auction_id}", False):
            st.divider()
            st.subheader("📊 위험도 분석")
            from components.risk_chart import render_risk_radar_chart
            render_risk_radar_chart(auction)
            if st.button("닫기", key=f"close_risk_{auction_id}"):
                st.session_state[f"show_risk_{auction_id}"] = False
                st.rerun()

        # AI 분석 결과 표시
        if st.session_state.get(f"show_analysis_{auction_id}", False):
            st.divider()
            st.subheader("📊 AI 권리분석 결과")
            from services import analyze_auction, generate_auction_report, get_report_filename
            with st.spinner("분석 중..."):
                analysis = analyze_auction(auction, provider="rule")
            st.markdown(analysis)

            # PDF 다운로드 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 PDF 리포트 생성", key=f"pdf_{auction_id}"):
                    with st.spinner("PDF 생성 중..."):
                        try:
                            pdf_bytes = generate_auction_report(auction, analysis)
                            filename = get_report_filename(auction)
                            st.session_state[f"pdf_data_{auction_id}"] = (pdf_bytes, filename)
                            st.success("PDF 생성 완료!")
                        except Exception as e:
                            st.error(f"PDF 생성 실패: {e}")

            # PDF 다운로드 링크
            if st.session_state.get(f"pdf_data_{auction_id}"):
                pdf_bytes, filename = st.session_state[f"pdf_data_{auction_id}"]
                with col2:
                    st.download_button(
                        label="⬇️ 다운로드",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        key=f"download_{auction_id}"
                    )

            if st.button("닫기", key=f"close_{auction_id}"):
                st.session_state[f"show_analysis_{auction_id}"] = False
                if f"pdf_data_{auction_id}" in st.session_state:
                    del st.session_state[f"pdf_data_{auction_id}"]
                st.rerun()


def render_auction_list(
    auctions: list,
    favorites: set = None,
    user_id: int = None,
    on_favorite_click=None
):
    """경매 물건 목록 렌더링"""

    if not auctions:
        st.info("조건에 맞는 물건이 없습니다.")
        return

    favorites = favorites or set()

    for auction in auctions:
        # dict 변환 (SQLAlchemy 모델인 경우)
        if hasattr(auction, '__dict__') and hasattr(auction, 'id'):
            auction_dict = {
                'id': auction.id,
                'apt_name': auction.apt_name,
                'address': auction.address,
                'min_price': auction.min_price,
                'appraisal_price': auction.appraisal_price,
                'auction_date': str(auction.auction_date) if auction.auction_date else None,
                'auction_count': auction.auction_count,
                'risk_level': auction.risk_level,
                'risk_reason': auction.risk_reason,
                'area': auction.area,
                'court': auction.court,
                'case_no': auction.case_no,
            }
        else:
            auction_dict = auction

        is_fav = auction_dict.get('id') in favorites
        render_auction_card(
            auction_dict,
            is_favorite=is_fav,
            show_favorite_button=user_id is not None,
            on_favorite_click=on_favorite_click,
            user_id=user_id
        )
