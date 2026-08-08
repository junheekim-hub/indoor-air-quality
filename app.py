import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import io

st.set_page_config(page_title="실시간 공기질 대시보드", page_icon="🌬️", layout="wide")

# ⭕ 본인의 실제 스프레드시트 ID
SHEET_ID = "1UZXPr9R4emD-RqnzBMYffm2c42qzJQKfIwz6Givxflc"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(CSV_URL, timeout=5)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = df.columns.str.strip()
        
        # 한글 날짜/시간 포맷("2026. 8. 9 오전 3:49:09") 및 다양한 형식을 안전하게 변환
        # 1) '오전'/'오후'를 AM/PM으로 변경 후 변환 시도
        time_str = df['Timestamp'].astype(str).str.replace('오전', 'AM').str.replace('오후', 'PM')
        df['Timestamp'] = pd.to_datetime(time_str, format='mixed', errors='coerce')
        
        # 변환 불가능한 값(NaN) 제거
        df = df.dropna(subset=['Timestamp'])
        return df
    except Exception as e:
        st.error(f"데이터 로드 상세 오류: {e}")
        return pd.DataFrame()

def calculate_wellness_index(co2, temp, humi):
    co2_score = max(0, min(100, 100 - (co2 - 400) * (100 / 1600)))
    temp_score = max(0, min(100, 100 - abs(temp - 23) * 8))
    humi_score = max(0, min(100, 100 - abs(humi - 50) * 2))
    return round((co2_score * 0.5) + (temp_score * 0.25) + (humi_score * 0.25), 1)

def calculate_wells_riley(co2, num_people=10, duration_hours=2.0):
    outdoor_co2 = 400.0
    co2_diff = max(co2 - outdoor_co2, 50.0)
    estimated_ventilation_m3h = (num_people * 0.005 * 3600 * 1000) / co2_diff
    
    quanta_rate = 14.0
    breathing_rate = 0.48
    exponent = -1.0 * (1 * quanta_rate * breathing_rate * duration_hours) / estimated_ventilation_m3h
    prob = (1.0 - np.exp(exponent)) * 100.0
    return round(prob, 2)

st.title("🌬️ 실시간 실내 공기질, 웰니스 & Wells-Riley 대시보드")

if st.button("🔄 최신 데이터 불러오기"):
    st.cache_data.clear()

df = load_data()

if not df.empty:
    latest = df.iloc[-1]
    filtered_co2 = float(latest['Filtered_CO2'])
    raw_co2 = float(latest['Raw_CO2'])
    temp = float(latest['Temperature'])
    humi = float(latest['Humidity'])
    
    wellness_score = calculate_wellness_index(filtered_co2, temp, humi)
    infection_prob = calculate_wells_riley(filtered_co2)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("CO2 (Kalman)", f"{filtered_co2:.1f} ppm", f"Raw: {raw_co2} ppm")
    col2.metric("온도", f"{temp:.1f} °C")
    col3.metric("습도", f"{humi:.1f} %")
    col4.metric("웰니스 점수", f"{wellness_score}점")
    col5.metric("Wells-Riley 감염률", f"{infection_prob}%")

    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("CO2 농도 추이")
        fig_co2 = go.Figure()
        fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Raw_CO2'], name="Raw", line=dict(color='gray', dash='dash')))
        fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Filtered_CO2'], name="Filtered", line=dict(color='green')))
        st.plotly_chart(fig_co2, use_container_width=True)

    with col_right:
        st.subheader("온·습도 추이")
        fig_th = go.Figure()
        fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Temperature'], name="온도", line=dict(color='red')))
        fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Humidity'], name="습도", line=dict(color='blue')))
        st.plotly_chart(fig_th, use_container_width=True)
else:
    st.error("불러올 수 있는 유효한 데이터가 없습니다. 시트 내용을 확인하세요.")
