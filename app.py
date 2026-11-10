import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="어르신 효도 혈압수첩", page_icon="❤️", layout="centered")

# 카톡/모바일 접근용 타이틀
st.title("👵 어르신 효도 혈압수첩")
st.subheader("오늘 측정한 혈압을 기입해 주세요.")

# 입력 폼
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
        # 데이터프레임 생성
        new_entry = pd.DataFrame([{
            "날짜": str(date),
            "시점": timing,
            "최고혈압": sys,
            "최저혈압": dia,
            "맥박": pulse,
            "메모": memo
        }])
        
        # 로컬 CSV 저장 (한글 깨짐 방지 utf-8-sig)
        new_entry.to_csv("blood_pressure_records.csv", mode='a', header=False, index=False, encoding='utf-8-sig')
        st.success("✅ 안전하게 기록되었습니다!")

# 최근 기록 보여주기
st.divider()
st.write("📊 **누적 기록 목록**")
try:
    df = pd.read_csv("blood_pressure_records.csv", names=["날짜", "시점", "최고혈압", "최저혈압", "맥박", "메모"])
    st.dataframe(df.tail(10), use_container_width=True)
except FileNotFoundError:
    st.info("아직 저장된 기록이 없습니다.")