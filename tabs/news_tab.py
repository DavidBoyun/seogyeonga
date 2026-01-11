"""
뉴스/유튜브 탭 - 경매 정보 수집
"""
import streamlit as st
from services import fetch_news, get_sample_youtube_videos
from components.news_item import render_news_list


def render_news_tab():
    """뉴스/유튜브 탭 렌더링"""

    # 헤더
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### 경매 정보")
    with col2:
        if st.button("🔄 새로고침", key="refresh_news"):
            st.cache_data.clear()
            st.rerun()

    # 콘텐츠 타입 선택
    content_type = st.radio(
        "콘텐츠 유형",
        ["📰 뉴스", "🎬 유튜브"],
        horizontal=True,
        key="content_type",
        label_visibility="collapsed"
    )

    st.markdown("---")

    if content_type == "📰 뉴스":
        render_news_section()
    else:
        render_youtube_section()


def render_news_section():
    """뉴스 섹션"""
    # 카테고리 필터
    categories = ["전체", "경매", "재개발", "분양", "부동산"]
    selected_category = st.radio(
        "카테고리",
        categories,
        horizontal=True,
        key="news_category",
        label_visibility="collapsed"
    )

    # 뉴스 로딩
    with st.spinner("뉴스를 불러오는 중..."):
        news_list = fetch_news_cached()

    # 카테고리 필터링
    if selected_category != "전체":
        filtered_news = [n for n in news_list if n.get('category') == selected_category]
    else:
        filtered_news = news_list

    # 결과 카운트
    st.caption(f"{len(filtered_news)}개 기사")

    # 뉴스 목록
    if filtered_news:
        render_news_list(filtered_news)
    else:
        st.info(f"'{selected_category}' 카테고리의 뉴스가 없습니다.")


def render_youtube_section():
    """유튜브 섹션"""
    st.caption("경매/부동산 관련 유튜브 영상")

    # 유튜브 영상 로딩
    videos = get_sample_youtube_videos()

    if not videos:
        st.info("유튜브 영상이 없습니다.")
        return

    st.caption(f"{len(videos)}개 영상")

    # 영상 카드 렌더링
    for video in videos:
        render_youtube_card(video)


def render_youtube_card(video: dict):
    """유튜브 영상 카드"""
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            # 썸네일
            st.image(video.get('thumbnail', ''), use_container_width=True)

        with col2:
            # 채널명
            st.caption(f"🎬 {video.get('channel', '')}")

            # 제목
            st.markdown(f"**{video.get('title', '')}**")

            # 요약
            summary = video.get('summary', '')
            if summary:
                st.text(summary[:100] + "..." if len(summary) > 100 else summary)

            # 보기 버튼
            st.link_button("▶️ 영상 보기", video.get('url', '#'), use_container_width=True)


@st.cache_data(ttl=600)  # 10분 캐시
def fetch_news_cached():
    """캐시된 뉴스 조회"""
    return fetch_news(limit=50)
