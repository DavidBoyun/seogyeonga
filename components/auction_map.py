"""
경매 물건 지도 컴포넌트 (카카오맵 - 스텁)
"""
import streamlit as st
from typing import List, Dict, Any


def render_auction_map(auctions: List[Dict[str, Any]], height: int = 500):
    """
    카카오맵에 경매 물건 표시

    현재: 스텁 (미구현)
    추후: 카카오맵 JavaScript API 연동

    Args:
        auctions: 경매 물건 목록 (lat, lng 필요)
        height: 지도 높이 (px)
    """

    # 카카오맵 API 키 체크
    from config import KAKAO_MAP_API_KEY

    if not KAKAO_MAP_API_KEY:
        # 스텁 UI
        st.markdown(f"""
        <div style="
            height: {height}px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
        ">
            <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
            <h3 style="margin: 0; font-size: 20px;">지도 뷰 (준비 중)</h3>
            <p style="margin: 8px 0 0 0; opacity: 0.8; font-size: 14px;">
                카카오맵 API 연동 예정
            </p>
            <p style="margin: 4px 0 0 0; opacity: 0.6; font-size: 12px;">
                현재 {len(auctions)}개 물건이 표시될 예정입니다
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 물건 위치 정보 표시 (스텁)
        if auctions:
            with st.expander("📍 물건 위치 정보 (미리보기)"):
                for auction in auctions[:5]:
                    if hasattr(auction, 'apt_name'):
                        name = auction.apt_name
                        lat = auction.lat
                        lng = auction.lng
                    else:
                        name = auction.get('apt_name', '아파트')
                        lat = auction.get('lat')
                        lng = auction.get('lng')

                    if lat and lng:
                        st.write(f"• {name}: ({lat:.4f}, {lng:.4f})")
                    else:
                        st.write(f"• {name}: 좌표 없음")

        return

    # TODO: 카카오맵 실제 구현
    # 카카오맵 JavaScript API를 사용하여 지도 표시
    #
    # kakao_map_html = f"""
    # <!DOCTYPE html>
    # <html>
    # <head>
    #     <script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_MAP_API_KEY}"></script>
    # </head>
    # <body>
    #     <div id="map" style="width:100%;height:{height}px;"></div>
    #     <script>
    #         var container = document.getElementById('map');
    #         var options = {{
    #             center: new kakao.maps.LatLng(37.5665, 126.9780),
    #             level: 9
    #         }};
    #         var map = new kakao.maps.Map(container, options);
    #
    #         // 마커 추가
    #         var positions = {json.dumps([{
    #             'lat': a.get('lat'),
    #             'lng': a.get('lng'),
    #             'name': a.get('apt_name')
    #         } for a in auctions if a.get('lat')])};
    #
    #         positions.forEach(function(pos) {{
    #             var marker = new kakao.maps.Marker({{
    #                 map: map,
    #                 position: new kakao.maps.LatLng(pos.lat, pos.lng),
    #                 title: pos.name
    #             }});
    #         }});
    #     </script>
    # </body>
    # </html>
    # """
    #
    # import streamlit.components.v1 as components
    # components.html(kakao_map_html, height=height)

    pass


def render_simple_map_placeholder(count: int = 0):
    """간단한 지도 플레이스홀더"""
    st.markdown(f"""
    <div style="
        height: 200px;
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: #64748b;
    ">
        <div style="font-size: 32px;">🗺️</div>
        <p style="margin: 8px 0 0 0;">지도 뷰 준비 중</p>
        {f'<p style="font-size: 12px; opacity: 0.7;">{count}개 물건</p>' if count else ''}
    </div>
    """, unsafe_allow_html=True)
