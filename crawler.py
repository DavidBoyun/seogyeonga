"""
서경아 - 서울 아파트 경매 크롤러
법원경매 사이트에서 서울 아파트 물건만 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date
from typing import List, Dict, Optional
import time

from config import (
    COURT_AUCTION_URL,
    SEOUL_SIDO_CODE,
    TARGET_ITEM_TYPES,
    SEOUL_SIGU_CODES,
    CRAWL_DELAY,
    PAGE_DELAY
)


class SeogyeongaCrawler:
    """서울 아파트 경매 크롤러"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = COURT_AUCTION_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Charset": "utf-8,euc-kr;q=0.7,*;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self._init_session()

    def _init_session(self):
        """세션 초기화 - 쿠키 획득"""
        try:
            # 메인 페이지로 세션 초기화
            resp = self.session.get(
                self.base_url,
                headers=self.headers,
                timeout=15
            )
            print(f"[OK] 세션 초기화 완료 (status: {resp.status_code})")
        except Exception as e:
            print(f"[ERROR] 세션 초기화 실패: {e}")

    def get_sigu_list(self, sido_code: str = SEOUL_SIDO_CODE) -> List[Dict]:
        """시군구 목록 조회"""
        url = f"{self.base_url}/RetrieveAucSigu.ajax"

        try:
            resp = self.session.post(
                url,
                headers=self.headers,
                data={
                    "sidoCode": sido_code,
                    "id2": "idSiguCode",
                    "id3": "idDongCode"
                },
                timeout=15
            )
            resp.encoding = 'euc-kr'

            soup = BeautifulSoup(resp.text, 'html.parser')
            options = soup.find_all('option')

            sigu_list = []
            for opt in options:
                value = opt.get('value', '').strip()
                name = opt.get_text(strip=True)
                if value and name and value != '':
                    sigu_list.append({"code": value, "name": name})

            print(f"[OK] 서울 시군구 {len(sigu_list)}개 조회")
            return sigu_list

        except Exception as e:
            print(f"[ERROR] 시군구 조회 실패: {e}")
            # 백업 코드 사용
            return [{"code": v, "name": k} for k, v in SEOUL_SIGU_CODES.items()]

    def get_auction_list(
        self,
        sido_code: str = SEOUL_SIDO_CODE,
        sigu_code: str = "",
        target_row: int = 1
    ) -> List[Dict]:
        """경매 물건 리스트 조회"""
        url = f"{self.base_url}/RetrieveRealEstMulDetailList.laf"

        form_data = {
            "_FORM_YN": "Y",
            "bubwLocGubun": "2",
            "daepyoSidoCd": sido_code,
            "daepyoSiguCd": sigu_code,
            "mDaepyoSidoCd": sido_code,
            "mDaepyoSiguCd": sigu_code,
            "srnID": "PNO102000",
            "targetRow": str(target_row),
        }

        try:
            resp = self.session.post(
                url,
                headers=self.headers,
                data=form_data,
                timeout=20
            )
            resp.encoding = 'euc-kr'

            return self._parse_auction_list(resp.text)

        except Exception as e:
            print(f"[ERROR] 경매 리스트 조회 실패: {e}")
            return []

    def _parse_auction_list(self, html: str) -> List[Dict]:
        """HTML에서 경매 물건 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        auctions = []

        # 테이블 찾기
        table = soup.find('table', class_='Ltbl_list')
        if not table:
            # 다른 클래스 시도
            table = soup.find('table', {'class': re.compile(r'tbl.*list', re.I)})

        if not table:
            return auctions

        tbody = table.find('tbody')
        if not tbody:
            tbody = table

        rows = tbody.find_all('tr')

        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 7:
                    continue

                auction = self._parse_row(cols)
                if auction:
                    auctions.append(auction)

            except Exception as e:
                continue

        return auctions

    def _parse_row(self, cols) -> Optional[Dict]:
        """테이블 행 파싱"""
        try:
            # 1. 사건번호 정보
            case_cell = cols[1] if len(cols) > 1 else cols[0]
            case_info = case_cell.get_text(separator=' ', strip=True)
            case_parts = case_info.split()
            court = case_parts[0] if len(case_parts) > 0 else ""
            case_no = case_parts[1] if len(case_parts) > 1 else ""

            # 2. 물건 정보
            item_cell = cols[2] if len(cols) > 2 else None
            if item_cell:
                item_info = item_cell.get_text(separator=' ', strip=True)
                item_parts = item_info.split()
                item_no = item_parts[0] if len(item_parts) > 0 else "1"
                item_type = item_parts[1] if len(item_parts) > 1 else ""
            else:
                item_no = "1"
                item_type = ""

            # 아파트/주상복합만 필터링
            if item_type not in TARGET_ITEM_TYPES:
                return None

            # 3. 소재지
            addr_cell = cols[3] if len(cols) > 3 else None
            address = ""
            area_info = ""

            if addr_cell:
                addr_div = addr_cell.find('div')
                if addr_div:
                    address = addr_div.get_text(separator=' ', strip=True)
                else:
                    address = addr_cell.get_text(separator=' ', strip=True)

                # 면적 정보
                area_spans = addr_cell.find_all('span')
                if area_spans:
                    area_info = area_spans[-1].get_text(strip=True)

            # 주소에서 구/동 추출
            addr_parts = address.split()
            sido = "서울특별시"
            gugun = ""
            dong = ""

            for part in addr_parts:
                if part.endswith("구"):
                    gugun = part
                elif part.endswith("동") or part.endswith("로"):
                    if not dong:
                        dong = part

            # 면적 파싱 (예: "84.5㎡" → 84.5)
            area = 0.0
            if area_info:
                area_match = re.search(r'([\d.]+)\s*[㎡m²]', area_info)
                if area_match:
                    area = float(area_match.group(1))

            # 4. 비고
            remarks_cell = cols[4] if len(cols) > 4 else None
            remarks = remarks_cell.get_text(separator=' ', strip=True) if remarks_cell else ""

            # 5. 감정가/최저가
            appraisal_price = 0
            min_price = 0

            if len(cols) > 5:
                value_cell = cols[5]
                value_divs = value_cell.find_all('div')

                if len(value_divs) >= 1:
                    value_text = re.sub(r'[^\d]', '', value_divs[0].get_text())
                    appraisal_price = int(value_text) if value_text else 0

                if len(value_divs) >= 2:
                    value_min_text = re.sub(r'[^\d]', '', value_divs[1].get_text())
                    min_price = int(value_min_text) if value_min_text else 0

            # 6. 경매 정보
            auction_info = ""
            auction_date_str = ""

            if len(cols) > 6:
                auction_cell = cols[6]
                auction_div = auction_cell.find('div')

                if auction_div:
                    onclick = auction_div.get('onclick', '')
                    date_match = re.search(r"'(\d{4}-\d{2}-\d{2})'", onclick)
                    if date_match:
                        auction_date_str = date_match.group(1)
                    auction_info = auction_div.get_text(strip=True)

            # 경매 차수 추출
            auction_count = 1
            count_match = re.search(r'(\d+)\s*차', auction_info)
            if count_match:
                auction_count = int(count_match.group(1))

            # 7. 상태
            status = ""
            if len(cols) > 7:
                status = cols[7].get_text(strip=True)

            # 위험 요소 추출 (비고에서)
            risk_items = self._extract_risk_items(remarks)
            risk_level, risk_reason = self._calculate_risk(risk_items, remarks)

            # 임차인/선순위권리 여부
            has_tenant = any(k in remarks for k in ["임차인", "대항력", "전세"])
            has_senior_rights = any(k in remarks for k in ["선순위", "가압류", "가처분", "지상권"])

            # 날짜 파싱
            auction_date = None
            if auction_date_str:
                try:
                    auction_date = datetime.strptime(auction_date_str, "%Y-%m-%d").date()
                except:
                    pass

            # 결과 반환 (DB 모델에 맞춤)
            return {
                "court": court,
                "case_no": f"{case_no}_{item_no}".replace(" ", "_"),
                "address": address,
                "sido": sido,
                "gugun": gugun,
                "dong": dong,
                "apt_name": self._extract_apt_name(address),
                "area": area,
                "floor": self._extract_floor(address),
                "appraisal_price": appraisal_price,
                "min_price": min_price,
                "auction_date": auction_date,
                "auction_count": auction_count,
                "status": status or "진행중",
                "risk_level": risk_level,
                "risk_reason": risk_reason,
                "has_tenant": has_tenant,
                "has_senior_rights": has_senior_rights,
                "remarks": remarks,
            }

        except Exception as e:
            return None

    def _extract_apt_name(self, address: str) -> str:
        """주소에서 아파트명 추출"""
        # 아파트, 단지, 동 등의 패턴
        apt_patterns = [
            r'([가-힣]+아파트)',
            r'([가-힣]+단지)',
            r'([가-힣]+타운)',
            r'([가-힣]+빌라)',
        ]
        for pattern in apt_patterns:
            match = re.search(pattern, address)
            if match:
                return match.group(1)
        return ""

    def _extract_floor(self, address: str) -> str:
        """주소에서 층수 추출"""
        floor_match = re.search(r'(\d+)\s*층', address)
        if floor_match:
            return f"{floor_match.group(1)}층"
        return ""

    def _extract_risk_items(self, text: str) -> List[str]:
        """비고에서 위험 요소 추출"""
        risk_keywords = [
            "유치권", "법정지상권", "선순위전세권", "선순위근저당",
            "대항력", "임차인", "가압류", "가처분", "점유",
            "명도", "지분", "지상권", "전세권"
        ]

        found = []
        for keyword in risk_keywords:
            if keyword in text:
                found.append(keyword)

        return found

    def _calculate_risk(self, risk_items: List[str], remarks: str) -> tuple:
        """위험도 계산"""
        # 위험도 룰
        critical_keywords = ["선순위전세권", "선순위근저당", "유치권", "법정지상권"]
        high_keywords = ["대항력", "가압류", "가처분", "지상권"]
        medium_keywords = ["임차인", "점유", "명도"]

        risk_level = "안전"
        reasons = []

        for keyword in critical_keywords:
            if keyword in risk_items or keyword in remarks:
                risk_level = "위험"
                reasons.append(keyword)

        if risk_level == "안전":
            for keyword in high_keywords:
                if keyword in risk_items or keyword in remarks:
                    risk_level = "주의"
                    reasons.append(keyword)

        if risk_level == "안전":
            for keyword in medium_keywords:
                if keyword in risk_items or keyword in remarks:
                    risk_level = "주의"
                    reasons.append(keyword)

        return risk_level, ", ".join(reasons) if reasons else None

    def crawl_seoul_apartments(self, max_pages: int = 3, sigu_codes: List[str] = None) -> List[Dict]:
        """서울 아파트 경매 물건 전체 크롤링"""
        all_auctions = []

        print("\n" + "=" * 50)
        print("  서경아 - 서울 아파트 경매 크롤링")
        print("=" * 50)

        # 시군구 목록
        if sigu_codes:
            sigu_list = [{"code": code, "name": code} for code in sigu_codes]
        else:
            sigu_list = self.get_sigu_list(SEOUL_SIDO_CODE)

        if not sigu_list:
            print("[WARN] 시군구 목록 없음, 백업 코드 사용")
            sigu_list = [{"code": v, "name": k} for k, v in SEOUL_SIGU_CODES.items()]

        total_sigu = len(sigu_list)

        for idx, sigu in enumerate(sigu_list, 1):
            print(f"\n[{idx}/{total_sigu}] {sigu['name']} 크롤링 중...")

            page = 1
            page_size = 20

            while page <= max_pages:
                target_row = (page - 1) * page_size + 1

                auctions = self.get_auction_list(
                    sido_code=SEOUL_SIDO_CODE,
                    sigu_code=sigu['code'],
                    target_row=target_row
                )

                if not auctions:
                    break

                # 아파트만 (이미 필터링됨)
                all_auctions.extend(auctions)

                print(f"   페이지 {page}: {len(auctions)}건 (누적: {len(all_auctions)}건)")

                if len(auctions) < page_size:
                    break

                page += 1
                time.sleep(PAGE_DELAY)

            time.sleep(CRAWL_DELAY)

        print("\n" + "=" * 50)
        print(f"  크롤링 완료! 총 {len(all_auctions)}건")
        print("=" * 50)

        return all_auctions

    def save_to_json(self, auctions: List[Dict], filename: str = "auctions.json"):
        """JSON 파일로 저장"""
        # date 객체를 문자열로 변환
        serializable = []
        for a in auctions:
            item = a.copy()
            if item.get('auction_date') and isinstance(item['auction_date'], date):
                item['auction_date'] = item['auction_date'].isoformat()
            serializable.append(item)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "updated_at": datetime.now().isoformat(),
                "total_count": len(serializable),
                "auctions": serializable
            }, f, ensure_ascii=False, indent=2)

        print(f"[OK] {filename} 저장 완료 ({len(auctions)}건)")
        return filename

    def save_to_db(self, auctions: List[Dict]) -> int:
        """DB에 저장"""
        from database import init_db, upsert_auction

        init_db()
        count = 0
        for auction in auctions:
            try:
                upsert_auction(auction)
                count += 1
            except Exception as e:
                print(f"[ERROR] DB 저장 실패: {auction.get('case_no')} - {e}")

        print(f"[OK] DB 저장 완료 ({count}건)")
        return count


def main():
    """메인 실행"""
    crawler = SeogyeongaCrawler()

    # 서울 아파트 크롤링 (각 구별 최대 3페이지)
    auctions = crawler.crawl_seoul_apartments(max_pages=3)

    if auctions:
        # JSON 저장
        crawler.save_to_json(auctions, "auctions.json")

        # DB 저장
        crawler.save_to_db(auctions)

        # 샘플 출력
        print("\n[샘플 데이터 - 최근 3건]")
        for auction in auctions[:3]:
            print(f"""
----------------------------------------
  {auction['address']}
  감정가: {auction['appraisal_price']:,}원
  최저가: {auction['min_price']:,}원
  입찰일: {auction['auction_date']}
  위험도: {auction['risk_level']}
  상태: {auction['status']}
----------------------------------------""")
    else:
        print("[WARN] 크롤링된 데이터가 없습니다.")


if __name__ == "__main__":
    main()
