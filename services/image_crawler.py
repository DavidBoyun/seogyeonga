"""
매물 사진 크롤러
- 네이버 부동산 이미지
- 법원 경매 감정평가 사진 (스텁)
"""
import os
import re
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup


# 네이버 부동산 API (비공식)
NAVER_LAND_SEARCH_URL = "https://m.land.naver.com/search/result/"
NAVER_LAND_COMPLEX_URL = "https://m.land.naver.com/complex/info/"

# 샘플 이미지 (Unsplash)
SAMPLE_APARTMENT_IMAGES = [
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=400",
]


def search_naver_complex(apt_name: str, address: str) -> Optional[str]:
    """
    네이버 부동산에서 아파트 단지 검색

    Returns: 단지 ID (complex_no) or None
    """
    try:
        # 검색 키워드 생성
        search_query = apt_name
        if address:
            # 주소에서 구/동 추출
            match = re.search(r'([\w]+구)\s*([\w]+동)?', address)
            if match:
                search_query = f"{match.group(1)} {apt_name}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        # 네이버 부동산 검색 API
        response = requests.get(
            f"https://m.land.naver.com/search/result/{search_query}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            # HTML에서 단지 정보 추출
            soup = BeautifulSoup(response.text, 'html.parser')

            # 단지 링크 찾기
            complex_links = soup.find_all('a', href=re.compile(r'/complex/info/\d+'))
            if complex_links:
                href = complex_links[0].get('href', '')
                match = re.search(r'/complex/info/(\d+)', href)
                if match:
                    return match.group(1)

        return None

    except Exception as e:
        print(f"[IMAGE] 네이버 단지 검색 실패: {e}")
        return None


def fetch_naver_images(complex_no: str, limit: int = 5) -> List[str]:
    """
    네이버 부동산 단지 이미지 조회

    Returns: 이미지 URL 리스트
    """
    if not complex_no:
        return []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        # 단지 상세 페이지
        response = requests.get(
            f"https://m.land.naver.com/complex/info/{complex_no}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 이미지 태그 찾기
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '') or img.get('data-src', '')
                if src and ('landthumb' in src or 'phinf.pstatic.net' in src):
                    # 고해상도 이미지로 변환
                    if 'type=' in src:
                        src = re.sub(r'type=\w+', 'type=m', src)
                    images.append(src)
                    if len(images) >= limit:
                        break

            return images

        return []

    except Exception as e:
        print(f"[IMAGE] 네이버 이미지 조회 실패: {e}")
        return []


def get_auction_images(auction: Dict[str, Any]) -> List[str]:
    """
    경매 물건 이미지 조회

    1. 네이버 부동산에서 검색
    2. 실패시 샘플 이미지 반환
    """
    apt_name = auction.get('apt_name', '')
    address = auction.get('address', '')

    # 네이버 부동산 검색 시도
    complex_no = search_naver_complex(apt_name, address)
    if complex_no:
        images = fetch_naver_images(complex_no)
        if images:
            return images

    # 샘플 이미지 반환
    return get_sample_images(auction)


def get_sample_images(auction: Dict[str, Any]) -> List[str]:
    """샘플 이미지 반환"""
    # 해시 기반으로 일관된 이미지 선택
    apt_name = auction.get('apt_name', 'default')
    hash_val = hash(apt_name) % len(SAMPLE_APARTMENT_IMAGES)

    # 2-3개 이미지 반환
    images = []
    for i in range(3):
        idx = (hash_val + i) % len(SAMPLE_APARTMENT_IMAGES)
        images.append(SAMPLE_APARTMENT_IMAGES[idx])

    return images


def get_court_auction_images(case_no: str, court: str) -> List[str]:
    """
    법원 경매 감정평가 사진 조회 (스텁)

    실제 구현시: 법원 경매 사이트에서 사건번호로 검색하여
    감정평가서 첨부 이미지를 다운로드

    현재: 미구현 (API 변경으로 인해)
    """
    # TODO: 법원 경매 사이트 API가 변경되어 구현 필요
    # 현재는 빈 리스트 반환
    print(f"[IMAGE] 법원 경매 이미지 조회 (미구현): {court} {case_no}")
    return []


# 이미지 캐시 (메모리)
_image_cache: Dict[str, List[str]] = {}


def get_cached_images(auction_id: str, auction: Dict[str, Any]) -> List[str]:
    """캐시된 이미지 조회"""
    if auction_id not in _image_cache:
        _image_cache[auction_id] = get_auction_images(auction)
    return _image_cache[auction_id]


def clear_image_cache():
    """이미지 캐시 초기화"""
    global _image_cache
    _image_cache = {}


# 테스트
if __name__ == "__main__":
    sample_auction = {
        "apt_name": "래미안블레스티지",
        "address": "서울특별시 서초구 반포동 20-1",
    }

    print("=== 이미지 검색 테스트 ===")
    images = get_auction_images(sample_auction)
    for i, img in enumerate(images):
        print(f"{i+1}. {img[:50]}...")
