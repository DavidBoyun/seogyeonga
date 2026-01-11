"""
사건번호 조회 페이지
작동하는 API를 사용하여 실제 경매 정보 조회
"""
import streamlit as st
import json
from services.court_crawler import (
    CourtAuctionCrawler,
    COURT_CODES,
    SEOUL_COURTS,
    format_case_number_for_api
)
from services import analyze_auction, generate_auction_report, get_report_filename
from components.risk_chart import render_risk_radar_chart


def render_case_lookup():
    """사건번호 조회 페이지 렌더링"""

    st.header("🔍 사건번호 조회")
    st.markdown("""
    법원경매 사이트에서 관심 물건의 **사건번호**를 입력하면
    AI가 분석해드립니다.
    """)

    # 입력 폼
    with st.form("case_lookup_form"):
        col1, col2 = st.columns([1, 2])

        with col1:
            # 법원 선택
            court_options = list(COURT_CODES.keys())
            # 서울 법원을 먼저 표시
            seoul_courts = [c for c in court_options if "서울" in c]
            other_courts = [c for c in court_options if "서울" not in c]
            sorted_courts = seoul_courts + other_courts

            selected_court = st.selectbox(
                "법원 선택",
                sorted_courts,
                index=0,
                help="물건이 등록된 법원을 선택하세요"
            )

        with col2:
            # 사건번호 입력
            case_no = st.text_input(
                "사건번호",
                placeholder="예: 2024타경12345",
                help="'타경' 포함 전체 사건번호를 입력하세요"
            )

        # 조회할 정보 선택
        info_types = st.multiselect(
            "조회할 정보",
            ["사건내역", "기일내역", "문건송달내역"],
            default=["사건내역"],
            help="조회하고 싶은 정보를 선택하세요"
        )

        submitted = st.form_submit_button("🔍 조회하기", use_container_width=True)

    # 예시 안내
    with st.expander("💡 사건번호 찾는 방법"):
        st.markdown("""
        1. [법원경매 사이트](https://www.courtauction.go.kr) 접속
        2. 관심 물건 검색
        3. 물건 상세 페이지에서 **사건번호** 확인
        4. 예: `2024타경12345` 형식

        **사건번호 형식:**
        - `연도` + `타경` + `번호`
        - 예: 2024타경12345, 2023타경98765
        """)

    # 조회 실행
    if submitted and case_no:
        # 입력 검증
        if "타경" not in case_no:
            st.error("사건번호에 '타경'이 포함되어야 합니다. 예: 2024타경12345")
            return

        # 크롤러 초기화
        crawler = CourtAuctionCrawler()

        # 각 정보 유형별 조회
        results = {}

        with st.spinner(f"'{case_no}' 조회 중..."):
            for info_type in info_types:
                result = crawler.get_case_detail(
                    court_name=selected_court,
                    case_no=case_no,
                    tab=info_type
                )
                results[info_type] = result

        # 결과 표시
        if any(results.values()):
            st.success(f"✅ 조회 완료: {selected_court} {case_no}")

            # 탭으로 결과 표시
            if len(info_types) > 1:
                result_tabs = st.tabs(info_types)
                for i, info_type in enumerate(info_types):
                    with result_tabs[i]:
                        display_result(info_type, results[info_type], case_no, selected_court)
            else:
                display_result(info_types[0], results[info_types[0]], case_no, selected_court)

            # AI 분석 섹션
            st.divider()
            render_ai_analysis(results, case_no, selected_court)

        else:
            st.warning("""
            조회 결과가 없습니다.

            **확인사항:**
            - 사건번호가 정확한가요?
            - 올바른 법원을 선택했나요?
            - 해당 사건이 현재 진행 중인가요?
            """)

    # 최근 조회 기록
    render_recent_lookups()


def display_result(info_type: str, data: dict, case_no: str, court: str):
    """조회 결과 표시"""

    if not data:
        st.info(f"{info_type} 정보가 없습니다.")
        return

    st.subheader(f"📋 {info_type}")

    if info_type == "사건내역":
        display_case_info(data)
    elif info_type == "기일내역":
        display_schedule_info(data)
    elif info_type == "문건송달내역":
        display_document_info(data)

    # 원본 데이터 보기 (접기)
    with st.expander("🔧 원본 데이터 (개발자용)"):
        st.json(data)


def display_case_info(data: dict):
    """사건내역 표시"""

    # 기본 정보 추출 (API 응답 구조에 따라 조정 필요)
    if isinstance(data, dict):
        # 리스트인 경우
        if "list" in data:
            items = data["list"]
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        for item in items[:5]:  # 최대 5개
            if isinstance(item, dict):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**물건 정보**")
                    st.write(f"- 소재지: {item.get('jbrsAddr', item.get('address', '-'))}")
                    st.write(f"- 물건종류: {item.get('mtrKndNm', item.get('propertyType', '-'))}")
                    st.write(f"- 면적: {item.get('excsvAr', item.get('area', '-'))}㎡")

                with col2:
                    st.markdown("**가격 정보**")
                    appraisal = item.get('aeeEvlAmt', item.get('appraisalPrice', 0))
                    min_price = item.get('lwsDspslPrc', item.get('minPrice', 0))

                    if appraisal:
                        st.write(f"- 감정가: {int(appraisal):,}원")
                    if min_price:
                        st.write(f"- 최저가: {int(min_price):,}원")
                    if appraisal and min_price:
                        discount = round((1 - min_price / appraisal) * 100)
                        st.write(f"- 할인율: {discount}%")

                st.divider()
    else:
        st.write(data)


def display_schedule_info(data: dict):
    """기일내역 표시"""

    if isinstance(data, dict) and "list" in data:
        items = data["list"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data] if data else []

    if items:
        for item in items[:10]:
            if isinstance(item, dict):
                date = item.get('dxdyDt', item.get('date', '-'))
                result = item.get('dxdyRsltNm', item.get('result', '-'))
                place = item.get('dxdyPlc', item.get('place', '-'))

                st.markdown(f"""
                - **{date}** | {result} | {place}
                """)
    else:
        st.info("기일내역이 없습니다.")


def display_document_info(data: dict):
    """문건송달내역 표시"""

    if isinstance(data, dict) and "list" in data:
        items = data["list"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data] if data else []

    if items:
        for item in items[:10]:
            if isinstance(item, dict):
                doc_name = item.get('ofdocNm', item.get('docName', '-'))
                send_date = item.get('sndngDt', item.get('sendDate', '-'))
                recv_date = item.get('rcptDt', item.get('recvDate', '-'))

                st.markdown(f"- **{doc_name}** | 송달: {send_date} | 수령: {recv_date}")
    else:
        st.info("문건송달내역이 없습니다.")


def render_ai_analysis(results: dict, case_no: str, court: str):
    """AI 분석 섹션"""

    st.subheader("🤖 AI 분석")

    # 사건내역에서 물건 정보 추출
    case_data = results.get("사건내역", {})

    # 분석용 데이터 구성
    auction_data = {
        "id": case_no,
        "case_no": case_no,
        "court": court,
        "apt_name": "조회된 물건",
        "address": "",
        "appraisal_price": 0,
        "min_price": 0,
        "auction_count": 1,
        "risk_level": "주의",
    }

    # API 결과에서 데이터 추출
    if isinstance(case_data, dict):
        items = case_data.get("list", [case_data])
        if items and isinstance(items[0], dict):
            item = items[0]
            auction_data.update({
                "address": item.get('jbrsAddr', item.get('address', '')),
                "apt_name": item.get('mtrNm', item.get('bldgNm', '조회된 물건')),
                "appraisal_price": int(item.get('aeeEvlAmt', 0) or 0),
                "min_price": int(item.get('lwsDspslPrc', 0) or 0),
                "area": float(item.get('excsvAr', 0) or 0),
            })

    col1, col2 = st.columns([2, 1])

    with col1:
        # AI 분석 버튼
        if st.button("🔍 AI 권리분석 실행", use_container_width=True):
            with st.spinner("AI가 분석 중입니다..."):
                analysis = analyze_auction(auction_data, provider="rule")

            st.markdown("### 분석 결과")
            st.markdown(analysis)

            # 세션에 저장
            st.session_state[f"analysis_{case_no}"] = analysis
            st.session_state[f"auction_data_{case_no}"] = auction_data

    with col2:
        # 위험도 차트
        st.markdown("### 위험도 평가")
        render_risk_radar_chart(auction_data)

    # PDF 리포트 생성
    if f"analysis_{case_no}" in st.session_state:
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 PDF 리포트 생성", use_container_width=True):
                with st.spinner("PDF 생성 중..."):
                    try:
                        analysis = st.session_state[f"analysis_{case_no}"]
                        auction = st.session_state[f"auction_data_{case_no}"]

                        pdf_bytes = generate_auction_report(auction, analysis)
                        filename = get_report_filename(auction)

                        st.session_state[f"pdf_{case_no}"] = (pdf_bytes, filename)
                        st.success("PDF 생성 완료!")
                    except Exception as e:
                        st.error(f"PDF 생성 실패: {e}")

        with col2:
            if f"pdf_{case_no}" in st.session_state:
                pdf_bytes, filename = st.session_state[f"pdf_{case_no}"]
                st.download_button(
                    "⬇️ PDF 다운로드",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )


def render_recent_lookups():
    """최근 조회 기록"""

    # 세션에서 조회 기록 가져오기
    if "lookup_history" not in st.session_state:
        st.session_state.lookup_history = []

    history = st.session_state.lookup_history

    if history:
        st.divider()
        st.subheader("📜 최근 조회")

        for item in history[-5:][::-1]:  # 최근 5개, 역순
            st.markdown(f"- {item['court']} **{item['case_no']}** ({item['time']})")


def add_to_history(court: str, case_no: str):
    """조회 기록 추가"""
    from datetime import datetime

    if "lookup_history" not in st.session_state:
        st.session_state.lookup_history = []

    st.session_state.lookup_history.append({
        "court": court,
        "case_no": case_no,
        "time": datetime.now().strftime("%m/%d %H:%M")
    })
