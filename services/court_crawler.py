"""
법원경매 크롤러 - 신규 /pgj/ API 대응
WebSquare 기반 시스템 + 전국 74개 법원 지원
"""
import os
import re
import json
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from bs4 import BeautifulSoup


# ============================================================
# 기본 설정
# ============================================================
COURT_BASE_URL = "https://www.courtauction.go.kr"

# API 엔드포인트 (확인된 작동 API)
API_ENDPOINTS = {
    "사건내역": f"{COURT_BASE_URL}/pgj/pgj15A/selectAuctnCsSrchRslt.on",
    "기일내역": f"{COURT_BASE_URL}/pgj/pgj15A/selectCsDtlDxdyDts.on",
    "문건송달내역": f"{COURT_BASE_URL}/pgj/pgj15A/selectDlvrOfdocDtsDtl.on",
    # 물건목록 검색 (추가 분석 필요)
    "물건검색": f"{COURT_BASE_URL}/pgj/pgjsearch/searchControllerMain.on",
}

# 기본 헤더
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


# ============================================================
# 전국 74개 법원 코드 (courtAuctionCrawler 참고)
# ============================================================
COURT_CODES = {
    # 서울
    "서울중앙지방법원": "B000210",
    "서울동부지방법원": "B000211",
    "서울남부지방법원": "B000212",
    "서울북부지방법원": "B000213",
    "서울서부지방법원": "B000215",
    # 경기
    "의정부지방법원": "B000214",
    "고양지원": "B214807",
    "남양주지원": "B214804",
    "수원지방법원": "B000250",
    "성남지원": "B000251",
    "여주지원": "B000252",
    "평택지원": "B000253",
    "안산지원": "B250826",
    "안양지원": "B000254",
    # 인천
    "인천지방법원": "B000240",
    "부천지원": "B000241",
    # 강원
    "춘천지방법원": "B000260",
    "강릉지원": "B000261",
    "원주지원": "B000262",
    "속초지원": "B000263",
    "영월지원": "B000264",
    # 충북
    "청주지방법원": "B000270",
    "충주지원": "B000271",
    "제천지원": "B000272",
    "영동지원": "B000273",
    # 충남/대전
    "대전지방법원": "B000280",
    "홍성지원": "B000281",
    "논산지원": "B000282",
    "천안지원": "B000283",
    "공주지원": "B000284",
    "서산지원": "B000285",
    # 경북/대구
    "대구지방법원": "B000310",
    "안동지원": "B000311",
    "경주지원": "B000312",
    "김천지원": "B000313",
    "상주지원": "B000314",
    "의성지원": "B000315",
    "영덕지원": "B000316",
    "포항지원": "B000317",
    "대구서부지원": "B000320",
    # 경남/부산/울산
    "부산지방법원": "B000410",
    "부산동부지원": "B000412",
    "부산서부지원": "B000414",
    "울산지방법원": "B000411",
    "창원지방법원": "B000420",
    "마산지원": "B000431",
    "진주지원": "B000421",
    "통영지원": "B000422",
    "밀양지원": "B000423",
    "거창지원": "B000424",
    # 전남/광주
    "광주지방법원": "B000510",
    "목포지원": "B000511",
    "장흥지원": "B000512",
    "순천지원": "B000513",
    "해남지원": "B000514",
    # 전북
    "전주지방법원": "B000520",
    "군산지원": "B000521",
    "정읍지원": "B000522",
    "남원지원": "B000523",
    # 제주
    "제주지방법원": "B000530",
}

# 역방향 조회용
COURT_CODES_REVERSE = {v: k for k, v in COURT_CODES.items()}

# 서울 법원 목록
SEOUL_COURTS = [
    "서울중앙지방법원",
    "서울동부지방법원",
    "서울남부지방법원",
    "서울북부지방법원",
    "서울서부지방법원",
]


# ============================================================
# 서울 시군구 코드
# ============================================================
SEOUL_SIDO_CODE = "11"

SEOUL_SGG_CODES = {
    "강남구": "11680",
    "강동구": "11740",
    "강북구": "11305",
    "강서구": "11500",
    "관악구": "11620",
    "광진구": "11215",
    "구로구": "11530",
    "금천구": "11545",
    "노원구": "11350",
    "도봉구": "11320",
    "동대문구": "11230",
    "동작구": "11590",
    "마포구": "11440",
    "서대문구": "11410",
    "서초구": "11650",
    "성동구": "11200",
    "성북구": "11290",
    "송파구": "11710",
    "양천구": "11470",
    "영등포구": "11560",
    "용산구": "11170",
    "은평구": "11380",
    "종로구": "11110",
    "중구": "11140",
    "중랑구": "11260",
}


# ============================================================
# 사건번호 파싱 유틸리티
# ============================================================
def parse_case_number(case_no: str) -> Tuple[str, str]:
    """
    사건번호를 연도와 번호로 분리

    Args:
        case_no: 사건번호 (예: "2022타경3944" 또는 "2024타경12345")

    Returns:
        (연도, 번호6자리) 튜플
    """
    # "2022타경3944" -> ("2022", "003944")
    match = re.match(r"(\d{4})타경(\d+)", case_no)
    if match:
        year = match.group(1)
        number = match.group(2).zfill(6)  # 6자리로 패딩
        return year, number
    return "", ""


def format_case_number_for_api(case_no: str) -> str:
    """
    API 요청용 사건번호 포맷

    Args:
        case_no: 사건번호 (예: "2022타경3944")

    Returns:
        API 형식 (예: "202201300003944")
    """
    year, number = parse_case_number(case_no)
    if year and number:
        return f"{year}0130{number}"
    return case_no


# ============================================================
# 메인 크롤러 클래스
# ============================================================
class CourtAuctionCrawler:
    """법원경매 크롤러 (신규 API)"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._initialized = False

    def _init_session(self) -> bool:
        """세션 초기화 (쿠키 획득)"""
        if self._initialized:
            return True

        try:
            # 메인 페이지 접속하여 세션 쿠키 획득
            response = self.session.get(
                f"{COURT_BASE_URL}/pgj/index.on",
                timeout=15
            )

            if response.status_code == 200:
                # Referer 헤더 추가
                self.session.headers.update({
                    "Referer": f"{COURT_BASE_URL}/pgj/index.on"
                })
                self._initialized = True
                print(f"[CRAWLER] 세션 초기화 성공")
                return True
            else:
                print(f"[CRAWLER] 세션 초기화 실패: {response.status_code}")
                return False

        except Exception as e:
            print(f"[CRAWLER] 세션 초기화 오류: {e}")
            return False

    def get_case_detail(
        self,
        court_name: str,
        case_no: str,
        tab: str = "사건내역"
    ) -> Optional[Dict[str, Any]]:
        """
        사건 상세 정보 조회 (확인된 작동 API)

        Args:
            court_name: 법원명 (예: "서울중앙지방법원")
            case_no: 사건번호 (예: "2022타경3944")
            tab: 조회할 정보 종류 ("사건내역", "기일내역", "문건송달내역")

        Returns:
            상세 정보 딕셔너리 또는 None
        """
        if not self._init_session():
            return None

        court_code = COURT_CODES.get(court_name)
        if not court_code:
            print(f"[CRAWLER] 알 수 없는 법원: {court_name}")
            return None

        # 사건번호 포맷
        formatted_case_no = format_case_number_for_api(case_no)

        # API URL
        api_url = API_ENDPOINTS.get(tab)
        if not api_url:
            print(f"[CRAWLER] 알 수 없는 탭: {tab}")
            return None

        # 페이로드 키 매핑
        payload_keys = {
            "사건내역": "dma_srchCsDtlInf",
            "기일내역": "dma_srchDxdyDtsLst",
            "문건송달내역": "dma_srchDlvrOfdocDts",
        }

        payload_key = payload_keys.get(tab, "dma_srchCsDtlInf")

        # 페이로드 구성
        payload = {
            payload_key: {
                "cortOfcCd": court_code,
                "csNo": formatted_case_no,
            }
        }

        # 문건송달내역의 경우 추가 파라미터
        if tab == "문건송달내역":
            payload[payload_key]["srchFlag"] = "F"

        try:
            response = self.session.post(
                api_url,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get("data")
                except json.JSONDecodeError:
                    print(f"[CRAWLER] JSON 파싱 실패")
                    return None
            else:
                print(f"[CRAWLER] API 요청 실패: {response.status_code}")
                return None

        except Exception as e:
            print(f"[CRAWLER] 요청 오류: {e}")
            return None

    def search_auctions(
        self,
        sido_code: str = SEOUL_SIDO_CODE,
        sgg_code: str = None,
        page: int = 1,
        page_size: int = 20,
        property_type: str = "아파트"
    ) -> Dict[str, Any]:
        """
        경매 물건 검색

        주의: 검색 API는 아직 완전히 분석되지 않음
        현재는 샘플 데이터 반환

        Args:
            sido_code: 시도 코드 (서울: 11)
            sgg_code: 시군구 코드 (강남구: 11680)
            page: 페이지 번호
            page_size: 페이지 크기
            property_type: 물건 종류

        Returns:
            검색 결과 딕셔너리
        """
        if not self._init_session():
            return {"items": [], "total": 0, "error": "세션 초기화 실패"}

        # 검색 API 시도 (WebSquare 파라미터)
        search_params = {
            "dma_srchMtrInfoLst": {
                "mvprpRletDvsCd": "1",  # 부동산
                "rprsAdongSdCd": sido_code,
                "rprsAdongSggCd": sgg_code or "",
                "pageNo": str(page),
                "rowPerPage": str(page_size),
                "objctCdLarClsCd": "001",  # 주거용
                "objctCdMidClsCd": "001001",  # 집합건물
            }
        }

        if property_type == "아파트":
            search_params["dma_srchMtrInfoLst"]["objctCdSmlClsCd"] = "001001001"

        try:
            response = self.session.post(
                API_ENDPOINTS["물건검색"],
                json=search_params,
                timeout=30
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    return self._parse_search_result(data)
                except json.JSONDecodeError:
                    # HTML 응답인 경우 파싱 시도
                    if "html" in response.headers.get("Content-Type", "").lower():
                        return self._parse_html_result(response.text)
                    return {"items": [], "total": 0, "error": "응답 파싱 실패"}
            else:
                print(f"[CRAWLER] 검색 실패: {response.status_code}")
                # 샘플 데이터 반환 (개발용)
                return self._get_sample_data(sgg_code)

        except Exception as e:
            print(f"[CRAWLER] 검색 오류: {e}")
            return self._get_sample_data(sgg_code)

    def _parse_search_result(self, data: Dict) -> Dict[str, Any]:
        """JSON 검색 결과 파싱"""
        items = []

        # WebSquare 응답 구조에 따라 파싱
        result_list = data.get("data", {}).get("list", [])
        if not result_list:
            result_list = data.get("list", [])
        if not result_list:
            result_list = data.get("data", {}).get("dlt_srchMtrInfoLst", [])

        for item in result_list:
            auction = {
                "id": item.get("caseNo") or item.get("cano") or item.get("csNo"),
                "court": item.get("cortNm") or item.get("courtName") or item.get("cortOfcNm"),
                "case_no": item.get("caseNo") or item.get("cano") or item.get("csNo"),
                "apt_name": item.get("objctNm") or item.get("bldgNm") or item.get("mtrNm"),
                "address": item.get("adrJbrs") or item.get("address") or item.get("jbrsAddr"),
                "area": float(item.get("ar", 0) or item.get("area", 0) or item.get("excsvAr", 0)),
                "appraisal_price": int(item.get("aeeEvlAmt", 0) or item.get("appraisedValue", 0)),
                "min_price": int(item.get("lwsDspslPrc", 0) or item.get("minBidPrice", 0)),
                "auction_date": item.get("saleDtm") or item.get("auctionDate") or item.get("dxdyDt"),
                "auction_count": int(item.get("slbdNo", 1) or item.get("bidCount", 1)),
                "status": item.get("prcsSttsCd") or item.get("status"),
            }
            items.append(auction)

        return {
            "items": items,
            "total": data.get("totalCount", len(items)),
            "page": data.get("pageNo", 1),
        }

    def _parse_html_result(self, html: str) -> Dict[str, Any]:
        """HTML 응답 파싱 (폴백)"""
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        # 테이블 형식 파싱 시도
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # 헤더 제외
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:
                    # 테이블 구조에 따라 파싱
                    items.append({
                        "id": cells[0].get_text(strip=True),
                        "case_no": cells[0].get_text(strip=True),
                        "address": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "apt_name": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                    })

        return {
            "items": items,
            "total": len(items),
            "page": 1,
            "source": "html_parsed"
        }

    def _get_sample_data(self, sgg_code: str = None) -> Dict[str, Any]:
        """샘플 데이터 반환 (개발용)"""
        # 구 이름 찾기
        gu_name = "강남구"
        for name, code in SEOUL_SGG_CODES.items():
            if code == sgg_code:
                gu_name = name
                break

        # 샘플 데이터
        sample_items = [
            {
                "id": f"2024타경{1000 + i}",
                "court": "서울중앙지방법원",
                "case_no": f"2024타경{1000 + i}",
                "apt_name": f"{gu_name} 래미안아파트 {101 + i}동",
                "address": f"서울특별시 {gu_name} 역삼동 123-{i}",
                "area": 84.5 + i * 5,
                "appraisal_price": 800000000 + i * 50000000,
                "min_price": 640000000 + i * 40000000,
                "auction_date": f"2025-02-{15 + i}",
                "auction_count": 1 + i % 3,
                "status": "진행",
                "risk_level": "안전" if i % 2 == 0 else "주의",
                "risk_reason": "" if i % 2 == 0 else f"{1 + i % 3}회 유찰",
                "addr1": gu_name,
            }
            for i in range(5)
        ]

        return {
            "items": sample_items,
            "total": len(sample_items),
            "page": 1,
            "source": "sample_data"
        }


# ============================================================
# 편의 함수들
# ============================================================
def crawl_seoul_auctions(
    gu_list: List[str] = None,
    max_pages: int = 3
) -> List[Dict[str, Any]]:
    """
    서울 아파트 경매 물건 크롤링

    Args:
        gu_list: 크롤링할 구 목록 (None이면 전체)
        max_pages: 구별 최대 페이지 수

    Returns:
        경매 물건 리스트
    """
    crawler = CourtAuctionCrawler()
    all_auctions = []

    target_gu = gu_list or list(SEOUL_SGG_CODES.keys())

    for gu_name in target_gu:
        sgg_code = SEOUL_SGG_CODES.get(gu_name)
        if not sgg_code:
            continue

        print(f"[CRAWLER] {gu_name} 크롤링 중...")

        for page in range(1, max_pages + 1):
            result = crawler.search_auctions(
                sido_code=SEOUL_SIDO_CODE,
                sgg_code=sgg_code,
                page=page,
            )

            items = result.get("items", [])
            if not items:
                break

            for item in items:
                # 위험도 계산
                item["risk_level"] = calculate_risk_level(item)
                item["risk_reason"] = get_risk_reason(item)
                item["addr1"] = gu_name

            all_auctions.extend(items)

            # 요청 간 딜레이
            time.sleep(1)

    return all_auctions


def crawl_nationwide_auctions(
    court_list: List[str] = None,
    property_type: str = "아파트"
) -> List[Dict[str, Any]]:
    """
    전국 아파트 경매 물건 크롤링 (한경아 모드)

    Args:
        court_list: 크롤링할 법원 목록 (None이면 전체)
        property_type: 물건 종류

    Returns:
        경매 물건 리스트
    """
    crawler = CourtAuctionCrawler()
    all_auctions = []

    target_courts = court_list or list(COURT_CODES.keys())

    for court_name in target_courts:
        print(f"[CRAWLER] {court_name} 크롤링 중...")

        # 각 법원별로 물건 검색
        # (실제 구현시 법원별 검색 API 사용)
        result = crawler.search_auctions(property_type=property_type)

        items = result.get("items", [])
        for item in items:
            item["court"] = court_name
            item["risk_level"] = calculate_risk_level(item)
            item["risk_reason"] = get_risk_reason(item)

        all_auctions.extend(items)
        time.sleep(1)

    return all_auctions


def calculate_risk_level(auction: Dict[str, Any]) -> str:
    """위험도 계산"""
    auction_count = auction.get("auction_count", 1)

    # 3회 이상 유찰
    if auction_count >= 3:
        return "주의"

    # 5회 이상 유찰
    if auction_count >= 5:
        return "위험"

    return "안전"


def get_risk_reason(auction: Dict[str, Any]) -> str:
    """위험 사유 생성"""
    reasons = []
    auction_count = auction.get("auction_count", 1)

    if auction_count >= 3:
        reasons.append(f"{auction_count}회 유찰")

    return ", ".join(reasons) if reasons else ""


# ============================================================
# 테스트
# ============================================================
if __name__ == "__main__":
    print("=== 법원경매 크롤러 테스트 ===\n")

    crawler = CourtAuctionCrawler()

    # 1. 사건 상세 조회 테스트 (작동 확인된 API)
    print("1. 사건 상세 조회 테스트")
    print("-" * 40)
    detail = crawler.get_case_detail(
        court_name="서울중앙지방법원",
        case_no="2022타경3944",
        tab="사건내역"
    )
    if detail:
        print(f"  상세 정보: {json.dumps(detail, indent=2, ensure_ascii=False)[:500]}...")
    else:
        print("  조회 실패 또는 데이터 없음")

    print()

    # 2. 검색 테스트
    print("2. 물건 검색 테스트 (강남구)")
    print("-" * 40)
    result = crawler.search_auctions(
        sido_code=SEOUL_SIDO_CODE,
        sgg_code=SEOUL_SGG_CODES["강남구"],
        page=1
    )

    print(f"  검색 결과: {result.get('total', 0)}건 (소스: {result.get('source', 'api')})")
    for item in result.get("items", [])[:3]:
        print(f"  - {item.get('apt_name')}: {item.get('min_price', 0):,}원")

    print()
    print("=== 테스트 완료 ===")
