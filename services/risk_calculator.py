"""
서경아 위험도 계산 (룰 기반, AI 없음)
"""
from typing import Tuple, Dict, Any


def calculate_risk(auction_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    룰 기반 위험도 계산

    Returns:
        (risk_level, risk_reason)
        risk_level: "안전" | "주의" | "위험"
    """

    has_senior_rights = auction_data.get('has_senior_rights', False)
    has_tenant = auction_data.get('has_tenant', False)
    auction_count = auction_data.get('auction_count', 1)
    remarks = auction_data.get('remarks', '') or ''

    # 특수 권리 키워드 체크
    danger_keywords = ['유치권', '법정지상권', '선순위전세권', '가등기', '지상권']
    caution_keywords = ['임차인', '대항력', '점유', '명도', '가압류']

    # 위험 판정 - 특수 권리
    for keyword in danger_keywords:
        if keyword in remarks:
            return "위험", f"{keyword} 존재"

    # 위험 판정 - 선순위 권리
    if has_senior_rights:
        return "위험", "선순위 권리 존재"

    # 주의 판정 - 주의 키워드
    for keyword in caution_keywords:
        if keyword in remarks:
            return "주의", f"{keyword} 있음 (확인 필요)"

    # 주의 판정 - 임차인
    if has_tenant:
        return "주의", "임차인 있음 (보증금 확인 필요)"

    # 주의 판정 - 다회 유찰
    if auction_count >= 3:
        return "주의", f"{auction_count}차 유찰 (원인 확인 필요)"

    # 주의 판정 - 2차
    if auction_count == 2:
        return "주의", "2차 경매 (유찰 사유 확인)"

    # 안전
    return "안전", "권리관계 단순"


def get_risk_emoji(risk_level: str) -> str:
    """위험도 이모지"""
    return {
        "안전": "🟢",
        "주의": "🟡",
        "위험": "🔴"
    }.get(risk_level, "⚪")


def get_risk_color(risk_level: str) -> str:
    """위험도 색상 (CSS)"""
    return {
        "안전": "#27ae60",
        "주의": "#f39c12",
        "위험": "#e74c3c"
    }.get(risk_level, "#999")
