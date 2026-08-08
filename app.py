import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests
import re

# ==========================================
# 0. Page Configuration
# ==========================================
st.set_page_config(
    page_title="Smart Classroom One-Health Dashboard",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern, Clean & Sleek UI
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Header Styling */
    .header-title {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .header-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #38BDF8;
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 0.3rem;
    }
    
    /* Nudge Banner */
    .nudge-container {
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.2rem;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
    }
    .nudge-good {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%);
        border: 1px solid #10B981;
        color: #34D399;
    }
    .nudge-moderate {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.25) 100%);
        border: 1px solid #F59E0B;
        color: #FBBF24;
    }
    .nudge-warning {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.25) 100%);
        border: 1px solid #EF4444;
        color: #F87171;
    }
    .nudge-icon {
        font-size: 2.8rem;
        line-height: 1;
    }
    .nudge-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .nudge-desc {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. Sidebar Controls (Occupancy & Config)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/hospital.png", width=64)
    st.title("⚙️ 설정 & 파라미터")
    st.markdown("---")
    
    st.subheader("👥 교실 점유 환경")
    # Point 2: Occupancy default updated to 30.0 with user control
    num_people = st.slider("재실 인원 (명)", min_value=1, max_value=50, value=30, step=1,
                           help="제안서 수치 기준: 학급당 약 30명")
    
    exposure_hours = st.slider("노출 시간 (시간)", min_value=0.5, max_value=12.0, value=6.0, step=0.5,
                             help="일일 교실 상주 시간 (기본 6시간)")
    
    st.markdown("---")
    st.subheader("🦠 오미크론 변이 설정")
    # Point 1: Quanta rate slider with Omicron range (725 ~ 2345)
    quanta_rate = st.slider("퀀타 방출률 (quanta/h)", min_value=500.0, max_value=2500.0, value=725.0, step=25.0,
                            help="오미크론 변이 퀀타 방출률: 725 ~ 2,345 quanta/h")
    
    st.markdown("---")
    sheet_url = st.text_input("Google Sheet CSV/Pub URL", 
                              value="", 
                              help="구글 시트 게시 URL이 설정되지 않은 경우 샘플 데이터를 시뮬레이션합니다.")
    
    if st.button("🔄 데이터 수동 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 2. Data Processing Core (Safeguarded)
# ==========================================
# Kalman Filter Implementation
def apply_kalman_filter(data, process_variance=1e-3, measurement_variance=1e-1):
    n_iter = len(data)
    sz = (n_iter,)
    xhat = np.zeros(sz)
    P = np.zeros(sz)
    xhatminus = np.zeros(sz)
    Pminus = np.zeros(sz)
    K = np.zeros(sz)

    xhat[0] = data[0] if n_iter > 0 else 400.0
    P[0] = 1.0

    for k in range(1, n_iter):
        xhatminus[k] = xhat[k-1]
        Pminus[k] = P[k-1] + process_variance
        K[k] = Pminus[k] / (Pminus[k] + measurement_variance)
        xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
        P[k] = (1 - K[k]) * Pminus[k]
        
    return xhat

# Wells-Riley & Wellness Calculations
def calculate_wells_riley(co2_ppm, num_people=30.0, exposure_hours=6.0, quanta_rate=725.0):
    # Air exchange rate estimation based on CO2 level
    # Base background CO2 ~ 400 ppm
    co2_diff = max(co2_ppm - 400.0, 10.0)
    # Estimated ventilation rate per person (m3/h)
    Qp = (0.018 * 3600) / (co2_diff / 1e6)  # Breathing rate ~0.018 m3/h
    Qp = max(Qp, 5.0) # floor at minimum ventilation
    
    # Total room ventilation rate Q (m3/h)
    Q = Qp * num_people
    
    # Wells-Riley Equation: P = 1 - exp(-I * p * q * t / Q)
    # I = 1 (infected person), p = 0.54 m3/h (pulmonary ventilation rate)
    p = 0.54
    I = 1.0
    exposure_prob = 1.0 - np.exp(-(I * p * quanta_rate * exposure_hours) / Q)
    risk_pct = float(exposure_prob * 100.0)
    return min(risk_pct, 99.9)

def calculate_wellness_score(co2, temp, humidity):
    # Score out of 100
    # CO2 penalty
    co2_score = max(0, 100 - (co2 - 400) * 0.08)
    # Temp penalty (ideal 20-24C)
    temp_score = max(0, 100 - abs(temp - 22.0) * 5)
    # Humidity penalty (ideal 40-60%)
    hum_score = max(0, 100 - abs(humidity - 50.0) * 1.5)
    
    total = co2_score * 0.5 + temp_score * 0.25 + hum_score * 0.25
    return max(0.0, min(100.0, total))

# Load Data Robustly (Point 4)
@st.cache_data(ttl=10)
def load_data():
    # Simulated realistic baseline data if no URL or error
    times = pd.date_range(end=datetime.now(), periods=40, freq='2min')
    np.random.seed(42)
    raw_co2 = 550 + 80 * np.sin(np.linspace(0, 6, 40)) + np.random.normal(0, 15, 40)
    temp = 26.8 + np.random.normal(0, 0.2, 40)
    hum = 84.4 + np.random.normal(0, 0.3, 40)
    
    df_sim = pd.DataFrame({
        'Timestamp': times,
        'Raw_CO2': raw_co2,
        'Temperature': temp,
        'Humidity': hum
    })
    
    if not sheet_url:
        df_sim['Filtered_CO2'] = apply_kalman_filter(df_sim['Raw_CO2'].values)
        return df_sim
        
    try:
        # Fetching Google Sheet CSV
        df = pd.read_csv(sheet_url)
        
        # Robust Column Mapping (Flexible matching)
        col_map = {}
        for col in df.columns:
            c_clean = str(col).strip().lower()
            if 'time' in c_clean or 'date' in c_clean or '일시' in c_clean or '시간' in c_clean:
                col_map[col] = 'Timestamp'
            elif 'raw' in c_clean or 'co2_raw' in c_clean or 'co2' in c_clean:
                if 'Raw_CO2' not in col_map.values():
                    col_map[col] = 'Raw_CO2'
            elif 'filter' in c_clean or 'kalman' in c_clean:
                col_map[col] = 'Filtered_CO2'
            elif 'temp' in c_clean or '온도' in c_clean:
                col_map[col] = 'Temperature'
            elif 'hum' in c_clean or '습도' in c_clean:
                col_map[col] = 'Humidity'
                
        df = df.rename(columns=col_map)
        
        # Korean Date String Parsing
        if 'Timestamp' in df.columns:
            def parse_korean_date(val):
                try:
                    val_str = str(val).strip()
                    val_str = val_str.replace('오전', 'AM').replace('오후', 'PM')
                    return pd.to_datetime(val_str)
                except:
                    return pd.NaT
            df['Timestamp'] = df['Timestamp'].apply(parse_korean_date)
            df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
            
        # Ensure CO2 columns exist
        if 'Raw_CO2' not in df.columns and 'Filtered_CO2' in df.columns:
            df['Raw_CO2'] = df['Filtered_CO2']
        elif 'Raw_CO2' in df.columns and 'Filtered_CO2' not in df.columns:
            df['Filtered_CO2'] = apply_kalman_filter(df['Raw_CO2'].values)
            
        if 'Temperature' not in df.columns: df['Temperature'] = 26.8
        if 'Humidity' not in df.columns: df['Humidity'] = 84.4
        
        return df if not df.empty else df_sim
    except Exception as e:
        return df_sim

df = load_data()

# Calculate latest values safely
try:
    latest = df.iloc[-1]
    raw_co2_val = float(latest.get('Raw_CO2', 600.0))
    filtered_co2_val = float(latest.get('Filtered_CO2', raw_co2_val))
    temp_val = float(latest.get('Temperature', 26.8))
    hum_val = float(latest.get('Humidity', 84.4))
except Exception:
    raw_co2_val, filtered_co2_val, temp_val, hum_val = 597.0, 608.1, 26.8, 84.4

# Calculate Wells-Riley & Wellness
wells_riley_risk = calculate_wells_riley(filtered_co2_val, num_people, exposure_hours, quanta_rate)
wellness_score = calculate_wellness_score(filtered_co2_val, temp_val, hum_val)

# ==========================================
# 3. Main Dashboard UI
# ==========================================

# Title Banner
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1rem;">
        <div>
            <div class="header-title">🏫 Smart Classroom One-Health Platform</div>
            <div class="header-subtitle">Data-to-Safety Pipeline | 실시간 공기질, 칼만 필터 및 Wells-Riley 오미크론 감염 위험도 대시보드</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Point 3: Nudge Banner Implementation (Behavioral Intervention UI)
if wells_riley_risk >= 5.0 or filtered_co2_val >= 1000:
    nudge_class = "nudge-warning"
    nudge_icon = "⚠️"
    nudge_title = "Warning: Open Windows Immediately!"
    nudge_desc = f"오미크론 감염 위험도({wells_riley_risk:.2f}%) 및 CO2 농도({filtered_co2_val:.1f} ppm)가 높습니다. 지금 창문을 열어 환기하세요!"
elif wells_riley_risk >= 2.0 or filtered_co2_val >= 800:
    nudge_class = "nudge-moderate"
    nudge_icon = "😐"
    nudge_title = "Caution: Ventilation Recommended"
    nudge_desc = f"공기 상태가 다소 답답합니다(감염률 {wells_riley_risk:.2f}%). 쉬는 시간에 교실 창문을 열어주세요."
else:
    nudge_class = "nudge-good"
    nudge_icon = "😊"
    nudge_title = "Optimal Air Quality & Safe Environment"
    nudge_desc = f"쾌적하고 안전한 학습 환경입니다 (감염 위험도 {wells_riley_risk:.2f}%). 정기적인 환기를 유지해주세요."

st.markdown(f"""
    <div class="nudge-container {nudge_class}">
        <div class="nudge-icon">{nudge_icon}</div>
        <div>
            <div class="nudge-title">{nudge_title}</div>
            <div class="nudge-desc">{nudge_desc}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Metric Cards Row
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">CO2 (Kalman Filter)</div>
            <div class="metric-value" style="color: #38BDF8;">{filtered_co2_val:.1f} <span style="font-size: 1rem;">ppm</span></div>
            <div class="metric-sub">Raw: {raw_co2_val:.1f} ppm</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">온도 (Temperature)</div>
            <div class="metric-value">{temp_val:.1f} <span style="font-size: 1rem;">°C</span></div>
            <div class="metric-sub">적정: 20 ~ 24 °C</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">습도 (Humidity)</div>
            <div class="metric-value">{hum_val:.1f} <span style="font-size: 1rem;">%</span></div>
            <div class="metric-sub">적정: 40 ~ 60 %</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    # Color condition for Wellness
    w_color = "#34D399" if wellness_score >= 70 else ("#FBBF24" if wellness_score >= 50 else "#F87171")
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">웰니스 점수</div>
            <div class="metric-value" style="color: {w_color};">{wellness_score:.1f} <span style="font-size: 1rem;">점</span></div>
            <div class="metric-sub">종합 공기질 지표</div>
        </div>
    """, unsafe_allow_html=True)

with c5:
    # Color condition for Wells-Riley
    r_color = "#F87171" if wells_riley_risk >= 5.0 else ("#FBBF24" if wells_riley_risk >= 2.0 else "#34D399")
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Wells-Riley 감염률</div>
            <div class="metric-value" style="color: {r_color};">{wells_riley_risk:.2f} <span style="font-size: 1rem;">%</span></div>
            <div class="metric-sub">오미크론 ({num_people}명 기준)</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. Interactive Time-Series Charts
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 CO2 농도 추이 (Raw vs. Kalman Filter)")
    fig_co2 = go.Figure()
    
    # Raw CO2 (Dashed Gray line)
    fig_co2.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Raw_CO2'],
        mode='lines', name='Raw (노이즈 포함)',
        line=dict(color='#94A3B8', width=1.5, dash='dash')
    ))
    
    # Filtered CO2 (Vibrant Green/Blue line)
    fig_co2.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Filtered_CO2'],
        mode='lines', name='Filtered (칼만 필터)',
        line=dict(color='#10B981', width=3)
    ))
    
    fig_co2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.5)',
        font=dict(color='#94A3B8'),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor='#334155'),
        yaxis=dict(showgrid=True, gridcolor='#334155', title='CO2 (ppm)')
    )
    st.plotly_chart(fig_co2, use_container_width=True)

with col_right:
    st.subheader("🌡️ 온·습도 추이 (Temperature & Humidity)")
    fig_th = go.Figure()
    
    # Temp
    fig_th.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Temperature'],
        mode='lines', name='온도 (°C)',
        line=dict(color='#EF4444', width=2.5)
    ))
    
    # Humidity
    fig_th.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Humidity'],
        mode='lines', name='습도 (%)',
        line=dict(color='#3B82F6', width=2.5)
    ))
    
    fig_th.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.5)',
        font=dict(color='#94A3B8'),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor='#334155'),
        yaxis=dict(showgrid=True, gridcolor='#334155')
    )
    st.plotly_chart(fig_th, use_container_width=True)
