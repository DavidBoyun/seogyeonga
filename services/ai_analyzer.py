"""
서경아 AI 권리분석 모듈
Ollama, DeepSeek, Claude 지원
"""

import os
import requests
from typing import Dict, Optional

# 환경변수
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# 기본 모델 설정
DEFAULT_PROVIDER = os.getenv("AI_PROVIDER", "ollama")  # ollama, deepseek, claude, rule


# ================================
# 프롬프트 템플릿
# ================================

SYSTEM_PROMPT = """당신은 '서경아', 서울 아파트 경매 전문 AI 분석가입니다.

## 역할
- 경매 초보자도 이해할 수 있게 쉬운 말로 설명
- 객관적인 정보 제공 (공포 유발 X)
- 위험 요소를 놓치지 않되, 과장하지 않음

## 분석 원칙
1. 종합 위험도를 상/중/하로 판단
2. 각 위험 요소별로 쉬운 설명
3. 초보자가 알아야 할 핵심 포인트
4. 구체적인 확인 사항

## 출력 형식
- 마크다운 형식
- 이모지 사용
- 핵심은 **볼드** 처리
- 2000자 이내로 간결하게"""

ANALYSIS_PROMPT = """다음 경매 물건을 분석해주세요.

[물건 정보]
- 소재지: {address}
- 아파트명: {apt_name}
- 면적: {area}㎡
- 관할법원: {court}
- 사건번호: {case_no}

[가격]
- 감정가: {appraisal_price}
- 최저가: {min_price} ({discount_rate}% 할인)
- 경매 차수: {auction_count}차

[상태]
- 입찰일: {auction_date}
- 위험도: {risk_level}
- 위험사유: {risk_reason}

---
종합 위험도, 주의사항, 체크리스트를 포함해서 분석해주세요.
마지막에 "이 분석은 참고용이며, 전문가 상담을 권장합니다"를 넣어주세요."""


class SeogyeongaAI:
    """서경아 AI 분석 클래스"""

    def __init__(self, provider: str = None):
        self.provider = provider or DEFAULT_PROVIDER

    def analyze(self, auction: Dict) -> str:
        """경매 물건 AI 분석"""

        prompt = self._build_prompt(auction)

        if self.provider == "ollama":
            return self._analyze_ollama(prompt)
        elif self.provider == "deepseek":
            return self._analyze_deepseek(prompt)
        elif self.provider == "claude":
            return self._analyze_claude(prompt)
        else:
            return self._fallback_analysis(auction)

    def _build_prompt(self, auction: Dict) -> str:
        """프롬프트 생성"""
        appraisal = auction.get('appraisal_price', 0)
        min_price = auction.get('min_price', 0)
        discount_rate = round((1 - min_price / appraisal) * 100, 1) if appraisal > 0 else 0

        return ANALYSIS_PROMPT.format(
            address=auction.get('address', '정보 없음'),
            apt_name=auction.get('apt_name', '아파트'),
            area=auction.get('area', 0),
            court=auction.get('court', '정보 없음'),
            case_no=auction.get('case_no', '정보 없음'),
            appraisal_price=self._format_price(appraisal),
            min_price=self._format_price(min_price),
            discount_rate=discount_rate,
            auction_count=auction.get('auction_count', 1),
            auction_date=auction.get('auction_date', '미정'),
            risk_level=auction.get('risk_level', '주의'),
            risk_reason=auction.get('risk_reason', '없음') or '없음'
        )

    def _analyze_ollama(self, prompt: str) -> str:
        """Ollama로 분석 (로컬 무료)"""
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "llama3.2",  # 또는 deepseek-r1, mistral 등
                    "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("response", self._fallback_msg())
            else:
                return self._fallback_msg() + f"\n(Ollama 오류: {response.status_code})"
        except Exception as e:
            return self._fallback_msg() + f"\n(Ollama 연결 실패: {e})"

    def _analyze_deepseek(self, prompt: str) -> str:
        """DeepSeek API로 분석"""
        if not DEEPSEEK_API_KEY:
            return self._fallback_msg() + "\n(DeepSeek API 키 없음)"

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return self._fallback_msg()
        except Exception as e:
            return self._fallback_msg() + f"\n(DeepSeek 오류: {e})"

    def _analyze_claude(self, prompt: str) -> str:
        """Claude API로 분석"""
        if not ANTHROPIC_API_KEY:
            return self._fallback_msg() + "\n(Claude API 키 없음)"

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return self._fallback_msg() + f"\n(Claude 오류: {e})"

    def _fallback_msg(self) -> str:
        return "AI 분석을 사용할 수 없어 룰 기반 분석을 제공합니다."

    def _fallback_analysis(self, auction: Dict) -> str:
        """룰 기반 분석 (AI 없이)"""
        risk_level = auction.get('risk_level', '주의')
        risk_reason = auction.get('risk_reason', '')
        apt_name = auction.get('apt_name', '아파트')

        # 위험도 아이콘
        icons = {'안전': '🟢', '위험': '🔴', '주의': '🟡'}
        level_map = {'안전': '하', '위험': '상', '주의': '중'}

        icon = icons.get(risk_level, '🟡')
        level = level_map.get(risk_level, '중')

        result = [f"## {icon} 종합 위험도: {level}"]
        result.append(f"\n### {apt_name} 분석 결과\n")

        if risk_level == '안전':
            result.append("""
**권리관계 양호**

이 물건은 특별한 권리상 하자가 발견되지 않았습니다.
비교적 안전한 물건으로 보입니다.
""")
        else:
            result.append("**주의사항**\n")
            if risk_reason:
                if '유치권' in risk_reason:
                    result.append("- **유치권**: 경매로 소멸하지 않을 수 있음. 현장 확인 필수\n")
                if '임차인' in risk_reason or '대항력' in risk_reason:
                    result.append("- **임차인**: 보증금 인수 가능성. 배당요구 확인 필요\n")
                if '가압류' in risk_reason:
                    result.append("- **가압류**: 대부분 매각으로 소멸. 상대적으로 안전\n")
                if '선순위' in risk_reason:
                    result.append("- **선순위 권리**: 인수 여부 확인 필요\n")
            else:
                result.append("- 위험 요소 상세 확인 필요\n")

        # 가격 분석
        appraisal = auction.get('appraisal_price', 0)
        min_price = auction.get('min_price', 0)
        auction_count = auction.get('auction_count', 1)

        if appraisal and min_price:
            discount = round((1 - min_price / appraisal) * 100)
            result.append(f"""
---
### 가격 분석
- 감정가 대비 **{discount}%** 할인
- 현재 **{auction_count}차** 경매
""")
            if auction_count >= 3:
                result.append("- 3차 이상 유찰: 입지나 권리관계 문제 가능성\n")

        result.append("""
---
### 입찰 전 체크리스트
1. 등기부등본 최신본 발급
2. 현황조사서 확인
3. 현장 방문
4. 예상 비용 계산

*이 분석은 참고용이며, 전문가 상담을 권장합니다.*
""")

        return "\n".join(result)

    def _format_price(self, price: int) -> str:
        if not price:
            return "-"
        if price >= 100000000:
            억 = price // 100000000
            만 = (price % 100000000) // 10000
            return f"{억}억 {만:,}만원" if 만 else f"{억}억원"
        elif price >= 10000:
            return f"{price // 10000:,}만원"
        return f"{price:,}원"


# 싱글톤
_ai_instance = None

def get_ai(provider: str = None) -> SeogyeongaAI:
    global _ai_instance
    if _ai_instance is None or provider:
        _ai_instance = SeogyeongaAI(provider)
    return _ai_instance

def analyze_auction(auction: Dict, provider: str = None) -> str:
    """경매 물건 분석"""
    ai = SeogyeongaAI(provider or "rule")  # 기본값: 룰 기반
    return ai.analyze(auction)


def generate_appraisal_summary(auction: Dict, case_data: Dict = None) -> str:
    """
    감정평가서 스타일 AI 요약 생성
    (실제 PDF 없이 사건 데이터 기반)

    Args:
        auction: 경매 물건 기본 정보
        case_data: API에서 받은 사건 상세 데이터

    Returns:
        감정평가서 스타일 요약 마크다운
    """
    apt_name = auction.get('apt_name', '대상 물건')
    address = auction.get('address', '-')
    area = auction.get('area', 0)
    appraisal_price = auction.get('appraisal_price', 0)
    min_price = auction.get('min_price', 0)
    court = auction.get('court', '-')
    case_no = auction.get('case_no', '-')
    auction_count = auction.get('auction_count', 1)
    risk_level = auction.get('risk_level', '주의')
    risk_reason = auction.get('risk_reason', '')

    # 가격 포맷팅
    def format_price(price):
        if not price:
            return "-"
        if price >= 100000000:
            억 = price // 100000000
            만 = (price % 100000000) // 10000
            return f"{억}억 {만:,}만원" if 만 else f"{억}억원"
        return f"{price // 10000:,}만원" if price >= 10000 else f"{price:,}원"

    # 할인율 계산
    discount_rate = round((1 - min_price / appraisal_price) * 100) if appraisal_price > 0 else 0

    # 위험도 아이콘
    risk_icons = {'안전': '🟢', '주의': '🟡', '위험': '🔴'}
    risk_icon = risk_icons.get(risk_level, '🟡')

    # 감정평가서 스타일 요약 생성
    summary = f"""
## 📋 AI 감정평가 요약

### 1. 물건 개요

| 항목 | 내용 |
|------|------|
| **물건명** | {apt_name} |
| **소재지** | {address} |
| **전용면적** | {area}㎡ ({round(area * 0.3025, 1) if area else 0}평) |
| **관할법원** | {court} |
| **사건번호** | {case_no} |

---

### 2. 가격 정보

| 구분 | 금액 |
|------|------|
| **감정가** | {format_price(appraisal_price)} |
| **최저매각가** | {format_price(min_price)} |
| **할인율** | {discount_rate}% |
| **경매차수** | {auction_count}차 |

"""

    # 시세 분석 (예상)
    if appraisal_price:
        summary += f"""
> 💡 **가격 포인트**
> - 감정가 대비 **{discount_rate}%** 할인된 가격으로 시작
> - {auction_count}차 경매 {"(신건)" if auction_count == 1 else f"({auction_count-1}회 유찰)"}
"""

    # 권리관계 분석
    summary += f"""
---

### 3. {risk_icon} 권리관계 분석

**종합 위험도: {risk_level}**

"""

    if risk_reason:
        reasons = risk_reason.split(',') if ',' in risk_reason else [risk_reason]
        for reason in reasons:
            reason = reason.strip()
            if '유치권' in reason:
                summary += """
⚠️ **유치권 주의**
- 유치권은 경매로 소멸하지 않을 수 있습니다
- 반드시 현장 방문하여 점유 현황 확인
- 유치권 금액과 근거 확인 필요
"""
            elif '임차인' in reason or '대항력' in reason:
                summary += """
⚠️ **임차인 확인 필요**
- 대항력 있는 임차인의 보증금은 인수될 수 있습니다
- 배당요구 여부 확인 필수
- 전입신고일, 확정일자 확인
"""
            elif '선순위' in reason:
                summary += """
⚠️ **선순위 권리 존재**
- 매각으로 소멸하지 않는 권리가 있을 수 있습니다
- 등기부등본에서 설정일자 반드시 확인
"""
            elif '유찰' in reason:
                summary += f"""
ℹ️ **{reason}**
- 반복 유찰은 입지, 권리관계, 하자 등 원인 파악 필요
- 할인율이 높아 기회일 수 있으나 신중한 검토 필요
"""
            else:
                summary += f"- {reason}\n"
    else:
        if risk_level == '안전':
            summary += """
✅ **특이사항 없음**
- 등기부등본상 특별한 권리 하자가 발견되지 않았습니다
- 비교적 안전한 물건으로 판단됩니다
"""
        else:
            summary += "- 상세 권리관계는 등기부등본과 현황조사서를 통해 확인하세요\n"

    # 입찰 전 체크리스트
    summary += """
---

### 4. 📝 입찰 전 체크리스트

| 순서 | 확인사항 | 중요도 |
|------|---------|--------|
| 1 | 등기부등본 최신본 발급 및 확인 | ⭐⭐⭐ |
| 2 | 현황조사서 열람 | ⭐⭐⭐ |
| 3 | 현장 방문 및 점유자 확인 | ⭐⭐⭐ |
| 4 | 인수되는 권리 확인 (선순위, 유치권 등) | ⭐⭐⭐ |
| 5 | 관리비 체납 여부 확인 | ⭐⭐ |
| 6 | 예상 낙찰가 및 총 비용 계산 | ⭐⭐ |
| 7 | 대출 가능 여부 사전 확인 | ⭐⭐ |

---

### 5. 💡 초보자를 위한 조언

"""

    if auction_count >= 3:
        summary += """
> 🔍 **여러 번 유찰된 물건입니다**
> - 할인율이 높아 매력적으로 보일 수 있으나
> - 유찰된 이유를 반드시 파악하세요 (입지, 권리관계, 하자 등)
> - 전문가 상담을 권장합니다
"""
    elif risk_level == '안전':
        summary += """
> ✅ **비교적 안전한 물건으로 보입니다**
> - 그래도 직접 현장 방문은 필수입니다
> - 등기부등본 최신본을 발급받아 확인하세요
> - 명도(인도) 문제가 없는지 확인하세요
"""
    else:
        summary += """
> ⚠️ **주의가 필요한 물건입니다**
> - 권리관계를 꼼꼼히 확인하세요
> - 잘 모르겠다면 전문가에게 문의하세요
> - 무리한 입찰은 피하세요
"""

    summary += """
---

⚠️ *이 분석은 AI가 제공하는 참고 정보입니다. 실제 투자 결정 시 반드시 전문가 상담과 현장 확인을 진행하세요.*
"""

    return summary
