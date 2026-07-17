import streamlit as st
import google.generativeai as genai

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Javis Gold AI", page_icon="🤖")
st.title("🤖 Javis Gold AI")

# รับ API Key จาก Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    api_key = st.text_input("กรอก Gemini API Key ที่นี่:", type="password")

if not api_key:
    st.info("👈 กรุณากรอก API Key ในแถบด้านซ้ายเพื่อเริ่มใช้งานครับบอส")
    st.stop()

# เชื่อมต่อ Google AI Studio (ระบบมาตรฐาน)
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# ระบบบันทึกประวัติการคุย
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงข้อความแชทก่อนหน้า
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ช่องพิมพ์ส่งข้อความ
if prompt := st.chat_input("พิมพ์ข้อความสั่ง Javis ได้เลยครับ..."):
    # บันทึกคำถามผู้ใช้
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # ส่งให้ Javis ตอบกลับ
    with st.chat_message("assistant"):
        with st.spinner("Javis กำลังคิดและประมวลผล..."):
            try:
                response = model.generate_content(prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")