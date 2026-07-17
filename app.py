import streamlit as st
import yfinance as ticker_data
import pandas as pd
from google import genai
from google.genai import types

# นำเข้าตัวอัดเสียง (Speech-to-Text)
try:
    from streamlit_mic_recorder import speech_to_text
    has_mic = True
except ImportError:
    has_mic = False

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Javis - Personal Gold AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Javis - Personal Gold & Macro AI Assistant")
st.caption("ระบบเลขาและผู้ช่วยวิเคราะห์การเทรดส่วนตัวของคุณ (Real-time & Voice-Enabled)")

# ==========================================
# 2. SIDEBAR - PROFILE & RISK CONTROL
# ==========================================
with st.sidebar:
    st.header("⚙️ System & API Settings")
    api_key = st.text_input("Gemini API Key:", type="password")
    
    st.markdown("---")
    st.header("👤 Personal Profile")
    user_name = st.text_input("ชื่อของคุณ (Javis จะใช้เรียกคุณ):", value="บอส")
    trading_style = st.selectbox(
        "สไตล์การเทรดหลักของคุณ:",
        ["Day Trading (จบในวัน)", "Scalping (เก็บสั้น)", "Swing Trading (ถือยาวหลายวัน)"]
    )
    
    st.markdown("---")
    st.header("🛡️ Risk Management")
    balance = st.number_input("Capital ($):", value=10000, step=1000)
    risk_pct = st.slider("Risk per Trade (%):", 0.5, 5.0, 1.0, 0.5)
    sl_pips = st.number_input("Stop Loss (Pips/Gaps):", value=50, step=10)
    
    risk_amount = balance * (risk_pct / 100)
    lot_size = risk_amount / (sl_pips * 10) if sl_pips > 0 else 0
    st.info(f"💡 **Max Loss:** ${risk_amount:.2f}\n\n📊 **Lot:** `{lot_size:.2f}` Lots")

# ==========================================
# 3. LIVE MARKET DATA ENGINE
# ==========================================
@st.cache_data(ttl=60)
def fetch_gold_data():
    try:
        gold = ticker_data.Ticker("GC=F")
        df = gold.history(period="5d", interval="1h")
        if df.empty: return None
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = current_price - prev_price
        
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        sma_20 = df['SMA_20'].iloc[-1] if not df['SMA_20'].isna().all() else current_price
        
        return {
            "price": round(current_price, 2),
            "change": round(change, 2),
            "sma_20": round(sma_20, 2),
            "trend": "BULLISH" if current_price > sma_20 else "BEARISH"
        }
    except:
        return None

market_data = fetch_gold_data()

col1, col2, col3, col4 = st.columns(4)
if market_data:
    col1.metric("XAU/USD Live", f"${market_data['price']}", f"{market_data['change']} USD")
    col2.metric("SMA 20 (1H)", f"${market_data['sma_20']}")
    col3.metric("Technical Bias", market_data['trend'])
    col4.metric("Risk Target", f"{risk_pct}% (${risk_amount})")

st.markdown("---")

# ==========================================
# 4. PERSONALIZED SYSTEM PROMPT (JAVIS PERSONA)
# ==========================================
SYSTEM_INSTRUCTION = f"""
คุณคือ 'Javis' (จาร์วิส) ระบบปัญญาประดิษฐ์และเลขาส่วนตัวผู้เชี่ยวชาญด้านเศรษฐกิจมหาภาคและการเทรดทองคำ (XAU/USD) ของคุณ {user_name}

[ข้อมูลโปรไฟล์ของเจ้านาย]:
- ชื่อเจ้านาย: คุณ {user_name} (เรียกเจ้านายว่า 'คุณ {user_name}' หรือ 'บอส')
- สไตล์การเทรด: {trading_style}
- พอร์ตปัจจุบัน: ${balance} | ยอมรับความเสี่ยงได้ {risk_pct}% (${risk_amount}) ต่อไม้

[ข้อมูลตลาด REAL-TIME ล่าสุด]:
- ราคาทองคำปัจจุบัน: ${market_data['price'] if market_data else 'N/A'}
- เส้นเฉลี่ย SMA 20 (1H): ${market_data['sma_20'] if market_data else 'N/A'}
- ทิศทางเทคนิค: {market_data['trend'] if market_data else 'N/A'}

[บุคลิกและสไตล์การสื่อสารของ Javis]:
1. สุภาพ ฉลาด รอบคอบ ถ่อมตัวแต่เต็มไปด้วยความมั่นใจ ใช้ภาษาไทยที่กระชับ สรุปประเด็นชัดเจน
2. เริ่มต้นคำตอบหรือลงท้ายด้วยสไตล์เลขาไฮเทค เช่น "สวัสดีครับบอส", "รับทราบครับคุณ {user_name}", "Javis พร้อมรับคำสั่งครับ"
3. เน้นความปลอดภัยของพอร์ต วิเคราะห์จากข่าวเศรษฐกิจสหรัฐฯ + ข้อมูล Real-time และคำนวณ Lot Size แนะนำ ({lot_size:.2f} Lots) ให้เจ้านายเสมอ
"""

# ==========================================
# 5. VOICE INPUT & QUICK BUTTONS
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"สวัสดีครับบอส ผม **Javis** เลขาส่วนตัวของคุณพร้อมปฏิบัติการแล้วครับ มีอะไรให้ Javis ช่วยวิเคราะห์เกี่ยวกับราคาทองคำหรือเศรษฐกิจวันนี้ไหมครับ?"}
    ]

# ส่วนการสั่งงานด้วยเสียง
voice_text = None
st.write("🎙️ **สั่งงาน Javis ด้วยเสียง:**")
if has_mic:
    voice_text = speech_to_text(
        start_prompt="🎙️ กดเพื่อเริ่มพูดสั่ง Javis",
        stop_prompt="🛑 กดเมื่อพูดเสร็จแล้ว",
        language='th',
        key='voice_input'
    )
else:
    st.warning("⚠️ กรุณาติดตั้ง `streamlit-mic-recorder` เพื่อใช้งานฟังก์ชันเสียง")

# ปุ่มลัดคำสั่งประจำ
st.write("⚡ **คำสั่งด่วนถึง Javis:**")
q_col1, q_col2, q_col3 = st.columns(3)

preset_prompt = None
if q_col1.button("📊 บรีฟภาพรวมทองวันนี้"):
    preset_prompt = "Javis ช่วยสรุปภาพรวมตลาดทองคำราคานี้ พร้อมกรอบแนวรับแนวต้าน ให้ผมหน่อย"
if q_col2.button("📰 ข่าวเศรษฐกิจสหรัฐฯ ล่าสุด"):
    preset_prompt = "Javis ช่วงนี้มีตัวเลขเศรษฐกิจสหรัฐฯ หรือข่าว Fed อะไรที่ต้องระวังบ้าง สรุปให้ฟังหน่อย"
if q_col3.button("🎯 คำนวณแผนเทรดสั้น"):
    preset_prompt = f"Javis ช่วยคำนวณจุดเข้า/จุด Cut สำหรับการเทรดสไตล์ {trading_style} ในราคาทองปัจจุบันให้หน่อย"

# แสดงประวัติแชท
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# รับคำสั่ง
user_text_input = st.chat_input("พิมพ์สั่งงาน Javis ที่นี่...")
user_input = user_text_input or voice_text or preset_prompt

if user_input:
    if not api_key:
        st.error("กรุณากรอก Gemini API Key ใน Sidebar ด้านซ้ายก่อนนะครับ!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(f"🎙️ *{user_input}*" if user_input == voice_text else user_input)

    try:
        client = genai.Client(api_key=api_key)
        contents = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        with st.chat_message("assistant"):
            with st.spinner(f"Javis กำลังประมวลผลข้อมูลให้คุณ {user_name}..."):
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.4,
                    )
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")