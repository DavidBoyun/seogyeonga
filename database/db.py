"""
서경아 데이터베이스 연결 및 CRUD
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import os

from .models import Base, Auction, User, Favorite, News

# DB 경로


def auction_to_dict(auction: Auction) -> Dict[str, Any]:
    """Auction 객체를 딕셔너리로 변환"""
    return {
        'id': auction.id,
        'court': auction.court,
        'case_no': auction.case_no,
        'address': auction.address,
        'sido': auction.sido,
        'gugun': auction.gugun,
        'dong': auction.dong,
        'apt_name': auction.apt_name,
        'area': auction.area,
        'floor': auction.floor,
        'appraisal_price': auction.appraisal_price,
        'min_price': auction.min_price,
        'auction_date': str(auction.auction_date) if auction.auction_date else None,
        'auction_count': auction.auction_count,
        'status': auction.status,
        'risk_level': auction.risk_level,
        'risk_reason': auction.risk_reason,
        'has_tenant': auction.has_tenant,
        'has_senior_rights': auction.has_senior_rights,
        'remarks': auction.remarks,
        'lat': auction.lat,
        'lng': auction.lng,
    }


def user_to_dict(user: User) -> Dict[str, Any]:
    """User 객체를 딕셔너리로 변환"""
    return {
        'id': user.id,
        'email': user.email,
        'nickname': user.nickname,
        'provider': user.provider,
    }


DB_PATH = os.path.join(os.path.dirname(__file__), "seogyeonga.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """데이터베이스 초기화"""
    Base.metadata.create_all(engine)
    print(f"[OK] DB 초기화 완료: {DB_PATH}")


@contextmanager
def get_session():
    """세션 컨텍스트 매니저"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ========== 경매 물건 CRUD ==========

def get_auctions(
    gugun: str = None,
    dong: str = None,
    min_price: int = None,
    max_price: int = None,
    auction_counts: List[int] = None,
    risk_levels: List[str] = None,
    days_until: int = None,
    order_by: str = "auction_date"
) -> List[Dict[str, Any]]:
    """경매 물건 조회 (필터링) - 딕셔너리 리스트 반환"""
    with get_session() as session:
        query = session.query(Auction).filter(Auction.status == '진행중')

        if gugun:
            query = query.filter(Auction.gugun == gugun)

        if dong:
            query = query.filter(Auction.dong == dong)

        if min_price:
            query = query.filter(Auction.min_price >= min_price)

        if max_price:
            query = query.filter(Auction.min_price <= max_price)

        if auction_counts:
            query = query.filter(Auction.auction_count.in_(auction_counts))

        if risk_levels:
            query = query.filter(Auction.risk_level.in_(risk_levels))

        if days_until:
            deadline = date.today() + timedelta(days=days_until)
            query = query.filter(Auction.auction_date <= deadline)
            query = query.filter(Auction.auction_date >= date.today())

        # 정렬
        if order_by == "auction_date":
            query = query.order_by(Auction.auction_date.asc())
        elif order_by == "price_low":
            query = query.order_by(Auction.min_price.asc())
        elif order_by == "price_high":
            query = query.order_by(Auction.min_price.desc())

        results = query.all()
        return [auction_to_dict(a) for a in results]


def get_auction_by_id(auction_id: int) -> Optional[Auction]:
    """ID로 경매 물건 조회"""
    with get_session() as session:
        return session.query(Auction).filter(Auction.id == auction_id).first()


def get_auction_by_case_no(case_no: str) -> Optional[Auction]:
    """사건번호로 경매 물건 조회"""
    with get_session() as session:
        return session.query(Auction).filter(Auction.case_no == case_no).first()


def upsert_auction(data: Dict[str, Any]) -> Auction:
    """경매 물건 추가/업데이트"""
    with get_session() as session:
        existing = session.query(Auction).filter(
            Auction.case_no == data['case_no']
        ).first()

        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            return existing
        else:
            auction = Auction(**data)
            session.add(auction)
            session.flush()
            return auction


def get_gugun_list() -> List[str]:
    """저장된 구 목록"""
    with get_session() as session:
        results = session.query(Auction.gugun).distinct().filter(
            Auction.gugun.isnot(None)
        ).all()
        return sorted([r[0] for r in results if r[0]])


def get_dong_list(gugun: str) -> List[str]:
    """특정 구의 동 목록"""
    with get_session() as session:
        results = session.query(Auction.dong).distinct().filter(
            Auction.gugun == gugun,
            Auction.dong.isnot(None)
        ).all()
        return sorted([r[0] for r in results if r[0]])


def get_auction_stats() -> Dict[str, int]:
    """통계"""
    with get_session() as session:
        total = session.query(Auction).filter(Auction.status == '진행중').count()
        safe = session.query(Auction).filter(
            Auction.status == '진행중',
            Auction.risk_level == '안전'
        ).count()
        return {"total": total, "safe": safe}


# ========== 사용자 CRUD ==========

def get_or_create_user(email: str, provider: str, provider_id: str, nickname: str = None) -> User:
    """사용자 조회 또는 생성"""
    with get_session() as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                provider=provider,
                provider_id=provider_id,
                nickname=nickname
            )
            session.add(user)
            session.flush()
        return user


def get_user_by_email(email: str) -> Optional[User]:
    """이메일로 사용자 조회"""
    with get_session() as session:
        return session.query(User).filter(User.email == email).first()


# ========== 관심 물건 CRUD ==========

def add_favorite(user_id: int, auction_id: int) -> bool:
    """관심 물건 추가"""
    with get_session() as session:
        existing = session.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.auction_id == auction_id
        ).first()

        if not existing:
            fav = Favorite(user_id=user_id, auction_id=auction_id)
            session.add(fav)
            return True
        return False


def remove_favorite(user_id: int, auction_id: int) -> bool:
    """관심 물건 제거"""
    with get_session() as session:
        fav = session.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.auction_id == auction_id
        ).first()

        if fav:
            session.delete(fav)
            return True
        return False


def is_favorite(user_id: int, auction_id: int) -> bool:
    """관심 물건 여부"""
    with get_session() as session:
        return session.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.auction_id == auction_id
        ).first() is not None


def get_user_favorites(user_id: int) -> List[Dict[str, Any]]:
    """사용자의 관심 물건 목록 - 딕셔너리 리스트 반환"""
    with get_session() as session:
        results = session.query(Auction).join(Favorite).filter(
            Favorite.user_id == user_id
        ).all()
        return [auction_to_dict(a) for a in results]


# ========== 뉴스 CRUD ==========

def get_news(category: str = None, region: str = None, limit: int = 20) -> List[News]:
    """뉴스 조회"""
    with get_session() as session:
        query = session.query(News)

        if category:
            query = query.filter(News.category == category)

        if region:
            query = query.filter(News.region == region)

        return query.order_by(News.published_at.desc()).limit(limit).all()


def add_news(data: Dict[str, Any]) -> Optional[News]:
    """뉴스 추가 (중복 체크)"""
    with get_session() as session:
        existing = session.query(News).filter(News.url == data['url']).first()
        if not existing:
            news = News(**data)
            session.add(news)
            session.flush()
            return news
        return None


# 초기화
if __name__ == "__main__":
    init_db()
