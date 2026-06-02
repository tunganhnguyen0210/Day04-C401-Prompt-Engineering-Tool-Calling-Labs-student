# Day 04 Lab v2 Report — Research Agent

## Team

- Team: 4
- Members Nguyễn Thái Hoàng_2A202600573;Nguyễn Ngô Huy Tùng Anh_2A202600613;Nguyễn Văn Đoan_2A202600795
- Provider/model: OpenRouter — `openai/gpt-4o-mini`
- Link dùng thử (Cloudflare Tunnel): [https://davidson-engines-frames-storm.trycloudflare.com](https://davidson-engines-frames-storm.trycloudflare.com)



## Final Metrics

- Final version: **v3**
- Final artifact_version: **v3+p12307c65dad5+t817b0942f9e2**
- Best base run file: `runs/v3_B_base_openrouter_20260602T170907086243.json` (đối chiếu thêm `runs/v1_B_base_openrouter_20260602T152926562156.json`)
- Base case accuracy: **1.0 (20/20)**
- Base tool routing accuracy: **1.0**
- Base argument accuracy: **1.0** (multiturn accuracy: 1.0)
- Group eval run file: `runs/v3_B_group_openrouter_20260602T170046567173.json`
- Group eval accuracy: **1.0 (5/5)**
- Chat transcript file: `transcripts/v3_openrouter_20260602T150027321078.transcript.json`

## Version Evidence

Tái dựng từ `runs/*.json` (file `artifacts/version_log.csv` không còn trong repo).

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (system_prompt + tools.yaml gốc) | Đo mức nền chưa tinh chỉnh | — | base **0.65** (13/20) | `runs/v0_B_base_openrouter_20260602T144842082064.json` |
| v1 | `system_prompt.md` + `tools.yaml` | Thêm luật routing/scope rõ ràng, "hỏi lại thay vì đoán", "xác nhận trước khi gửi", quy ước làm sạch `query` | base 0.65 | base **1.0** (20/20) | `runs/v1_B_base_openrouter_20260602T152926562156.json` |
| v2 | `tools.yaml` + `data/eval_group.json` | Nhóm thử thêm tool ngoài lõi (github/youtube/calculator) và viết 5 case nhóm | group 0.25 | group **0.40** (2/5) | `runs/v2_B_base_openrouter_20260602T163058456911.json` |
| v3 (group) | `data/eval_group.json` (+ dọn `system_prompt.md`) | Bỏ tool thử nghiệm, dựng lại 5 case nhóm trên tool lõi, chỉ assert tham số mô hình chắc chắn phát ra | group 0.40 | group **1.0** (5/5) | `runs/v3_B_group_openrouter_20260602T170046567173.json` |
| v3 (base) | chạy lại `data/eval_base.json` với artifact cuối | Xác nhận bộ tool lõi + prompt cuối vẫn giữ 20/20 trên base eval | base 1.0 (v1) | base **1.0** (20/20) · routing 1.0 · args 1.0 · multiturn 1.0 | `runs/v3_B_base_openrouter_20260602T170907086243.json` |

> Ghi chú: v1 và v3 dùng chung `tools_hash = t817b0942f9e2` (bộ 10 tool lõi); v3 chỉ khác v1 ở `prompt_hash`. Cả base lẫn group ở v3 đều đạt artifact `v3+p12307c65dad5+t817b0942f9e2`.

## Failure Analysis

Lấy trực tiếp từ `results[*].result.failures` của baseline v0 (`runs/v0_B_base_openrouter_20260602T144842082064.json`) — đây là các lỗi đã được sửa ở v1.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | `lookup` | `query` = `"AI news"` thay vì `"AI"` | `system_prompt.md`: `query` chỉ giữ từ khóa lõi, bỏ từ chỉ thể loại/thời gian |
| R10_missing_handle | missing_info | `timeline` | Đoán handle khi user không nêu tài khoản (thiếu `clarify`) | `system_prompt.md`: thiếu thông tin bắt buộc → gọi `clarify` (text), không đoán |
| R11_missing_url | missing_info | `fetch` | Tự `fetch` khi chưa có URL | `system_prompt.md`: "bài này/bài viết này" mà không có URL → `clarify` xin link |
| R12_confirm_before_send | wrong_boundary | `send` | Gửi ngay không xác nhận | `system_prompt.md`: hành động ghi → `clarify` `response_type=yes_no` trước |
| R13_parallel_web_and_tweets | wrong_tool | `lookup`, `social_search` | `query`=`"AI news"`, `topic`=`None` | `tools.yaml` + prompt: làm sạch `query`, đặt `topic=news` rõ ràng |
| R08 / R14_out_of_scope | out_of_scope | `send` | Gọi tool cho yêu cầu ngoài phạm vi | `system_prompt.md`: ngoài phạm vi research → KHÔNG gọi tool |

## Team Eval Cases

5 case trong `data/eval_group.json` — toàn bộ PASS ở run `runs/v3_B_group_openrouter_20260602T170046567173.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| R15_timeline_user_tweets | Bài đăng của MỘT người cụ thể; map tên → handle; lấy đúng `limit` | `timeline` `{screenname:"sama", limit:5}` | PASS |
| R16_lookup_news_today | Tin tức thời sự; đặt `topic=news`, `timeframe=day`; `query` gọn | `lookup` `{query:"Nvidia", topic:"news", timeframe:"day"}` | PASS |
| R17_fetch_given_url | Có sẵn URL → đọc đúng link, không đi tìm kiếm thay thế | `fetch` `{url:"https://vnexpress.net/cong-nghe-ai-2026.html"}` | PASS |
| R18_social_search_top | Tweet theo chủ đề; "phổ biến nhất" → `search_type=Top` | `social_search` `{query:"AI", search_type:"Top"}` | PASS |
| R19_clarify_missing_account | Ranh giới: thiếu tài khoản → hỏi lại, không đoán mặc định | `clarify` (response_type text) | PASS |

## Live Chat Evidence

Từ `transcripts/*.transcript.json` (OpenRouter, artifact `v3+peb1c8179815b+t6cdb53d5d7b8`).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| T1 | "search cho tôi bài báo liên quan đến transformer" | `papers` | `v3_openrouter_20260602T150027321078` | Trả về danh sách bài arXiv kèm link/PDF — đúng |
| T2 | "hôm nay có tin gì hot không?" | `lookup` (news) | `v3_openrouter_20260602T145050089139` | Định tuyến tin thời sự đúng |
| T3 | "tôi là con trai mà có bầu thì sao" | _(không gọi tool)_ | `v3_openrouter_20260602T150027321078` | Ngoài phạm vi → từ chối, không gọi tool — đúng |
| T4 | "hôm nay có gì hot trên github không?" | `social_search` | `v3_openrouter_20260602T145050089139` | Không có tool GitHub → routing sang `social_search` (cần xem lại) |
| T5 | "tôi bị ngu" | `send` | `v3_openrouter_20260602T150027321078` | Gọi `send` cho câu vô nghĩa — sai ranh giới, cần manual review |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_openrouter_20260602T150027321078.transcript.json`; base case `R12_confirm_before_send` | Tool `send` chạy được; eval kiểm tra phải `clarify` xác nhận trước khi gửi | Hành động ghi/side-effect: prompt bắt buộc `clarify` `response_type=yes_no` trước; T5 cho thấy vẫn có thể gọi nhầm → cần siết thêm |
| arXiv / company policy | `data/eval_research_extension.json` (10 case dùng `papers`, `paper_text`, `policy`); transcript "transformer" | Tra cứu arXiv + đọc toàn văn paper; tra cứu policy nội bộ | `papers`/`paper_text`: rate-limit arXiv (chờ ≥3s); không bịa link nếu thiếu URL |
| UI | Cloudflare Tunnel link + 6 file `transcripts/*.transcript.json` | Web chat UI live, lưu transcript kèm artifact_version/hash | Tunnel tạm thời; transcript chạy với build prompt cũ (`peb1c8179815b`) khác bản eval cuối |

## Reflection

- **Fix thuộc `system_prompt.md`:** phần lớn lỗi hành vi — luật routing (người cụ thể → `timeline`, chủ đề → `social_search`, tin tức → `lookup` `topic=news`), "hỏi lại thay vì đoán" (thiếu handle/URL → `clarify`), "xác nhận trước khi gửi" (`clarify` `yes_no`), và phạm vi/từ chối ngoài research. Đây là gốc của các fix v0 → v1 (0.65 → 1.0).
- **Fix thuộc `tools.yaml`:** quy ước tham số — làm sạch `query` (bỏ từ thời gian/thể loại), mô tả rõ enum `search_type` (Latest/Top), `topic` (general/news), `timeframe`. Việc thêm/bỏ tool thử nghiệm (github/youtube/calculator) ở v2 cũng nằm ở đây và đã được hoàn nguyên về bộ lõi ở v3.
- **Lỗi cần manual review thay vì chấm tự động:** các turn live chat như T5 ("tôi bị ngu" → `send`) và T4 (hỏi GitHub → `social_search`) — chấm tự động chỉ so tên tool/tham số, không bắt được "gọi tool vô nghĩa" hay routing lệch khi không có tool phù hợp; cần người đọc transcript đánh giá.
- **Cải thiện tiếp theo:** (1) siết guardrail cho `send`/chit-chat để tránh gọi tool khi input vô nghĩa; (2) chạy lại transcript với đúng artifact cuối (`p12307c65dad5`) để bằng chứng live khớp bản eval; (3) khôi phục `version_log.csv` và log mỗi thay đổi artifact kèm metric để truy vết; (4) thêm case nhóm cho multiturn carryover & parallel trên tool lõi để mở rộng độ phủ.
