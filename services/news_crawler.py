"""
서경아 뉴스/유튜브 크롤러 + AI 요약
"""
import feedparser
import requests
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

# 경매/부동산 관련 RSS 피드
NEWS_FEEDS = {
    "매경 부동산": "https://www.mk.co.kr/rss/30100041/",
    "한경 부동산": "https://www.hankyung.com/feed/realestate",
    "조선 부동산": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
}

# 경매/부동산 유튜브 채널 (RSS)
YOUTUBE_CHANNELS = {
    "부동산김사부": "UCqX3oNq9KqO3dX3X1X1X1X1",  # 예시 ID
    "경매의신": "UC1234567890abcdef",
    "부동산스터디": "UC0987654321fedcba",
}

# 유튜브 검색 키워드
YOUTUBE_SEARCH_KEYWORDS = [
    "서울 아파트 경매",
    "법원경매 초보",
    "아파트 권리분석",
    "경매 낙찰 후기",
]

# 경매 관련 키워드
AUCTION_KEYWORDS = [
    "경매", "낙찰", "입찰", "유찰", "법원경매",
    "강제경매", "임의경매", "공매", "경매시장"
]

# 부동산 키워드
REALESTATE_KEYWORDS = [
    "아파트", "재건축", "재개발", "분양", "매매",
    "전세", "월세", "부동산", "주택", "토지"
]


def fetch_news(limit: int = 50) -> List[Dict[str, Any]]:
    """뉴스 수집"""
    all_news = []

    for source, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')

                # HTML 태그 제거
                summary = re.sub(r'<[^>]+>', '', summary)[:300]

                # 발행일 파싱
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    published_at = datetime(*published[:6])
                else:
                    published_at = datetime.now()

                # 카테고리 분류
                category = classify_news(title + " " + summary)

                # 지역 추출
                region = extract_region(title + " " + summary)

                all_news.append({
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "url": link,
                    "published_at": published_at,
                    "category": category,
                    "region": region
                })

        except Exception as e:
            print(f"[ERROR] {source} 뉴스 수집 실패: {e}")

    # 최신순 정렬
    all_news.sort(key=lambda x: x['published_at'], reverse=True)

    return all_news[:limit]


def classify_news(text: str) -> str:
    """뉴스 카테고리 분류"""
    text = text.lower()

    # 경매 관련
    for keyword in AUCTION_KEYWORDS:
        if keyword in text:
            return "경매"

    # 재건축/재개발
    if "재건축" in text or "재개발" in text:
        return "재개발"

    # 분양
    if "분양" in text:
        return "분양"

    # 기타 부동산
    for keyword in REALESTATE_KEYWORDS:
        if keyword in text:
            return "부동산"

    return "기타"


def extract_region(text: str) -> str:
    """텍스트에서 지역 추출"""
    seoul_districts = [
        "강남", "서초", "송파", "강동", "마포",
        "영등포", "용산", "성동", "광진", "동작",
        "관악", "금천", "구로", "양천", "강서",
        "은평", "서대문", "종로", "중구", "성북",
        "동대문", "중랑", "노원", "도봉", "강북"
    ]

    for district in seoul_districts:
        if district in text:
            return f"{district}구"

    if "서울" in text:
        return "서울"

    return ""


def format_time_ago(dt: datetime) -> str:
    """시간 포맷 (N시간 전)"""
    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        if diff.days == 1:
            return "어제"
        return f"{diff.days}일 전"

    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}시간 전"

    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes}분 전"

    return "방금"


# ================================
# 유튜브 크롤링
# ================================

def fetch_youtube_videos(limit: int = 20) -> List[Dict[str, Any]]:
    """유튜브 영상 수집 (RSS 기반)"""
    videos = []

    # 채널 RSS에서 최신 영상 가져오기
    for channel_name, channel_id in YOUTUBE_CHANNELS.items():
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:5]:
                video_id = entry.get('yt_videoid', '')
                title = entry.get('title', '')
                published = entry.get('published_parsed')

                if published:
                    published_at = datetime(*published[:6])
                else:
                    published_at = datetime.now()

                videos.append({
                    "title": title,
                    "video_id": video_id,
                    "channel": channel_name,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                    "published_at": published_at,
                    "category": "유튜브",
                    "summary": "",  # AI로 채울 예정
                })
        except Exception as e:
            print(f"[ERROR] {channel_name} 유튜브 수집 실패: {e}")

    # 최신순 정렬
    videos.sort(key=lambda x: x['published_at'], reverse=True)
    return videos[:limit]


def get_sample_youtube_videos() -> List[Dict[str, Any]]:
    """샘플 유튜브 데이터 (API 없이 테스트용)"""
    return [
        {
            "title": "2024년 서울 아파트 경매 시장 전망 총정리",
            "video_id": "sample1",
            "channel": "부동산김사부",
            "url": "https://www.youtube.com/watch?v=sample1",
            "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "published_at": datetime.now(),
            "category": "유튜브",
            "summary": "서울 아파트 경매 시장 동향과 2024년 전망을 분석합니다.",
        },
        {
            "title": "법원경매 초보자 필수! 권리분석 완벽 가이드",
            "video_id": "sample2",
            "channel": "경매의신",
            "url": "https://www.youtube.com/watch?v=sample2",
            "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "published_at": datetime.now(),
            "category": "유튜브",
            "summary": "경매 초보자를 위한 권리분석 방법을 단계별로 설명합니다.",
        },
        {
            "title": "강남 아파트 경매 낙찰 후기 - 실제 수익 공개",
            "video_id": "sample3",
            "channel": "부동산스터디",
            "url": "https://www.youtube.com/watch?v=sample3",
            "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "published_at": datetime.now(),
            "category": "유튜브",
            "summary": "실제 강남 아파트 경매 낙찰 경험과 수익을 공유합니다.",
        },
    ]


# ================================
# AI 요약 기능
# ================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

SUMMARY_PROMPT = """다음 뉴스/콘텐츠를 경매 투자자 관점에서 2-3문장으로 요약해주세요.
핵심 정보와 투자 시사점을 포함해주세요.

제목: {title}
내용: {content}

요약:"""


def summarize_with_ollama(title: str, content: str) -> str:
    """Ollama로 요약 (로컬 무료)"""
    try:
        prompt = SUMMARY_PROMPT.format(title=title, content=content[:1000])
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[ERROR] Ollama 요약 실패: {e}")
    return ""


def summarize_with_deepseek(title: str, content: str) -> str:
    """DeepSeek API로 요약"""
    if not DEEPSEEK_API_KEY:
        return ""

    try:
        prompt = SUMMARY_PROMPT.format(title=title, content=content[:1000])
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[ERROR] DeepSeek 요약 실패: {e}")
    return ""


def summarize_content(title: str, content: str, provider: str = "auto") -> str:
    """콘텐츠 AI 요약"""
    if provider == "ollama":
        return summarize_with_ollama(title, content)
    elif provider == "deepseek":
        return summarize_with_deepseek(title, content)
    elif provider == "auto":
        # Ollama 먼저 시도, 실패하면 DeepSeek
        result = summarize_with_ollama(title, content)
        if not result and DEEPSEEK_API_KEY:
            result = summarize_with_deepseek(title, content)
        return result
    return ""


def fetch_news_with_summary(limit: int = 20, summarize: bool = False) -> List[Dict[str, Any]]:
    """뉴스 수집 + AI 요약"""
    news_list = fetch_news(limit)

    if summarize:
        for news in news_list:
            if not news.get('summary') or len(news['summary']) < 50:
                ai_summary = summarize_content(news['title'], news.get('summary', ''))
                if ai_summary:
                    news['ai_summary'] = ai_summary

    return news_list


def fetch_all_content(news_limit: int = 15, video_limit: int = 5) -> Dict[str, List]:
    """뉴스 + 유튜브 통합 수집"""
    return {
        "news": fetch_news(news_limit),
        "videos": get_sample_youtube_videos()[:video_limit],  # 샘플 사용
    }


# 테스트
if __name__ == "__main__":
    print("=== 뉴스 ===")
    news = fetch_news(5)
    for n in news:
        print(f"[{n['category']}] {n['title'][:50]}... - {n['source']}")

    print("\n=== 유튜브 ===")
    videos = get_sample_youtube_videos()
    for v in videos:
        print(f"[{v['channel']}] {v['title']}")
