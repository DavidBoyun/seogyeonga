"""
법원경매 크롤러 v2 - 신규 /pgj/pgjsearch API 사용
실제 작동하는 검색 API를 사용한 크롤러
"""
import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# 설정
# ============================================================
COURT_BASE_URL = "https://www.courtauction.go.kr"

# API 엔드포인트
API_ENDPOINTS = {
    "search": f"{COURT_BASE_URL}/pgj/pgjsearch/searchControllerMain.on",
    "case_detail": f"{COURT_BASE_URL}/pgj/pgj15A/selectAuctnCsSrchRslt.on",
    "schedule": f"{COURT_BASE_URL}/pgj/pgj15A/selectCsDtlDxdyDts.on",
    "documents": f"{COURT_BASE_URL}/pgj/pgj15A/selectDlvrOfdocDtsDtl.on",
}

# 기본 헤더
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/json;charset=UTF-8",
}

# 법원 코드
COURT_CODES = {
    "서울중앙지방법원": "B000210",
    "서울동부지방법원": "B000211",
    "서울남부지방법원": "B000212",
    "서울북부지방법원": "B000213",
    "서울서부지방법원": "B000215",
    "의정부지방법원": "B000214",
    "수원지방법원": "B000250",
    "인천지방법원": "B000240",
}

COURT_CODES_REVERSE = {v: k for k, v in COURT_CODES.items()}

# 용도 코드 (아파트 필터링용)
USAGE_CODES = {
    "아파트": ["10101", "10102"],  # 일반아파트, 주상복합
    "오피스텔": ["10106"],
    "다세대": ["10103", "10104"],
}


# ============================================================
# 크롤러 클래스
# ============================================================
class CourtAuctionCrawlerV2:
    """법원경매 크롤러 v2 - 신규 API 사용"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._initialized = False

    def _init_session(self) -> bool:
        """세션 초기화 (쿠키 획득)"""
        if self._initialized:
            return True

        try:
            response = self.session.get(
                f"{COURT_BASE_URL}/pgj/index.on",
                timeout=15
            )

            if response.status_code == 200:
                self.session.headers.update({
                    "Referer": f"{COURT_BASE_URL}/pgj/index.on",
                    "submissionid": "mf_wfm_mainFrame_sbm_selectGdsDtlSrch",
                    "sc-userid": "SYSTEM",
                })
                self._initialized = True
                print("[CRAWLER] 세션 초기화 성공")
                return True
            else:
                print(f"[CRAWLER] 세션 초기화 실패: {response.status_code}")
                return False

        except Exception as e:
            print(f"[CRAWLER] 세션 초기화 오류: {e}")
            return False

    def search_auctions(
        self,
        court_code: str = "",
        sido_code: str = "",
        sgg_code: str = "",
        usage_codes: List[str] = None,
        bid_start_date: str = None,
        bid_end_date: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        경매 물건 검색

        Args:
            court_code: 법원 코드 (예: "B000210", 빈 문자열이면 전체)
            sido_code: 시도 코드 (예: "11" 서울)
            sgg_code: 시군구 코드
            usage_codes: 용도 코드 리스트 (아파트: ["10101", "10102"])
            bid_start_date: 입찰 시작일 (YYYYMMDD)
            bid_end_date: 입찰 종료일 (YYYYMMDD)
            page: 페이지 번호
            page_size: 페이지 크기

        Returns:
            검색 결과 딕셔너리
        """
        if not self._init_session():
            return {"items": [], "total": 0, "error": "세션 초기화 실패"}

        # 기본 날짜 설정 (오늘 ~ 2주 후)
        today = datetime.now()
        if not bid_start_date:
            bid_start_date = today.strftime("%Y%m%d")
        if not bid_end_date:
            bid_end_date = (today + timedelta(days=14)).strftime("%Y%m%d")

        # 페이로드 구성
        payload = {
            "dma_pageInfo": {
                "pageNo": page,
                "pageSize": page_size,
                "bfPageNo": "",
                "startRowNo": "",
                "totalCnt": "",
                "totalYn": "Y",
                "groupTotalCount": ""
            },
            "dma_srchGdsDtlSrchInfo": {
                "rletDspslSpcCondCd": "",
                "bidDvsCd": "000331",  # 기일입찰
                "mvprpRletDvsCd": "00031R",  # 부동산
                "cortAuctnSrchCondCd": "0004601",
                "rprsAdongSdCd": sido_code,
                "rprsAdongSggCd": sgg_code,
                "rprsAdongEmdCd": "",
                "rdnmSdCd": "",
                "rdnmSggCd": "",
                "rdnmNo": "",
                "mvprpDspslPlcAdongSdCd": "",
                "mvprpDspslPlcAdongSggCd": "",
                "mvprpDspslPlcAdongEmdCd": "",
                "rdDspslPlcAdongSdCd": "",
                "rdDspslPlcAdongSggCd": "",
                "rdDspslPlcAdongEmdCd": "",
                "cortOfcCd": court_code,
                "jdbnCd": "",
                "execrOfcDvsCd": "",
                "lclDspslGdsLstUsgCd": "",
                "mclDspslGdsLstUsgCd": "",
                "sclDspslGdsLstUsgCd": "",
                "cortAuctnMbrsId": "",
                "aeeEvlAmtMin": "",
                "aeeEvlAmtMax": "",
                "lwsDspslPrcRateMin": "",
                "lwsDspslPrcRateMax": "",
                "flbdNcntMin": "",
                "flbdNcntMax": "",
                "objctArDtsMin": "",
                "objctArDtsMax": "",
                "mvprpArtclKndCd": "",
                "mvprpArtclNm": "",
                "mvprpAtchmPlcTypCd": "",
                "notifyLoc": "off",
                "lafjOrderBy": "",
                "pgmId": "PGJ151F01",
                "csNo": "",
                "cortStDvs": "1",
                "statNum": 1,
                "bidBgngYmd": bid_start_date,
                "bidEndYmd": bid_end_date,
                "dspslDxdyYmd": "",
                "fstDspslHm": "",
                "scndDspslHm": "",
                "thrdDspslHm": "",
                "fothDspslHm": "",
                "dspslPlcNm": "",
                "lwsDspslPrcMin": "",
                "lwsDspslPrcMax": "",
                "grbxTypCd": "",
                "gdsVendNm": "",
                "fuelKndCd": "",
                "carMdyrMax": "",
                "carMdyrMin": "",
                "carMdlNm": "",
                "sideDvsCd": ""
            }
        }

        try:
            response = self.session.post(
                API_ENDPOINTS["search"],
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # HTML 리다이렉트 확인
                if response.text.strip().startswith("<!DOCTYPE"):
                    print("[CRAWLER] 세션 만료 - 재초기화")
                    self._initialized = False
                    return self.search_auctions(
                        court_code, sido_code, sgg_code, usage_codes,
                        bid_start_date, bid_end_date, page, page_size
                    )

                data = response.json()

                if "data" in data:
                    page_info = data["data"].get("dma_pageInfo", {})
                    raw_items = data["data"].get("dlt_srchResult", [])

                    # 아이템 파싱
                    items = [self._parse_item(item) for item in raw_items]

                    # 아파트 필터링
                    if usage_codes:
                        items = [
                            item for item in items
                            if any(code in item.get("usage_code", "") for code in usage_codes)
                        ]

                    return {
                        "items": items,
                        "total": int(page_info.get("totalCnt", 0)),
                        "page": page,
                        "page_size": page_size,
                        "source": "pgj_api"
                    }

            return {"items": [], "total": 0, "error": f"API 오류: {response.status_code}"}

        except Exception as e:
            print(f"[CRAWLER] 검색 오류: {e}")
            return {"items": [], "total": 0, "error": str(e)}

    def _parse_item(self, raw: Dict) -> Dict[str, Any]:
        """원시 데이터를 표준 형식으로 파싱"""
        return {
            "id": raw.get("docid", ""),
            "case_no": raw.get("srnSaNo", ""),
            "court_code": raw.get("boCd", ""),
            "court_name": raw.get("jiwonNm", ""),
            "dept_name": raw.get("jpDeptNm", ""),
            "address": raw.get("printSt", ""),
            "sido": raw.get("hjguSido", ""),
            "sigu": raw.get("hjguSigu", ""),
            "dong": raw.get("hjguDong", ""),
            "building_name": raw.get("buldNm", ""),
            "building_detail": raw.get("buldList", ""),
            "appraisal_price": int(raw.get("gamevalAmt", 0) or 0),
            "min_price": int(raw.get("minmaePrice", 0) or 0),
            "bid_count": int(raw.get("yuchalCnt", 0) or 0),
            "auction_date": self._parse_date(raw.get("maeGiil", "")),
            "auction_time": raw.get("maeHh1", ""),
            "auction_place": raw.get("maePlace", ""),
            "usage_name": raw.get("dspslUsgNm", ""),
            "usage_code": raw.get("sclsUtilCd", ""),
            "area_info": raw.get("pjbBuldList", ""),
            "area_min": float(raw.get("minArea", 0) or 0),
            "area_max": float(raw.get("maxArea", 0) or 0),
            "status_code": raw.get("jinstatCd", ""),
            "tel": raw.get("tel", ""),
            "note": raw.get("mulBigo", ""),
            "x_coord": raw.get("wgs84Xcordi", ""),
            "y_coord": raw.get("wgs84Ycordi", ""),
        }

    def _parse_date(self, date_str: str) -> str:
        """날짜 문자열 파싱"""
        if not date_str or len(date_str) != 8:
            return ""
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    def get_case_detail(
        self,
        court_code: str,
        case_no: str,
    ) -> Optional[Dict[str, Any]]:
        """
        사건 상세 정보 조회

        Args:
            court_code: 법원 코드
            case_no: API 형식 사건번호 (예: "20220130003944")
        """
        if not self._init_session():
            return None

        payload = {
            "dma_srchCsDtlInf": {
                "cortOfcCd": court_code,
                "csNo": case_no,
            }
        }

        try:
            response = self.session.post(
                API_ENDPOINTS["case_detail"],
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("data")

        except Exception as e:
            print(f"[CRAWLER] 상세조회 오류: {e}")

        return None


# ============================================================
# 편의 함수
# ============================================================
def search_seoul_apartments(
    max_pages: int = 5,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    서울 아파트 경매 물건 검색

    Args:
        max_pages: 최대 페이지 수
        page_size: 페이지당 결과 수

    Returns:
        경매 물건 리스트
    """
    crawler = CourtAuctionCrawlerV2()
    all_items = []

    for page in range(1, max_pages + 1):
        print(f"[CRAWLER] 페이지 {page} 검색 중...")

        result = crawler.search_auctions(
            sido_code="11",  # 서울
            page=page,
            page_size=page_size,
        )

        items = result.get("items", [])
        if not items:
            break

        all_items.extend(items)
        print(f"  - {len(items)}건 추가 (총 {len(all_items)}건)")

        if len(items) < page_size:
            break

        time.sleep(1)

    # 아파트만 필터링
    apartment_items = [
        item for item in all_items
        if "아파트" in item.get("usage_name", "") or "주상복합" in item.get("usage_name", "")
    ]

    print(f"\n[CRAWLER] 총 {len(all_items)}건 중 아파트 {len(apartment_items)}건")
    return apartment_items


# ============================================================
# 테스트
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("법원경매 크롤러 v2 테스트")
    print("=" * 60)

    crawler = CourtAuctionCrawlerV2()

    # 검색 테스트
    print("\n1. 서울 전체 검색 테스트")
    print("-" * 40)
    result = crawler.search_auctions(
        sido_code="11",
        page=1,
        page_size=10
    )

    print(f"총 건수: {result.get('total', 0)}")
    print(f"가져온 건수: {len(result.get('items', []))}")

    for item in result.get("items", [])[:3]:
        print(f"\n- {item['case_no']}")
        print(f"  {item['court_name']} | {item['address'][:30]}...")
        print(f"  감정가: {item['appraisal_price']:,}원")
        print(f"  최저가: {item['min_price']:,}원")
        print(f"  용도: {item['usage_name']}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
