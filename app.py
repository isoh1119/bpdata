import streamlit as st
import pandas as pd
from datetime import datetime
import zoneinfo
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 페이지 설정
st.set_page_config(page_title="혈압수첩", page_icon="❤️", layout="centered")

# ★ [UI 추가] 모바일 최적화 및 큰 글씨/큰 버튼 CSS
st.markdown("""
<style>
/* 입력칸 글씨 크기 및 높이 대폭 키우기 */
div[data-testid="stNumberInput"] input {
    font-size: 38px !important;
    height: 85px !important;
    text-align: center !important;
    font-weight: bold !important;
    color: #111 !important;
}
/* ★ [신규] 안내 문구(placeholder)를 연한 회색으로, 크기는 적당히 크게 */
div[data-testid="stNumberInput"] input::placeholder {
    color: #d0d0d0 !important; /* 아주 연한 회색 */
    font-weight: normal !important;
    font-size: 28px !important;
}
/* 라벨(제목) 글씨 키우기 */
div[data-testid="stNumberInput"] label p,
div[data-testid="stDateInput"] label p,
div[data-testid="stTextInput"] label p {
    font-size: 24px !important;
    font-weight: bold !important;
    color: #333 !important;
}
/* 날짜 입력칸 크기 키우기 */
div[data-testid="stDateInput"] input {
    font-size: 28px !important;
    height: 75px !important;
    text-align: center !important;
    font-weight: bold !important;
}
/* 플러스/마이너스 버튼 숨기기 */
div[data-testid="stNumberInput"] button {
    display: none !important;
}
/* 측정 시점(라디오 버튼) 글씨 키우기 */
div[data-testid="stRadio"] label p {
    font-size: 24px !important;
    font-weight: bold !important;
}
/* 저장 버튼 크기 대폭 키우기 */
div[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    height: 90px !important;
    font-size: 30px !important;
    font-weight: 800 !important;
    border-radius: 15px !important;
    margin-top: 1rem;
}
/* 빈칸 입력 시 뜨는 경고/에러 메시지 글씨 크기 키우기 */
div[data-testid="stAlert"] p {
    font-size: 24px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# 2. 구글 시트 연결
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    raw = st.secrets["gcp_json"]
    creds_dict = json.loads(raw, strict=False) if isinstance(raw, str) else dict(raw)
    pk = creds_dict.get("private_key", "")
    if "\\n" in pk:
        creds_dict["private_key"] = pk.replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

# 3. 연결 + 명확한 오류 표시
try:
    with st.spinner("구글 시트와 안전하게 연결하는 중입니다..."):
        client = init_connection()
        sheet = client.open("어르신 효도 혈압수첩").sheet1
except Exception as e:
    st.error(f"❌ 구글 시트 연결 오류: {type(e).__name__}: {e}")
    st.info(
        "확인 순서:\n"
        "1. 구글 시트 제목이 정확히 '어르신 효도 혈압수첩'인지\n"
        "2. 서비스 계정 이메일에 시트 편집자 권한이 있는지\n"
        "3. GCP에서 새 키를 발급받았고 차단되지 않았는지\n"
        "4. Streamlit Secrets의 gcp_json이 '''...''' 로 감싸져 있는지"
    )
    st.stop()

# 4. 사용자 분기
user_type = st.query_params.get("user", "father")

if user_type == "mother":
    user_name = "어머니"
    display_name = "박금자 님"
    icon = "👩"
else:
    user_name = "아버지"
    display_name = "임병헌 님"
    icon = "👨"

# 앱 제목 및 인사말
app_title = f"{icon} 혈압수첩"
st.title(app_title)

st.markdown(
    f"""
    <div style='font-size: 1.4rem; line-height: 1.6; margin-bottom: 2rem; color: #333;'>
        안녕하세요, <b>{display_name}</b>!<br>
        오늘 측정한 혈압을 기입해 주세요. ❤️
    </div>
    """,
    unsafe_allow_html=True
)

# ★ 한국 시간(KST) 설정
kst = zoneinfo.ZoneInfo("Asia/Seoul")

# 5. 입력 폼
with st.form("blood_pressure_form"):
    date = st.date_input("측정 날짜", datetime.now(kst).date())
    
    timing = st.radio("측정 시점", ["☀️ 아침", "🌙 저녁"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        # placeholder="입력" 추가
        sbp = st.number_input("최고 혈압", min_value=50, max_value=230, value=None, placeholder="입력")
    with col2:
        # placeholder="입력" 추가
        dbp = st.number_input("최저 혈압", min_value=30, max_value=150, value=None, placeholder="입력")

    # placeholder="입력" 추가
    pulse = st.number_input("맥박수 (1분당)", min_value=30, max_value=200, value=None, placeholder="입력")
    memo = st.text_input("증상 / 특이사항 (선택)")

    submitted = st.form_submit_button("❤️ 기록 저장하기", use_container_width=True)

    if submitted:
        # 빈 칸으로 제출했을 때 경고
        if sbp is None or dbp is None or pulse is None:
            st.warning("⚠️ 혈압과 맥박 수치를 모두 입력해 주세요!")
        else:
            try:
                timestamp = f"{date} {datetime.now(kst).strftime('%H:%M:%S')}"
                row = [timestamp, user_name, timing, sbp, dbp, pulse, memo]
                sheet.append_row(row)
                st.success("✅ 구글 시트에 안전하게 기록되었습니다!")
                st.cache_resource.clear()
            except Exception as e:
                st.error(f"저장 중 오류: {type(e).__name__}: {e}")

# 6. 최근 기록
st.divider()
st.write(f"📊 **{display_name} 최근 누적 기록**")
try:
    data = sheet.get_all_values()
    if len(data) > 1:
        headers = [h.strip() for h in data[0]]
        df = pd.DataFrame(data[1:], columns=headers)
        if "구분(사용자)" not in df.columns:
            st.error(f"⚠️ 시트 1행 헤더를 확인하세요. 현재 헤더: {headers}")
        else:
            user_df = df[df["구분(사용자)"] == user_name]
            st.dataframe(user_df.tail(10), use_container_width=True)
    else:
        st.info("아직 저장된 기록이 없습니다.")
except Exception as e:
    st.error(f"데이터 로딩 오류: {type(e).__name__}: {e}")
