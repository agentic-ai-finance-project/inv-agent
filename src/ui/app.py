import streamlit as st
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
# numpy needed for plot helper function's linspace
import numpy as np
from plotly.subplots import make_subplots # 新增 Plotly Subplots 導入
import os
import json
import streamlit.components.v1 as components # 用於執行自動捲動的 JavaScript

# 1. 設定 & 樣式
# Page config: 修改 initial_sidebar_state 為 expanded 以便展示設定
st.set_page_config(
    page_title="AI Investment Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# 簡單保留整體深色風格（但不再用 card 的 HTML）
st.markdown("""
    <style>
    
    /* 1. 全域背景設定 (主面板) */
    .stApp {
        background-color: #202124; /* 深灰背景 */
        color: #e8eaed;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 2. Sidebar (側邊欄) 樣式優化 */
    [data-testid="stSidebar"] {
        background-color: #252629; 
        border-right: 1px solid #3c4043;
    }
    
    /* Sidebar 文字強制亮白 */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* 修正 Sidebar 內的 Radio button 選項文字顏色 */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div p {
        color: #ffffff !important;
    }
    
    /* 3. 輸入框 (Text Area) 樣式 */
    .stTextArea textarea {
        background-color: #303134;
        color: #e8eaed;        
        caret-color: #ffffff;
        font-size: 16px;        
        border: 1px solid #5f6368; 
        border-radius: 8px;        
        padding: 12px 15px;       
    }
    .stTextArea textarea:focus {
        border-color: #8ab4f8 !important; 
        box-shadow: 0 0 0 2px rgba(138, 180, 248, 0.3); 
    }
    .stTextArea label p {
        color: #ffffff !important;
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
    .stTextArea textarea::placeholder {
        color: #9aa0a6 !important; 
        opacity: 1;
    }

    /* 4. Tab 分頁樣式 */
    /* 未選中 */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="false"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        opacity: 0.7;
    }
    /* 選中 */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* 5. 下拉選單 (Selectbox) 樣式維持 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #303134 !important;
        color: #ffffff !important;
        border-color: #5f6368 !important;
    }
            
    /* 6. 工具列 (Toolbar) 樣式優化 */
    [data-testid="stToolbar"] {
        background-color: #202124;
        color: #e8eaed;
    }
    .stAppDeployButton {
        display: none;
    }
            
    /* 7. Sidebar 收折/展開按鈕修正 */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #202124 !important;
        color: #ffffff !important;
    }
    button[data-testid="stExpandSidebarButton"] {
        background-color: transparent !important;
        border: none !important;
    }
    button[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
        color: #ffffff !important;
    }
    
    /* Sidebar 內部按鈕 */
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] button[kind="headerNoPadding"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] {
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebar"] button[kind="header"] [data-testid="stIconMaterial"],
    [data-testid="stSidebar"] button[kind="headerNoPadding"] [data-testid="stIconMaterial"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] [data-testid="stIconMaterial"] {
        color: #ffffff !important;
    }
    
    /* 8. Status Widget & Expander 樣式修正 */
    div.stExpander summary,
    div.stExpander summary *,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary * {
        color: #000000 !important;
        fill: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
    }
    div.stExpander summary,
    div[data-testid="stExpander"] summary {
        background-color: #9D9D9D !important; 
        transition: background-color 0.2s ease, color 0.2s ease;
        border-radius: 4px;
    }
    
    /* 9. Metric (數據指標) 樣式修正 */
    [data-testid="stMetricLabel"] p {
        color: #e8eaed !important;
    }
    [data-testid="stMetricValue"] div {
        color: #ffffff !important;
    }
            
    /* 10. Alert Container 文字顏色優化 */
    [data-testid="stAlertContainer"] {
        color: #e8eaed !important;
    }
    [data-testid="stAlertContainer"] p,
    [data-testid="stAlertContainer"] li,
    [data-testid="stAlertContainer"] ul,
    [data-testid="stAlertContainer"] strong,
    [data-testid="stAlertContainer"] h1,
    [data-testid="stAlertContainer"] h2,
    [data-testid="stAlertContainer"] h3,
    [data-testid="stAlertContainer"] div[data-testid="stMarkdownContainer"] {
        color: #e8eaed !important;
    }
    [data-testid="stAlertContainer"] a {
        color: #8ab4f8 !important;
    }

    /* ============================================================
       11. [修正版] Google Finance 風格 (針對 Key: main_chart_period_selector)
       使用 :has() 選擇器來準確偵測選中狀態
       ============================================================ */
    
    /* 1. 定位容器：橫向排列 */
    .st-key-main_chart_period_selector div[role="radiogroup"] {
        flex-direction: row !important;
        gap: 0 !important;
        border-bottom: 1px solid #3c4043;
        padding-bottom: 0px;
        margin-bottom: 15px;
    }

    /* 2. 隱藏圓圈 (Radio Circle) */
    .st-key-main_chart_period_selector label > div:first-child {
        display: none !important;
    }

    /* 3. 標籤基礎樣式 (Tab Base) */
    .st-key-main_chart_period_selector label {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important; /* 預留底部空間 */
        margin: 0 !important;
        padding: 5px 15px !important;
        border-radius: 0 !important; /* 去除圓角 */
        transition: all 0.2s;
        width: auto !important;
    }
    
    /* 4. 未選中時的文字顏色 */
    .st-key-main_chart_period_selector label p {
        color: #9aa0a6 !important;
        font-weight: 500;
    }

    /* 5. 滑鼠懸停 (Hover) */
    .st-key-main_chart_period_selector label:hover {
        background-color: rgba(255,255,255,0.05) !important;
    }
    .st-key-main_chart_period_selector label:hover p {
        color: #e8eaed !important;
    }

    /* 6. [關鍵修正] 選中狀態 (Checked) 
       使用 :has(input:checked) 來偵測 label 內部是否有被選中的 input */
    .st-key-main_chart_period_selector label:has(input:checked) {
        border-bottom: 3px solid #8ab4f8 !important; /* 底部藍線 */
    }
    
    /* 選中狀態的文字顏色 */
    .st-key-main_chart_period_selector label:has(input:checked) p {
        color: #8ab4f8 !important; /* 藍色文字 */
        font-weight: bold;
    }
    
    </style>
    """, unsafe_allow_html=True)

# 2. 開發模式與檔案讀取
# 設定為 True 以讀取本地 JSON 檔案，False 則呼叫 API
USE_MOCK_DATA = False
MOCK_FILE_PATH = "real_data_snapshot.json" # 請確保檔案名稱正確

def get_mock_data():
    """從本地檔案讀取 JSON 快照"""
    if os.path.exists(MOCK_FILE_PATH):
        try:
            with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"檔案格式錯誤：無法解析 {MOCK_FILE_PATH}")
            return None
    else:
        st.error(f"找不到檔案：{MOCK_FILE_PATH} (請確認檔案位於正確路徑)")
        return None

# ---------------------------------------------------------
# Helper: 內容抽取 + 標題偵測 + Markdown 渲染
# ---------------------------------------------------------
def extract_text_from_content(content):
    """兼容字串 / LangChain content=[{'type':'text','text':...}] 結構."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return "\n".join(parts)
    return str(content)


def is_section_title(line: str) -> bool:
    """判斷一行是否為 section 標題（避免 bullet / 句子被誤認）。"""
    line = line.strip()
    if not line:
        return False

    # **粗體標題**
    if re.match(r"^\*\*(.+)\*\*$", line):
        return True

    # bullet 不是標題
    if line.startswith("*") or line.startswith("-"):
        return False

    # 有冒號多半是句子
    if "：" in line or ":" in line:
        return False

    # 太長當敘述，不當標題
    if len(line) > 30:
        return False

    # 純中文 / 英文 / 數字 / 括號 / 空白，多半是小節標題
    if re.match(r"^[\u4e00-\u9fa5A-Za-z0-9（）() ]+$", line):
        return True

    return False


def render_sections_markdown(raw_text: str, heading_level: int = 3):
    """
    把 LLM 輸出轉成結構化 Markdown：
    - 自動偵測小節標題
    - 開頭非標題文字當「整體說明」
    - 每個 section 用 ### 標題 + 內文
    """
    text = extract_text_from_content(raw_text)
    if not text or not text.strip():
        st.info("沒有可顯示的內容")
        return

    # heading 標記，例如 3 -> "###"
    h = "#" * heading_level

    # 拿掉純空行
    lines = [l for l in text.split("\n") if l.strip() != ""]

    sections = []
    intro_lines = []
    current_title = None
    current_body = []

    for line in lines:
        if current_title is None and not sections and not is_section_title(line):
            # 最前面的非標題行 → 視為整體說明
            intro_lines.append(line)
            continue

        if is_section_title(line):
            # 遇到新標題，先收掉上一段
            if current_title is not None:
                sections.append((current_title, "\n".join(current_body)))
            # 去掉外層 **
            clean_title = line.strip().strip("*")
            current_title = clean_title
            current_body = []
        else:
            current_body.append(line)

    # 收尾
    if current_title is not None:
        sections.append((current_title, "\n".join(current_body)))

    # 開頭 intro 放在最前面
    if intro_lines:
        sections = [("整體說明", "\n".join(intro_lines))] + sections

    # 渲染
    first = True
    for title, body in sections:
        if not title and not body:
            continue

        if not first:
            st.markdown("---")
        first = False

        st.markdown(f"{h} {title}")
        if body and body.strip():
            # 直接丟給 markdown，保留原本 bullet / 粗體 / 連結
            st.markdown(body)


# ---------------------------------------------------------
# 既有 Helper: yfinance、chart、數字格式化
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="1d"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        interval = "1d"
        if period == "1d":
            interval = "1m"
        elif period == "5d":
            interval = "15m"
        elif period in ["1mo", "3mo"]:
            interval = "1h"
            
        history = stock.history(period=period, interval=interval)
        if history.empty and period == "1d":
            history = stock.history(period="1d", interval="15m")
        return info, history
    except Exception:
        return None, None

@st.cache_data(ttl=3600)
def get_ta_base_data(ticker):
    """Fetch 2 years (or max) of daily data for technical analysis to ensure sufficient lookback."""
    # Fetch 2 years for sufficient lookback (e.g., MA200)
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="2y", interval="1d") 
        
        # If 2 years of data is unavailable, fall back to max available data
        if history.empty or len(history) < 200: 
            history = stock.history(period="max", interval="1d")
            
        # Return an empty DataFrame structure if fetching still fails
        if history.empty:
            return yf.Ticker("AAPL").history(period="1d").head(0)
            
        return history
    except Exception:
        # Return an empty DataFrame structure for safety
        return yf.Ticker("AAPL").history(period="1d").head(0)

def plot_stock_chart(history, ticker, chart_type='line'):
    if history.empty:
        return go.Figure()

    # 1. 準備數據
    start_price = history['Close'].iloc[0]
    end_price = history['Close'].iloc[-1]
    
    # 決定線條顏色 (綠漲紅跌)
    line_color = "#81c995" if end_price >= start_price else "#f28b82" 
    
    # --- [修改重點] 決定 Y 軸範圍 (非對稱留白，避免標籤被切掉) ---
    min_price = history['Low'].min()
    max_price = history['High'].max()
    price_range = max_price - min_price

    if price_range > 0:
        # 上方留更多空間給 "最高點" 標註 (因為有 ay=-40 的向上偏移)
        # 將比例從 0.1 提高到 0.3 (30%)
        top_padding = price_range * 0.3  
        # 下方留白也稍微增加到 15%
        bottom_padding = price_range * 0.15 
    else:
        # 極端情況：這段時間價格完全沒變
        top_padding = max_price * 0.05
        bottom_padding = max_price * 0.05

    y_range = [min_price - bottom_padding, max_price + top_padding]
    # ---------------------------------------------------------

    # X 軸時間格式邏輯
    time_diff = history.index[-1] - history.index[0]
    if time_diff <= timedelta(days=1):
        date_format = "%H:%M"; hover_format = "%H:%M"
    elif time_diff <= timedelta(days=365):
        date_format = "%m/%d"; hover_format = "%b %d"
    else:
        date_format = "%Y/%m"; hover_format = "%b %Y"
        
    # 自定義 X 軸刻度
    num_ticks = 7
    if len(history) > num_ticks:
        tick_indices = np.linspace(0, len(history) - 1, num=num_ticks, dtype=int)
        tick_vals = [history.index[i] for i in tick_indices]
        tick_text = [history.index[i].strftime(date_format) for i in tick_indices]
    else:
        tick_vals = history.index
        tick_text = [d.strftime(date_format) for d in history.index]

    fig = go.Figure()
    
    # 2. 繪製圖表 (Candlestick 或 Line)
    if chart_type == 'candlestick':
        fig.add_trace(go.Candlestick(
            x=history.index,
            open=history['Open'], high=history['High'],
            low=history['Low'], close=history['Close'],
            name=ticker,
            increasing=dict(line=dict(color='#81c995', width=1)),
            decreasing=dict(line=dict(color='#f28b82', width=1)),
            hovertemplate="%{x|%b %d}<br>開: %{open:.2f}<br>高: %{high:.2f}<br>低: %{low:.2f}<br>收: %{close:.2f}<extra></extra>"
        ))
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        high_idx = history['High'].idxmax()
        high_val = history['High'].max()
        low_idx = history['Low'].idxmin()
        low_val = history['Low'].min()
        
    else: # 'line' chart
        fig.add_trace(go.Scatter(
            x=history.index, 
            y=history['Close'],
            mode='lines',
            fill='tozeroy',
            line=dict(color=line_color, width=2),
            fillcolor=f"rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)",
            name=ticker,
            hovertemplate=f"%{{x|{hover_format}}}<br>Price: %{{y:.2f}}<extra></extra>"
        ))
        
        high_idx = history['Close'].idxmax()
        high_val = history['Close'].max()
        low_idx = history['Close'].idxmin()
        low_val = history['Close'].min()

    # 3. 添加標註 (Annotations)
    annotations = []

    # A. 最高點標註
    annotations.append(dict(
        x=high_idx, y=high_val,
        xref="x", yref="y",
        text=f"最高: {high_val:.2f}",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
        arrowcolor="#e8eaed", ax=0, ay=-40, # 箭頭向上偏移 40px
        font=dict(color="#e8eaed", size=11),
        bgcolor="rgba(32, 33, 36, 0.7)",
        bordercolor="#5f6368", borderwidth=1, borderpad=4
    ))

    # B. 最低點標註
    annotations.append(dict(
        x=low_idx, y=low_val,
        xref="x", yref="y",
        text=f"最低: {low_val:.2f}",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
        arrowcolor="#e8eaed", ax=0, ay=40, # 箭頭向下偏移 40px
        font=dict(color="#e8eaed", size=11),
        bgcolor="rgba(32, 33, 36, 0.7)",
        bordercolor="#5f6368", borderwidth=1, borderpad=4
    ))
    
    # C. 最新收盤價
    annotations.append(dict(
        x=history.index[-1], y=history['Close'].iloc[-1],
        xref="x", yref="y",
        text=f"現價: {history['Close'].iloc[-1]:.2f}",
        showarrow=True, arrowhead=1,
        arrowcolor=line_color,
        ax=20, ay=0,
        xanchor="left",
        font=dict(color=line_color, size=12, weight="bold"),
        bgcolor="rgba(32, 33, 36, 0.8)"
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            type='category', showgrid=False, showticklabels=True,
            linecolor='#3c4043', tickfont=dict(color='#9aa0a6'),
            tickmode='array', tickvals=tick_vals, ticktext=tick_text
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#3c4043', showticklabels=True,
            tickfont=dict(color='#9aa0a6'), side='right',
            range=y_range # 使用新的 range
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        hovermode="x unified",
        showlegend=False,
        annotations=annotations
    )
    return fig


def format_large_number(num):
    if not num:
        return "-"
    if num >= 1_000_000_000_000:
        return f"{num/1_000_000_000_000:.2f}兆"
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}億"
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}百萬"
    return f"{num:,.2f}"


# ---------------------------------------------------------
# NEW Helper for Technical Analysis Calculation
# ---------------------------------------------------------

def calculate_sma(history, window):
    """Calculates Simple Moving Average on the Close price."""
    return history['Close'].rolling(window=window).mean()

def calculate_rsi(df, window=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss
    # 使用 .replace 處理除以零導致的 inf 值
    rsi = 100 - (100 / (1 + rs)).replace([np.inf, -np.inf], np.nan).fillna(100) 
    return rsi

def calculate_mtm(df, window=10):
    """Calculates Momentum Index (MTM)"""
    return df['Close'].diff(window)

# ---------------------------------------------------------
# Refactored Helper for Technical Analysis Plotting
# ---------------------------------------------------------

def plot_technical_analysis(history, ticker, price_lines=None, indicator_list=None, title="技術分析"):
    """
    Plots the stock price (Candlestick) with optional price lines (MA, Bands) 
    and optional indicators (like RSI, MTM) in separate subplots.
    """
    indicator_list = indicator_list or []
    if history.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor='#202124', plot_bgcolor='#202124', height=500,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text="暫無數據", showarrow=False, font=dict(size=20, color='#f28b82'))]
        )
        return fig

    # Determine subplot layout based on the number of indicators
    rows = 1 + len(indicator_list)
    vertical_spacing = 0.02

    if rows == 1:
        row_heights = [1.0]
        specs = [[{"secondary_y": False}]]
        chart_height = 500
    else:
        # Price chart (Row 1) takes 40% height, indicators share the remaining 60%
        price_height = 0.4
        indicator_single_height = (1.0 - price_height) / (rows - 1)
        
        row_heights = [price_height] + [indicator_single_height] * (rows - 1)
        specs = [[{"secondary_y": False}]] * rows
        chart_height = 450 + 150 * (rows - 1) # ~750 for 3 rows
        
    fig = make_subplots(
        rows=rows, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=vertical_spacing,
        row_heights=row_heights,
        specs=specs
    )

    # 1. Price Chart (Candlestick)
    fig.add_trace(go.Candlestick(
        x=history.index,
        open=history['Open'],
        high=history['High'],
        low=history['Low'],
        close=history['Close'],
        name='股價 (Candlestick)',
        increasing=dict(line=dict(color='#81c995')), # Green
        decreasing=dict(line=dict(color='#f28b82')), # Red
        yaxis='y1',
        hovertemplate="%{x|%Y/%m/%d}<br>開: %{open:.2f}<br>高: %{high:.2f}<br>低: %{low:.2f}<br>收: %{close:.2f}<extra></extra>"
    ), row=1, col=1)
    
    # 2. Add Price Technical Lines (e.g., MA, Bands)
    if price_lines:
        for line_data, name, color in price_lines:
            if line_data is not None and not line_data.empty:
                # 只繪製在 plotting window 內的數據
                line_data_plot = line_data[line_data.index.isin(history.index)]
                
                fig.add_trace(go.Scatter(
                    x=line_data_plot.index,
                    y=line_data_plot.values,
                    mode='lines',
                    name=name,
                    line=dict(color=color, width=2),
                    yaxis='y1',
                    opacity=0.8
                ), row=1, col=1)

    # 3. Add Indicator Subplots
    for i, indicator_data in enumerate(indicator_list):
        row_index = i + 2 # Indicators start from row 2
        
        indicator_data_plot = indicator_data["series"][indicator_data["series"].index.isin(history.index)]
        
        fig.add_trace(go.Scatter(
            x=indicator_data_plot.index,
            y=indicator_data_plot.values,
            mode='lines',
            name=indicator_data["name"],
            line=dict(color=indicator_data["color"], width=2),
            yaxis=f'y{row_index}'
        ), row=row_index, col=1)

        # Add horizontal lines for RSI overbought/oversold levels
        if indicator_data.get("type") == "RSI":
            fig.add_hline(y=70, line_dash="dash", line_color="#E93E33", opacity=0.8, row=row_index, col=1, annotation_text="超買 (70)", annotation_position="top left", annotation_font_color="#E93E33")
            fig.add_hline(y=30, line_dash="dash", line_color="#81c995", opacity=0.8, row=row_index, col=1, annotation_text="超賣 (30)", annotation_position="bottom left", annotation_font_color="#81c995")
            fig.update_yaxes(range=[0, 100], row=row_index, col=1) # Standard RSI range

        # Add horizontal line for MTM zero axis
        elif indicator_data.get("type") == "MTM":
            fig.add_hline(y=0, line_dash="dash", line_color="#9aa0a6", opacity=0.8, row=row_index, col=1)
            
        # Set Y-axis title dynamically
        fig.update_yaxes(
            title=indicator_data["name"],
            showgrid=True,
            gridcolor='#303134',
            showticklabels=True,
            tickfont=dict(color='#9aa0a6'),
            side='right',
            row=row_index, col=1
        )

    # --- Layout Configuration ---
    # Determine the time range for X-axis ticks
    time_diff = history.index[-1] - history.index[0]
    if time_diff <= timedelta(days=365 * 2):
        date_format = "%Y/%m"
    else:
        date_format = "%Y"

    num_ticks = 10
    if len(history) > num_ticks:
        tick_indices = np.linspace(0, len(history) - 1, num=num_ticks, dtype=int)
        tick_vals = [history.index[i] for i in tick_indices]
        tick_text = [history.index[i].strftime(date_format) for i in tick_indices]
    else:
        tick_vals = history.index
        tick_text = [d.strftime(date_format) for d in history.index]
        
    # Get price range for Y-axis (excluding indicator lines for cleaner range)
    min_price = history['Low'].min()
    max_price = history['High'].max()
    padding = (max_price - min_price) * 0.1 if max_price != min_price else max_price * 0.05
    y_range = [min_price - padding, max_price + padding]

    fig.update_layout(
        title=dict(text=f"**{title}** - {ticker}", font=dict(color='#e8eaed', size=16), x=0.05, y=0.98),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            type='category',
            showgrid=False, 
            linecolor='#3c4043',
            tickfont=dict(color='#9aa0a6'),
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_text,
            rangeslider_visible=False # Hide the range slider for a cleaner look
        ),
        yaxis=dict(
            title='股價 (Price)',
            showgrid=True, 
            gridcolor='#303134',
            showticklabels=True,
            tickfont=dict(color='#9aa0a6'),
            side='right',
            range=y_range
        ),
        paper_bgcolor='#202124', # Match app background
        plot_bgcolor='#202124',
        height=chart_height,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.02 if rows == 1 else 0.99, xanchor="left", x=0.05)
    )
    return fig

custom_divider = '<div style="border-top: 1px solid #3c4043; margin: 15px 0;"></div>'
# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 控制面板")
    
    # 0. 問題輸入
    st.markdown("### [<ins>問題輸入</ins>](#input-area)", unsafe_allow_html=True)
    st.markdown(custom_divider, unsafe_allow_html=True)
    
    # 1. 市場數據 (連結)
    st.markdown("### [<ins>市場數據</ins>](#dashboard-area)", unsafe_allow_html=True)
    
    # 股票選擇器 (維持上一版的邏輯)
    current_tickers = []
    if 'research_result' in st.session_state:
        current_tickers = st.session_state.research_result.get("tickers", [])
    
    sidebar_selected_ticker = None
    if current_tickers:
        if len(current_tickers) > 1:
            st.caption("選擇分析標的")
            sidebar_selected_ticker = st.selectbox("股票代號", options=current_tickers, label_visibility="collapsed")
        else:
            sidebar_selected_ticker = current_tickers[0]
            st.caption(f"目前標的: {sidebar_selected_ticker}")
    else:
        st.caption("尚未進行分析")
        
    st.markdown("<br>", unsafe_allow_html=True)

    # --- [修改 2] 圖表類型選單 (改回原本的樣子：垂直 Radio 或一般水平) ---
    st.caption("圖表設定") # 增加一個小標題讓排版好看
    chart_type_map = {"Line": "line", "Candle": "candlestick"}
    selected_chart_type_key = st.radio(
        "圖表類型", 
        options=list(chart_type_map.keys()), 
        index=0,
        horizontal=True, # 如果想要原本垂直的，把這裡改成 False
        label_visibility="collapsed"
    )
    selected_chart_type = chart_type_map[selected_chart_type_key]
    
    st.markdown(custom_divider, unsafe_allow_html=True)

    # 2. 投資報告
    st.markdown("### [<ins>投資報告</ins>](#report-area)", unsafe_allow_html=True)
    
    # --- [修改 3] "選擇章節" 只是副標題，不是按鈕 ---
    st.caption("選擇閱讀章節") # 使用 caption 作為副標題
    report_section = st.radio(
        "章節選擇隱藏標題", # 這個標題會被隱藏
        options=["📊 總覽 (Summary)", "📈 技術面 (Technical)", "📰 基本面 (Fundamental)", "🔗 原始資料 (Raw)"],
        index=0,
        label_visibility="collapsed" # 隱藏 Radio 自身的標題
    )
    
    st.markdown(custom_divider, unsafe_allow_html=True)
    st.caption("v1.8.0 • AI Investment Analyst")
# ---------------------------------------------------------
# Main Application (Modified: 恢復錨點與搜尋後自動捲動)
# ---------------------------------------------------------

# [錨點 1] 輸入區錨點 (設定偏移量避免被 Header 遮擋)
st.markdown('<div id="input-area" style="position:relative; top:-60px; visibility:hidden;"></div>', unsafe_allow_html=True)

st.title("🤖 AI 投資分析助理")

if USE_MOCK_DATA:
    st.caption(f"🛠️ 開發模式: 讀取本地檔案 `{MOCK_FILE_PATH}`")

query = st.text_area(
    "請輸入您的投資問題或感興趣的股票：",
    placeholder="例如：分析台積電 (TSM) 和輝達 (NVDA) 的近期表現與風險...",
    height=120
)

# --- 風格選擇與按鈕排版區 ---
c_style, c_hint, c_space, c_btn = st.columns([2.5, 3.5, 4, 2])

with c_style:
    style_display = st.selectbox(
        "選擇投資風格",
        options=["穩健型 (Balanced)", "保守型 (Conservative)", "積極型 (Aggressive)"],
        index=0, 
        label_visibility="collapsed",
        key="style_selector_main"
    )
    style_map = {"穩健型 (Balanced)": "Balanced", "保守型 (Conservative)": "Conservative", "積極型 (Aggressive)": "Aggressive"}
    selected_style = style_map[style_display]

with c_hint:
    st.markdown(
        """<div style="padding-top: 10px; color: #9aa0a6; font-size: 14px;">
        ⬅️ 選擇您的投資風格
        </div>""", 
        unsafe_allow_html=True
    )

with c_btn:
    start_analysis = st.button("🚀 開始分析", type="primary", use_container_width=True)

# ---------------------------------------
# 分析邏輯
# ---------------------------------------
if start_analysis:
    if not query:
        st.warning("請輸入問題")
    else:
        with st.status("代理人團隊正在啟動...", expanded=True) as status:
            st.write("🔍 正在檢索市場數據與相關新聞...")
            
            payload = {"query": query, "style": selected_style}
            response_json = None
            status_code = 500

            try:
                if USE_MOCK_DATA:
                    import time; time.sleep(1) 
                    st.write("🤖 正在調用大型語言模型進行推論...")
                    time.sleep(1)
                    mock_data = get_mock_data()
                    if mock_data:
                        response_json = mock_data; status_code = 200
                else:
                    st.write("⏳ 正在進行深度多面向分析 (技術面/基本面/風險)...")
                    try:
                        response = requests.post("http://localhost:8000/research", json=payload)
                        status_code = response.status_code
                        if status_code == 200: response_json = response.json()
                    except Exception as e_req:
                        st.error(f"API 連線失敗: {str(e_req)}")

                if status_code == 200 and response_json:
                    st.write("✅ 數據檢索與清洗完成")
                    st.write("✅ 技術指標運算完畢 (RSI, MACD, MA)")
                    st.write("✅ 風險官評估報告已生成")
                    
                    st.session_state.research_result = response_json
                    status.update(label="分析完成！報告已生成", state="complete", expanded=False)
                    
                    # [關鍵功能] 搜尋完成後，設定 Flag 觸發自動捲動
                    st.session_state['trigger_scroll_dashboard'] = True
                    # --- [新增] 強制重跑以更新 Sidebar 的股票列表 ---
                    st.rerun()
                    
                else:
                    error_msg = response.text if not USE_MOCK_DATA and 'response' in locals() else "無法讀取數據"
                    st.error(f"分析過程發生錯誤: {error_msg}")
                    status.update(label="分析失敗", state="error", expanded=True)
                    
            except Exception as e:
                st.error(f"系統錯誤: {str(e)}")
                status.update(label="執行失敗", state="error", expanded=True)

# ---------------------------------------
# 結果顯示區
# ---------------------------------------
if 'research_result' in st.session_state:
    result = st.session_state.research_result
    selected_ticker = sidebar_selected_ticker
    
    stock_info = {}; history_1mo = None
    if selected_ticker:
        stock = yf.Ticker(selected_ticker)
        stock_info = stock.info

    st.markdown("---")
    
    # [錨點 2] 儀表板錨點 (保留)
    st.markdown('<div id="dashboard-area" style="position:relative; top:-60px; visibility:hidden;"></div>', unsafe_allow_html=True)
    
    # =========================================================
    #  Expander 1: 市場數據儀表板
    # =========================================================
    with st.expander(f"📈 市場數據儀表板 - {selected_ticker if selected_ticker else ''}", expanded=True):
        if selected_ticker and stock_info:
            
            # --- [修改 1] 時間區間選擇器移到這裡 (Google Style) ---
            # 這裡的 Radio 會被上方的 CSS 自動渲染成 Tab 樣式
            period_map = {
                "1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", 
                "YTD": "ytd", "1Y": "1y", "5Y": "5y", "Max": "max"
            }
            
            # 建立幾列來排版：左邊放時間Tab，右邊(選填)可以放其他資訊
            c_tab, c_dummy = st.columns([7, 3]) 
            with c_tab:
                selected_period_label = st.radio(
                    "Time Period",
                    options=list(period_map.keys()),
                    index=2, # Default 1M
                    horizontal=True,
                    label_visibility="collapsed",
                    key="main_chart_period_selector"
                )
            selected_period_code = period_map[selected_period_label]
            
            # 重新抓取對應時間的數據 (因為 selected_period_code 現在是在這裡定義的)
            _, history_period = get_stock_data(selected_ticker, period=selected_period_code)
            
            # (以下維持原本的價格顯示與繪圖邏輯)
            current_price = stock_info.get('currentPrice', stock_info.get('regularMarketPrice', 0))
            
            # 計算漲跌幅邏輯...
            if history_period is not None and not history_period.empty:
                start_p = stock_info.get('previousClose', history_period['Open'].iloc[0]) if selected_period_code == "1d" else history_period['Close'].iloc[0]
                end_p = stock_info.get('currentPrice') if selected_period_code == "1d" and stock_info.get('currentPrice') else history_period['Close'].iloc[-1]
                change = end_p - start_p; change_pct = (change / start_p) * 100
            else: change = 0; change_pct = 0
            
            color_class = "#81c995" if change >= 0 else "#f28b82"; sign = "+" if change >= 0 else ""; period_text = "今天" if selected_period_code == "1d" else f"過去 {selected_period_label}"

            # 顯示大字價格
            st.markdown(f"""
                <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 0px;">
                    <span style="font-size: 32px; font-weight: 600; color: #e8eaed;">{current_price:.2f}</span>
                    <span style="font-size: 14px; color: #9aa0a6;">{stock_info.get('currency', 'USD')}</span>
                    <span style="font-size: 16px; color: {color_class}; font-weight: 500;">{sign}{change:.2f} ({change_pct:.2f}%) {sign if change >=0 else '↓'} {period_text}</span>
                </div>
            """, unsafe_allow_html=True)

            # 繪圖
            if history_period is not None and not history_period.empty:
                # 使用 Sidebar 選定的 chart type
                fig_main = plot_stock_chart(history_period, selected_ticker, chart_type=selected_chart_type)
                st.plotly_chart(fig_main, use_container_width=True, config={'displayModeBar': False})
            else: st.warning("暫無此時段股價數據")

            # 底部基本面指標 (維持原樣)
            st.markdown("<br>", unsafe_allow_html=True) 
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("市值 (Market Cap)", format_large_number(stock_info.get('marketCap'))); st.metric("開盤 (Open)", f"{stock_info.get('open', '-'):.2f}" if isinstance(stock_info.get('open'), (int, float)) else "-")
            with c2: st.metric("本益比 (P/E)", f"{stock_info.get('trailingPE', '-'):.2f}" if stock_info.get('trailingPE') else "-"); st.metric("52週高點", f"{stock_info.get('fiftyTwoWeekHigh', '-'):.2f}")
            with c3:
                dy = stock_info.get('dividendYield') or stock_info.get('trailingAnnualDividendYield')
                st.metric("殖利率 (Yield)", f"{dy*100:.2f}%" if dy else "-"); st.metric("52週低點", f"{stock_info.get('fiftyTwoWeekLow', '-'):.2f}")
        else: st.info("請先選擇股票以查看市場數據。")
            
    st.markdown("<br>", unsafe_allow_html=True)

    # [錨點 3] 報告錨點 (保留)
    st.markdown('<div id="report-area" style="position:relative; top:-60px; visibility:hidden;"></div>', unsafe_allow_html=True)

    # =========================================================
    #  Expander 2: AI 投資報告
    # =========================================================
    with st.expander(f"📝 AI 投資報告 - {selected_ticker if selected_ticker else ''}", expanded=True):
        
        if report_section == "📊 總覽 (Summary)":
            st.markdown("### 💡 最終投資建議")
            render_sections_markdown(result.get("final_report", ""))
            st.markdown("---")
            st.markdown("### ⚠️ 風險評估")
            raw_risk = extract_text_from_content(result.get("risk_assessment", "無風險評估內容"))
            garbage = ["作為首席風險官，我的職責是扮演「魔鬼代言人」，專注於識別潛在的下行風險，特別是那些可能被市場普遍樂觀情緒所忽略的方面。針對您「最近微軟可以買嗎」的提問，我的評估如下：", "作為首席風險官，", "身為風險評估員，", "以下是我的風險評估："]
            for p in garbage: raw_risk = raw_risk.replace(p, "")
            render_sections_markdown(raw_risk.strip())

        elif report_section == "📈 技術面 (Technical)":
            st.info(extract_text_from_content(result.get("technical_strategy", "暫無技術策略總結")))
            if selected_ticker:
                history_full = get_ta_base_data(selected_ticker)
                has_data = not history_full.empty
                with st.expander("▶️ 趨勢分析 (Trend Analysis)", expanded=False):
                    if has_data:
                        ma20 = calculate_sma(history_full, 20); ma50 = calculate_sma(history_full, 50)
                        one_year_ago = datetime.now() - timedelta(days=365)
                        hist_plot = history_full[history_full.index >= one_year_ago.strftime('%Y-%m-%d')]; 
                        if hist_plot.empty: hist_plot = history_full
                        st.plotly_chart(plot_technical_analysis(hist_plot, selected_ticker, price_lines=[(ma20, "MA20", "#4285F4"), (ma50, "MA50", "#E93E33")], title="趨勢分析"), use_container_width=True, config={'displayModeBar': False})
                    render_sections_markdown(result.get("trend_analysis", ""))
                with st.expander("▶️ 型態觀察 (Chart Patterns)", expanded=False):
                    if has_data:
                        ma50 = calculate_sma(history_full, 50)
                        st.plotly_chart(plot_technical_analysis(hist_plot, selected_ticker, price_lines=[(ma50, "MA50", "#FF5722")], title="型態觀察"), use_container_width=True, config={'displayModeBar': False})
                    render_sections_markdown(result.get("pattern_analysis", ""))
                with st.expander("▶️ 動能指標 (Momentum Indicators)", expanded=False):
                    if has_data:
                        rsi14 = calculate_rsi(history_full, 14); mtm10 = calculate_mtm(history_full, 10)
                        indicator_list = [{"series": rsi14, "name": "RSI (14)", "color": "#FFC107", "type": "RSI"}, {"series": mtm10, "name": "MTM (10)", "color": "#4285F4", "type": "MTM"}]
                        st.plotly_chart(plot_technical_analysis(hist_plot, selected_ticker, indicator_list=indicator_list, title="動能指標"), use_container_width=True, config={'displayModeBar': False})
                    render_sections_markdown(result.get("indicator_analysis", ""))
            else: st.warning("未識別股票代號。")

        elif report_section == "📰 基本面 (Fundamental)":
            with st.expander("📊 數據分析 (Numbers)", expanded=False): render_sections_markdown(result.get("data_analysis", "暫無數據分析"))
            with st.expander("📰 新聞摘要 (Narrative)", expanded=True): 
                raw_news = extract_text_from_content(result.get("news_analysis", "暫無新聞分析"))
                
                # --- [修改] 遇到 "新聞連結 (新聞連結)" 就直接切斷後面的內容 ---
                # 這裡設定幾個可能的標題變體以防 Markdown 格式不同
                pattern = r"(?:#+|\*\*|__)?\s*新聞連結\s*[(\uff08].*?新聞連結.*"
                
                # 使用 re.split 切割，只取第一部分 (匹配到的標題之前的所有內容)
                # flags=re.IGNORECASE 讓比對不分大小寫
                parts = re.split(pattern, raw_news, maxsplit=1, flags=re.IGNORECASE)
                
                clean_news = parts[0].strip()
                
                render_sections_markdown(clean_news)
            

        elif report_section == "🔗 原始資料 (Raw)":
            # 根據使用者要求，移除「🔗 參考來源」及其連結內容
            with st.expander("查看原始 JSON 回應 (Debug)"): st.json(result)

# =========================================================
#  Late Injection for Auto-Scrolling
#  (保留：僅用於搜尋完成後跳轉至儀表板)
# =========================================================
js_scroll_code = ""

# 1. 分析完成 -> 滑到 儀表板 (#dashboard-area)
if st.session_state.get('trigger_scroll_dashboard'):
    js_scroll_code += """
        const dash = window.parent.document.getElementById('dashboard-area');
        if (dash) {
            console.log("Scrolling to Dashboard...");
            dash.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    """
    st.session_state['trigger_scroll_dashboard'] = False 

# 執行 JS
if js_scroll_code:
    components.html(
        f"<script>setTimeout(function() {{ {js_scroll_code} }}, 600);</script>",
        height=0, width=0
    )