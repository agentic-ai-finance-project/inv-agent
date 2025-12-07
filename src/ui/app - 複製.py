import streamlit as st
import requests
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import re
import numpy as np
import pandas as pd

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
    .stApp {
        background-color: #202124;
        color: #e8eaed;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTextArea textarea {
        background-color: #303134;
        color: #e8eaed;
        border: 1px solid #3c4043;
        border-radius: 8px;
    }
    /* 修正 Streamlit 預設的 Plotly 容器寬度問題 */
    .stPlotlyChart {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
# Technical Analysis Helpers (for Plotting)
# ---------------------------------------------------------

def calculate_rsi(df, window=14):
    """Calculate Relative Strength Index (RSI) using Pandas for Plotly."""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    # Use Exponential Moving Average (EMA) for smoothing, common for RSI
    # In yfinance tools, we used SMA, but EMA is often more standard for RSI. Sticking to SMA for consistency with tools.py logic if possible
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    # Replace inf with nan, then fillna(100) for cases where there is only gain (loss is 0)
    rsi = 100 - (100 / (1 + rs)).replace([np.inf, -np.inf], np.nan).fillna(100)
    return rsi

def get_technical_history(ticker, period="6mo"):
    """
    Fetches price history and calculates technical indicators needed for plotting.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch data for at least 6 months to ensure MA_50 is calculated
        history = stock.history(period="6mo", interval="1d")
        
        if history.empty:
            return None, None
            
        df = history.copy()
        
        # Calculate Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        df['RSI_14'] = calculate_rsi(df, window=14)
        
        # Only keep recent data for plotting (last 90 days for clarity)
        df_plot = df.iloc[-90:].copy()
        
        # Fill NaN values in the start of SMA columns with the actual price for a clean plot start
        for ma in ['SMA_20', 'SMA_50']:
             df_plot[ma] = df_plot[ma].fillna(df_plot['Close'])

        # Drop rows where RSI is NaN (initial 13 days of the window)
        df_plot = df_plot.dropna(subset=['RSI_14'])
        
        return stock.info, df_plot
        
    except Exception:
        return None, None

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
# Plotting Function
# ---------------------------------------------------------

def plot_technical_analysis(df, ticker):
    """
    Creates a combined plot of Price + MA and RSI subplot.
    """
    if df.empty:
        return go.Figure()

    # Create subplots: 2 rows (Price/MA, RSI) and 1 column
    # The heights ratio ensures the price chart is larger
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.05,
                        row_heights=[0.7, 0.3])

    # --- 1. Price and MA Plot (Row 1) ---
    line_color = "#81c995" if df['Close'].iloc[-1] >= df['Close'].iloc[0] else "#f28b82"

    # Candlestick chart (optional, use line chart for simplicity and consistency with initial structure)
    # fig.add_trace(go.Candlestick(x=df.index,
    #                              open=df['Open'],
    #                              high=df['High'],
    #                              low=df['Low'],
    #                              close=df['Close'],
    #                              name='Price'), row=1, col=1)

    # Line plot (default)
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'],
        mode='lines',
        line=dict(color=line_color, width=2),
        fill='tozeroy',
        fillcolor=f"rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)",
        name='價格',
        hovertemplate='%{y:.2f}<extra></extra>'
    ), row=1, col=1)
    
    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#ffe082', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#80deea', width=1), name='SMA 50'), row=1, col=1)

    # --- 2. RSI Plot (Row 2) ---
    rsi_color = "#81c995" if df['RSI_14'].iloc[-1] >= 50 else "#f28b82"
    
    # RSI Line
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['RSI_14'], 
        line=dict(color=rsi_color, width=2), 
        name='RSI (14)', 
        hovertemplate='%{y:.2f}<extra></extra>'
    ), row=2, col=1)

    # Overbought/Oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="#f28b82", row=2, col=1, name='超買')
    fig.add_hline(y=30, line_dash="dash", line_color="#81c995", row=2, col=1, name='超賣')
    fig.add_hline(y=50, line_dash="dot", line_color="#9aa0a6", row=2, col=1, name='中線')

    # --- Global Layout Configuration ---
    fig.update_layout(
        title=f'{ticker} 技術分析圖表 (過去 90 日)',
        title_font_color='#e8eaed',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, linecolor='#3c4043'),
        yaxis=dict(showgrid=True, gridcolor='#3c4043', side='right'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=550,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.01, font=dict(color="#9aa0a6"))
    )

    # Configure axes for individual subplots
    fig.update_xaxes(
        showgrid=False, 
        tickfont=dict(color='#9aa0a6'),
        rangeslider_visible=False,
        row=1, col=1
    )
    fig.update_yaxes(
        title='價格 (Price)', 
        title_font_color='#9aa0a6',
        showgrid=True, 
        gridcolor='#3c4043', 
        tickfont=dict(color='#9aa0a6'),
        side='right',
        row=1, col=1
    )
    fig.update_xaxes(
        showgrid=True, 
        gridcolor='#3c4043', 
        tickfont=dict(color='#9aa0a6'),
        row=2, col=1
    )
    fig.update_yaxes(
        title='RSI', 
        title_font_color='#9aa0a6',
        range=[0, 100], 
        showgrid=True, 
        gridcolor='#3c4043', 
        tickfont=dict(color='#9aa0a6'),
        side='right',
        row=2, col=1
    )
    
    return fig


# ---------------------------------------------------------
# Main Application Logic
# ---------------------------------------------------------

st.title("🤖 AI 投資分析助理")

query = st.text_area(
    "請輸入您的投資問題或感興趣的股票：",
    placeholder="例如：分析台積電 (TSM) 和輝達 (NVDA) 的近期表現與風險...",
    height=100
)

if st.button("🚀 開始分析", type="primary"):
    if not query:
        st.warning("請輸入問題")
    else:
        # 清除歷史結果以顯示新查詢
        if 'research_result' in st.session_state:
            del st.session_state.research_result
            
        with st.spinner("代理人團隊正在進行深度研究..."):
            try:
                response = requests.post("http://localhost:8000/research", json={"query": query})
                if response.status_code == 200:
                    st.session_state.research_result = response.json()
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")

if 'research_result' in st.session_state:
    result = st.session_state.research_result
    tickers = result.get("tickers", [])
    
    st.markdown("---")
    
    # 1. Dashboard & Charting
    if tickers:
        st.subheader("📈 市場儀表板")
        
        selected_ticker = tickers[0]
        if len(tickers) > 1:
            selected_ticker = st.radio("選擇股票", tickers, horizontal=True, label_visibility="collapsed")
        
        info, tech_history = get_technical_history(selected_ticker)
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0)) if info else 0
        
        if tech_history is not None and not tech_history.empty:
            
            # Use the latest 90-day data for change calculation displayed in the header
            start_price = tech_history['Close'].iloc[0]
            end_price = tech_history['Close'].iloc[-1]
            change = end_price - start_price
            change_pct = (change / start_price) * 100
            
            color_class = "#81c995" if change >= 0 else "#f28b82"
            sign = "+" if change >= 0 else ""
            
            st.markdown(
                f"<div style='color: #9aa0a6; font-size: 14px; margin-bottom: 5px;'>市場概況 > {info.get('longName', selected_ticker)}</div>",
                unsafe_allow_html=True
            )
            
            st.markdown(f"""
                <div style="display: flex; align-items: baseline; gap: 10px; margin-top: -10px;">
                    <span style="font-size: 36px; font-weight: 400; color: #e8eaed;">{current_price:.2f}</span>
                    <span style="font-size: 14px; color: #9aa0a6;">{info.get('currency', 'USD')}</span>
                    <span style="font-size: 16px; color: {color_class}; font-weight: 500;">
                        {sign}{change:.2f} ({change_pct:.2f}%) {sign if change >=0 else '↓'} (過去 90 日)
                    </span>
                </div>
                <div style="color: #9aa0a6; font-size: 12px; margin-bottom: 20px;">
                    已收盤 • 免責聲明
                </div>
            """, unsafe_allow_html=True)

            # --- Technical Chart (Combined Plot) ---
            st.plotly_chart(
                plot_technical_analysis(tech_history, selected_ticker),
                use_container_width=True,
                config={'displayModeBar': False}
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            # Replicating original dashboard metrics
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

    # 2. 報告區
    st.markdown("---")
    st.subheader("📝 AI 投資報告")
    
    # 9 Tabs for comprehensive report (matching the new agent structure)
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

    with t4_tab: # TECHNICAL STRATEGY
        render_sections_markdown(result.get("technical_strategy", "無技術策略總結。"))
        
    with t5_tab: # TREND ANALYSIS
        render_sections_markdown(result.get("trend_analysis", "無趨勢分析。"))

    with t6_tab: # PATTERN ANALYSIS
        render_sections_markdown(result.get("pattern_analysis", "無型態分析。"))
        
    with t7_tab: # INDICATOR ANALYSIS
        render_sections_markdown(result.get("indicator_analysis", "無指標分析。"))

    with t8_tab:
        raw_risk = extract_text_from_content(result.get("risk_assessment", "無風險評估"))
        # Clean up boilerplate language sometimes added by LLMs to the Risk Manager output
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