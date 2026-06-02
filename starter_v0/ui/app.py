from __future__ import annotations

import sys
import os
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

# Đảm bảo thư mục gốc nằm trong sys.path để các import cục bộ hoạt động hoàn hảo
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# pyrefly: ignore [missing-import]
import streamlit as st

# Import các thành phần cốt lõi của agent
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# Nạp cấu hình môi trường (.env)
load_lab_env(ROOT)
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"

# ----------------- HỆ THỐNG GIAO DIỆN PREMIUM (CSS & EFFECTS) -----------------
st.set_page_config(
    page_title="Trợ Lý Nghiên Cứu AI — Antigravity Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nhúng Google Font 'Outfit' và viết CSS tùy chỉnh có hiệu ứng Animation, Gradient & Phát sáng (Glow)
st.markdown("""
<style>
    /* Nhập font chữ Outfit cao cấp từ Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Thiết lập font chữ Outfit cho các thẻ cha cấp cao nhất, để các thẻ con tự kế thừa một cách tự nhiên */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Ép màu tất cả tiêu đề h1, h2, h3, h4, h5, h6 sang màu Trắng Sáng để có độ tương phản tốt nhất */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Làm trong suốt thanh Topbar trắng mặc định của Streamlit */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        backdrop-filter: blur(12px) !important;
    }
    
    /* Tông nền Slate/Space chuyên nghiệp, dễ nhìn, độ tương phản hài hòa */
    .stApp {
        background-color: #0b0f19 !important;
        background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0b0f19 80%) !important;
    }
    
    /* Hiệu ứng Phát sáng nhẹ nhàng cho banner */
    @keyframes pulse-glow {
        0% { 
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.2);
        }
        50% { 
            box-shadow: 0 4px 30px rgba(56, 189, 248, 0.3);
            border-color: rgba(56, 189, 248, 0.4);
        }
        100% { 
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.2);
        }
    }
    
    /* Banner tiêu đề thiết kế mờ ảo Glassmorphism */
    .header-banner {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 2.2rem;
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.25);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        animation: pulse-glow 8s infinite ease-in-out;
    }
    
    .header-title {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #34d399 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800 !important;
        font-size: 2.6rem !important;
        margin: 0 !important;
        letter-spacing: -0.5px !important;
    }
    
    .header-subtitle {
        color: #e2e8f0 !important; /* Tăng độ sáng chữ */
        font-size: 1.1rem !important;
        margin-top: 0.5rem !important;
        font-weight: 400 !important;
    }
    
    /* Điều chỉnh độ tương phản và màu sắc hiển thị của các TABS */
    div[data-testid="stTabs"] button {
        color: #94a3b8 !important; /* Màu xám bạc dễ đọc */
        font-size: 1rem !important;
        font-weight: 500 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stTabs"] button:hover {
        color: #38bdf8 !important; /* Chuyển màu xanh khi di chuột */
    }
    
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    
    /* Thiết kế nhãn phiên bản (Badge Version) */
    .version-badge {
        background: linear-gradient(90deg, #312e81 0%, #1e1b4b 100%) !important;
        color: #c7d2fe !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: 9999px !important;
        font-size: 0.8rem !important;
        font-family: monospace !important;
        border: 1px solid #4338ca !important;
        display: inline-block !important;
        box-shadow: 0 2px 8px rgba(67, 56, 202, 0.3) !important;
    }
    
    /* Sửa đổi toàn bộ Bong Bóng Chat để ép màu chữ trắng sáng cực kỳ dễ đọc */
    div[data-testid="stChatMessage"] {
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
        border-radius: 12px !important;
    }
    
    /* Bong bóng tin nhắn User (Lẻ) */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
    }
    
    /* Bong bóng tin nhắn Assistant (Chẵn) */
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
    }
    
    /* Ép tất cả các văn bản bên trong Bong bóng chat thành màu trắng sáng có độ tương phản cao */
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] li, 
    div[data-testid="stChatMessage"] strong, 
    div[data-testid="stChatMessage"] blockquote {
        color: #f8fafc !important; /* Màu trắng sáng tinh khiết */
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
    }
    
    /* Định hình Khung Accordion/Expander để không bị chìm chữ */
    div[data-testid="stExpander"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 8px !important;
        margin-top: 0.5rem !important;
    }
    
    /* Ép tiêu đề expander thành màu xanh sáng nổi bật */
    div[data-testid="stExpander"] summary {
        color: #38bdf8 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] summary p, div[data-testid="stExpander"] summary span {
        color: #38bdf8 !important;
        font-weight: 600 !important;
    }
    
    /* Ép chữ bên trong nội dung expander thành màu sáng bạc dễ đọc */
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] p, 
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] pre, 
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] code {
        color: #e2e8f0 !important;
    }
    
    /* Thẻ hiển thị Tool Call trong quá trình chạy */
    .round-card {
        background: rgba(30, 41, 59, 0.55) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-left: 5px solid #6366f1 !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .round-card:hover {
        border-color: #38bdf8 !important;
        border-left-color: #38bdf8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.2) !important;
    }
    .round-card span, .round-card p {
        color: #38bdf8 !important;
    }
    
    /* Nút bấm (Button) */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #06b6d4 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.6rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Nền của Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #080c14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Căn chỉnh nhãn Sidebar */
    .stSelectbox label, .stSlider label, .stTextInput label, section[data-testid="stSidebar"] p {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)


# ----------------- CÁC HÀM TRỢ GIÚP -----------------
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@st.cache_data
def get_transcript_label(filename: str) -> str:
    path = TRANSCRIPTS_DIR / filename
    if not path.exists():
        return filename
    try:
        parts = filename.replace(".transcript.json", "").split("_")
        version = parts[0] if parts else "N/A"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        turns = data.get("turns", [])
        created_at_raw = data.get("created_at", "")
        time_str = ""
        if created_at_raw:
            try:
                dt = datetime.fromisoformat(created_at_raw)
                time_str = dt.strftime("%d/%m %H:%M")
            except:
                pass
        if not time_str and len(parts) >= 3:
            ts = parts[2]
            try:
                time_str = f"{ts[6:8]}/{ts[4:6]} {ts[9:11]}:{ts[11:13]}"
            except:
                pass
        if turns:
            first_query = turns[0].get("user", "")
            if len(first_query) > 22:
                first_query = first_query[:22] + "..."
            return f"🕒 {time_str} | [{version.upper()}] \"{first_query}\""
        else:
            return f"🕒 {time_str} | [{version.upper()}] (Trống)"
    except Exception:
        return filename



def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def trim_history(history: list[dict[str, str]], window: int) -> list[dict[str, str]]:
    if window <= 0:
        return []
    return history[-window * 2:]


def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": "unknown_tool", "message": f"Không có mã nguồn thực thi cho công cụ '{call.name}'"},
        }
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def tool_results_message(events: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json.dumps(events, ensure_ascii=False, indent=2, default=str)}\n\n"
            "Chỉ sử dụng những kết quả công cụ này. Nếu người dùng yêu cầu làm bản tin tổng hợp và các item đã sẵn sàng, "
            "hãy gọi công cụ format bản tin. Nếu không, hãy trả lời trực tiếp cho người dùng kèm dẫn nguồn chính xác."
        ),
    }


def assistant_tool_message(response_text: str | None, calls: list[ToolCall]) -> dict[str, str]:
    call_summary = [{"name": call.name, "args": call.args} for call in calls]
    content = response_text or "Tôi đang thực thi các công cụ được yêu cầu."
    return {
        "role": "assistant",
        "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json.dumps(call_summary, ensure_ascii=False, indent=2)}",
    }


# ----------------- VÒNG LẶP GỌI TOOL TRỰC QUAN TIẾNG VIỆT -----------------
def run_model_tool_loop_st(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
) -> dict[str, Any]:
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    # Tạo một placeholder để render động quá trình gọi tool
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        for round_index in range(1, max_tool_rounds + 1):
            st.markdown(f"**🔄 Vòng Thực Thi Thứ {round_index} / {max_tool_rounds}**")
            
            with st.spinner("🤖 Trí tuệ nhân tạo đang suy nghĩ và lập kế hoạch gọi công cụ..."):
                response = provider.complete(working_messages, tools, model=model, temperature=0.0)
            
            calls = response.tool_calls
            round_record: dict[str, Any] = {
                "round": round_index,
                "assistant_text": response.text,
                "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
                "tool_results": [],
            }

            # Nếu không cần gọi thêm tool nào -> dừng vòng lặp và trả câu trả lời văn bản
            if not calls:
                rounds.append(round_record)
                if response.text:
                    st.success("✨ Đã hoàn thành xử lý. Đang tạo câu trả lời cuối cùng...")
                status_placeholder.empty()
                return {
                    "status": "answered",
                    "assistant_text": response.text or "",
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            # Nếu LLM yêu cầu gọi công cụ
            working_messages.append(assistant_tool_message(response.text, calls))
            non_clarification_events: list[dict[str, Any]] = []

            st.warning(f"🔧 Trợ lý AI kích hoạt **{len(calls)}** cuộc gọi công cụ (Tool Call):")
            
            for call in calls:
                # Tạo thẻ Card trực quan cho từng công cụ thực thi
                st.markdown(f"""
                <div class="round-card">
                    <span style="font-weight:700; color:#38bdf8; font-size:1.1rem;">🛠️ Thực thi công cụ: <code>{call.name}</code></span>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔍 Xem chi tiết quá trình chạy `{call.name}`", expanded=True):
                    st.markdown("**1. Tham số đầu vào (Arguments):**")
                    st.json(call.args)
                    
                    with st.spinner(f"Đang chạy '{call.name}' cục bộ (Local execution)..."):
                        event = execute_tool_call(call)
                    
                    st.markdown("**2. Kết quả trả về (Execution Result):**")
                    st.json(event.get("result", {}))
                    
                    round_record["tool_results"].append(event)
                    all_tool_events.append(event)

                    result = event.get("result", {})
                    # Kiểm tra xem có phải công cụ cần hỏi lại/chờ xác nhận từ người dùng không (awaiting_user)
                    if isinstance(result, dict) and result.get("awaiting_user"):
                        question = result.get("question") or call.args.get("question") or "Vui lòng cung cấp thêm thông tin cần thiết."
                        rounds.append(round_record)
                        st.info("⚠️ Hộp thoại làm rõ (Clarify) được kích hoạt. Đang dừng để đợi phản hồi từ người dùng.")
                        status_placeholder.empty()
                        return {
                            "status": "waiting_for_user",
                            "assistant_text": question,
                            "rounds": rounds,
                            "tool_events": all_tool_events,
                        }

                    non_clarification_events.append(event)

            rounds.append(round_record)
            working_messages.append(tool_results_message(non_clarification_events))
            st.divider()

        status_placeholder.empty()
        return {
            "status": "max_tool_rounds",
            "assistant_text": f"Đã dừng sau {max_tool_rounds} vòng thực thi. Đạt giới hạn định mức của lượt này.",
            "rounds": rounds,
            "tool_events": all_tool_events,
        }


# ----------------- LƯU NHẬT KÝ RA DISK (TRANSCRIPT) -----------------
def save_transcript_file(transcript: dict[str, Any], path: Path) -> None:
    transcript["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


# ----------------- XÂY DỰNG GIAO DIỆN CHÍNH -----------------

# Banner tiêu đề trang chủ
st.markdown("""
<div class="header-banner">
    <h1 class="header-title">🔬 Hệ Thống Trợ Lý Nghiên Cứu AI — Antigravity</h1>
    <p class="header-subtitle">Giao diện điều khiển đa lượt (Multi-turn chat) kết hợp trực quan hóa tiến trình gọi công cụ và đánh giá hiệu năng tự động.</p>
</div>
""", unsafe_allow_html=True)

# ----------------- THANH ĐIỀU KHIỂN BÊN HÔNG (SIDEBAR) -----------------
st.sidebar.markdown("<h2 style='text-align: center; color: #38bdf8;'>⚙️ CẤU HÌNH HỆ THỐNG</h2>", unsafe_allow_html=True)

# Chọn Version của sinh viên
version = st.sidebar.selectbox("Phiên bản Prompt & Tools", ["v0", "v1", "v2", "v3"], index=3)

# Đọc file prompt hệ thống và tools.yaml
system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

if system_prompt_path.exists() and tools_path.exists():
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    
    st.sidebar.markdown(f"""
    <div style="background-color: rgba(99, 102, 241, 0.1); border: 1px solid #4338ca; border-radius: 8px; padding: 0.8rem; margin-bottom: 1rem; text-align:center;">
        <span style="color:#a5b4fc; font-weight:bold; font-size:0.85rem;">MÃ PHIÊN BẢN HIỆN TẠI</span><br/>
        <code style="color:#38bdf8; font-size:0.8rem;">{artifact_version.artifact_version}</code>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.error("❌ Không tìm thấy 'system_prompt.md' hoặc 'tools.yaml' trong thư mục artifacts.")
    st.stop()

# Chọn Provider và Model
provider_name = st.sidebar.selectbox("Nhà cung cấp Mô hình (Provider)", ["openrouter", "openai", "anthropic", "gemini"], index=0)
model_override = st.sidebar.text_input("Mô hình tùy chọn (Ghi đè)", placeholder="Để trống nếu dùng mặc định")

# Cấu hình tham số chạy
history_window = st.sidebar.slider("Cửa sổ ngữ cảnh (Số cặp lượt chat)", 1, 10, 5)
max_tool_rounds = st.sidebar.slider("Giới hạn số vòng gọi Tool", 1, 8, 4)

# Khởi tạo dữ liệu hội thoại trong Session State của Streamlit
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.history = []
    st.session_state.chat_history = []
    
    transcript_id = f"{safe_slug(version)}_{safe_slug(provider_name)}_{st.session_state.session_id}"
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    
    st.session_state.transcript_data = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_override or "default",
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#a5b4fc;'>📝 FILE NHẬT KÝ ĐANG GHI:</h3>", unsafe_allow_html=True)
st.sidebar.code(st.session_state.transcript_path.name, language="text")

# Nút Xóa lịch sử hội thoại
if st.sidebar.button("🧹 Tạo cuộc hội thoại mới"):
    st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.history = []
    st.session_state.chat_history = []
    st.session_state.current_loaded_file = None
    transcript_id = f"{safe_slug(version)}_{safe_slug(provider_name)}_{st.session_state.session_id}"
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript_data = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_override or "default",
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.rerun()

# --- LỊCH SỬ CUỘC HỘI THOẠI (PAST CONVERSATIONS LOADER) ---
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#a5b4fc;'>📜 LỊCH SỬ HỘI THOẠI</h3>", unsafe_allow_html=True)

if TRANSCRIPTS_DIR.exists():
    past_files = sorted(list(TRANSCRIPTS_DIR.glob("*.transcript.json")), key=os.path.getmtime, reverse=True)
    if past_files:
        file_options = ["--- Chọn hội thoại cần tải ---"] + [f.name for f in past_files]
        
        def display_label(filename):
            if filename == "--- Chọn hội thoại cần tải ---":
                return "--- 📂 Chọn cuộc hội thoại cũ ---"
            return get_transcript_label(filename)
            
        selected_past = st.sidebar.selectbox("Khôi phục cuộc hội thoại cũ:", file_options, format_func=display_label, key="past_conversations_select")
        
        if selected_past != "--- Chọn hội thoại cần tải ---":
            # Tránh nạp lại liên tục nếu file đã được nạp
            if st.session_state.get("current_loaded_file") != selected_past:
                try:
                    past_path = TRANSCRIPTS_DIR / selected_past
                    with open(past_path, "r", encoding="utf-8") as f:
                        past_data = json.load(f)
                    
                    # Cập nhật Session State
                    st.session_state.session_id = selected_past.split("_")[-1].replace(".transcript.json", "")
                    st.session_state.transcript_path = past_path
                    st.session_state.transcript_data = past_data
                    
                    st.session_state.history = []
                    st.session_state.chat_history = []
                    
                    for turn in past_data.get("turns", []):
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": turn.get("user")
                        })
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": turn.get("assistant_text"),
                            "rounds": turn.get("rounds", [])
                        })
                        st.session_state.history.append({
                            "role": "user",
                            "content": turn.get("user")
                        })
                        st.session_state.history.append({
                            "role": "assistant",
                            "content": turn.get("assistant_text")
                        })
                        
                    st.session_state.current_loaded_file = selected_past
                    st.sidebar.success("⚡ Nạp hội thoại thành công!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Lỗi nạp file: {e}")
    else:
        st.sidebar.info("Chưa có lịch sử hội thoại nào.")
else:
    st.sidebar.info("Thư mục transcripts chưa có.")



# ----------------- TẠO TABS GIAO DIỆN (CHAT - TRANSCRIPT - EVAL) -----------------
tab1, tab2, tab3 = st.tabs([
    "💬 Tương Tác Trực Tiếp (Live Chat)", 
    "🗂️ Duyệt Nhật Ký Hội Thoại (Transcripts)", 
    "📊 Trình Chạy Đánh Giá Hiệu Năng (Eval Launcher)"
])

# ---- TAB 1: KHÔNG GIAN TƯƠNG TÁC CHAT ----
with tab1:
    st.markdown("<h3 style='color:#38bdf8;'>💬 Trò chuyện cùng Trợ lý Nghiên cứu AI</h3>", unsafe_allow_html=True)
    st.markdown("Hãy đặt câu hỏi nghiên cứu, yêu cầu tổng hợp thông tin hoặc xuất bản tin lên Telegram ở khung chat bên dưới.")
    
    # Hiển thị các tin nhắn đã có trong lịch sử trò chuyện trực quan
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Nếu lượt trò chuyện này có ghi nhận quá trình gọi công cụ (tool calls), hiển thị chi tiết
            if "rounds" in msg and msg["rounds"]:
                with st.expander("🔍 Theo vết tiến trình gọi công cụ (Tool Call Trace)", expanded=False):
                    for r in msg["rounds"]:
                        st.markdown(f"**Vòng {r['round']}**")
                        if r["tool_calls"]:
                            st.write("🔧 Công cụ đã gọi:", r["tool_calls"])
                        if r["tool_results"]:
                            st.write("📥 Kết quả trả về:")
                            st.json(r["tool_results"])
                            
    # Khung nhập câu hỏi của người dùng
    user_input = st.chat_input("Nhập yêu cầu nghiên cứu của bạn tại đây...")
    
    if user_input:
        # Hiển thị ngay tin nhắn của User
        with st.chat_message("user"):
            st.markdown(user_input)
        
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Thiết lập tin nhắn gửi cho LLM
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, history_window),
            {"role": "user", "content": user_input},
        ]
        
        turn_index = len(st.session_state.transcript_data["turns"]) + 1
        turn_record = {
            "turn_index": turn_index,
            "started_at": now_iso(),
            "user": user_input,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }
        
        # Gọi vòng lặp Agent và hiển thị các bước gọi tool trực quan
        try:
            provider = make_provider(provider_name)
            selected_model = model_override if model_override else getattr(provider, "default_model", None)
            
            result = run_model_tool_loop_st(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=selected_model,
                max_tool_rounds=max_tool_rounds
            )
            
            turn_record.update(result)
            assistant_text = result["assistant_text"]
            
            # Hiển thị câu trả lời cuối cùng của Assistant
            with st.chat_message("assistant"):
                st.markdown(assistant_text)
                if result.get("rounds"):
                    with st.expander("🔍 Theo vết tiến trình gọi công cụ (Tool Call Trace)", expanded=False):
                        for r in result["rounds"]:
                            st.markdown(f"**Vòng {r['round']}**")
                            if r["tool_calls"]:
                                st.write("🔧 Công cụ đã gọi:", r["tool_calls"])
                            if r["tool_results"]:
                                st.write("📥 Kết quả trả về:")
                                st.json(r["tool_results"])
            
            # Lưu vào Context Ngữ cảnh
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})
            
            # Lưu vào lịch sử chat trực quan
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_text,
                "rounds": result.get("rounds", [])
            })
            
        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {str(exc)}"
            turn_record.update({
                "status": "provider_error",
                "error": err_msg,
            })
            with st.chat_message("assistant"):
                st.error(f"❌ Lỗi nhà cung cấp mô hình (Provider Exception): {err_msg}")
        
        # Lưu kết quả lượt chat ra file transcript
        turn_record["ended_at"] = now_iso()
        st.session_state.transcript_data["turns"].append(turn_record)
        save_transcript_file(st.session_state.transcript_data, st.session_state.transcript_path)


# ---- TAB 2: DUYỆT NHẬT KÝ TRANSCRIPTS (VAI TRÒ C CHỦ ĐẠO) ----
with tab2:
    st.markdown("<h3 style='color:#38bdf8;'>🗂️ Phân tích & Duyệt Nhật Ký Hội Thoại (Transcripts)</h3>", unsafe_allow_html=True)
    st.markdown("Bộ công cụ hỗ trợ Vai trò C rà soát các tệp hội thoại mẫu, kiểm tra thứ tự công cụ được kích hoạt và đảm bảo độ mượt của ngữ cảnh.")
    
    if TRANSCRIPTS_DIR.exists():
        # Lấy danh sách tệp sắp xếp theo thời gian sửa đổi mới nhất
        files = sorted(list(TRANSCRIPTS_DIR.glob("*.transcript.json")), key=os.path.getmtime, reverse=True)
        if files:
            selected_file = st.selectbox("Chọn tệp nhật ký để tiến hành phân tích", [f.name for f in files])
            file_path = TRANSCRIPTS_DIR / selected_file
            
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    st.markdown(f"""
                    <div style="background-color:rgba(52, 211, 153, 0.1); border:1px solid #34d399; border-radius:8px; padding:1rem; margin-bottom:1.5rem;">
                        <span style="color:#a7f3d0; font-weight:bold;">✅ Đã nạp thành công tệp nhật ký:</span> <code>{selected_file}</code>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 📊 Tổng Quan Metadata:")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Nhà cung cấp (Provider)", data.get("provider").upper())
                    col2.metric("Mã Phiên Bản (Artifact)", data.get("artifact_version", "N/A")[:20])
                    col3.metric("Tổng số lượt thoại (Turns)", len(data.get("turns", [])))
                    
                    st.markdown("---")
                    st.markdown("#### 💬 Lịch Sử Chi Tiết Từng Lượt Thoại:")
                    
                    for turn in data.get("turns", []):
                        with st.container():
                            st.markdown(f"**Lượt Tương Tác {turn.get('turn_index')}** (Trạng thái: `{turn.get('status')}` | Thời gian chạy: `{turn.get('started_at')}` -> `{turn.get('ended_at')}`):")
                            st.info(f"🧑 **Người Dùng (User):** {turn.get('user')}")
                            st.success(f"🤖 **Trợ Lý AI (Agent):** {turn.get('assistant_text')}")
                            
                            if turn.get("tool_events"):
                                with st.expander("🛠️ Xem chi tiết các Tool đã thực thi trong lượt này", expanded=False):
                                    for idx, event in enumerate(turn.get("tool_events", [])):
                                        st.markdown(f"🔹 **#{idx+1} — Công cụ: `{event.get('tool')}`**")
                                        st.write("Tham số đầu vào (Arguments):", event.get("args"))
                                        st.markdown("Kết quả thực thi (Result):")
                                        st.json(event.get("result", {}))
                            st.divider()
                except Exception as e:
                    st.error(f"❌ Lỗi định dạng JSON của tệp: {e}")
        else:
            st.info("ℹ️ Thư mục `transcripts/` hiện tại chưa có tệp nhật ký nào. Hãy chat với Agent để tạo tệp nhật ký đầu tiên.")
    else:
        st.info("ℹ️ Chưa có lịch sử hội thoại nào được lưu. Hãy chat với Agent ở Tab 1.")


# ---- TAB 3: TRÌNH CHẠY ĐÁNH GIÁ HIỆU NĂNG TỰ ĐỘNG (EVAL LAUNCHER) ----
with tab3:
    st.markdown("<h3 style='color:#38bdf8;'>📊 Bảng Điều Khiển Chạy Đánh Giá Hiệu Năng Tự Động (Eval Launcher)</h3>", unsafe_allow_html=True)
    st.markdown("Vai trò C có thể dễ dàng chạy bộ đánh giá tự động, đo đạc độ chính xác của định tuyến (Routing) và tham số (Arguments) mà không cần nhập lệnh terminal phức tạp.")
    
    col1, col2 = st.columns(2)
    suite = col1.selectbox("Bộ ca kiểm thử (Suite)", ["base", "group", "extension"])
    eval_cases_file = col2.selectbox("File định nghĩa các ca kiểm thử (.json)", ["eval_base.json", "eval_group.json", "eval_research_extension.json"])
    
    if st.button("🚀 Khởi Chạy Bộ Đánh Giá"):
        # Tự động phát hiện python trong môi trường ảo tùy thuộc vào OS để chạy lệnh chuẩn xác nhất
        python_executable = "python"
        if os.path.exists(".venv\\Scripts\\python.exe"):
            python_executable = ".venv\\Scripts\\python.exe"
        elif os.path.exists(".venv/bin/python"):
            python_executable = ".venv/bin/python"
            
        cmd = f"{python_executable} run_eval.py --provider {provider_name} --version {version} --suite {suite} --eval-cases data/{eval_cases_file}"
        
        st.markdown("**Lệnh thực thi hệ thống:**")
        st.code(cmd, language="bash")
        
        # Thực thi shell command trực quan và xuất log stdout/stderr
        with st.status("🛠️ Đang kết nối shell và thực thi bộ chấm điểm tự động `run_eval.py`...", expanded=True) as status_box:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(ROOT)
            )
            stdout, stderr = proc.communicate()
            status_box.update(label="✅ Thực thi đánh giá hiệu năng thành công!", state="complete")
            
        st.success("🎉 Quá trình chấm điểm hoàn tất!")
        
        if stdout:
            st.markdown("📊 **Kết quả chi tiết (Standard Output):**")
            st.code(stdout.decode("utf-8"))
        if stderr:
            st.markdown("⚠️ **Nhật ký cảnh báo / Sai lệch (Standard Error):**")
            st.code(stderr.decode("utf-8"))
            
        # Tìm file kết quả eval runs mới nhất để trực quan hóa
        if RUNS_DIR.exists():
            runs_files = sorted(list(RUNS_DIR.glob("*.json")), key=os.path.getmtime, reverse=True)
            if runs_files:
                latest_run = runs_files[0]
                try:
                    run_log = json.loads(latest_run.read_text(encoding="utf-8"))
                    st.markdown("### 🏆 Báo Cáo Điểm Số Thực Tế:")
                    summary = run_log.get("summary", {})
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tổng số ca kiểm thử", summary.get("total_cases", 0))
                    c2.metric("Số ca Vượt qua (Pass)", summary.get("passed_cases", 0))
                    
                    accuracy = summary.get("case_accuracy", 0.0)
                    c3.metric("Tỷ lệ Chính xác tổng quát", f"{accuracy * 100:.2f}%")
                    
                    routing_acc = summary.get("tool_routing_accuracy", 0.0)
                    c4.metric("Độ chính xác Định Tuyến (Routing)", f"{routing_acc * 100:.2f}%" if routing_acc is not None else "N/A")
                    
                    st.markdown("**Kết quả phân tích lỗi chi tiết:**")
                    st.json(summary)
                except Exception as e:
                    st.warning(f"Không thể giải mã file kết quả chạy gần nhất: {e}")
