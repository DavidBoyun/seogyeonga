# 서경아 (Seogyeonga)

서울 아파트 경매 AI 분석 서비스

## 기능

- 경매 물건 목록 조회 (샘플 데이터)
- **사건번호 조회** - 실제 법원경매 API 연동
- AI 권리분석
- PDF 리포트 생성
- 뉴스/유튜브 정보

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud 배포

1. GitHub에 이 폴더 푸시
2. [Streamlit Cloud](https://share.streamlit.io) 연결
3. Main file: `app.py` 선택
4. Secrets 설정 (선택)

## 기술 스택

- Streamlit
- Python 3.9+
- SQLAlchemy
- Requests
- Plotly

## 라이선스

MIT

---
서경아 | 서울 아파트 경매 AI 분석 서비스
