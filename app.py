import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 구글 시트 연결 설정 (개인키 포맷 에러 방지 처리 포함)
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Secrets의 딕셔너리 정보 가져오기
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # private_key의 줄바꿈 문자 및 불필요한 공백/캐리지 리턴(\r) 완벽 정돈
    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        pk = pk.replace("\\n", "\n").replace("\r\n", "\n").strip()
        creds_dict["private_key"] = pk

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

client = init_connection()
sheet = client.open("어르신 효도 혈압수첩").sheet1

# URL 파라미터로 아버님/어머님 구분
query_params = st.query_params
user_type = query_params.get("user", "father")

if user_type == "mother":
    app_title = "👩 어머니 효도 혈압수첩"
    user_name = "어머니"
else:
    app_title = "👨 아버지 효도 혈압수첩"
    user_name = "아버지"

st.set_page_config(page_title=app_title, page_icon="❤️", layout="centered")

st.title(app_title)
st.subheader(f"안녕하세요! {user_name} 오늘 측정한 혈압을 기입해 주세요.")

with st.form("blood_pressure_form"):
    date = st.date_input("측정 날짜", datetime.now())
    timing = st.radio("측정 시점", ["☀️ 아침", "🌙 저녁"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        sys = st.number_input("최고 혈압 (수축기)", 50, 230, 120)
    with col2:
        dia = st.number_input("최저 혈압 (이완기)", 30, 150, 80)
        
    pulse = st.number_input("맥박수 (1분당)", 30, 200, 72)
    memo = st.text_input("증상 / 특이사항 (선택)")
    
    submitted = st.form_submit_button("❤️ 기록 저장하기", use_container_width=True)
    
    if submitted:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_time, user_name, timing, sys, dia, pulse, memo]
        sheet.append_row(row)
        st.success("✅ 구글 시트에 안전하게 기록되었습니다!")

# 최근 기록 보여주기
st.divider()
st.write(f"📊 **{user_name} 최근 누적 기록**")
try:
    data = sheet.get_all_values()
    if len(data) > 1:
        df = pd.DataFrame(data[1:], columns=data[0])
        user_df = df[df["구분(사용자)"] == user_name]
        st.dataframe(user_df.tail(10), use_container_width=True)
    else:
        st.info("아직 저장된 기록이 없습니다.")
except Exception as e:
    st.info("데이터를 불러오는 중입니다...")
