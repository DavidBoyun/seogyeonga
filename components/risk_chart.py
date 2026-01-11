"""
위험도 Radar Chart 컴포넌트
"""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List


def calculate_risk_scores(auction: Dict[str, Any]) -> Dict[str, int]:
    """경매 물건의 위험도 점수 계산 (0-100)"""

    scores = {
        "권리관계": 70,      # 기본값: 보통
        "가격경쟁력": 50,
        "입지/시세": 60,
        "임차인": 70,
        "유찰횟수": 80,
    }

    risk_level = auction.get('risk_level', '주의')
    risk_reason = auction.get('risk_reason', '') or ''

    # 권리관계 점수
    if risk_level == "안전":
        scores["권리관계"] = 90
    elif risk_level == "위험":
        scores["권리관계"] = 30
    else:
        scores["권리관계"] = 60

    # 위험 사유별 점수 조정
    if "유치권" in risk_reason:
        scores["권리관계"] -= 30
    if "가압류" in risk_reason:
        scores["권리관계"] -= 10
    if "선순위" in risk_reason:
        scores["권리관계"] -= 20
    if "임차인" in risk_reason or "대항력" in risk_reason:
        scores["임차인"] = 40

    # 가격 경쟁력 (할인율 기반)
    appraisal = auction.get('appraisal_price', 0)
    min_price = auction.get('min_price', 0)
    if appraisal and min_price:
        discount = (1 - min_price / appraisal) * 100
        if discount >= 40:
            scores["가격경쟁력"] = 95
        elif discount >= 30:
            scores["가격경쟁력"] = 80
        elif discount >= 20:
            scores["가격경쟁력"] = 65
        else:
            scores["가격경쟁력"] = 50

    # 유찰 횟수
    auction_count = auction.get('auction_count', 1)
    if auction_count == 1:
        scores["유찰횟수"] = 90  # 신건
    elif auction_count == 2:
        scores["유찰횟수"] = 70
    elif auction_count == 3:
        scores["유찰횟수"] = 50
    else:
        scores["유찰횟수"] = 30  # 4차 이상

    # 입지/시세 (강남 3구 등 프리미엄 지역)
    address = auction.get('address', '')
    premium_areas = ["강남구", "서초구", "송파구", "용산구", "마포구"]
    good_areas = ["영등포구", "성동구", "광진구", "동작구", "양천구"]

    for area in premium_areas:
        if area in address:
            scores["입지/시세"] = 90
            break
    else:
        for area in good_areas:
            if area in address:
                scores["입지/시세"] = 75
                break

    # 점수 범위 제한 (0-100)
    for key in scores:
        scores[key] = max(0, min(100, scores[key]))

    return scores


def render_risk_radar_chart(auction: Dict[str, Any]):
    """위험도 레이더 차트 렌더링"""

    scores = calculate_risk_scores(auction)

    categories = list(scores.keys())
    values = list(scores.values())

    # 차트를 닫기 위해 첫 값을 마지막에 추가
    categories.append(categories[0])
    values.append(values[0])

    # 색상 결정
    avg_score = sum(values[:-1]) / len(values[:-1])
    if avg_score >= 70:
        line_color = "#10B981"  # 녹색
        fill_color = "rgba(16, 185, 129, 0.3)"
    elif avg_score >= 50:
        line_color = "#F59E0B"  # 노랑
        fill_color = "rgba(245, 158, 11, 0.3)"
    else:
        line_color = "#EF4444"  # 빨강
        fill_color = "rgba(239, 68, 68, 0.3)"

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        name='위험도 점수'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
            ),
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 점수 요약
    st.markdown(f"**종합 점수: {avg_score:.0f}점**")

    # 상세 점수 표시
    cols = st.columns(5)
    for i, (cat, score) in enumerate(list(scores.items())[:5]):
        with cols[i]:
            if score >= 70:
                st.success(f"{cat}\n{score}점")
            elif score >= 50:
                st.warning(f"{cat}\n{score}점")
            else:
                st.error(f"{cat}\n{score}점")


def render_risk_summary(auction: Dict[str, Any]):
    """위험도 요약 카드"""

    scores = calculate_risk_scores(auction)
    avg_score = sum(scores.values()) / len(scores)

    # 종합 등급
    if avg_score >= 80:
        grade = "A"
        grade_color = "#10B981"
        grade_text = "매우 좋음"
    elif avg_score >= 70:
        grade = "B"
        grade_color = "#34D399"
        grade_text = "좋음"
    elif avg_score >= 60:
        grade = "C"
        grade_color = "#FBBF24"
        grade_text = "보통"
    elif avg_score >= 50:
        grade = "D"
        grade_color = "#F97316"
        grade_text = "주의"
    else:
        grade = "F"
        grade_color = "#EF4444"
        grade_text = "위험"

    with st.container(border=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 48px; font-weight: bold; color: {grade_color};">
                    {grade}
                </div>
                <div style="font-size: 14px; color: #6B7280;">
                    {grade_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.caption("항목별 점수")
            for cat, score in scores.items():
                progress = score / 100
                if score >= 70:
                    bar_color = "green"
                elif score >= 50:
                    bar_color = "orange"
                else:
                    bar_color = "red"
                st.progress(progress, text=f"{cat}: {score}점")
