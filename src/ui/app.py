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

# 1. 設定 & 樣式
# Page config
st.set_page_config(
    page_title="AI Investment Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 簡單保留整體深色風格（但不再用 card 的 HTML）
st.markdown("""
    <style>
    /* 1. 全域背景設定 */
    .stApp {
        background-color: #202124;
        color: #e8eaed;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 2. 輸入框 (Text Area) Google 風格化 */
    .stTextArea textarea {
        background-color: #303134;
        color: #e8eaed;         
        caret-color: #ffffff;   /* 游標純白 */
        font-size: 16px;        
        border: 1px solid #5f6368; 
        border-radius: 8px;        
        padding: 12px 15px;       
    }
    .stTextArea textarea:focus {
        border-color: #8ab4f8 !important; 
        box-shadow: 0 0 0 2px rgba(138, 180, 248, 0.3); 
    }
    
    /* 3. 輸入框與選單的標題 (Label) 顏色 */
    .stTextArea label p, 
    .stSelectbox label p {
        color: #ffffff !important; /* 純白標題 */
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }

    /* 4. 輸入框提示文字 (Placeholder) */
    .stTextArea textarea::placeholder {
        color: #9aa0a6 !important; 
        opacity: 1;
    }
    
    /* --------------------------------------------------------- */
    /* --- 新增修改區域 --- */
    /* --------------------------------------------------------- */

    /* 5. 市場儀表板選項 (Radio Buttons) 文字顏色 */
    /* 針對 st.radio 的選項文字進行設定 */
    .stRadio div[role="radiogroup"] p {
        color: #ffffff !important; /* 強制變白 */
        font-size: 1rem;
    }

    /* 6. AI 投資報告分頁 (Tabs) 選項文字顏色 */
    /* 設定 "未被選擇" 的 Tab 文字顏色 */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="false"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; /* 未選中時：純白 */
        opacity: 0.7;              /* 稍微加一點透明度區分，若要全亮可改為 1 */
    }

    /* 設定 "已被選擇" 的 Tab 文字顏色 (保持白色或亮色) */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important; /* 選中時：純白 */
        font-weight: bold;         /* 加粗表示選中 */
    }

    /* 調整 Tab 整體字體大小 */
    .stTabs [data-baseweb="tab-list"] button p {
        font-size: 1.1rem;
    }

    /* 7. Selectbox (下拉選單) 樣式維持 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #303134 !important;
        color: #ffffff !important;
        border-color: #5f6368 !important;
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

    start_price = history['Close'].iloc[0]
    end_price = history['Close'].iloc[-1]
    # 決定顏色 (用於連線圖，或 K 棒的線條顏色)
    line_color = "#81c995" if end_price >= start_price else "#f28b82" 
    
    min_price = history['Low'].min()
    max_price = history['High'].max()
    padding = (max_price - min_price) * 0.05 if max_price != min_price else max_price * 0.01
    y_range = [min_price - padding, max_price + padding]

    time_diff = history.index[-1] - history.index[0]
    if time_diff <= timedelta(days=1):
        date_format = "%H:%M"
        hover_format = "%H:%M"
    elif time_diff <= timedelta(days=365):
        date_format = "%m/%d"
        hover_format = "%b %d"
    else:
        date_format = "%Y/%m"
        hover_format = "%b %Y"
        
    num_ticks = 7
    if len(history) > num_ticks:
        # NOTE: numpy is required for this logic
        # import numpy as np
        tick_indices = np.linspace(0, len(history) - 1, num=num_ticks, dtype=int)
        tick_vals = [history.index[i] for i in tick_indices]
        tick_text = [history.index[i].strftime(date_format) for i in tick_indices]
    else:
        tick_vals = history.index
        tick_text = [d.strftime(date_format) for d in history.index]

    fig = go.Figure()
    
    if chart_type == 'candlestick':
        # Candlestick 繪圖邏輯
        fig.add_trace(go.Candlestick(
            x=history.index,
            open=history['Open'],
            high=history['High'],
            low=history['Low'],
            close=history['Close'],
            name=ticker,
            increasing=dict(line=dict(color='#81c995', width=1)), # Green line
            decreasing=dict(line=dict(color='#f28b82', width=1)), # Red line
            hovertemplate="%{x|%b %d}<br>開: %{open:.2f}<br>高: %{high:.2f}<br>低: %{low:.2f}<br>收: %{close:.2f}<extra></extra>"
        ))
        # 移除 Candlestick 預設的範圍滑塊 (Range Slider)
        fig.update_layout(xaxis_rangeslider_visible=False) 
    else: # 'line' chart (default) 
        # 原有的連線圖繪圖邏輯
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

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            type='category',
            showgrid=False, 
            showticklabels=True,
            linecolor='#3c4043',
            tickfont=dict(color='#9aa0a6'),
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_text
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#3c4043',
            showticklabels=True,
            tickfont=dict(color='#9aa0a6'),
            side='right',
            range=y_range
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        hovermode="x unified",
        showlegend=False
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


# ---------------------------------------------------------
# Main Application
# ---------------------------------------------------------

st.title("🤖 AI 投資分析助理")

if USE_MOCK_DATA:
    st.caption(f"🛠️ 開發模式: 讀取本地檔案 `{MOCK_FILE_PATH}`")

query = st.text_area(
    "請輸入您的投資問題或感興趣的股票：",
    placeholder="例如：分析台積電 (TSM) 和輝達 (NVDA) 的近期表現與風險...",
    height=100
)

# --- 新增功能：投資風格選擇與按鈕排版 ---
col_options, col_btn = st.columns([1, 4], gap="medium")

with col_options:
    style_display = st.selectbox(
        "選擇投資風格",
        options=["穩健型 (Balanced)", "保守型 (Conservative)", "積極型 (Aggressive)"],
        index=0, # 預設穩健型
        help="這將影響風險評估員的標準與報告的語氣"
    )

# 將顯示名稱轉換為後端參數
style_map = {
    "穩健型 (Balanced)": "Balanced",
    "保守型 (Conservative)": "Conservative",
    "積極型 (Aggressive)": "Aggressive"
}
selected_style = style_map[style_display]

# 按鈕邏輯 (透過 columns 排版後，將按鈕放在右側，這裡使用 vertical_alignment="bottom" 的效果通常需要 Streamlit 1.31+，若舊版可忽略)
with col_btn:
    # 為了讓按鈕跟左邊的選單對齊，可以加一點空白 (視版本而定，新版可用 vertical_alignment)
    st.write("") 
    st.write("") 
    start_analysis = st.button("🚀 開始分析", type="primary")

# ---------------------------------------

if start_analysis:
    if not query:
        st.warning("請輸入問題")
    else:
        # 在 spinner 顯示當前的風格，增加互動感
        with st.spinner(f"代理人團隊正在以「{style_display}」進行深度研究..."):
            try:
                # 假設 API 在 localhost:8000 運行
                response = requests.post("http://localhost:8000/research", json={"query": query})
                if response.status_code == 200:
                    st.session_state.research_result = response.json()
                else:
                    # --- 將 style 參數加入 payload ---
                    payload = {
                        "query": query, 
                        "style": selected_style 
                    }
                    response = requests.post("http://localhost:8000/research", json=payload)
                    # --------------------------------------
                    
                    if response.status_code == 200:
                        st.session_state.research_result = response.json()
                    else:
                        st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if 'research_result' in st.session_state:
    result = st.session_state.research_result
    tickers = result.get("tickers", [])
    
    # 確保有股票代號才能顯示儀表板和技術分析圖
    if tickers:
        selected_ticker = tickers[0]
        if len(tickers) > 1:
            st.markdown("---")
            selected_ticker = st.radio("選擇股票", tickers, horizontal=True, label_visibility="collapsed")
    else:
        # 如果沒有識別出股票代號，則無法繪圖，但仍可顯示報告
        selected_ticker = None


    # 1. Dashboard
    st.markdown("---")
    if selected_ticker:
        st.subheader("📈 市場儀表板")
        
        period_options = {
            "1 天": "1d", "5 天": "5d", "1 個月": "1mo", "6 個月": "6mo",
            "本年迄今": "ytd", "1 年": "1y", "5 年": "5y", "最久": "max"
        }
        if 'selected_period_label' not in st.session_state:
            st.session_state.selected_period_label = "1 個月"
            
        stock = yf.Ticker(selected_ticker)
        info = stock.info
        
        if info:
            st.markdown(
                f"<div style='color: #9aa0a6; font-size: 14px; margin-bottom: 5px;'>市場概況 > {info.get('longName', selected_ticker)}</div>",
                unsafe_allow_html=True
            )
            
            # Time Period Selector
            selected_label = st.radio(
                "Time Period",
                options=list(period_options.keys()),
                horizontal=True,
                label_visibility="collapsed",
                key=f"period_selector_{selected_ticker}",
                index=2
            )
            selected_period_code = period_options[selected_label]

            # Chart Type Selection (Added in previous step)
            chart_type_map = {"連線圖 (Line)": "line", "K 棒圖 (Candlestick)": "candlestick"}
            chart_type_label = st.radio(
                "Chart Type",
                options=list(chart_type_map.keys()),
                horizontal=True,
                label_visibility="collapsed",
                key=f"chart_type_selector_{selected_ticker}",
                index=0,
            )
            selected_chart_type = chart_type_map[chart_type_label]
            
            _, history = get_stock_data(selected_ticker, period=selected_period_code)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if history is not None and not history.empty:
                if selected_period_code == "1d":
                    start_price = info.get('previousClose', history['Open'].iloc[0])
                    end_price = history['Close'].iloc[-1]
                    if info.get('currentPrice'):
                        end_price = info.get('currentPrice')
                else:
                    start_price = history['Close'].iloc[0]
                    end_price = history['Close'].iloc[-1]
                change = end_price - start_price
                change_pct = (change / start_price) * 100
            else:
                change = 0
                change_pct = 0
                
            color_class = "#81c995" if change >= 0 else "#f28b82"
            sign = "+" if change >= 0 else ""
            period_text = "今天" if selected_period_code == "1d" else f"過去 {selected_label}"
            
            st.markdown(f"""
                <div style="display: flex; align-items: baseline; gap: 10px; margin-top: -10px;">
                    <span style="font-size: 36px; font-weight: 400; color: #e8eaed;">{current_price:.2f}</span>
                    <span style="font-size: 14px; color: #9aa0a6;">{info.get('currency', 'USD')}</span>
                    <span style="font-size: 16px; color: {color_class}; font-weight: 500;">
                        {sign}{change:.2f} ({change_pct:.2f}%) {sign if change >=0 else '↓'} {period_text}
                    </span>
                </div>
                <div style="color: #9aa0a6; font-size: 12px; margin-bottom: 20px;">
                    已收盤 • 免責聲明
                </div>
            """, unsafe_allow_html=True)

            if history is not None and not history.empty:
                st.plotly_chart(
                    plot_stock_chart(history, selected_ticker, chart_type=selected_chart_type),
                    use_container_width=True,
                    config={'displayModeBar': False}
                )
            else:
                st.warning("暫無此時段數據")

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    **開盤**：{info.get('open', '-')}  
                    **最高**：{info.get('dayHigh', '-')}  
                    **最低**：{info.get('dayLow', '-')}
                """)
            with col2:
                mkt_cap = format_large_number(info.get('marketCap'))
                pe_ratio = f"{info.get('trailingPE', '-'):.2f}" if info.get('trailingPE') else "-"
                div_yield_raw = info.get('dividendYield')
                if div_yield_raw is not None:
                    div_yield = f"{div_yield_raw:.2f}%"
                else:
                    div_yield_raw = info.get('trailingAnnualDividendYield')
                    div_yield = f"{div_yield_raw*100:.2f}%" if div_yield_raw is not None else "-"
                st.markdown(f"""
                    **市值**：{mkt_cap}  
                    **本益比**：{pe_ratio}  
                    **殖利率**：{div_yield}
                """)
            with col3:
                high_52 = info.get('fiftyTwoWeekHigh', '-')
                low_52 = info.get('fiftyTwoWeekLow', '-')
                div_rate = info.get('dividendRate', '-')
                st.markdown(f"""
                    **52 週高點**：{high_52}  
                    **52 週低點**：{low_52}  
                    **股利金額**：{div_rate}
                """)
        else:
            st.error(f"無法獲取 {selected_ticker} 的數據")
    else:
        st.warning("未識別出股票代號，無法顯示市場儀表板。")


    # 2. 報告區
    st.markdown("---")
    st.subheader("📝 AI 投資報告")
    
    # 9 Tabs for comprehensive report
    t1, t2_tab, t3_tab, t4_tab, t5_tab, t6_tab, t7_tab, t8_tab, t9_tab = st.tabs([
        "最終建議", "數據分析", "新聞摘要", 
        "技術策略總結", 
        "技術 - 趨勢", 
        "技術 - 型態", 
        "技術 - 指標",
        "風險評估", 
        "新聞來源"
    ])
    
    with t1:
        render_sections_markdown(result.get("final_report", ""))

    with t2_tab:
        render_sections_markdown(result.get("data_analysis", ""))

    with t3_tab:
        render_sections_markdown(result.get("news_analysis", ""))

    with t4_tab:
        render_sections_markdown(result.get("technical_strategy", "無技術策略總結。"))
        
    with t5_tab:
        # 趨勢分析圖表 (MA20/MA50)
        if selected_ticker:
            # 1. 獲取足夠 lookback 的數據 (2年)
            history_full = get_ta_base_data(selected_ticker)

            if not history_full.empty:
                # 2. 定義繪圖範圍 (過去一年)
                one_year_ago = datetime.now() - timedelta(days=365)
                history_plot = history_full[history_full.index >= one_year_ago.strftime('%Y-%m-%d')]
                
                if history_plot.empty:
                    history_plot = history_full

                # 3. 於完整數據集上計算指標
                ma20 = calculate_sma(history_full, 20)
                ma50 = calculate_sma(history_full, 50)

                price_lines = [
                    (ma20, "20日移動平均 (MA20)", "#4285F4"), # Google Blue
                    (ma50, "50日移動平均 (MA50)", "#E93E33") # Google Red
                ]

                fig = plot_technical_analysis(
                    history_plot, 
                    selected_ticker, 
                    price_lines=price_lines,
                    title="股價趨勢分析 (MA20/MA50)"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning(f"無法獲取 {selected_ticker} 的股價數據進行技術趨勢分析。")
        
        render_sections_markdown(result.get("trend_analysis", "無趨勢分析。"))

    with t6_tab:
        # 型態分析圖表 (K 棒 + MA50 供參考)
        if selected_ticker:
            # 1. 獲取足夠 lookback 的數據 (2年)
            history_full = get_ta_base_data(selected_ticker)

            if not history_full.empty:
                # 2. 定義繪圖範圍 (過去一年)
                one_year_ago = datetime.now() - timedelta(days=365)
                history_plot = history_full[history_full.index >= one_year_ago.strftime('%Y-%m-%d')]

                if history_plot.empty:
                    history_plot = history_full
                
                # 3. 於完整數據集上計算指標
                ma50 = calculate_sma(history_full, 50)
                
                price_lines = [
                    (ma50, "50日移動平均 (MA50)", "#FF5722") # Orange
                ]

                fig = plot_technical_analysis(
                    history_plot, 
                    selected_ticker, 
                    price_lines=price_lines,
                    title="股價型態觀察"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning(f"無法獲取 {selected_ticker} 的股價數據進行技術型態分析。")

        render_sections_markdown(result.get("pattern_analysis", "無型態分析。"))
        
    with t7_tab:
        # 指標分析圖表 (RSI 14 & MTM 10)
        if selected_ticker:
            # 1. 獲取足夠 lookback 的數據 (2年)
            history_full = get_ta_base_data(selected_ticker)

            if not history_full.empty:
                # 2. 定義繪圖範圍 (過去一年)
                one_year_ago = datetime.now() - timedelta(days=365)
                history_plot = history_full[history_full.index >= one_year_ago.strftime('%Y-%m-%d')]

                if history_plot.empty:
                    history_plot = history_full

                # 3. 於完整數據集上計算指標
                rsi14 = calculate_rsi(history_full, window=14)
                mtm10 = calculate_mtm(history_full, window=10)
                
                # RSI 屬於獨立指標，傳遞給 indicator_list
                indicator_list = []
                indicator_list.append({
                    "series": rsi14, 
                    "name": "RSI (14)", 
                    "color": "#FFC107", 
                    "type": "RSI"
                })
                indicator_list.append({
                    "series": mtm10, 
                    "name": "動能指數 (MTM 10)", 
                    "color": "#4285F4", 
                    "type": "MTM"
                })

                fig = plot_technical_analysis(
                    history_plot, 
                    selected_ticker, 
                    price_lines=[],
                    indicator_list=indicator_list, # 傳遞兩個指標
                    title="動能指標分析 (RSI 14 & MTM 10)"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning(f"無法獲取 {selected_ticker} 的股價數據進行技術指標分析。")

        render_sections_markdown(result.get("indicator_analysis", "無指標分析。"))

    with t8_tab:
        raw_risk = extract_text_from_content(result.get("risk_assessment", "無風險評估"))
        raw_risk = raw_risk.replace(
            '作為首席風險官，我的職責是扮演「魔鬼代言人」，專注於識別潛在的下行風險，特別是那些可能被市場普遍樂觀情緒所忽略的方面。針對您「最近微軟可以買嗎」的提問，我的評估如下：',
            ''
        )
        if "作為首席風險官" in raw_risk:
            parts = raw_risk.split('\n\n', 1)
            if len(parts) > 1 and "作為首席風險官" in parts[0]:
                raw_risk = parts[1]
        render_sections_markdown(raw_risk)

    with t9_tab:
        news_content = extract_text_from_content(result.get("news_analysis", ""))
        links = re.findall(r'\[([^\]]+)\]\((http[^\)]+)\)', news_content)

        st.markdown("**新聞來源列表**")
        if links:
            for title, url in links:
                st.markdown(f"- [{title}]({url})")
        else:
            st.info("報告中未檢測到明確的新聞連結，請參考「新聞摘要」分頁中的內容。")
