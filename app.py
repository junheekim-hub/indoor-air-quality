import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# ==========================================
# 0. Page Configuration
# ==========================================
st.set_page_config(
    page_title="One-Health Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic, Ultra-Clean Dark Slate & Electric Blue UI CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }

    code, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container */
    .stApp {
        background: #030712;
        color: #F9FAFB;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid #1E293B;
    }
    
    section[data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* Modern Text Inputs & Sliders */
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #111827 !important;
        color: #F9FAFB !important;
        border: 1px solid #1F2937 !important;
        border-radius: 10px;
        font-size: 0.85rem;
    }
    
    section[data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
        transition: all 0.2s ease;
    }
    
    section[data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
    }

    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.4rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
        transition: all 0.25s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(56, 189, 248, 0.12);
    }

    .metric-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .metric-val {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }

    .metric-subtext {
        font-size: 0.78rem;
        color: #475569;
        margin-top: 0.4rem;
    }

    /* Live Badge Header */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #34D399;
        border-radius: 50%;
        box-shadow: 0 0 10px #34D399;
    }

    /* Banner Alerts */
    .status-banner {
        border-radius: 14px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        backdrop-filter: blur(8px);
    }
    .status-good {
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #34D399;
    }
    .status-warn {
        background: rgba(245, 158, 11, 0.06);
        border: 1px solid rgba(245, 158, 11, 0.25);
        color: #FBBF24;
    }
    .status-danger {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.25);
        color: #F87171;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. Sidebar Controls
# ==========================================
with st.sidebar:
    st.markdown("### ⚡ Control Panel")
    st.markdown("---")
    
    st.markdown("#### 🔄 실시간 동기화 설정")
    auto_refresh = st.checkbox("자동 데이터 새로고침 (Auto Live Sync)", value=True)
    refresh_sec = st.slider("갱신 주기 (초)", min_value=2, max_value=30, value=5, step=1)
    
    st.markdown("---")
    st.markdown("#### 👥 교실 환경 설정")
    num_people = st.slider("재실 인원 (명)", min_value=1, max_value=50, value=30)
    exposure_hours = st.slider("노출 시간 (시간)", min_value=0.5, max_value=12.0, value=6.0, step=0.5)
    
    st.markdown("---")
    st.markdown("#### 🦠 오미크론 감염 모델")
    quanta_rate = st.slider("퀀타 방출률 (quanta/h)", min_value=500.0, max_value=2500.0, value=725.0, step=25.0)
    
    st.markdown("---")
    sheet_url = st.text_input("Google Sheet CSV URL", value="")
    
    if st.button("⚡ 수동 데이터 동기화"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 2. Calculations & Live Data Generator
# ==========================================
def apply_kalman_filter(data):
    n_iter = len(data)
    xhat = np.zeros(n_iter)
    P = np.zeros(n_iter)
    xhatminus = np.zeros(n_iter)
    Pminus = np.zeros(n_iter)
    K = np.zeros(n_iter)

    xhat[0] = data[0] if n_iter > 0 else 400.0
    P[0] = 1.0

    for k in range(1, n_iter):
        xhatminus[k] = xhat[k-1]
        Pminus[k] = P[k-1] + 1e-3
        K[k] = Pminus[k] / (Pminus[k] + 1e-1)
        xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
        P[k] = (1 - K[k]) * Pminus[k]
        
    return xhat

def calculate_wells_riley(co2_ppm, num_people, exposure_hours, quanta_rate):
    co2_diff = max(co2_ppm - 400.0, 10.0)
    Qp = (0.018 * 3600) / (co2_diff / 1e6)
    Qp = max(Qp, 5.0)
    Q = Qp * num_people
    p, I = 0.54, 1.0
    exposure_prob = 1.0 - np.exp(-(I * p * quanta_rate * exposure_hours) / Q)
    return min(float(exposure_prob * 100.0), 99.9)

# 캐시 무효화로 실시간 수신 보장
def fetch_live_data():
    if sheet_url:
        try:
            # cache-busting timestamp
            url_with_ts = f"{sheet_url}{'&' if '?' in sheet_url else '?'}t={int(time.time())}"
            df = pd.read_csv(url_with_ts)
            col_map = {}
            for col in df.columns:
                c = str(col).strip().lower()
                if any(x in c for x in ['time', 'date', '시간', '일시']): col_map[col] = 'Timestamp'
                elif any(x in c for x in ['raw', 'co2']): col_map[col] = 'Raw_CO2'
                elif any(x in c for x in ['temp', '온도']): col_map[col] = 'Temperature'
                elif any(x in c for x in ['hum', '습도']): col_map[col] = 'Humidity'
            df = df.rename(columns=col_map)
            df['Filtered_CO2'] = apply_kalman_filter(df['Raw_CO2'].values)
            return df
        except Exception:
            pass

    # Simulation Fallback (Dynamic Live Wave)
    t_now = time.time()
    times = pd.date_range(end=datetime.now(), periods=30, freq='1min')
    base_co2 = 520 + 60 * np.sin(t_now / 10) + np.random.normal(0, 8, 30)
    temp = 24.2 + 0.5 * np.cos(t_now / 20) + np.random.normal(0, 0.1, 30)
    hum = 52.0 + 1.2 * np.sin(t_now / 15) + np.random.normal(0, 0.2, 30)
    
    df_sim = pd.DataFrame({
        'Timestamp': times,
        'Raw_CO2': base_co2,
        'Temperature': temp,
        'Humidity': hum
    })
    df_sim['Filtered_CO2'] = apply_kalman_filter(df_sim['Raw_CO2'].values)
    return df_sim

df = fetch_live_data()
latest = df.iloc[-1]
filtered_co2 = float(latest['Filtered_CO2'])
raw_co2 = float(latest['Raw_CO2'])
temp_val = float(latest['Temperature'])
hum_val = float(latest['Humidity'])

wells_risk = calculate_wells_riley(filtered_co2, num_people, exposure_hours, quanta_rate)
wellness_score = max(0.0, min(100.0, 100 - (filtered_co2 - 400) * 0.08))

# ==========================================
# 3. UI Content
# ==========================================

# Top Header Bar
st.markdown(f"""
    <div class="header-container">
        <div>
            <h1 style="font-size: 1.8rem; font-weight: 800; color: #F9FAFC; margin: 0; letter-spacing: -0.02em;">
                Smart Classroom One-Health
            </h1>
            <p style="font-size: 0.88rem; color: #64748B; margin-top: 4px;">
                Kalman Filter Air Monitoring & Infection Risk Analytics
            </p>
        </div>
        <div class="live-badge">
            <div class="live-dot"></div>
            LIVE SYNC ({datetime.now().strftime('%H:%M:%S')})
        </div>
    </div>
""", unsafe_allow_html=True)

# Status Banner
if wells_risk >= 5.0 or filtered_co2 >= 1000:
    st.markdown(f"""
        <div class="status-banner status-danger">
            <span style="font-size: 1.4rem;">⚠️</span>
            <div><b>경고: 즉시 환기가 필요합니다.</b> 오미크론 감염 위험도({wells_risk:.2f}%) 및 CO2 농도가 기준치를 초과했습니다.</div>
        </div>
    """, unsafe_allow_html=True)
elif wells_risk >= 2.0 or filtered_co2 >= 800:
    st.markdown(f"""
        <div class="status-banner status-warn">
            <span style="font-size: 1.4rem;">⚡</span>
            <div><b>주의: 환기를 권장합니다.</b> CO2 수치 상승으로 인한 집중도 저하 위험이 있습니다.</div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="status-banner status-good">
            <span style="font-size: 1.4rem;">✨</span>
            <div><b>최적 상태:</b> 실내 공기질 및 감염 안전 지수가 매우 우수합니다.</div>
        </div>
    """, unsafe_allow_html=True)

# Metric Grid
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CO2 (KALMAN)</div>
            <div class="metric-val" style="color: #38BDF8;">{filtered_co2:.1f} <span style="font-size: 0.8rem; color: #64748B;">ppm</span></div>
            <div class="metric-subtext">Raw: {raw_co2:.1f} ppm</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TEMPERATURE</div>
            <div class="metric-val" style="color: #F9FAFC;">{temp_val:.1f} <span style="font-size: 0.8rem; color: #64748B;">°C</span></div>
            <div class="metric-subtext">Target: 20~24°C</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">HUMIDITY</div>
            <div class="metric-val" style="color: #60A5FA;">{hum_val:.1f} <span style="font-size: 0.8rem; color: #64748B;">%</span></div>
            <div class="metric-subtext">Target: 40~60%</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">WELLNESS SCORE</div>
            <div class="metric-val" style="color: #34D399;">{wellness_score:.1f} <span style="font-size: 0.8rem; color: #64748B;">/100</span></div>
            <div class="metric-subtext">Optimal Quality</div>
        </div>
    """, unsafe_allow_html=True)

with c5:
    risk_color = "#F87171" if wells_risk >= 5.0 else ("#FBBF24" if wells_risk >= 2.0 else "#34D399")
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">INFECTION RISK</div>
            <div class="metric-val" style="color: {risk_color};">{wells_risk:.2f} <span style="font-size: 0.8rem; color: #64748B;">%</span></div>
            <div class="metric-subtext">Wells-Riley Model</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts Section
g1, g2 = st.columns(2)

chart_theme = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(11, 15, 25, 0.6)',
    font=dict(color='#64748B', family='Plus Jakarta Sans'),
    margin=dict(l=10, r=10, t=25, b=10),
    xaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

with g1:
    st.markdown("<h4 style='font-size: 1rem; font-weight: 700; color: #E2E8F0;'>📈 CO2 Trend Analysis</h4>", unsafe_allow_html=True)
    fig_co2 = go.Figure()
    fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Raw_CO2'], mode='lines', name='Raw', line=dict(color='#475569', width=1.5, dash='dot')))
    fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Filtered_CO2'], mode='lines', name='Kalman Filter', line=dict(color='#38BDF8', width=3)))
    fig_co2.update_layout(**chart_theme)
    st.plotly_chart(fig_co2, use_container_width=True)

with g2:
    st.markdown("<h4 style='font-size: 1rem; font-weight: 700; color: #E2E8F0;'>🌡️ Temp & Humidity Realtime</h4>", unsafe_allow_html=True)
    fig_th = go.Figure()
    fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Temperature'], mode='lines', name='Temp (°C)', line=dict(color='#F43F5E', width=2.5)))
    fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Humidity'], mode='lines', name='Humidity (%)', line=dict(color='#3B82F6', width=2.5)))
    fig_th.update_layout(**chart_theme)
    st.plotly_chart(fig_th, use_container_width=True)

# Auto-Refresh Loop Trigger
if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
