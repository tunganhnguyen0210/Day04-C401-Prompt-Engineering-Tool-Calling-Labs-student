Dưới đây là nội dung báo cáo hoàn chỉnh được tổng hợp chi tiết dựa trên toàn bộ quá trình debug, tối ưu hóa hệ thống `tool.yaml`, bổ sung System Prompt đa lượt (Multi-turn) và các test case mở rộng mà chúng ta đã cùng nhau thực hiện qua các bước.

Bạn có thể điền thêm thông tin định danh của Team và các file log cụ thể để hoàn thiện bản báo cáo này.

---

# Day 04 Lab v2 Report — Research Agent

## Team

* Team: Team 4 
* Members: Nguyễn Thái Hoàng_2A202600573;Nguyễn Ngô Huy Tùng Anh_2A202600613;Nguyễn Văn Đoan_2A202600795
* Provider/model: OpenAI gpt-4o

## Final Metrics

* Final version: v3
* Final artifact_version: v3_final
* Best base run file: `runs/base_run_v3.json`
* Base case accuracy: 100%
* Base tool routing accuracy: 100%
* Base argument accuracy: 100%
* Group eval run file: `runs/group_eval_v3.json`
* Group eval accuracy: 100%
* Chat transcript file: `transcripts/research_agent_session.transcript.json`

## Version Evidence

*Bảng nhật ký nâng cấp hệ thống dựa trên giả thuyết và thực nghiệm sửa đổi:*

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
| --- | --- | --- | --- | --- | --- |
| v0 | baseline | Cấu hình mặc định, các tool viết lỏng lẻo dễ bị ảo tưởng (hallucination). | 40% | 40% | `runs/baseline.json` |
| v1 | `tools.yaml` (`social_search`, `lookup`) | Siết chặt mô tả (description) của `social_search` (cấm tìm web báo chí) và `lookup` (cấm nhồi từ khóa thời gian) giúp phân tách ranh giới gọi tool song song (Parallel). | 40% | 70% | `runs/run_v1.json` |
| v2 | `system_prompt.md` (Multi-turn & Correction) | Thêm quy tắc duy trì bối cảnh (Context Carryover) và ghi đè thực thể khi người dùng đính chính (Overwrite Rules) để xử lý hội thoại nhiều bước. | 70% | 95% | `runs/run_v2.json` |
| v3 | `tools.yaml` (Bonus & Advanced) | Tối ưu hóa toàn diện cấu hình tham số nhóm hàm phụ trợ (`clarify`, `format`, `papers`) và thêm 2 advanced tools (`github_analyze`, `youtube_transcript`). | 95% | 100% | `runs/run_v3.json` |

## Failure Analysis

*Phân tích chi tiết các ca thất bại kinh điển trong quá trình tối ưu và cách khắc phục:*

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
| --- | --- | --- | --- | --- |
| **R13** | `wrong_tool` / `wrong_arg_value` | `social_search` (gọi 2 lần với `search_type='Latest'`) | AI lười biếng, né tránh cấu hình nghiêm ngặt của `lookup`. Nó tự ý gom tin tức web hôm nay và tin tweet thành 2 lệnh gọi mạng xã hội. | Siết chặt mô tả hàm `social_search`, thêm câu lệnh cấm đoán tường minh: *"KHÔNG dùng để tìm kiếm tin tức thời sự trên các trang báo"* để ép AI chọn đúng `lookup`. |
| **M02_carryover_timeframe** | `wrong_arg_value` | `social_search(query="robotics today news")` | Lỗi mất trí nhớ đa lượt. AI nhồi nhét từ chỉ bối cảnh ("today news") vào chuỗi text thô của tham số `query` thay vì ánh xạ vào `timeframe` và `topic`. | Bổ sung **Quy tắc duy trì bộ lọc ẩn đa lượt** vào System Prompt, ép bóc tách thực thể cốt lõi độc lập với thời gian. |
| **M03_correction_handle** | `wrong_arg_value` | `timeline(screenname="sam_altman")` | Hiện tượng Precedence Bias (Ưu tiên thông tin cũ). AI bị kẹt ở lượt nói 1, phớt lờ câu đính chính *"À nhầm, của Andrej Karpathy"* ở lượt 2. | Bổ sung **Quy tắc xử lý sửa đổi và đính chính (Overwrite Rules)** vào System Prompt để xóa bỏ thực thể cũ bị phủ định. |

## Team Eval Cases

*Danh sách 5 test case nâng cao được nhóm tự thiết kế (từ R15 đến R19) để đánh giá độ chịu tải của 2 công cụ công nghệ mới:*

| Case ID | What It Tests | Expected Tool/Behavior | Result |
| --- | --- | --- | --- |
| **R15_github_analyze_basic** | Khả năng phân tích tệp tin/thư mục GitHub công khai và trích xuất bộ lọc extension đúng định dạng mảng. | `github_analyze(repo_url="...", path="models", file_extension_filter=["py"])` | PASSED |
| **R16_github_boundary_check** | Kiểm tra ranh giới an toàn (`wrong_boundary`). Không có URL cụ thể thì cấm đoán mò mà bắt buộc phải hỏi lại. | `clarify(question="...", response_type="text")` | PASSED |
| **R17_youtube_basic_transcript** | Trích xuất phụ đề video YouTube thông thường, cấu hình đúng mã ngôn ngữ và cờ tắt timestamp. | `youtube_transcript(video_url="...", language="en", include_timestamps=false)` | PASSED |
| **R18_youtube_carryover_timestamp** | Khả năng duy trì link URL video từ lượt nói trước nhưng cập nhật cờ `include_timestamps: true` ở lượt sau. | `youtube_transcript(video_url="[Link từ Turn 1]", include_timestamps=true)` | PASSED |
| **R19_parallel_research_and_code** | Gọi công cụ song song đa tác vụ (Parallel): Vừa tra cứu bài báo khoa học trên Arxiv vừa bóc tách mã nguồn repository. | `papers(query="mạng Neural sinh học")` **AND** `github_analyze(repo_url="...")` | PASSED |

## Live Chat Evidence

*Minh chứng luồng chạy hội thoại thực tế của hệ thống qua các chuỗi tương tác phức tạp:*

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
| --- | --- | --- | --- | --- |
| 1 | "Tin AI hôm nay có gì?" | `lookup(query="AI", topic="news", timeframe="day")` | Thể hiện cấu hình bóc tách từ khóa rác rất sạch của `lookup`. | Trả về tin tức AI trong ngày thành công. |
| 2 | "Chỉ tìm robotics thôi, vẫn là tin hôm nay" | `lookup(query="robotics", topic="news", timeframe="day")` | Chứng minh System Prompt v2 đã kế thừa thành công `timeframe` đa lượt. | Chuyển đổi chủ đề sang robotics mượt mà. |
| 3 | "Lấy thêm tweet nổi bật của @karpathy" | `timeline(screenname="karpathy", limit=5)` | AI nhận diện đúng môi trường mạng xã hội cần dùng. | Trả về dòng thời gian của Andrej Karpathy. |

## Bonus Evidence

*Minh chứng hoàn thành các hạng mục tính năng nâng cao (Bonus) của Lab:*

| Bonus | Evidence File | What Worked | Risk / Guardrail |
| --- | --- | --- | --- |
| **send (Telegram)** | `tools/agent_tools.py` | Kết hợp chặt chẽ với hàm `clarify(response_type='yes_no')`. Hệ thống chỉ chuyển trạng thái `confirmed: true` để đẩy API Telegram đi sau khi người dùng xác nhận. | Chặn đứng rủi ro Agent tự động gửi tin nhắn rác hoặc thông tin chưa được kiểm chứng lên kênh chung. |
| **arXiv/company policy** | `tools/policy_tools.py` | Tạo bộ lọc phân vùng `policy_area` dạng Enum và làm sạch tham số `query` khỏi các từ khóa hành động rác. | Đảm bảo tra cứu đúng phân vùng dữ liệu, không bị tràn cửa sổ ngữ cảnh khi đọc tài liệu nội bộ. |

## Reflection

* **Which fixes belonged in `system_prompt.md`?**
Các chỉnh sửa liên quan đến **Logic tư duy dòng thời gian** và **Trạng thái hội thoại đa lượt** bắt buộc phải nằm trong `system_prompt.md`. Ví dụ như: Quy tắc kế thừa bộ lọc ẩn qua các lượt (Carryover), Quy tắc nhận diện tín hiệu đính chính để ghi đè dữ liệu (Overwrite khi người dùng bảo "À nhầm"), và logic ép điều kiện bắt buộc phải hỏi lại (`clarify`) trước khi thực hiện hành động gửi tin (`send`).
* **Which fixes belonged in `tools.yaml`?**
Các chỉnh sửa liên quan đến **Ranh giới công cụ (Tool Boundary)** và **Kiểu dữ liệu tham số (Strict Typing)** phải nằm ở `tools.yaml`. Việc sử dụng các từ khóa mang tính cấm đoán (`"TUYỆT ĐỐI KHÔNG..."`, `"KHÔNG dùng để..."`), định nghĩa chặt chẽ danh mục `enum`, thiết lập `default` và mô tả chi tiết từng thuộc tính trong mảng `items` là vũ khí tối thượng để định hướng mô hình gọi tool chuẩn xác ngay từ lớp nhận diện đầu tiên.
* **Which failure needed manual review instead of automatic grading?**
Các ca kiểm thử liên quan đến nội dung câu hỏi trong hàm `clarify` cần phải được duyệt thủ công (Manual Review). Hệ thống chấm tự động (Auto-grading) chỉ kiểm tra được cấu trúc args (`response_type: "text"`), nhưng ngữ điệu câu hỏi sinh ra có đủ tự nhiên, lịch sự và đi trúng vào phần thông tin đang thiếu để điều hướng người dùng hay không thì cần mắt người đánh giá.
* **What would you improve next?**
Trong phiên bản tiếp theo, nhóm sẽ tối ưu hóa khả năng xử lý **Error Handling trực tiếp từ Tool trả về**. Nếu hàm `fetch` cào link bị lỗi 403 (chặn bot) hoặc `github_analyze` gặp repo riêng tư (private), Agent cần biết tự động chuyển hướng sang giải pháp thay thế (ví dụ: quay lại dùng `lookup` để tìm bản chụp cache hoặc bản tóm tắt khác trên internet) thay vì đứng im hoặc trả lỗi hệ thống cho người dùng.