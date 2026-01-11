"""
서경아 설정
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 앱 정보
APP_NAME = "서경아"
APP_VERSION = "1.0.0"

# 카카오맵 (미구현 - 플레이스홀더)
KAKAO_MAP_API_KEY = os.getenv("KAKAO_MAP_API_KEY", "")

# OAuth (미구현 - 플레이스홀더)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# 이메일 (미구현 - 플레이스홀더)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# DB
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database", "seogyeonga.db")

# ========== 크롤링 설정 ==========
COURT_AUCTION_URL = "https://www.courtauction.go.kr"
SEOUL_SIDO_CODE = "11"  # 서울

# 타겟 물건 종류
TARGET_ITEM_TYPES = ["아파트", "주상복합"]

# 크롤링 딜레이 (초)
CRAWL_DELAY = 1.0
PAGE_DELAY = 0.5

# 서울 시군구 코드
SEOUL_SIGU_CODES = {
    "강남구": "680",
    "서초구": "740",
    "송파구": "500",
    "강동구": "530",
    "마포구": "440",
    "영등포구": "620",
    "용산구": "320",
    "성동구": "260",
    "광진구": "290",
    "중구": "140",
    "종로구": "110",
    "노원구": "410",
    "도봉구": "380",
    "강북구": "350",
    "성북구": "230",
    "동대문구": "200",
    "중랑구": "170",
    "은평구": "470",
    "서대문구": "350",
    "양천구": "560",
    "강서구": "590",
    "구로구": "650",
    "금천구": "710",
    "동작구": "770",
    "관악구": "800",
}

# 서울 구 목록
SEOUL_GUGUN = [
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구"
]

# 법원 코드
COURT_CODES = {
    "서울중앙지방법원": "B000210",
    "서울동부지방법원": "B000211",
    "서울서부지방법원": "B000215",
    "서울남부지방법원": "B000212",
    "서울북부지방법원": "B000213",
}

# 법원 목록
COURTS = [
    "서울중앙지방법원",
    "서울동부지방법원",
    "서울서부지방법원",
    "서울남부지방법원",
    "서울북부지방법원",
]
