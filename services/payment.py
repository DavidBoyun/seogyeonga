"""
서경아 결제 서비스 모듈
토스페이먼츠 연동

사용법:
1. 토스페이먼츠 개발자센터에서 API 키 발급
2. .env에 TOSS_CLIENT_KEY, TOSS_SECRET_KEY 설정
3. 테스트 모드에서 개발 후 라이브 모드로 전환
"""

import os
import base64
import requests
import hashlib
import hmac
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ================================
# 설정
# ================================

# 토스페이먼츠 API 키
TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "")
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "")

# API 엔드포인트
TOSS_API_URL = "https://api.tosspayments.com/v1"

# 테스트 모드 (개발용)
TOSS_TEST_MODE = os.getenv("TOSS_TEST_MODE", "true").lower() == "true"

# 테스트용 키 (토스페이먼츠 공식 테스트 키)
if TOSS_TEST_MODE and not TOSS_CLIENT_KEY:
    TOSS_CLIENT_KEY = "test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq"
    TOSS_SECRET_KEY = "test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R"


# ================================
# 가격 플랜
# ================================

PRICE_PLANS = {
    "basic_monthly": {
        "id": "basic_monthly",
        "name": "Basic 월간",
        "price": 9900,
        "period": "monthly",
        "features": [
            "AI 물건 분석 월 10건",
            "기본 권리분석",
            "관심물건 알림 50건",
        ],
        "analysis_limit": 10,
    },
    "basic_yearly": {
        "id": "basic_yearly",
        "name": "Basic 연간",
        "price": 99000,  # 2개월 무료
        "period": "yearly",
        "features": [
            "AI 물건 분석 월 10건",
            "기본 권리분석",
            "관심물건 알림 50건",
            "2개월 무료 (17% 할인)",
        ],
        "analysis_limit": 10,
    },
    "pro_monthly": {
        "id": "pro_monthly",
        "name": "Pro 월간",
        "price": 29900,
        "period": "monthly",
        "features": [
            "AI 분석 무제한",
            "고급 권리분석 (Claude)",
            "낙찰가 예측",
            "우선 알림",
            "API 접근",
        ],
        "analysis_limit": -1,  # 무제한
    },
    "pro_yearly": {
        "id": "pro_yearly",
        "name": "Pro 연간",
        "price": 299000,  # 2개월 무료
        "period": "yearly",
        "features": [
            "AI 분석 무제한",
            "고급 권리분석 (Claude)",
            "낙찰가 예측",
            "우선 알림",
            "API 접근",
            "2개월 무료 (17% 할인)",
        ],
        "analysis_limit": -1,
    },
    "single_report": {
        "id": "single_report",
        "name": "단건 리포트",
        "price": 4900,
        "period": "once",
        "features": [
            "AI 감정평가 요약 1건",
            "권리분석 리포트",
            "PDF 다운로드",
        ],
        "analysis_limit": 1,
    },
}


# ================================
# 토스페이먼츠 API
# ================================

def get_auth_header() -> Dict[str, str]:
    """토스페이먼츠 인증 헤더 생성"""
    # Base64 인코딩: secretKey:
    auth_string = f"{TOSS_SECRET_KEY}:"
    encoded = base64.b64encode(auth_string.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


def create_payment(
    order_id: str,
    amount: int,
    order_name: str,
    customer_email: str = None,
    customer_name: str = None,
) -> Dict:
    """
    결제 준비 (결제창 호출용 데이터 생성)

    실제 결제는 클라이언트에서 토스 SDK로 진행
    이 함수는 결제 정보를 준비하는 역할
    """
    return {
        "clientKey": TOSS_CLIENT_KEY,
        "orderId": order_id,
        "amount": amount,
        "orderName": order_name,
        "customerEmail": customer_email,
        "customerName": customer_name,
        "successUrl": f"{os.getenv('APP_URL', 'http://localhost:8501')}/payment/success",
        "failUrl": f"{os.getenv('APP_URL', 'http://localhost:8501')}/payment/fail",
    }


def confirm_payment(payment_key: str, order_id: str, amount: int) -> Tuple[bool, Dict]:
    """
    결제 승인 (서버에서 호출)

    토스 결제창에서 결제 완료 후 서버에서 최종 승인

    Args:
        payment_key: 토스에서 발급한 결제 키
        order_id: 주문 ID
        amount: 결제 금액

    Returns:
        (성공 여부, 응답 데이터)
    """
    try:
        response = requests.post(
            f"{TOSS_API_URL}/payments/confirm",
            headers=get_auth_header(),
            json={
                "paymentKey": payment_key,
                "orderId": order_id,
                "amount": amount,
            },
            timeout=30,
        )

        data = response.json()

        if response.status_code == 200:
            return True, data
        else:
            return False, data

    except Exception as e:
        return False, {"error": str(e)}


def get_payment(payment_key: str) -> Tuple[bool, Dict]:
    """결제 정보 조회"""
    try:
        response = requests.get(
            f"{TOSS_API_URL}/payments/{payment_key}",
            headers=get_auth_header(),
            timeout=30,
        )

        data = response.json()
        return response.status_code == 200, data

    except Exception as e:
        return False, {"error": str(e)}


def cancel_payment(
    payment_key: str,
    cancel_reason: str,
    cancel_amount: int = None,
) -> Tuple[bool, Dict]:
    """결제 취소"""
    try:
        payload = {"cancelReason": cancel_reason}
        if cancel_amount:
            payload["cancelAmount"] = cancel_amount

        response = requests.post(
            f"{TOSS_API_URL}/payments/{payment_key}/cancel",
            headers=get_auth_header(),
            json=payload,
            timeout=30,
        )

        data = response.json()
        return response.status_code == 200, data

    except Exception as e:
        return False, {"error": str(e)}


# ================================
# 빌링 (정기결제)
# ================================

def create_billing_key(
    customer_key: str,
    auth_key: str,
) -> Tuple[bool, Dict]:
    """
    빌링키 발급 (정기결제용)

    카드 정보 등록 후 빌링키 발급
    """
    try:
        response = requests.post(
            f"{TOSS_API_URL}/billing/authorizations/issue",
            headers=get_auth_header(),
            json={
                "customerKey": customer_key,
                "authKey": auth_key,
            },
            timeout=30,
        )

        data = response.json()
        return response.status_code == 200, data

    except Exception as e:
        return False, {"error": str(e)}


def charge_billing(
    billing_key: str,
    customer_key: str,
    amount: int,
    order_id: str,
    order_name: str,
) -> Tuple[bool, Dict]:
    """
    빌링키로 결제 (정기결제 실행)
    """
    try:
        response = requests.post(
            f"{TOSS_API_URL}/billing/{billing_key}",
            headers=get_auth_header(),
            json={
                "customerKey": customer_key,
                "amount": amount,
                "orderId": order_id,
                "orderName": order_name,
            },
            timeout=30,
        )

        data = response.json()
        return response.status_code == 200, data

    except Exception as e:
        return False, {"error": str(e)}


# ================================
# 헬퍼 함수
# ================================

def generate_order_id(user_id: str, plan_id: str) -> str:
    """주문 ID 생성"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"SGY_{user_id}_{plan_id}_{timestamp}"


def get_plan_info(plan_id: str) -> Optional[Dict]:
    """플랜 정보 조회"""
    return PRICE_PLANS.get(plan_id)


def calculate_subscription_end(plan_id: str, start_date: datetime = None) -> datetime:
    """구독 종료일 계산"""
    if start_date is None:
        start_date = datetime.now()

    plan = PRICE_PLANS.get(plan_id)
    if not plan:
        return start_date

    if plan["period"] == "monthly":
        return start_date + timedelta(days=30)
    elif plan["period"] == "yearly":
        return start_date + timedelta(days=365)
    else:
        return start_date


def format_price(price: int) -> str:
    """가격 포맷팅"""
    return f"₩{price:,}"


# ================================
# 테스트
# ================================

if __name__ == "__main__":
    print("=" * 60)
    print("Payment Service Test")
    print("=" * 60)

    print(f"\nTest Mode: {TOSS_TEST_MODE}")
    print(f"Client Key: {TOSS_CLIENT_KEY[:20]}...")

    print("\n--- Price Plans ---")
    for plan_id, plan in PRICE_PLANS.items():
        print(f"{plan['name']}: KRW {plan['price']:,}")

    print("\n--- Generate Order ID ---")
    order_id = generate_order_id("user123", "basic_monthly")
    print(f"Order ID: {order_id}")

    print("\n--- Create Payment Data ---")
    payment_data = create_payment(
        order_id=order_id,
        amount=9900,
        order_name="서경아 Basic 월간 구독",
        customer_email="test@example.com",
    )
    print(f"Payment Data: {payment_data}")
