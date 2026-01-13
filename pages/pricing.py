"""
서경아 요금제 페이지
토스페이먼츠 결제 연동
"""

import streamlit as st
from services.payment import (
    PRICE_PLANS,
    TOSS_CLIENT_KEY,
    TOSS_TEST_MODE,
    create_payment,
    generate_order_id,
    format_price,
)
from components.auth import get_current_user_id

# 페이지 설정
st.set_page_config(
    page_title="요금제 - 서경아",
    page_icon="💳",
    layout="wide",
)


def render_pricing_page():
    """요금제 페이지 렌더링"""

    st.markdown("# 💳 요금제")
    st.markdown("서경아 AI 경매 분석 서비스를 시작하세요")

    # 테스트 모드 알림
    if TOSS_TEST_MODE:
        st.info("🧪 **테스트 모드** - 실제 결제되지 않습니다")

    st.markdown("---")

    # 요금제 카드
    col1, col2, col3 = st.columns(3)

    # Basic 플랜
    with col1:
        render_plan_card(
            "basic",
            "Basic",
            "입문 투자자용",
            [
                ("월간", "basic_monthly", 9900),
                ("연간", "basic_yearly", 99000),
            ],
            features=[
                "AI 물건 분석 월 10건",
                "기본 권리분석",
                "관심물건 알림 50건",
            ],
            color="#4A90D9",
        )

    # Pro 플랜
    with col2:
        render_plan_card(
            "pro",
            "Pro",
            "적극 투자자용",
            [
                ("월간", "pro_monthly", 29900),
                ("연간", "pro_yearly", 299000),
            ],
            features=[
                "AI 분석 **무제한**",
                "고급 권리분석 (Claude AI)",
                "낙찰가 예측",
                "우선 알림",
                "API 접근",
            ],
            color="#9B59B6",
            recommended=True,
        )

    # 단건 리포트
    with col3:
        render_plan_card(
            "single",
            "단건 리포트",
            "한 건만 필요할 때",
            [
                ("1건", "single_report", 4900),
            ],
            features=[
                "AI 감정평가 요약",
                "상세 권리분석",
                "PDF 다운로드",
            ],
            color="#27AE60",
        )

    st.markdown("---")

    # 자주 묻는 질문
    render_faq()


def render_plan_card(
    plan_type: str,
    title: str,
    subtitle: str,
    options: list,
    features: list,
    color: str,
    recommended: bool = False,
):
    """요금제 카드 렌더링"""

    # 추천 배지
    if recommended:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {color}, {color}dd);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 8px;
            ">추천</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"### {title}")
    st.markdown(f"*{subtitle}*")

    # 가격 옵션
    if len(options) > 1:
        option_labels = [f"{opt[0]} {format_price(opt[2])}" for opt in options]
        selected_idx = st.radio(
            "결제 주기",
            range(len(options)),
            format_func=lambda i: option_labels[i],
            key=f"plan_{plan_type}_option",
            horizontal=True,
            label_visibility="collapsed",
        )
        selected_option = options[selected_idx]
    else:
        selected_option = options[0]

    plan_id = selected_option[1]
    price = selected_option[2]

    # 가격 표시
    st.markdown(f"## {format_price(price)}")

    # 연간 할인 표시
    if "yearly" in plan_id:
        monthly_equiv = price // 12
        st.markdown(f"*월 {format_price(monthly_equiv)} (17% 할인)*")

    st.markdown("---")

    # 기능 목록
    for feature in features:
        st.markdown(f"- {feature}")

    st.markdown("")

    # 결제 버튼
    user_id = get_current_user_id()

    if st.button(
        f"{title} 시작하기",
        key=f"btn_{plan_id}",
        type="primary" if recommended else "secondary",
        use_container_width=True,
    ):
        if not user_id:
            st.warning("로그인이 필요합니다")
            return

        # 결제 데이터 생성
        order_id = generate_order_id(user_id, plan_id)
        plan_info = PRICE_PLANS.get(plan_id, {})

        payment_data = create_payment(
            order_id=order_id,
            amount=price,
            order_name=f"서경아 {plan_info.get('name', title)}",
            customer_email=None,  # 사용자 이메일
        )

        # 세션에 결제 정보 저장
        st.session_state["pending_payment"] = {
            "order_id": order_id,
            "plan_id": plan_id,
            "amount": price,
            "payment_data": payment_data,
        }

        # 결제 모달 표시
        show_payment_modal(payment_data, plan_info)


def show_payment_modal(payment_data: dict, plan_info: dict):
    """결제 모달 표시"""

    st.markdown("---")
    st.markdown("### 결제 진행")

    # 토스페이먼츠 결제창 호출 스크립트
    # 실제로는 JavaScript SDK를 통해 결제창을 띄워야 함
    # Streamlit에서는 iframe 또는 외부 링크 방식 사용

    if TOSS_TEST_MODE:
        st.info("""
        **테스트 모드 안내**

        실제 서비스에서는 토스페이먼츠 결제창이 열립니다.
        현재는 테스트 모드이므로 결제가 진행되지 않습니다.

        **테스트 결제 방법:**
        1. 토스페이먼츠 개발자센터 가입
        2. 테스트 API 키 발급
        3. .env에 TOSS_CLIENT_KEY, TOSS_SECRET_KEY 설정
        """)

    # 결제 정보 표시
    st.markdown(f"""
    | 항목 | 내용 |
    |------|------|
    | 상품명 | {plan_info.get('name', '-')} |
    | 결제금액 | {format_price(payment_data['amount'])} |
    | 주문번호 | `{payment_data['orderId']}` |
    """)

    # 테스트용 결제 완료 버튼
    if TOSS_TEST_MODE:
        if st.button("테스트 결제 완료", type="primary"):
            st.success("결제가 완료되었습니다! (테스트)")
            st.balloons()

            # 실제로는 여기서 DB에 구독 정보 저장
            st.session_state["subscription"] = {
                "plan_id": st.session_state["pending_payment"]["plan_id"],
                "status": "active",
            }


def render_faq():
    """자주 묻는 질문"""

    st.markdown("### 자주 묻는 질문")

    with st.expander("무료 체험이 있나요?"):
        st.markdown("""
        네! 회원가입 후 **7일간 무료 체험**이 가능합니다.
        무료 체험 중에는 Basic 플랜의 모든 기능을 사용할 수 있습니다.
        """)

    with st.expander("언제든 해지할 수 있나요?"):
        st.markdown("""
        물론입니다. **언제든 해지 가능**하며, 해지 후에도 결제 기간이 끝날 때까지 서비스를 이용할 수 있습니다.
        환불은 결제일로부터 7일 이내에 요청 시 전액 환불됩니다.
        """)

    with st.expander("연간 결제의 장점은?"):
        st.markdown("""
        연간 결제 시 **2개월 무료** (17% 할인)가 적용됩니다.
        - Basic 월간: ₩9,900 × 12 = ₩118,800
        - Basic 연간: **₩99,000** (₩19,800 절약)
        """)

    with st.expander("Pro 플랜은 뭐가 다른가요?"):
        st.markdown("""
        Pro 플랜은 **전문 투자자**를 위한 플랜입니다:

        - **AI 분석 무제한**: 월 제한 없이 원하는 만큼 분석
        - **Claude AI 권리분석**: 더 정교한 AI 분석
        - **낙찰가 예측**: 과거 데이터 기반 예측
        - **API 접근**: 자동화 연동 가능
        """)

    with st.expander("결제 수단은?"):
        st.markdown("""
        **토스페이먼츠**를 통해 다양한 결제 수단을 지원합니다:
        - 신용카드/체크카드
        - 계좌이체
        - 간편결제 (토스, 카카오페이, 네이버페이 등)
        """)


# 메인
if __name__ == "__main__":
    render_pricing_page()
