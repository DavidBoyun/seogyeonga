"""
법원경매 감정평가서 PDF 크롤러
- PDF 다운로드
- 이미지 추출
- 텍스트 파싱
"""
import os
import re
import io
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tempfile

# PDF 처리 라이브러리
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


# 법원경매 사이트 설정
COURT_AUCTION_BASE = "https://www.courtauction.go.kr"
COURT_AUCTION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.courtauction.go.kr/",
}


class AppraisalCrawler:
    """감정평가서 크롤러"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(COURT_AUCTION_HEADERS)
        self.temp_dir = tempfile.gettempdir()

    def get_appraisal_pdf_url(self, court_code: str, case_no: str, item_no: str = "1") -> Optional[str]:
        """
        감정평가서 PDF URL 조회

        Args:
            court_code: 법원 코드 (예: B000210 = 서울중앙지방법원)
            case_no: 사건번호 (예: 2024타경12345)
            item_no: 물건번호 (기본값: 1)

        Returns:
            PDF 다운로드 URL or None
        """
        # 법원경매 사이트의 감정평가서 URL 패턴
        # 실제로는 사이트 분석이 필요하며, 아래는 예상 패턴입니다

        # 방법 1: 직접 URL 구성 (사이트 구조에 따라 다름)
        pdf_url = (
            f"{COURT_AUCTION_BASE}/RetrieveRealEstAstOrgFile.laf"
            f"?jiwonNm={court_code}&saession={case_no}&maession={item_no}"
        )

        return pdf_url

    def download_appraisal_pdf(
        self,
        court_code: str,
        case_no: str,
        item_no: str = "1"
    ) -> Optional[bytes]:
        """
        감정평가서 PDF 다운로드

        Returns:
            PDF 바이트 데이터 or None
        """
        try:
            # PDF URL 조회
            pdf_url = self.get_appraisal_pdf_url(court_code, case_no, item_no)
            if not pdf_url:
                return None

            # PDF 다운로드
            response = self.session.get(pdf_url, timeout=30)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower() or response.content[:4] == b'%PDF':
                    return response.content

            print(f"[APPRAISAL] PDF 다운로드 실패: {response.status_code}")
            return None

        except Exception as e:
            print(f"[APPRAISAL] 다운로드 오류: {e}")
            return None

    def save_pdf(self, pdf_bytes: bytes, filename: str) -> str:
        """PDF를 임시 파일로 저장"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        return filepath


class AppraisalParser:
    """감정평가서 PDF 파서"""

    def __init__(self):
        pass

    def extract_images(self, pdf_bytes: bytes, max_images: int = 10) -> List[bytes]:
        """
        PDF에서 이미지 추출

        Returns:
            이미지 바이트 리스트
        """
        images = []

        if HAS_PYMUPDF:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                for page_num in range(min(len(doc), 5)):  # 처음 5페이지만
                    page = doc[page_num]
                    image_list = page.get_images()

                    for img_index, img in enumerate(image_list):
                        if len(images) >= max_images:
                            break

                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        images.append(image_bytes)

                doc.close()
            except Exception as e:
                print(f"[PARSER] 이미지 추출 오류: {e}")

        return images

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        PDF에서 텍스트 추출

        Returns:
            전체 텍스트
        """
        text = ""

        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for page in pdf.pages[:20]:  # 처음 20페이지
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            except Exception as e:
                print(f"[PARSER] pdfplumber 오류: {e}")

        elif HAS_PYMUPDF:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    text += page.get_text() + "\n\n"
                doc.close()
            except Exception as e:
                print(f"[PARSER] PyMuPDF 텍스트 추출 오류: {e}")

        return text

    def parse_appraisal_info(self, text: str) -> Dict[str, Any]:
        """
        감정평가서 텍스트에서 주요 정보 파싱

        Returns:
            파싱된 정보 딕셔너리
        """
        info = {
            "appraisal_price": None,      # 감정가
            "land_area": None,            # 대지면적
            "building_area": None,        # 건물면적
            "floor": None,                # 층
            "direction": None,            # 방향
            "built_year": None,           # 준공년도
            "structure": None,            # 구조
            "rights_analysis": [],        # 권리분석
            "special_notes": [],          # 특이사항
            "location_features": [],      # 입지 특성
        }

        # 감정가 추출
        price_patterns = [
            r'감정가[금액:\s]*(\d{1,3}(?:,\d{3})*)',
            r'평가가액[:\s]*(\d{1,3}(?:,\d{3})*)',
            r'감정평가액[:\s]*(\d{1,3}(?:,\d{3})*)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                info["appraisal_price"] = int(price_str)
                break

        # 면적 추출
        area_match = re.search(r'전용면적[:\s]*([\d.]+)\s*㎡', text)
        if area_match:
            info["building_area"] = float(area_match.group(1))

        land_match = re.search(r'대지[면적:\s]*([\d.]+)\s*㎡', text)
        if land_match:
            info["land_area"] = float(land_match.group(1))

        # 층수 추출
        floor_match = re.search(r'(\d+)\s*층', text)
        if floor_match:
            info["floor"] = int(floor_match.group(1))

        # 준공년도 추출
        year_match = re.search(r'준공[:\s]*(\d{4})', text)
        if year_match:
            info["built_year"] = int(year_match.group(1))

        # 권리분석 키워드 추출
        risk_keywords = {
            "유치권": "유치권 신고 있음 - 현장 확인 필수",
            "가압류": "가압류 설정 - 매각으로 소멸",
            "저당권": "저당권 설정",
            "전세권": "전세권 설정",
            "임차인": "임차인 있음 - 대항력 확인 필요",
            "점유자": "점유자 있음 - 인도 문제 확인",
        }

        for keyword, desc in risk_keywords.items():
            if keyword in text:
                info["rights_analysis"].append(desc)

        # 특이사항 추출
        if "누수" in text:
            info["special_notes"].append("누수 흔적 있음")
        if "균열" in text:
            info["special_notes"].append("균열 발견")
        if "노후" in text:
            info["special_notes"].append("시설 노후화")

        return info

    def parse_full_appraisal(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        감정평가서 전체 파싱

        Returns:
            {
                "images": [bytes, ...],
                "text": str,
                "info": {...},
                "summary": str
            }
        """
        result = {
            "images": [],
            "text": "",
            "info": {},
            "summary": ""
        }

        # 이미지 추출
        result["images"] = self.extract_images(pdf_bytes)

        # 텍스트 추출
        result["text"] = self.extract_text(pdf_bytes)

        # 정보 파싱
        if result["text"]:
            result["info"] = self.parse_appraisal_info(result["text"])

        # 요약 생성 (간단 버전)
        info = result["info"]
        summary_parts = []

        if info.get("appraisal_price"):
            price = info["appraisal_price"]
            if price >= 100000000:
                price_str = f"{price // 100000000}억"
            else:
                price_str = f"{price // 10000:,}만"
            summary_parts.append(f"감정가: {price_str}원")

        if info.get("building_area"):
            summary_parts.append(f"전용면적: {info['building_area']}㎡")

        if info.get("floor"):
            summary_parts.append(f"{info['floor']}층")

        if info.get("built_year"):
            summary_parts.append(f"준공: {info['built_year']}년")

        if info.get("rights_analysis"):
            summary_parts.append(f"권리사항: {', '.join(info['rights_analysis'][:3])}")

        result["summary"] = " | ".join(summary_parts)

        return result


def get_appraisal_data(auction: Dict[str, Any]) -> Dict[str, Any]:
    """
    경매 물건의 감정평가서 데이터 조회

    Args:
        auction: 경매 물건 정보 (court, case_no 필요)

    Returns:
        감정평가서 파싱 결과
    """
    # 법원 코드 매핑
    court_codes = {
        "서울중앙지방법원": "B000210",
        "서울동부지방법원": "B000211",
        "서울서부지방법원": "B000215",
        "서울남부지방법원": "B000212",
        "서울북부지방법원": "B000213",
    }

    court = auction.get('court', '')
    case_no = auction.get('case_no', '')

    court_code = court_codes.get(court, "B000210")

    # 사건번호에서 연도와 번호 추출
    case_match = re.match(r'(\d{4})타경(\d+)', case_no)
    if not case_match:
        return {"error": "사건번호 형식 오류"}

    crawler = AppraisalCrawler()
    parser = AppraisalParser()

    # PDF 다운로드
    pdf_bytes = crawler.download_appraisal_pdf(court_code, case_no)

    if not pdf_bytes:
        # 다운로드 실패시 샘플 데이터 반환
        return get_sample_appraisal_data(auction)

    # PDF 파싱
    return parser.parse_full_appraisal(pdf_bytes)


def get_sample_appraisal_data(auction: Dict[str, Any]) -> Dict[str, Any]:
    """
    샘플 감정평가서 데이터 (테스트용)
    """
    apt_name = auction.get('apt_name', '아파트')
    min_price = auction.get('min_price', 0)
    appraisal_price = auction.get('appraisal_price', 0)

    return {
        "images": [],  # 실제로는 이미지 바이트 리스트
        "text": f"""
        감정평가서

        물건의 표시: {apt_name}
        소재지: {auction.get('address', '')}

        감정가격: {appraisal_price:,}원

        1. 물건 개요
        - 전용면적: {auction.get('area', 0)}㎡
        - 구조: 철근콘크리트

        2. 권리분석
        {auction.get('risk_reason', '특이사항 없음')}

        3. 감정평가 의견
        본 물건은 일반적인 아파트로서...
        """,
        "info": {
            "appraisal_price": appraisal_price,
            "building_area": auction.get('area'),
            "rights_analysis": [auction.get('risk_reason')] if auction.get('risk_reason') else [],
        },
        "summary": f"감정가: {appraisal_price // 100000000}억원 | 면적: {auction.get('area')}㎡",
        "is_sample": True
    }


# AI 요약 통합
def summarize_appraisal_with_ai(appraisal_data: Dict[str, Any], provider: str = "auto") -> str:
    """
    감정평가서를 AI로 쉽게 요약

    Args:
        appraisal_data: parse_full_appraisal 결과
        provider: ai provider (ollama, deepseek, auto)

    Returns:
        쉽게 풀어쓴 요약문
    """
    from services.news_crawler import summarize_content

    text = appraisal_data.get("text", "")
    if not text:
        return "감정평가서 내용을 불러올 수 없습니다."

    # 텍스트가 너무 길면 앞부분만
    if len(text) > 3000:
        text = text[:3000] + "..."

    prompt = f"""
다음은 법원경매 감정평가서 내용입니다.
경매 초보자도 이해할 수 있게 쉬운 말로 핵심만 요약해주세요.

감정평가서 내용:
{text}

다음 형식으로 요약해주세요:
1. 물건 개요 (면적, 층수, 위치 등)
2. 감정가 및 시세
3. 주의사항 (권리관계, 임차인 등)
4. 초보자를 위한 한줄 조언
"""

    summary = summarize_content("감정평가서 요약", prompt, provider)

    if not summary:
        # AI 실패시 기본 요약
        info = appraisal_data.get("info", {})
        return f"""
📋 **감정평가서 요약**

**감정가**: {info.get('appraisal_price', 0):,}원
**면적**: {info.get('building_area', '-')}㎡

**권리사항**:
{chr(10).join(['- ' + r for r in info.get('rights_analysis', ['특이사항 없음'])])}

**특이사항**:
{chr(10).join(['- ' + n for n in info.get('special_notes', ['없음'])])}

*자동 파싱된 정보입니다. 원본 문서를 반드시 확인하세요.*
"""

    return summary


# 테스트
if __name__ == "__main__":
    # 라이브러리 체크
    print(f"PyMuPDF 설치됨: {HAS_PYMUPDF}")
    print(f"pdfplumber 설치됨: {HAS_PDFPLUMBER}")

    # 샘플 테스트
    sample_auction = {
        "apt_name": "테스트아파트",
        "address": "서울시 강남구",
        "area": 84.5,
        "appraisal_price": 1500000000,
        "min_price": 1050000000,
        "risk_reason": "선순위 임차인 있음",
    }

    data = get_sample_appraisal_data(sample_auction)
    print("\n=== 샘플 감정평가서 데이터 ===")
    print(f"요약: {data['summary']}")
