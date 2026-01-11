"""
서경아 PDF 리포트 생성 서비스
경매 물건 분석 리포트 (4,900원 트립와이어)
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os


# 한글 폰트 설정 (Windows 기준)
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_NAME = "Malgun"

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
    else:
        # 대체 폰트 경로 시도
        alt_paths = [
            "C:/Windows/Fonts/gulim.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        ]
        for path in alt_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(FONT_NAME, path))
                break
except Exception as e:
    print(f"[WARN] 한글 폰트 로드 실패: {e}")
    FONT_NAME = "Helvetica"


def format_price(price: int) -> str:
    """가격 포맷 (억/만원)"""
    if not price:
        return "-"
    if price >= 100000000:
        억 = price // 100000000
        만 = (price % 100000000) // 10000
        return f"{억}억 {만:,}만원" if 만 else f"{억}억원"
    elif price >= 10000:
        return f"{price // 10000:,}만원"
    return f"{price:,}원"


def get_risk_color(risk_level: str) -> colors.Color:
    """위험도별 색상"""
    risk_colors = {
        "안전": colors.HexColor("#10B981"),
        "주의": colors.HexColor("#F59E0B"),
        "위험": colors.HexColor("#EF4444"),
    }
    return risk_colors.get(risk_level, colors.gray)


def create_styles() -> Dict[str, ParagraphStyle]:
    """스타일 생성"""
    base_styles = getSampleStyleSheet()

    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base_styles["Title"],
            fontName=FONT_NAME,
            fontSize=24,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            fontName=FONT_NAME,
            fontSize=12,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER,
            spaceAfter=30,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            fontName=FONT_NAME,
            fontSize=16,
            textColor=colors.HexColor("#1F2937"),
            spaceBefore=20,
            spaceAfter=10,
            leftIndent=0,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            fontName=FONT_NAME,
            fontSize=13,
            textColor=colors.HexColor("#374151"),
            spaceBefore=15,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName=FONT_NAME,
            fontSize=10,
            textColor=colors.HexColor("#4B5563"),
            leading=16,
            spaceAfter=8,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            fontName=FONT_NAME,
            fontSize=9,
            textColor=colors.HexColor("#9CA3AF"),
            alignment=TA_CENTER,
        ),
        "Warning": ParagraphStyle(
            "Warning",
            fontName=FONT_NAME,
            fontSize=10,
            textColor=colors.HexColor("#B45309"),
            backColor=colors.HexColor("#FEF3C7"),
            leftIndent=10,
            rightIndent=10,
            spaceBefore=10,
            spaceAfter=10,
        ),
    }
    return styles


def generate_auction_report(
    auction: Dict[str, Any],
    analysis: str = "",
    include_checklist: bool = True
) -> bytes:
    """경매 물건 PDF 리포트 생성"""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    styles = create_styles()
    story = []

    # ===== 표지 =====
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("🏠 서경아 경매 분석 리포트", styles["Title"]))
    story.append(Spacer(1, 10*mm))

    apt_name = auction.get('apt_name', '아파트')
    story.append(Paragraph(apt_name, styles["Title"]))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        f"생성일: {datetime.now().strftime('%Y년 %m월 %d일')}",
        styles["Subtitle"]
    ))

    # 위험도 배지
    risk_level = auction.get('risk_level', '주의')
    risk_color = get_risk_color(risk_level)
    story.append(Spacer(1, 20*mm))

    risk_table = Table(
        [[f"종합 위험도: {risk_level}"]],
        colWidths=[80*mm],
    )
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', (0, 0), (-1, -1), 5),
    ]))
    story.append(risk_table)

    story.append(PageBreak())

    # ===== 물건 개요 =====
    story.append(Paragraph("📋 물건 개요", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))

    # 기본 정보 테이블
    info_data = [
        ["항목", "내용"],
        ["소재지", auction.get('address', '-')],
        ["아파트명", apt_name],
        ["면적", f"{auction.get('area', 0)}㎡"],
        ["관할법원", auction.get('court', '-')],
        ["사건번호", auction.get('case_no', '-')],
        ["경매차수", f"{auction.get('auction_count', 1)}차"],
        ["입찰일", str(auction.get('auction_date', '-'))],
    ]

    info_table = Table(info_data, colWidths=[40*mm, 120*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#374151")),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10*mm))

    # ===== 가격 정보 =====
    story.append(Paragraph("💰 가격 정보", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))

    appraisal = auction.get('appraisal_price', 0)
    min_price = auction.get('min_price', 0)
    discount = round((1 - min_price / appraisal) * 100) if appraisal else 0

    price_data = [
        ["구분", "금액", "비고"],
        ["감정가", format_price(appraisal), "법원 감정 기준"],
        ["최저입찰가", format_price(min_price), f"감정가 대비 {100-discount}%"],
        ["할인율", f"-{discount}%", ""],
    ]

    price_table = Table(price_data, colWidths=[40*mm, 60*mm, 60*mm])
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(price_table)
    story.append(Spacer(1, 10*mm))

    # ===== 위험 분석 =====
    story.append(Paragraph("⚠️ 위험 분석", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))

    risk_reason = auction.get('risk_reason', '')
    if risk_reason:
        story.append(Paragraph(f"위험 사유: {risk_reason}", styles["Warning"]))
    else:
        story.append(Paragraph("특별한 위험 요소가 발견되지 않았습니다.", styles["Body"]))

    story.append(Spacer(1, 5*mm))

    # AI 분석 결과
    if analysis:
        story.append(Paragraph("🤖 AI 권리분석 결과", styles["Heading2"]))
        # 마크다운 변환 (간단한 처리)
        analysis_text = analysis.replace("**", "").replace("##", "").replace("#", "")
        for line in analysis_text.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
        story.append(Spacer(1, 10*mm))

    # ===== 체크리스트 =====
    if include_checklist:
        story.append(PageBreak())
        story.append(Paragraph("✅ 입찰 전 체크리스트", styles["Heading1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))

        checklist_items = [
            "☐ 등기부등본 최신본 발급 확인",
            "☐ 현황조사서 내용 검토",
            "☐ 매각물건명세서 확인",
            "☐ 임차인 현황 파악",
            "☐ 배당요구종기 확인",
            "☐ 현장 방문 및 상태 확인",
            "☐ 관리비 체납 여부 확인",
            "☐ 예상 취득세/등록세 계산",
            "☐ 입찰보증금 준비 (최저가의 10%)",
            "☐ 잔금 조달 계획 수립",
        ]

        for item in checklist_items:
            story.append(Paragraph(item, styles["Body"]))
        story.append(Spacer(1, 10*mm))

    # ===== 면책조항 =====
    story.append(Spacer(1, 20*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 5*mm))

    disclaimer = """
    본 리포트는 참고용으로 제공되며, 투자 결정의 근거로 사용할 수 없습니다.
    실제 투자 전 반드시 법률 전문가 및 부동산 전문가와 상담하시기 바랍니다.
    서경아는 본 리포트의 내용에 대해 법적 책임을 지지 않습니다.
    """
    story.append(Paragraph(disclaimer.strip(), styles["Caption"]))

    # PDF 생성
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def get_report_filename(auction: Dict[str, Any]) -> str:
    """리포트 파일명 생성"""
    apt_name = auction.get('apt_name', 'auction')
    date_str = datetime.now().strftime('%Y%m%d')
    return f"서경아_분석리포트_{apt_name}_{date_str}.pdf"


# 테스트
if __name__ == "__main__":
    sample_auction = {
        "id": 1,
        "apt_name": "강남힐스테이트",
        "address": "서울특별시 강남구 역삼동 123-45",
        "area": 84.5,
        "court": "서울중앙지방법원",
        "case_no": "2024타경12345",
        "auction_count": 2,
        "auction_date": "2024-02-15",
        "appraisal_price": 1500000000,
        "min_price": 1050000000,
        "risk_level": "주의",
        "risk_reason": "선순위 임차인 있음 (보증금 3억)",
    }

    pdf_bytes = generate_auction_report(sample_auction)
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF 생성 완료: test_report.pdf")
