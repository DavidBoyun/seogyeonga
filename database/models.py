"""
서경아 데이터베이스 모델 (SQLAlchemy)
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Date, DateTime, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Auction(Base):
    """경매 물건"""
    __tablename__ = 'auctions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    court = Column(String(50), nullable=False)  # 관할법원
    case_no = Column(String(50), nullable=False, unique=True)  # 사건번호
    address = Column(String(200), nullable=False)  # 주소
    sido = Column(String(20))  # 시도
    gugun = Column(String(20))  # 구군
    dong = Column(String(30))  # 동
    apt_name = Column(String(100))  # 아파트명
    area = Column(Float)  # 면적 (m2)
    floor = Column(String(20))  # 층수
    appraisal_price = Column(Integer)  # 감정가
    min_price = Column(Integer)  # 최저가
    auction_date = Column(Date)  # 입찰일
    auction_count = Column(Integer, default=1)  # 경매차수
    status = Column(String(20), default='진행중')  # 상태
    risk_level = Column(String(10))  # 위험도 (안전/주의/위험)
    risk_reason = Column(String(200))  # 위험 사유
    has_tenant = Column(Boolean, default=False)  # 임차인 여부
    has_senior_rights = Column(Boolean, default=False)  # 선순위권리 여부
    remarks = Column(Text)  # 비고 (권리분석 등)
    lat = Column(Float)  # 위도
    lng = Column(Float)  # 경도
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 관계
    favorites = relationship("Favorite", back_populates="auction")


class User(Base):
    """사용자"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False, unique=True)
    nickname = Column(String(50))
    provider = Column(String(20), nullable=False)  # google / naver
    provider_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 관계
    favorites = relationship("Favorite", back_populates="user")


class Favorite(Base):
    """관심 물건"""
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    auction_id = Column(Integer, ForeignKey('auctions.id'), nullable=False)
    notify_d3 = Column(Boolean, default=True)  # D-3 알림
    notify_d1 = Column(Boolean, default=True)  # D-1 알림
    created_at = Column(DateTime, default=datetime.now)

    # 유니크 제약
    __table_args__ = (UniqueConstraint('user_id', 'auction_id'),)

    # 관계
    user = relationship("User", back_populates="favorites")
    auction = relationship("Auction", back_populates="favorites")


class News(Base):
    """뉴스"""
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text)
    source = Column(String(50))  # 출처
    url = Column(String(500), nullable=False, unique=True)
    published_at = Column(DateTime)
    category = Column(String(30))  # 경매/부동산/재개발 등
    region = Column(String(30))  # 관련 지역
    created_at = Column(DateTime, default=datetime.now)
