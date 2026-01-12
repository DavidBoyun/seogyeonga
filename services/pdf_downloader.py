"""
감정평가서 PDF 다운로더
한국감정평가사협회(kapanet.or.kr) 서버에서 PDF 다운로드
"""
import re
import requests
from pathlib import Path
from typing import Optional, Tuple


# 감정평가사협회 PDF 서버
KAPANET_BASE_URL = "https://ca.kapanet.or.kr"

# 헤더
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}


def get_pdf_url_from_viewer(viewer_url: str) -> Optional[str]:
    """
    뷰어 페이지에서 실제 PDF URL 추출

    Args:
        viewer_url: 뷰어 페이지 URL

    Returns:
        실제 PDF URL 또는 None
    """
    try:
        headers = {**DEFAULT_HEADERS, "Referer": "https://www.courtauction.go.kr/"}
        resp = requests.get(viewer_url, headers=headers, timeout=15)

        if resp.status_code != 200:
            return None

        # HTML에서 PDF URL 추출
        # 패턴: src='/825B2D1A/001/EF313201/UI241206-01-001.pdf'
        match = re.search(r"\.src\s*=\s*['\"]([^'\"]+\.pdf)['\"]", resp.text)
        if match:
            pdf_path = match.group(1)
            return f"{KAPANET_BASE_URL}{pdf_path}"

        return None

    except Exception as e:
        print(f"[PDF] 뷰어 페이지 오류: {e}")
        return None


def download_appraisal_pdf(
    court_code: str,
    case_no: str,
    item_no: str,
    doc_id: str,
    doc_date: str,
    output_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    감정평가서 PDF 다운로드

    Args:
        court_code: 법원 코드 (예: "B000210" 또는 "000210")
        case_no: 사건번호 (예: "20240130005845")
        item_no: 물건번호 (예: "1")
        doc_id: 문서 ID (예: "UI241206-01-001")
        doc_date: 문서 날짜 (예: "20241213")
        output_path: 저장 경로 (None이면 자동 생성)

    Returns:
        (성공 여부, 파일 경로 또는 에러 메시지)
    """
    # 법원 코드 정규화 (B000210 → 000210)
    if court_code.startswith("B"):
        court_code = court_code[1:]

    # 뷰어 URL 구성
    viewer_url = f"{KAPANET_BASE_URL}/view/{court_code}/{case_no}/{item_no}/{doc_id}/{doc_date}"

    # 실제 PDF URL 얻기
    pdf_url = get_pdf_url_from_viewer(viewer_url)
    if not pdf_url:
        return False, "PDF URL을 찾을 수 없습니다"

    # PDF 다운로드
    try:
        headers = {**DEFAULT_HEADERS, "Referer": f"{KAPANET_BASE_URL}/"}
        resp = requests.get(pdf_url, headers=headers, timeout=60)

        if resp.status_code != 200:
            return False, f"다운로드 실패: {resp.status_code}"

        # PDF 확인
        if not resp.content.startswith(b"%PDF"):
            return False, "유효한 PDF 파일이 아닙니다"

        # 저장 경로
        if not output_path:
            output_path = f"appraisal_{case_no}_{item_no}.pdf"

        Path(output_path).write_bytes(resp.content)

        return True, output_path

    except Exception as e:
        return False, f"다운로드 오류: {e}"


def download_pdf_direct(pdf_url: str, output_path: str) -> Tuple[bool, str]:
    """
    직접 PDF URL로 다운로드

    Args:
        pdf_url: PDF URL
        output_path: 저장 경로

    Returns:
        (성공 여부, 파일 경로 또는 에러 메시지)
    """
    try:
        headers = {**DEFAULT_HEADERS, "Referer": f"{KAPANET_BASE_URL}/"}
        resp = requests.get(pdf_url, headers=headers, timeout=60)

        if resp.status_code != 200:
            return False, f"다운로드 실패: {resp.status_code}"

        if not resp.content.startswith(b"%PDF"):
            return False, "유효한 PDF 파일이 아닙니다"

        Path(output_path).write_bytes(resp.content)
        return True, output_path

    except Exception as e:
        return False, f"다운로드 오류: {e}"


# ============================================================
# 테스트
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("감정평가서 PDF 다운로더 테스트")
    print("=" * 60)

    # 테스트 케이스 (2024타경5845)
    viewer_url = "https://ca.kapanet.or.kr/view/000210/20240130005845/1/UI241206-01-001/20241213"

    print(f"\n뷰어 URL: {viewer_url}")

    # PDF URL 추출
    pdf_url = get_pdf_url_from_viewer(viewer_url)
    print(f"PDF URL: {pdf_url}")

    if pdf_url:
        # 다운로드
        output = Path(__file__).parent.parent / "data" / "test_download.pdf"
        success, result = download_pdf_direct(pdf_url, str(output))

        if success:
            print(f"\n다운로드 성공: {result}")
            print(f"파일 크기: {output.stat().st_size:,} bytes")
        else:
            print(f"\n다운로드 실패: {result}")
