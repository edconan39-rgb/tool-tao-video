import io
import time
import base64
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Test Kết Nối Muse API", page_icon="🧪", layout="wide")
st.title("🧪 Trạm Kiểm Tra Kết Nối Muse API (Tạo Video Thử Nghiệm)")

# Hàm chuyển ảnh tải lên thành định dạng gửi qua API
def image_to_data_uri(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

with st.sidebar:
    st.header("🔑 Thông tin kết nối Muse")
    auth_prefix = st.selectbox(
        "Kiểu xác thực (Header)", 
        ["Bearer (Phổ biến nhất)", "Key (Dùng cho Fal.ai)"]
    )
    muse_key = st.text_input("1. Dán Muse API Key vào đây:", type="password")
    endpoint_url = st.text_input(
        "2. Đường dẫn API (Endpoint URL):", 
        value="https://queue.fal.run/fal-ai/musev"
    )

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Dữ liệu gửi đi")
    test_file = st.file_uploader("Tải thử 1 ảnh lên (Nếu test Image-to-Video):", type=["png", "jpg", "jpeg", "webp"])
    test_img = Image.open(test_file) if test_file else None
    if test_img:
        st.image(test_img, width=220)
        
    test_prompt = st.text_area(
        "Prompt tạo video thử nghiệm:", 
        value="Cinematic slow pan camera movement, luxury product commercial lighting, high detail, 4k"
    )
    
    btn_test = st.button("🚀 Bấm Test Tạo Video Ngay", type="primary")

with col2:
    st.subheader("2. Kết quả phản hồi từ API")
    if btn_test:
        if not muse_key:
            st.error("⚠️ Bạn chưa dán Muse API Key ở cột bên trái!")
        else:
            prefix = "Key" if "Key" in auth_prefix else "Bearer"
            headers = {
                "Authorization": f"{prefix} {muse_key.strip()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": test_prompt,
                "aspect_ratio": "9:16",
                "duration": 5
            }
            if test_img:
                payload["image_url"] = image_to_data_uri(test_img)

            with st.spinner("Đang gửi tín hiệu sang máy chủ Muse..."):
                try:
                    res = requests.post(endpoint_url.strip(), headers=headers, json=payload, timeout=60)
                    st.write(f"**Mã trạng thái (Status Code):** `{res.status_code}`")
                    
                    try:
                        data = res.json()
                    except Exception:
                        data = {"raw_text": res.text}

                    # Hiển thị chi tiết phản hồi để kiểm tra
                    with st.expander("Xem chi tiết dữ liệu máy chủ trả về (JSON)", expanded=True):
                        st.json(data)

                    # Nếu có sẵn link video hoặc mã chờ render
                    video_url = data.get("video_url") or (data.get("video", {}) if isinstance(data.get("video"), dict) else {}).get("url")
                    status_url = data.get("status_url")

                    if video_url:
                        st.success("🎉 Tạo video thành công!")
                        st.video(video_url)
                    elif status_url:
                        st.info("⏳ Máy chủ đã nhận lệnh và đang render video... Tự động kiểm tra tiến trình:")
                        progress_box = st.empty()
                        for i in range(40):
                            time.sleep(5)
                            chk = requests.get(status_url, headers=headers, timeout=30).json()
                            state = str(chk.get("status", "")).upper()
                            progress_box.write(f"Lần kiểm tra {i+1}: Trạng thái = `{state}`")
                            
                            if state in ["COMPLETED", "SUCCEEDED", "SUCCESS"]:
                                res_url = chk.get("response_url")
                                final_data = requests.get(res_url, headers=headers).json() if res_url else chk
                                final_vid = (
                                    final_data.get("video_url") 
                                    or final_data.get("video", {}).get("url")
                                    or final_data.get("output", {}).get("video_url")
                                )
                                if final_vid:
                                    st.success("🎉 Video đã render xong!")
                                    st.video(final_vid)
                                else:
                                    st.json(final_data)
                                break
                            elif state in ["FAILED", "ERROR"]:
                                st.error("Lỗi khi render:")
                                st.json(chk)
                                break
                except Exception as e:
                    st.error(f"❌ Lỗi kết nối: {e}")
