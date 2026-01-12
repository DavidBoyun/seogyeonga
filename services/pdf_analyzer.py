"""
감정평가서 PDF 분석기
PDF에서 텍스트 추출 및 주요 정보 파싱
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

# PDF 처리 라이브러리 (선택적 import)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class AppraisalPDFAnalyzer:
    """감정평가서 PDF 분석기"""

    def __init__(self):
        # 추출 패턴
        self.patterns = {
            # 기본 정보
            "case_no": r"사건번호[:\s]*(\d{4}타경\d+)",
            "court": r"(서울[가-힣]+지방법원)",
            "appraisal_date": r"평가기준일[:\s]*(\d{4}[.\-년]\s*\d{1,2}[.\-월]\s*\d{1,2}일?)",

            # 물건 정보
            "address": r"소\s*재\s*지[:\s]*([^\n]+)",
            "land_area": r"토지[면적:\s]*([\d,.]+)\s*㎡",
            "building_area": r"건물[면적:\s]*([\d,.]+)\s*㎡",
            "exclusive_area": r"전용면적[:\s]*([\d,.]+)\s*㎡",

            # 가격 정보
            "total_price": r"감정평가액[:\s]*([\d,]+)\s*원",
            "land_price": r"토지[가액가격:\s]*([\d,]+)\s*원",
            "building_price": r"건물[가액가격:\s]*([\d,]+)\s*원",
            "price_per_pyeong": r"평당[단가가격:\s]*([\d,]+)\s*원",

            # 건물 정보
            "building_year": r"(준공|신축|사용승인)[년일:\s]*(\d{4})",
            "structure": r"구\s*조[:\s]*([^\n]+)",
            "floors": r"층\s*수[:\s]*([^\n]+)",
        }

    def extract_text(self, pdf_path: str) -> str:
        """
        PDF에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            추출된 텍스트
        """
        text = ""

        # 방법 1: pdfplumber (권장)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

                if len(text.strip()) > 100:
                    return text
            except Exception as e:
                print(f"[PDF] pdfplumber 오류: {e}")

        # 방법 2: PyMuPDF (폴백)
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()

                if len(text.strip()) > 100:
                    return text
            except Exception as e:
                print(f"[PDF] PyMuPDF 오류: {e}")

        return text

    def parse_info(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 주요 정보 추출

        Args:
            text: PDF 텍스트

        Returns:
            추출된 정보 딕셔너리
        """
        result = {}

        for key, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 건물 연도는 그룹 2
                if key == "building_year":
                    result[key] = match.group(2) if len(match.groups()) > 1 else match.group(1)
                else:
                    result[key] = match.group(1).strip()

        # 가격 정규화 (쉼표 제거)
        price_keys = ["total_price", "land_price", "building_price", "price_per_pyeong"]
        for key in price_keys:
            if key in result:
                try:
                    result[key] = int(result[key].replace(",", ""))
                except:
                    pass

        # 면적 정규화
        area_keys = ["land_area", "building_area", "exclusive_area"]
        for key in area_keys:
            if key in result:
                try:
                    result[key] = float(result[key].replace(",", ""))
                except:
                    pass

        return result

    def analyze(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 분석 (텍스트 추출 + 정보 파싱)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            분석 결과 딕셔너리
        """
        # 텍스트 추출
        text = self.extract_text(pdf_path)

        if len(text.strip()) < 100:
            return {
                "success": False,
                "error": "텍스트 추출 실패 (스캔 PDF일 수 있음)",
                "text_length": len(text),
                "raw_text": text[:500] if text else "",
            }

        # 정보 파싱
        info = self.parse_info(text)

        return {
            "success": True,
            "info": info,
            "text_length": len(text),
            "raw_text": text[:2000],  # 처음 2000자
        }

    def get_summary(self, pdf_path: str) -> str:
        """
        PDF 요약 생성 (AI 분석 전 단계)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            요약 텍스트
        """
        result = self.analyze(pdf_path)

        if not result["success"]:
            return f"분석 실패: {result.get('error', '알 수 없는 오류')}"

        info = result["info"]
        lines = ["## 감정평가서 요약", ""]

        if "address" in info:
            lines.append(f"**소재지**: {info['address']}")

        if "total_price" in info:
            price = info["total_price"]
            if price >= 100000000:
                lines.append(f"**감정평가액**: {price / 100000000:.1f}억원")
            else:
                lines.append(f"**감정평가액**: {price / 10000:.0f}만원")

        if "exclusive_area" in info:
            area_m2 = info["exclusive_area"]
            area_py = area_m2 / 3.3058
            lines.append(f"**전용면적**: {area_m2:.2f}㎡ ({area_py:.1f}평)")

        if "building_year" in info:
            lines.append(f"**준공년도**: {info['building_year']}년")

        if "structure" in info:
            lines.append(f"**구조**: {info['structure']}")

        return "\n".join(lines)


def check_pdf_type(pdf_path: str) -> str:
    """
    PDF 타입 확인 (텍스트/스캔/혼합)

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        "text", "scanned", "mixed" 중 하나
    """
    analyzer = AppraisalPDFAnalyzer()
    text = analyzer.extract_text(pdf_path)

    if len(text.strip()) > 500:
        return "text"
    elif len(text.strip()) < 50:
        return "scanned"
    else:
        return "mixed"


# ============================================================
# 테스트
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("감정평가서 PDF 분석기 테스트")
    print("=" * 60)

    # 테스트 PDF
    test_pdf = Path(__file__).parent.parent / "data" / "test_appraisal_real.pdf"

    if not test_pdf.exists():
        print(f"테스트 PDF 없음: {test_pdf}")
        exit(1)

    print(f"\nPDF 파일: {test_pdf}")
    print(f"파일 크기: {test_pdf.stat().st_size:,} bytes")

    # PDF 타입 확인
    pdf_type = check_pdf_type(str(test_pdf))
    print(f"\nPDF 타입: {pdf_type}")

    # 분석
    analyzer = AppraisalPDFAnalyzer()
    result = analyzer.analyze(str(test_pdf))

    print(f"\n분석 결과:")
    print(f"  성공: {result['success']}")
    print(f"  텍스트 길이: {result['text_length']:,}자")

    if result["success"]:
        print(f"\n추출된 정보:")
        for key, value in result["info"].items():
            print(f"  {key}: {value}")

        print(f"\n" + "=" * 60)
        print("요약:")
        print("=" * 60)
        print(analyzer.get_summary(str(test_pdf)))
