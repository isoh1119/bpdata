import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 페이지 설정 (반드시 최상단)
st.set_page_config(page_title="어르신 효도 혈압수첩", page_icon="❤️", layout="centered")

# 2. 구글 시트 연결
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    raw = st.secrets["gcp_json"]
    # TOML이 dict로 파싱한 경우와 str인 경우 모두 대응
    creds_dict = json.loads(raw) if isinstance(raw, str) else dict(raw)

    # 혹시 남아있을 literal "\\n" 안전 보정 (json.loads가 이미 처리했으면 no-op)
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

# 4. 사용자 분기 (화면 표시용 이름과 시트 저장용 이름 분리)
user_type = st.query_params.get("user", "father")

if user_type == "mother":
    user_name = "어머니"          # 구글 시트에 저장될 값 (기존 데이터 유지용)
    display_name = "박금자 님"     # 화면에 표시될 이름
    icon = "👩"
else:
    user_name = "아버지"          # 구글 시트에 저장될 값 (기존 데이터 유지용)
    display_name = "임병헌 님"     # 화면에 표시될 이름
    icon = "👨"

# 앱 제목 변경 (어르신 효도 삭제)
app_title = f"{icon} 혈압수첩"

st.title(app_title)

# 모바일 화면에 맞게 폰트 크기와 줄바꿈을 조정한 인사말
st.markdown(
    f"""
    <div style='font-size: 1.2rem; line-height: 1.6; margin-bottom: 2rem; color: #333;'>
        안녕하세요, <b>{display_name}</b>!<br>
        오늘 측정한 혈압을 기입해 주세요. ❤️
    </div>
    """,
    unsafe_allow_html=True
)

# 5. 입력 폼
with st.form("blood_pressure_form"):
    date = st.date_input("측정 날짜", datetime.now().date())
    timing = st.radio("측정 시점", ["☀️ 아침", "🌙 저녁"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        sbp = st.number_input("최고 혈압 (수축기)", 50, 230, 120)
    with col2:
        dbp = st.number_input("최저 혈압 (이완기)", 30, 150, 80)

    pulse = st.number_input("맥박수 (1분당)", 30, 200, 72)
    memo = st.text_input("증상 / 특이사항 (선택)")

    submitted = st.form_submit_button("❤️ 기록 저장하기", use_container_width=True)

    if submitted:
        try:
            # ★ 사용자가 선택한 날짜 + 현재 시각
            timestamp = f"{date} {datetime.now().strftime('%H:%M:%S')}"
            row = [timestamp, user_name, timing, sbp, dbp, pulse, memo]
            sheet.append_row(row)
            st.success("✅ 구글 시트에 안전하게 기록되었습니다!")
            st.cache_resource.clear()   # 다음 렌더에서 최신 데이터 다시 읽기
        except Exception as e:
            st.error(f"저장 중 오류: {type(e).__name__}: {e}")

# 6. 최근 기록
st.divider()
st.write(f"📊 **{display_name} 최근 누적 기록**")  # 여기를 display_name 으로 변경
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
