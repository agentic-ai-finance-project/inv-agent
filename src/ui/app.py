# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/ui/app.py

import streamlit as st
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
# numpy needed for plot helper function's linspace
import numpy as np

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
# 既有 Helper: yfinance、chart、數字格式化
# ---------------------------------------------------------

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


def plot_google_finance_chart(history, ticker):
    if history.empty:
        return go.Figure()

    start_price = history['Close'].iloc[0]
    end_price = history['Close'].iloc[-1]
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
# Main Application
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
        with st.spinner("代理人團隊正在進行深度研究..."):
            try:
                # 假設 API 在 localhost:8000 運行
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
    
    # 1. Dashboard
    if tickers:
        st.subheader("📈 市場儀表板")
        
        selected_ticker = tickers[0]
        if len(tickers) > 1:
            selected_ticker = st.radio("選擇股票", tickers, horizontal=True, label_visibility="collapsed")
        
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
            
            selected_label = st.radio(
                "Time Period",
                options=list(period_options.keys()),
                horizontal=True,
                label_visibility="collapsed",
                key=f"period_selector_{selected_ticker}",
                index=2
            )
            selected_period_code = period_options[selected_label]
            
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
                    plot_google_finance_chart(history, selected_ticker),
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
        render_sections_markdown(result.get("trend_analysis", "無趨勢分析。"))

    with t6_tab:
        render_sections_markdown(result.get("pattern_analysis", "無型態分析。"))
        
    with t7_tab:
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