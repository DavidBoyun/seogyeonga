"""
뉴스 아이템 컴포넌트 - Streamlit 네이티브 UI
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from services import format_time_ago


def get_category_emoji(category: str) -> str:
    """카테고리별 이모지"""
    emojis = {
        "경매": "🔨",
        "재개발": "🏗️",
        "분양": "🏠",
        "부동산": "📊",
        "기타": "📰",
    }
    return emojis.get(category, "📰")


def render_news_item(news: Dict[str, Any]):
    """뉴스 아이템 렌더링 - Streamlit 네이티브"""

    title = news.get('title', '')
    summary = news.get('summary', '') or ''
    source = news.get('source', '')
    url = news.get('url', '#')
    published_at = news.get('published_at')
    category = news.get('category', '기타')
    region = news.get('region', '')

    # 시간 포맷
    if isinstance(published_at, datetime):
        time_ago = format_time_ago(published_at)
    else:
        time_ago = ""

    # 카테고리 이모지
    cat_emoji = get_category_emoji(category)

    # 요약 처리
    if len(summary) > 150:
        summary_text = summary[:150] + '...'
    else:
        summary_text = summary

    # Streamlit 네이티브 카드
    with st.container(border=True):
        # 헤더: 카테고리 + 지역
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"{cat_emoji} {category}" + (f" | {region}" if region else ""))
        with col2:
            st.caption(time_ago)

        # 제목
        st.markdown(f"**{title}**")

        # 요약
        if summary_text:
            st.text(summary_text)

        # 푸터: 출처 + 링크
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"📰 {source}")
        with col2:
            st.link_button("기사 보기", url, use_container_width=True)


def render_news_list(news_list: List[Dict[str, Any]], category_filter: str = None):
    """뉴스 목록 렌더링"""

    if not news_list:
        st.info("뉴스가 없습니다.")
        return

    # 필터링
    if category_filter and category_filter != "전체":
        news_list = [n for n in news_list if n.get('category') == category_filter]

    if not news_list:
        st.info(f"'{category_filter}' 카테고리의 뉴스가 없습니다.")
        return

    for news in news_list:
        # dict 변환 (SQLAlchemy 모델인 경우)
        if hasattr(news, '__dict__') and not isinstance(news, dict):
            news_dict = {
                'title': news.title,
                'summary': news.summary,
                'source': news.source,
                'url': news.url,
                'published_at': news.published_at,
                'category': news.category,
                'region': news.region,
            }
        else:
            news_dict = news

        render_news_item(news_dict)
