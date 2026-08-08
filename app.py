import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# ==========================================
# 0. Page Configuration & Custom CSS (Mobile Optimized)
# ==========================================
st.set_page_config(
    page_title="One-Health Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }

    .stApp {
        background: #030712;
        color: #F9FAFB;
    }

    section[data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid #1E293B;
    }
    
    section[data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }

    /* Metric Cards - Mobile Friendly Grid */
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .metric-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.3rem;
    }

    .metric-title {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #64748B;
        text-transform: uppercase;
    }

    .status-tag {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .tag-good { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .tag-moderate { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .tag-danger { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }

    .metric-val {
        font-size: 1.6rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .metric-subtext {
        font-size: 0.72rem;
        color: #475569;
        margin-top: 0.3rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .live-dot {
        width: 6px;
        height: 6px;
        background-color: #34D399;
        border-radius: 50%;
        box-shadow: 0 0 8px #34D399;
    }

    .status-banner {
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        font-size: 0.85rem;
    }
    .status-good { background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); color: #34D399; }
    .status-warn { background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.25); color: #FBBF24; }
    .status-danger { background: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.25); color: #F87171; }

    [data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

try:
    with open(__file__, "r", encoding="utf-8") as f:
        current_code = f.read()
except Exception:
    current_code = "# app.py source code"

# ==========================================
# 1. Sidebar Controls
# ==========================================
with st.sidebar:
    st.markdown("### ⚡ Control Panel")
    st.markdown("---")
    
    auto_refresh = st.checkbox("자동 새로고침", value=True)
    refresh_sec = st.slider("갱신 주기 (초)", min_value=2, max_value=30, value=5)
    
    st.markdown("---")
    num_people = st.slider("재실 인원 (명)", min_value=1, max_value=50, value=30)
    exposure_hours = st.slider("노출 시간 (시간)", min_value=0.5, max_value=12.0, value=6.0, step=0.5)
    quanta_rate = st.slider("퀀타 방출률", min_value=500.0, max_value=2500.0, value=725.0, step=25.0)
    
    sheet_url = st.text_input("Google Sheet CSV URL", value="")
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("동기화"):
            st.cache_data.clear()
            st.rerun()
    with col_sb2:
        st.download_button(
            label="소스 받기",
            data=current_code,
            file_name="app.py",
            mime="text/x-python"
        )

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
    Qp = max((0.018 * 3600) / (co2_diff / 1e6), 5.0)
    Q = Qp * num_people
    exposure_prob = 1.0 - np.exp(-(1.0 * 0.54 * quanta_rate * exposure_hours) / Q)
    return min(float(exposure_prob * 100.0), 99.9)

def fetch_live_data():
    if sheet_url:
        try:
            url_with_ts = f"{sheet_url}{'&' if '?' in sheet_url else '?'}t={int(time.time())}"
            df = pd.read_csv(url_with_ts)
            col_map = {}
            for col in df.columns:
                c = str(col).strip().lower()
                if any(x in c for x in ['time', 'date', '시간']): col_map[col] = 'Timestamp'
                elif any(x in c for x in ['raw', 'co2']): col_map[col] = 'Raw_CO2'
                elif any(x in c for x in ['temp', '온도']): col_map[col] = 'Temperature'
                elif any(x in c for x in ['hum', '습도']): col_map[col] = 'Humidity'
            df = df.rename(columns=col_map)
            df['Filtered_CO2'] = apply_kalman_filter(df['Raw_CO2'].values)
            return df
        except Exception:
            pass

    t_now = time.time()
    times = pd.date_range(end=datetime.now(), periods=30, freq='1min')
    base_co2 = 475 + 15 * np.sin(t_now / 10) + np.random.normal(0, 5, 30)
    temp = 24.4 + 0.3 * np.cos(t_now / 20) + np.random.normal(0, 0.1, 30)
    hum = 52.5 + 0.8 * np.sin(t_now / 15) + np.random.normal(0, 0.2, 30)
    
    df_sim = pd.DataFrame({'Timestamp': times, 'Raw_CO2': base_co2, 'Temperature': temp, 'Humidity': hum})
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
# 3. Status Helpers
# ==========================================
def get_co2_status(val):
    if val < 800: return ("좋음", "tag-good", "#38BDF8")
    elif val < 1000: return ("보통", "tag-moderate", "#FBBF24")
    else: return ("나쁨", "tag-danger", "#F87171")

def get_temp_status(val):
    if 20.0 <= val <= 24.0: return ("적정", "tag-good", "#F9FAFC")
    elif 18.0 <= val < 20.0 or 24.0 < val <= 26.0: return ("보통", "tag-moderate", "#FBBF24")
    else: return ("부적절", "tag-danger", "#F87171")

def get_hum_status(val):
    if 40.0 <= val <= 60.0: return ("적정", "tag-good", "#60A5FA")
    elif 30.0 <= val < 40.0 or 60.0 < val <= 70.0: return ("보통", "tag-moderate", "#FBBF24")
    else: return ("부적절", "tag-danger", "#F87171")

def get_wellness_status(val):
    if val >= 80: return ("우수", "tag-good", "#34D399")
    elif val >= 60: return ("양호", "tag-moderate", "#FBBF24")
    else: return ("주의", "tag-danger", "#F87171")

def get_risk_status(val):
    if val < 2.0: return ("안전", "tag-good", "#34D399")
    elif val < 5.0: return ("주의", "tag-moderate", "#FBBF24")
    else: return ("위험", "tag-danger", "#F87171")

co2_st, co2_tag, co2_clr = get_co2_status(filtered_co2)
temp_st, temp_tag, temp_clr = get_temp_status(temp_val)
hum_st, hum_tag, hum_clr = get_hum_status(hum_val)
well_st, well_tag, well_clr = get_wellness_status(wellness_score)
risk_st, risk_tag, risk_clr = get_risk_status(wells_risk)

# ==========================================
# 4. UI Rendering (Mobile Responsive Grid)
# ==========================================
st.markdown(f"""
    <div class="header-container">
        <div>
            <h1 style="font-size: 1.4rem; font-weight: 800; color: #F9FAFC; margin: 0;">
                Smart Classroom One-Health
            </h1>
            <p style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">
                Air Monitoring & Risk Analytics
            </p>
        </div>
        <div class="live-badge">
            <div class="live-dot"></div>
            LIVE
        </div>
    </div>
""", unsafe_allow_html=True)

if wells_risk >= 5.0 or filtered_co2 >= 1000:
    st.markdown(f"""<div class="status-banner status-danger"><span>⚠️</span><div><b>즉시 환기 필요</b> (위험도: {wells_risk:.2f}%)</div></div>""", unsafe_allow_html=True)
elif wells_risk >= 2.0 or filtered_co2 >= 800:
    st.markdown(f"""<div class="status-banner status-warn"><span>⚡</span><div><b>환기 권장</b> (CO2 상승)</div></div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="status-banner status-good"><span>✨</span><div><b>최적 상태 유지 중</b></div></div>""", unsafe_allow_html=True)

cols = st.columns(2)

metrics_data = [
    ("CO2 (KALMAN)", f"{filtered_co2:.1f}", "ppm", co2_st, co2_tag, co2_clr, f"Raw: {raw_co2:.1f}"),
    ("TEMPERATURE", f"{temp_val:.1f}", "°C", temp_st, temp_tag, temp_clr, "적정: 20~24°C"),
    ("HUMIDITY", f"{hum_val:.1f}", "%", hum_st, hum_tag, hum_clr, "적정: 40~60%"),
    ("WELLNESS", f"{wellness_score:.1f}", "/100", well_st, well_tag, well_clr, "권장: 80점↑"),
    ("INFECTION RISK", f"{wells_risk:.2f}", "%", risk_st, risk_tag, risk_clr, "기준: < 2.0%")
]

for idx, (title, val, unit, st_txt, st_tag, st_clr, sub) in enumerate(metrics_data):
    target_col = cols[idx % 2]
    with target_col:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">{title}</span>
                    <span class="status-tag {st_tag}">{st_txt}</span>
                </div>
                <div class="metric-val" style="color: {st_clr};">{val} <span style="font-size: 0.75rem; color: #64748B;">{unit}</span></div>
                <div class="metric-subtext">
                    <span>{sub}</span>
                    <span style="font-size: 1.1rem; font-weight: bold; color: #38BDF8;">➔</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

chart_theme = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(11, 15, 25, 0.6)',
    font=dict(color='#64748B', family='Plus Jakarta Sans', size=10),
    margin=dict(l=5, r=5, t=20, b=5),
    xaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

plotly_clean_config = {'displayModeBar': False}

st.markdown("<h4 style='font-size: 0.9rem; font-weight: 700; color: #E2E8F0;'>📈 CO2 Trend Analysis</h4>", unsafe_allow_html=True)
fig_co2 = go.Figure()
fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Raw_CO2'], mode='lines', name='Raw', line=dict(color='#475569', width=1, dash='dot')))
fig_co2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Filtered_CO2'], mode='lines', name='Kalman', line=dict(color='#38BDF8', width=2.5)))
fig_co2.update_layout(**chart_theme)
st.plotly_chart(fig_co2, use_container_width=True, config=plotly_clean_config)

st.markdown("<h4 style='font-size: 0.9rem; font-weight: 700; color: #E2E8F0; margin-top: 15px;'>🌡️ Temp & Humidity</h4>", unsafe_allow_html=True)
fig_th = go.Figure()
fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Temperature'], mode='lines', name='Temp', line=dict(color='#F43F5E', width=2)))
fig_th.add_trace(go.Scatter(x=df['Timestamp'], y=df['Humidity'], mode='lines', name='Humidity', line=dict(color='#3B82F6', width=2)))
fig_th.update_layout(**chart_theme)
st.plotly_chart(fig_th, use_container_width=True, config=plotly_clean_config)

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
