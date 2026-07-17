import streamlit as st
from google import genai
from PIL import Image

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Javis Gold AI", page_icon="🤖")
st.title("🤖 Javis Gold AI")

# รับ API Key จาก Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    api_key = st.text_input("กรอก Gemini API Key ใหม่ที่นี่:", type="password")

if not api_key:
    st.info("👈 กรุณากรอก API Key ในแถบด้านซ้ายเพื่อเริ่มใช้งานครับบอส")
    st.stop()

# สร้าง Client เชื่อมต่อผ่าน SDK ตัวใหม่
client = genai.Client(api_key=api_key)

# ช่องอัปโหลดรูปภาพ (เช่น รูปภาพกราฟเทรด)
uploaded_file = st.file_uploader("แนบรูปภาพกราฟ/เอกสาร (ถ้ามี):", type=["png", "jpg", "jpeg"])
image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="รูปภาพที่แนบ", use_container_width=True)

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

    # ส่งให้ Javis วิเคราะห์และตอบกลับ
    with st.chat_message("assistant"):
        with st.spinner("Javis กำลังคิดและประมวลผล..."):
            try:
                # จัดเตรียมข้อมูลส่งให้โมเดล (รองรับทั้งข้อความและรูปภาพ)
                contents = [prompt]
                if image:
                    contents.append(image)

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents
                )
                
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")