"""
서경아 알림 서비스
- 카카오톡 알림 (D-3, D-1)
- 이메일 알림 (Resend)
"""
import os
import requests
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional


# 환경변수
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8502/callback")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")


# ================================
# 카카오톡 알림
# ================================

class KakaoNotifier:
    """카카오톡 알림 서비스"""

    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.api_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def send_message(self, message: Dict) -> bool:
        """카카오톡 메시지 발송"""
        if not self.access_token:
            print("[KAKAO] Access token이 없습니다.")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            # 텍스트 메시지 템플릿
            template = {
                "object_type": "text",
                "text": message.get("text", ""),
                "link": {
                    "web_url": message.get("url", "https://www.courtauction.go.kr"),
                    "mobile_web_url": message.get("url", "https://www.courtauction.go.kr"),
                },
                "button_title": message.get("button", "자세히 보기")
            }

            import json
            response = requests.post(
                self.api_url,
                headers=headers,
                data={"template_object": json.dumps(template)},
                timeout=10
            )

            if response.status_code == 200:
                print(f"[KAKAO] 메시지 발송 성공")
                return True
            else:
                print(f"[KAKAO] 발송 실패: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"[KAKAO] 오류: {e}")
            return False

    def send_auction_reminder(self, auction: Dict[str, Any], days_until: int) -> bool:
        """경매 입찰일 알림"""
        apt_name = auction.get('apt_name', '아파트')
        min_price = auction.get('min_price', 0)
        auction_date = auction.get('auction_date', '')

        # 가격 포맷
        if min_price >= 100000000:
            price_str = f"{min_price // 100000000}억"
        else:
            price_str = f"{min_price // 10000:,}만"

        # 긴급도에 따른 메시지
        if days_until <= 1:
            urgency = "🚨 [긴급]"
        elif days_until <= 3:
            urgency = "⚠️ [알림]"
        else:
            urgency = "📢 [안내]"

        message_text = f"""{urgency} 입찰일 D-{days_until}

🏠 {apt_name}
💰 최저가: {price_str}
📅 입찰일: {auction_date}

지금 바로 확인하세요!"""

        return self.send_message({
            "text": message_text,
            "url": "https://www.courtauction.go.kr",
            "button": "법원경매 바로가기"
        })


def get_kakao_auth_url() -> str:
    """카카오 로그인 인증 URL 생성"""
    if not KAKAO_REST_API_KEY:
        return ""

    return (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=talk_message"
    )


def get_kakao_token(auth_code: str) -> Optional[str]:
    """인증 코드로 액세스 토큰 발급"""
    if not KAKAO_REST_API_KEY:
        return None

    try:
        response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": KAKAO_REST_API_KEY,
                "redirect_uri": KAKAO_REDIRECT_URI,
                "code": auth_code,
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"[KAKAO] 토큰 발급 실패: {response.text}")
            return None

    except Exception as e:
        print(f"[KAKAO] 토큰 오류: {e}")
        return None


# ================================
# 이메일 알림 (Resend)
# ================================

def send_auction_reminder(user_email: str, auction: Dict[str, Any], days_until: int) -> bool:
    """입찰일 알림 발송 (이메일)"""

    apt_name = auction.get('apt_name', '아파트')
    address = auction.get('address', '')
    min_price = auction.get('min_price', 0)
    auction_date = auction.get('auction_date', '')

    # 가격 포맷
    if min_price >= 100000000:
        price_str = f"{min_price // 100000000}억원"
    else:
        price_str = f"{min_price // 10000:,}만원"

    subject = f"[서경아] {apt_name} 입찰일 D-{days_until}"

    if not RESEND_API_KEY:
        print(f"[EMAIL] 알림 발송 (미구현)")
        print(f"  To: {user_email}")
        print(f"  제목: {subject}")
        print(f"  내용: {apt_name} / {price_str} / {auction_date}")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1f2937;">🏠 입찰일 알림 (D-{days_until})</h2>

            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #374151;">{apt_name}</h3>
                <p style="margin: 5px 0; color: #6b7280;">{address}</p>
                <p style="margin: 10px 0; font-size: 24px; font-weight: bold; color: #2563eb;">
                    최저가: {price_str}
                </p>
                <p style="margin: 5px 0; color: #dc2626; font-weight: bold;">
                    📅 입찰일: {auction_date}
                </p>
            </div>

            <a href="https://www.courtauction.go.kr" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                법원경매 사이트 바로가기
            </a>

            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px;">
                이 메일은 서경아에서 발송되었습니다.
            </p>
        </div>
        """

        resend.Emails.send({
            "from": "서경아 <noreply@seogyeonga.com>",
            "to": user_email,
            "subject": subject,
            "html": html
        })
        return True

    except Exception as e:
        print(f"[EMAIL] 발송 오류: {e}")
        return False


def send_welcome_email(user_email: str, nickname: str = None) -> bool:
    """가입 환영 이메일"""

    if not RESEND_API_KEY:
        print(f"[EMAIL] 환영 이메일 (미구현)")
        print(f"  To: {user_email}")
        return False

    return False


# ================================
# 알림 스케줄러
# ================================

def check_and_send_reminders(favorites: List[Dict[str, Any]], user_tokens: Dict[str, str] = None):
    """
    관심 물건 입찰일 체크 및 알림 발송

    favorites: 사용자의 관심 물건 리스트
    user_tokens: {"email": "xxx", "kakao_token": "xxx"}
    """
    today = date.today()
    user_tokens = user_tokens or {}

    for auction in favorites:
        auction_date_str = auction.get('auction_date')
        if not auction_date_str:
            continue

        try:
            if isinstance(auction_date_str, str):
                auction_date = datetime.strptime(auction_date_str, "%Y-%m-%d").date()
            else:
                auction_date = auction_date_str
        except:
            continue

        days_until = (auction_date - today).days

        # D-3 또는 D-1 알림
        if days_until in [3, 1]:
            apt_name = auction.get('apt_name', '아파트')
            print(f"[REMINDER] {apt_name} - D-{days_until}")

            # 이메일 알림
            if user_tokens.get('email'):
                send_auction_reminder(user_tokens['email'], auction, days_until)

            # 카카오톡 알림
            if user_tokens.get('kakao_token'):
                notifier = KakaoNotifier(user_tokens['kakao_token'])
                notifier.send_auction_reminder(auction, days_until)


# 테스트
if __name__ == "__main__":
    sample_auction = {
        "apt_name": "테스트아파트",
        "address": "서울시 강남구 테스트동 123",
        "min_price": 500000000,
        "auction_date": "2024-02-15",
    }

    # 테스트 알림
    send_auction_reminder("test@example.com", sample_auction, 3)
    send_auction_reminder("test@example.com", sample_auction, 1)

    # 카카오 인증 URL 출력
    auth_url = get_kakao_auth_url()
    if auth_url:
        print(f"\n카카오 인증 URL: {auth_url}")
