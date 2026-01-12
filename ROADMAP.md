# 서경아 개발 로드맵

> 작성일: 2024-01-12
> 최종 업데이트: 2026-01-12 17:20
> 목표: MVP → 실제 운영 가능한 서비스
> 확장: 서경아(서울) → 한경아(전국 아파트)

---

## 현재 상태 (2026-01-12)

### 완료된 기능
| 기능 | 상태 | 파일 |
|------|------|------|
| Streamlit UI | ✅ OK | `app.py` |
| AI 권리분석 | ✅ OK | `services/ai_analyzer.py` |
| PDF 리포트 생성 | ✅ OK | `services/pdf_report.py` |
| Radar Chart 위험도 | ✅ OK | `components/risk_chart.py` |
| 뉴스/유튜브 크롤링 | ✅ OK | `services/news_crawler.py` |
| **법원 크롤러 (60개 법원)** | ✅ OK | `services/court_crawler.py` |
| **사건번호 조회** | ✅ OK | `tabs/case_lookup.py` |
| 배포 설정 | ✅ OK | `.streamlit/config.toml` |
| **Streamlit Cloud 배포** | ✅ OK | [seogyeonga.streamlit.app](https://seogyeonga-wggf87rh2g7krntnpspvyf.streamlit.app/) |

### 작동하는 핵심 기능
```
사건번호 조회 → 실제 법원경매 API 연동 → AI 분석 → PDF 리포트
```

### 개발 중인 기능
| 기능 | 상태 | 비고 |
|------|------|------|
| 물건 목록 검색 | 🚧 개발 중 | 구 API deprecated, 신규 API 분석 필요 |
| **AI 감정평가 요약** | ✅ 완료 | 사건 데이터 기반 감정평가서 스타일 분석 |
| 실제 이미지 크롤링 | 📋 예정 | 감정평가서 PDF에서 추출 |

---

## 완료된 Phase

### ✅ Phase 1: 배포 완료

#### 1-1. Streamlit Cloud 배포
```
상태: ✅ 완료
결과: https://seogyeonga-wggf87rh2g7krntnpspvyf.streamlit.app/
GitHub: https://github.com/DavidBoyun/seogyeonga
```

#### 1-2. QA 테스트
```
상태: ✅ 완료
- 사이드바 중복 메뉴 수정 (pages/ → tabs/)
- 사건번호 조회 기능 정상 작동 확인
```

---

### 🚧 Phase 2: 실제 데이터 연동 (진행 중)

#### 2-1. 검색 API 분석
```
상태: 🔍 분석 완료 (구 API deprecated)

발견 사항:
- 구 API (RetrieveRealEstMulDetailList.laf): 404 반환
- 신규 시스템 (/pgj/): WebSquare 기반
- 사건번호 조회 API: 정상 작동

다음 단계:
- Option A: 신규 /pgj/ 검색 API 파라미터 분석
- Option B: 하옥션(Hauction) 등 대체 소스 연동
- Option C: Selenium/Playwright로 동적 크롤링
```

#### 2-2. AI 감정평가 요약 (✅ 완료)
```
상태: ✅ 완료

구현 내용:
- generate_appraisal_summary() 함수 추가
- 감정평가서 스타일의 상세 분석 리포트 생성
- 물건 개요, 가격 정보, 권리관계, 체크리스트, 초보자 조언 포함
- 사건조회 탭에서 "AI 감정평가 요약" 선택 가능
- PDF 리포트에 포함 가능

참고: 실제 PDF 다운로드는 URL 분석 후 추가 예정
```

#### 2-2. 감정평가서 연동 (핵심 가치)
```
현재: 구조만 완성
목표: 실제 PDF 다운로드 및 파싱

단계:
1. PDF 다운로드 URL 분석
2. PyMuPDF로 이미지 추출
3. pdfplumber로 텍스트 추출
4. AI 요약 기능 연결

가치: "AI가 읽어주는 감정평가서" = 유료 결제 포인트
```

#### 2-3. 사용자 경험 개선
```
- 로딩 상태 개선
- 에러 메시지 친화적으로
- 모바일 반응형 확인
```

---

### Phase 3: 2주차 (Day 8-14)

#### 3-1. 카카오 로그인
```
준비물:
- 카카오 개발자 앱 등록
- Redirect URI 설정 (Streamlit Cloud URL)

구현:
- OAuth 2.0 플로우
- 사용자 DB 저장
- 즐겨찾기 기능 활성화
```

#### 3-2. 유료 기능 설계
```
무료:
- 사건번호 조회
- 기본 AI 분석

유료 (트립와이어 4,900원):
- 상세 PDF 리포트
- 감정평가서 AI 요약
- 권리분석 상세 설명

구독 (월 9,900원):
- 무제한 리포트
- 알림 서비스
- 우선 지원
```

---

### Phase 4: 3주차 (Day 15-21)

#### 4-1. 결제 시스템
```
옵션:
- 토스페이먼츠 (사업자 필요)
- 카카오페이
- 페이팔 (해외 결제)

MVP: 카카오페이 간편결제
```

#### 4-2. 알림 서비스
```
카카오톡 알림:
- 비즈니스 채널 등록
- 알림톡 템플릿 승인
- D-3, D-1 자동 발송

이메일 (대안):
- Resend 또는 SendGrid
- 비용 효율적
```

---

### Phase 5: 4주차+ (성장)

#### 5-1. 한경아 확장
```
서울 → 전국:
- 60개 법원 이미 지원
- 지역 선택 UI 추가
- 브랜딩: "서경아" → "한경아"
```

#### 5-2. 커뮤니티 기능
```
경매 일기:
- 관심 물건 메모
- 답사 사진 업로드
- 입찰 결과 기록

커뮤니티:
- 후기 공유
- 질문/답변
```

#### 5-3. 데이터 수익화
```
- 경매 트렌드 리포트
- 낙찰가 예측 AI
- B2B API 제공
```

---

## 기술 스택

### 현재
```
Frontend: Streamlit
Backend: Python
Database: SQLite (SQLAlchemy)
AI: Rule-based + DeepSeek/Claude API (선택)
```

### 확장 시
```
Frontend: Next.js (필요 시)
Backend: FastAPI
Database: PostgreSQL (Supabase)
Infra: Vercel / Railway
```

---

## 핵심 원칙

### 1. Ship Fast
```
"완벽한 것보다 작동하는 것"
- 기능 하나씩 배포
- 피드백 받고 개선
```

### 2. User First
```
"사용자가 원하는 것만 만든다"
- 자동 검색? → 사용자가 요청하면
- 예쁜 UI? → 기능이 먼저
```

### 3. Revenue Focus
```
"돈이 되는 기능부터"
- 무료로 가치 증명
- 유료로 전환 유도
- 감정평가서 AI 요약 = 핵심
```

---

## 다음 액션 (지금 바로)

### Step 1: GitHub 배포
```bash
# seogyeonga 폴더에서
git init
git add .
git commit -m "Initial commit: 서경아 MVP"
git remote add origin https://github.com/YOUR_USERNAME/seogyeonga.git
git push -u origin main
```

### Step 2: Streamlit Cloud 연결
```
1. https://share.streamlit.io 접속
2. GitHub 연동
3. seogyeonga 저장소 선택
4. Main file: app.py
5. Deploy!
```

### Step 3: URL 공유
```
생성된 URL을 지인에게 공유하고 피드백 수집
```

---

## API 기술 문서

### 확인된 작동 API
```
사건내역: /pgj/pgj15A/selectAuctnCsSrchRslt.on
기일내역: /pgj/pgj15A/selectCsDtlDxdyDts.on
문건송달: /pgj/pgj15A/selectDlvrOfdocDtsDtl.on
```

### 요청 형식
```json
{
    "dma_srchCsDtlInf": {
        "cortOfcCd": "B000210",
        "csNo": "202201300003944"
    }
}
```

### 사건번호 변환
```
"2024타경12345" → "202401300012345"
(연도 + "0130" + 번호 6자리 제로패딩)
```

---

*Last updated: 2026-01-12 03:50*
