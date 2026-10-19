import time
import json
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class SceneItem(BaseModel):
    scene_number: int = Field(description="Số thứ tự cảnh")
    duration: str = Field(description="Thời lượng, ví dụ: 5s")
    voiceover_vi: str = Field(description="Lời thoại tiếng Việt")
    video_prompt_en: str = Field(description="Prompt tiếng Anh chi tiết mô tả hình ảnh, chuyển động, khóa form sản phẩm từ ảnh gốc")

class VideoScript(BaseModel):
    campaign_title: str = Field(description="Tên chiến dịch video")
    product_lock_note: str = Field(description="Ghi chú đặc điểm nhận diện sản phẩm từ ảnh")
    scenes: list[SceneItem]

st.set_page_config(page_title="AI Video Studio", page_icon="🎬", layout="wide")
st.title("🎬 Studio Tạo Kịch Bản & Video từ Hình Ảnh")

with st.sidebar:
    st.header("🔑 Cấu hình Hệ thống")
    gemini_key = st.text_input("Dán Gemini API Key vào đây", type="password")
    muse_key = st.text_input("Muse API Key (Tích hợp sau)", type="password", placeholder="Đang ở chế độ chờ...")
    st.divider()
    aspect_ratio = st.selectbox("Tỉ lệ khung hình", ["9:16 (TikTok/Reels)", "16:9 (YouTube)", "1:1 (Vuông)"])
    num_scenes = st.slider("Số phân cảnh", 1, 6, 3)

st.subheader("1. Cung cấp Hình ảnh & Ý tưởng")
col_img1, col_img2 = st.columns(2)

with col_img1:
    prod_file = st.file_uploader("📦 Tải ảnh Sản phẩm lên đây", type=["png", "jpg", "jpeg", "webp"])
    prod_img = Image.open(prod_file) if prod_file else None
    if prod_img:
        st.image(prod_img, caption="Ảnh sản phẩm", width=250)

with col_img2:
    model_file = st.file_uploader("🧑 Tải ảnh Người mẫu / Bối cảnh (Nếu có)", type=["png", "jpg", "jpeg", "webp"])
    model_img = Image.open(model_file) if model_file else None
    if model_img:
        st.image(model_img, caption="Ảnh người mẫu / bối cảnh", width=250)

idea_text = st.text_area("Mô tả thêm yêu cầu của bạn:", placeholder="Ví dụ: Làm video quảng cáo sang trọng, giữ nguyên thiết kế sản phẩm trong ảnh...")

if "script_result" not in st.session_state:
    st.session_state.script_result = None

if st.button("✨ Phân Tích Ảnh & Viết Kịch Bản", type="primary"):
    if not gemini_key:
        st.error("Bạn quên dán Gemini API Key ở cột bên trái rồi!")
    elif not prod_img and not idea_text.strip():
        st.warning("Hãy tải lên ít nhất 1 tấm ảnh hoặc nhập mô tả ý tưởng!")
    else:
        with st.spinner("AI đang nhìn ảnh và viết kịch bản phân cảnh..."):
            try:
                client = genai.Client(api_key=gemini_key)
                contents = []
                if prod_img:
                    contents.append(prod_img)
                if model_img:
                    contents.append(model_img)
                
                prompt_instruction = f"""
                Phân tích kỹ hình ảnh đính kèm (nếu có) để khóa đặc điểm hình dáng, màu sắc, chất liệu sản phẩm/nhân vật.
                Tạo kịch bản {num_scenes} phân cảnh cho tỉ lệ {aspect_ratio}.
                Yêu cầu bổ sung của người dùng: {idea_text}
                """
                contents.append(prompt_instruction)

                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VideoScript,
                        temperature=0.6
                    )
                )
                st.session_state.script_result = json.loads(res.text)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")

if st.session_state.script_result:
    data = st.session_state.script_result
    st.divider()
    st.subheader(f"2. Kịch bản: {data['campaign_title']}")
    st.info(f"🔒 **Khóa nhận diện hình ảnh:** {data['product_lock_note']}")

    for scene in data["scenes"]:
        s_no = scene["scene_number"]
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**🎬 Cảnh {s_no}** ({scene['duration']})")
                st.text_input("Lời thoại:", value=scene["voiceover_vi"], key=f"vo_{s_no}")
                final_prompt = st.text_area("Video Prompt (Chỉnh sửa tùy ý):", value=scene["video_prompt_en"], height=100, key=f"pr_{s_no}")
                
                if st.button(f"🎥 Tạo Video Cảnh {s_no}", key=f"btn_{s_no}"):
                    with c2:
                        with st.spinner("Đang xử lý tạo video..."):
                            time.sleep(2)
                            if not muse_key:
                                st.success("✅ Đã đóng gói Ảnh gốc + Prompt sẵn sàng! (Chờ gắn API Muse)")
                                st.code(final_prompt, language="text")
            with c2:
                st.caption("Khu vực hiển thị Video sau khi render")
