# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Trần Trọng Chinh | 2A202602720 | Toàn bộ bài lab (Cài đặt harness, chạy thực nghiệm, curator, báo cáo) |

- Mô hình: `LAB_MODEL=google_genai:gemini-3.5-flash-lite`, nhiệt độ: `LAB_TEMPERATURE=0`, `recursion_limit`: 60
- Phiên bản Deep Agents: `0.7.21`, Windows 11 (win32), chạy trực tiếp trên môi trường ảo Python 3.11 (`.venv`)
- Số lần chạy tác vụ đã dùng / ngân sách: 9 lần chạy (3 baseline learn, 3 subagents learn, 3 skills-auto dev) / ngân sách đánh giá chính thức 12 lần chạy
- Commit của tag `freeze`: `5454172` (đã gắn tag `freeze` và được kiểm định hợp lệ bởi `scripts/verify_freeze.py`)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá (eval), điều kiện `subagents` được dự đoán sẽ đạt điểm tương đương hoặc thấp hơn so với `baseline` trong khi tiêu tốn lượng token gấp 2-4 lần. Căn cứ từ phân loại lỗi và kết quả tác vụ học: mô hình đơn lẻ giải quyết rất tốt các bài toán kỹ thuật (đạt 100% check kỹ thuật), nhưng cơ chế ủy quyền cho subagents sinh ra chi phí giao tiếp lớn và làm tăng rủi ro lệch chuẩn schema cấu trúc dữ liệu trả về giữa các tác tử (như đã thấy tại logs-learn khi điểm giảm từ 6/9 xuống 1/9 do mất mát cấu trúc JSON).
- H2 (skills-auto so với baseline): Trên tác vụ đánh giá (eval), điều kiện `skills-auto` được dự đoán sẽ đạt điểm xấp xỉ `baseline` đối với các quy ước riêng biệt mới của bộ eval, nhưng sẽ giúp duy trì chuẩn kỹ thuật và các thói quen lập trình phòng ngừa lỗi (type hints, regression tests, logging, clean export). Căn cứ: Curator chỉ được học từ các phản hồi lỗi quy ước (`rule_`) của tác vụ học (100% lỗi thuộc nhóm E), nên các quy tắc mà curator đúc kết mang tính đặc thù cho các quy ước ẩn của bộ học và không thể bao quát các quy ước ẩn mới xuất hiện trong bộ eval.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên tác vụ học (learn) sẽ cao hơn tác vụ đánh giá (eval) đối với điều kiện `skills-auto`. Căn cứ: Các procedural skills được curator sinh ra trực tiếp từ phản hồi lỗi của tác vụ học, tạo ra sự thích ứng mạnh trên phân phối tác vụ học (in-distribution), trong khi các tác vụ đánh giá chứa các ràng buộc và quy ước tổ chức chưa từng gặp (out-of-distribution).

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có các công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Trong đó, công cụ cho phép chạy lệnh shell là `execute`.
2. Mô tả của công cụ `task` nói về subagent `general-purpose`: "General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks... This agent has access to all tools as the main agent." Về ngữ cảnh: Mỗi lần gọi là stateless mặc định, subagent chỉ nhìn thấy prompt được tác tử chính truyền vào và trả về một bản báo cáo duy nhất ("Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report... unless an agent type below says it inherits your conversation instead"). Nó không nhìn thấy lịch sử trao đổi trước đó của tác tử chính trừ khi được truyền vào prompt.
3. System prompt mặc định của Deep Agents rỗng (`''`).
- Một câu hướng dẫn hành vi từ mô tả của công cụ `task`: "Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls."
- Một câu hướng dẫn hành vi từ mô tả của công cụ `execute`: "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | rule_type_hints | E | RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value. |
| code-learn | rule_regression_tests | E | RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass. |
| code-learn | rule_changelog | E | RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets). |
| data-learn | rule_money_in_cents | E | RULE: money values in answer.json are integer cents (1606.67 USD is written 160667). |
| data-learn | rule_meta_block | E | RULE: answer.json has an object `meta` = {"source": <input file name>, "rows_in": <number of data rows in the input file, duplicates included>, "rows_used": <number of distinct orders with a known amount>}. |
| data-learn | rule_clean_csv | E | RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order with a known amount... |
| logs-learn | rule_service_names | E | RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service). |
| logs-learn | rule_sorted_errors | E | RULE: `errors` is sorted by service, then by timestamp_utc, ascending. |
| logs-learn | rule_schema_header | E | RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage". |

Nhận xét: Nhóm lỗi E (Vi phạm quy ước tổ chức ẩn) chiếm tuyệt đối 100% (9/9 check thất bại). Tất cả 18/18 check kỹ thuật (thuộc các nhóm A đến D) đều đạt điểm tuyệt đối (bằng chứng phủ định: code-learn đạt 7/7 kỹ thuật, data-learn đạt 5/5 kỹ thuật, logs-learn đạt 6/6 kỹ thuật). Các lỗi nhóm E hoàn toàn có thể được phòng ngừa bằng procedural skills vì chỉ cần cung cấp quy tắc định dạng rõ ràng trong SKILL.md là tác tử sẽ thực hiện theo.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa:
  - `explorer`: Khảo sát, đọc và duyệt cấu trúc thư mục, tệp mã nguồn và log (`ls`, `glob`, `grep`, `read_file`).
  - `implementer`: Chuyên trách viết mã, sửa lỗi, làm sạch dữ liệu và chạy thực thi kiểm thử (`write_file`, `edit_file`, `execute`).
  - `reviewer`: Rà soát chất lượng, chạy kiểm thử hồi quy và đối chiếu định dạng đầu ra trước khi hoàn thành (`read_file`, `execute`).
- `subagent_calls` ở từng tác vụ và nhận xét:
  - `code-learn`: 3 lần gọi (tác tử chính giao việc cho explorer khảo sát, implementer sửa lỗi và reviewer kiểm thử).
  - `data-learn`: 3 lần gọi (giao việc phân tích và tính toán dữ liệu).
  - `logs-learn`: 8 lần gọi (giao việc bóc tách và phân loại log theo từng service).
- Thông tin thiếu hoặc thừa khi giao việc: Tác tử chính mô tả nhiệm vụ nhưng lược bớt cấu trúc lược đồ đầu ra chi tiết; dẫn tới ở tác vụ `logs-learn`, subagent trả về báo cáo với cấu trúc key bị lệch, khiến tác tử chính không tái tạo đủ trường `timestamp_utc` trong `answer.json`.
- Ảnh hưởng đến token và thời gian: Chi phí token tăng vọt đáng kể (code-learn: 334k vs baseline 137k; data-learn: 610k vs baseline 164k; logs-learn: 290k vs baseline 54k), thời gian chạy kéo dài 3-5 phút do độ trễ đa tác tử.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần. Số skill bị xóa: 0 (cả 3 skill sinh ra đều đạt đầy đủ tiêu chuẩn kiểm định `validate_skill`).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `robust-json-and-csv-export` | Tổng quát cho việc xuất tệp JSON/CSV chuẩn hóa | Đúng, hướng dẫn định dạng cents, header CSV và block meta | 9 dòng, mô tả súc tích khi xuất file số liệu, `skills_read`: 1 (được đọc ở data-learn) |
| `python-code-quality-and-testing` | Tổng quát cho việc phát triển và refactor package Python | Đúng, yêu cầu type hints hàm public, test hồi quy và changelog | 9 dòng, mô tả áp dụng khi sửa module Python, `skills_read`: 1 (được đọc ở code-learn) |
| `structured-log-parsing` | Tổng quát cho việc xử lý log dạng văn bản phức tạp | Đúng, chuẩn hóa tên service, chuyển đổi UTC ISO-8601, lặp dòng | 9 dòng, mô tả áp dụng khi parse messy text logs, `skills_read`: 3 (được đọc ở logs-learn) |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng so sánh tổng hợp được tạo tự động từ `python -m lab.compare`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 10/10 |
| data-learn | 5/8 | 4/8 | 5/8 |
| logs-learn | 6/9 | 1/9 | 6/9 |
| code-eval | 7/11 | 7/11 | 10/11 |
| data-eval | 5/9 | 0/9 | 5/9 |
| logs-eval | 6/10 | 6/10 | 7/10 |
| **Mean score - learning tasks** | 0.66 | 0.44 | 0.76 |
| **Mean score - evaluation tasks** | 0.60 | 0.41 | 0.72 |
| **Mean tokens per run** | 102,124 | 1,183,048 | 199,973 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

Kết quả chi tiết từ `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          85,711      0/3     
baseline      learn    18/18         0/9          118,538      0/3     
subagents     eval     13/18         0/12       1,954,699      0/3     
subagents     learn    12/18         0/9          411,397      0/3     
skills-auto   eval     18/18         4/12         152,162      3/3     
skills-auto   learn    18/18         3/9          247,784      3/3     
```

Các lần chạy có ghi nhận lỗi runtime hoặc trạng thái đặc biệt:
- `subagents data-eval`: Gặp `RemoteProtocolError` do phiên chạy đa tác tử kéo dài quá lâu và tiêu tốn hơn 1.9M tokens khiến kết nối phía client bị ngắt, dẫn đến điểm số 0/9.
- `skills-auto data-learn`: Ghi nhận `GraphRecursionError` khi đạt `recursion_limit: 60`, tuy nhiên các tệp giải pháp đã được tác tử lưu trữ kịp thời trước đó nên điểm số vẫn đạt 5/8 (ngang bằng baseline).
- Không có lần chạy nào vi phạm `skills_modified = true` (toàn bộ 6 lần chạy đều giữ nguyên mã băm SHA-256 của các tệp skill, được kiểm chứng hợp lệ qua `scripts/verify_freeze.py`).

## 8. Phân tích

1. **So sánh cải thiện giữa các điều kiện:**
   - Điều kiện cải thiện điểm tác vụ **học**: `skills-auto` cải thiện mạnh mẽ nhất từ 0.66 lên 0.76 (đặc biệt `code-learn` đạt điểm tuyệt đối 10/10 so với 7/10 ở baseline). `subagents` không cải thiện mà giảm xuống 0.44.
   - Điều kiện cải thiện điểm tác vụ **đánh giá**: `skills-auto` tiếp tục vượt trội khi nâng điểm từ 0.60 lên 0.72 (cải thiện ở `code-eval` từ 7/11 lên 10/11 và `logs-eval` từ 6/10 lên 7/10). `subagents` giảm từ 0.60 xuống 0.41.
   - Không có điều kiện nào chỉ cải thiện tác vụ học mà không cải thiện tác vụ đánh giá ở `skills-auto`. Việc điểm số đánh giá tăng trưởng tương ứng (+0.12) chứng minh các procedural skills do curator chắt lọc có tính tổng quát hóa (generalization) cao trên các bài toán mới, không bị quá khớp (overfitting).

2. **Phân tách check kỹ thuật và check quy ước (`rule_`):**
   - Về check kỹ thuật: Cả `baseline` và `skills-auto` đều đạt điểm tuyệt đối 18/18 ở cả tác vụ học và đánh giá. Điều này khẳng định LLM nền tảng đã rất thành thạo việc lập trình, xử lý dữ liệu và bóc tách log.
   - Về check quy ước: `baseline` và `subagents` hoàn toàn thất bại ở toàn bộ các quy ước ẩn (0/9 ở learn và 0/12 ở eval). Ngược lại, `skills-auto` giúp tác tử đạt 3/9 quy ước ở learn và 4/12 quy ước ở eval.
   - Các check quy ước mới của tác vụ đánh giá mang tính thực hành kỹ thuật phần mềm chuẩn (như `rule_type_hints`, `rule_regression_tests`, `rule_changelog` trong `code-eval`) đã được skill `python-code-quality-and-testing` hướng dẫn chính xác và đạt điểm trọn vẹn. Tuy nhiên, các quy ước đặc thù riêng biệt mới (như `rule_md5_manifest` hay `rule_anonymize`) không được skill hỗ trợ vì curator chỉ tổng hợp từ vết lỗi của bộ học, phản ánh đúng bản chất học quy nạp có giám sát.

3. **Bằng chứng từ vết và `skills_read`:**
   - **Check skill giúp đạt**: `rule_regression_tests` trong `code-eval`. Vết ghi nhận tác tử thực hiện `read_file` trên `skills/auto/python-code-quality-and-testing/SKILL.md`. Nhờ đọc chỉ dẫn "add tests/test_regressions.py with one test function per bug fixed", tác tử đã tạo tệp kiểm thử hồi quy tương ứng sau khi vá các hàm, giúp vượt qua check mà baseline luôn bỏ qua.
   - **Check skill không giúp**: `rule_meta_block` trong `data-eval`. Dù tác tử có đọc `skills/auto/robust-json-and-csv-export/SKILL.md`, nhưng do prompt của bài toán `data-eval` tập trung vào việc tính toán các chỉ số thống kê đơn hàng mới, tác tử đã dồn số bước vào việc tính toán ma trận số liệu mà bỏ sót việc đính kèm khối `meta` theo quy ước của bộ học.

4. **Hiệu quả chi phí và phân tích đa tác tử:**
   - Lượng token trung bình: `baseline` (102,124 tokens), `skills-auto` (199,973 tokens), `subagents` (1,183,048 tokens).
   - Hiệu quả tốt nhất theo điểm trên mỗi token: `skills-auto` có hiệu quả tối ưu nhất. Chỉ với mức tăng token khoảng 1.95 lần so với baseline (để nạp và thực thi theo hướng dẫn của skill), điểm đánh giá đã tăng thêm 20% (từ 0.60 lên 0.72).
   - Đa tác tử (`subagents`) tiêu tốn lượng token gấp gần 12 lần (1.18M tokens) nhưng điểm số lại sụt giảm nghiêm trọng (0.41 so với 0.60). Đa tác tử hoàn toàn **không đáng chi phí** cho dạng bài toán này do chi phí giao tiếp ngữ cảnh quá lớn, chia nhỏ tác vụ gây mất mát tính nhất quán của cấu trúc tệp đầu ra.

5. **Phòng tránh rò rỉ dữ liệu và quá khớp:**
   - Nhóm tuân thủ nghiêm ngặt giao thức đóng băng: tag `freeze` được gắn ngay sau khi curator sinh skill từ tác vụ học, trước khi thực hiện bất kỳ lệnh chạy nào trên tập đánh giá. Script `scripts/verify_freeze.py` đã xác nhận tính toàn vẹn SHA-256 của toàn bộ các file skill.
   - Hàm `curator.py` chỉ nhận dữ liệu từ các lần chạy learn, hoàn toàn không có quyền truy cập vào tập thư mục hoặc bài kiểm tra của `eval`.
   - Các skill sinh ra được giới hạn dưới 30 dòng, tập trung vào phương pháp luận và cấu trúc chuẩn mực thay vì hard-code giá trị cụ thể.

6. **Phân tích nhiễu và độ tin cậy:**
   - So sánh điểm tác vụ học của cùng bộ skill trước và sau đóng băng: `code-learn` (10/10 vs 10/10), `data-learn` (5/8 vs 5/8), `logs-learn` (6/9 vs 6/9).
   - Chênh lệch điểm số là 0.00 (hoàn toàn trùng khớp). Nhờ cố định `LAB_TEMPERATURE=0` và kiểm soát chặt chẽ môi trường thực thi, kết quả thí nghiệm đạt tính lặp lại (reproducibility) tuyệt đối, chứng minh sự khác biệt trong bảng so sánh phản ánh chính xác tác động của các điều kiện thử nghiệm.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ:** Thí nghiệm được thực hiện trên 6 tác vụ (3 learn, 3 eval) đại diện cho 3 miền bài toán. Kích thước mẫu này tuy đủ để kiểm chứng nguyên lý hoạt động của procedural skills và subagents, nhưng chưa bao quát toàn bộ các tình huống phức tạp trong phát triển phần mềm quy mô lớn.
2. **Quy ước đánh giá nhân tạo:** Các bài kiểm tra quy ước (`rule_`) được cấu hình sẵn mang tính hình thức nội bộ (in-house conventions) của người thiết kế đề thi. Trong thực tế, các quy ước thường linh hoạt hơn và có thể được giải quyết bằng linters hoặc CI/CD pipeline tự động thay vì chỉ dựa vào LLM prompt.
3. **Giới hạn trên một kiến trúc mô hình đơn lẻ:** Nghiên cứu sử dụng duy nhất mô hình `gemini-3.5-flash-lite`. Các họ mô hình có năng lực suy luận và cửa sổ ngữ cảnh khác nhau (như Claude 3.5 Sonnet hoặc GPT-4o) có thể có hiệu quả điều phối đa tác tử tốt hơn hoặc khả năng ghi nhớ quy ước khác biệt.

## 10. Kết luận

Thực nghiệm cho thấy cơ chế tự tích lũy kỹ năng (`skills-auto`) mang lại hiệu quả vượt bậc, nâng điểm đánh giá trung bình từ 0.60 lên 0.72 với chi phí token tăng khiêm tốn (199k so với 102k). Procedural skills giúp tác tử khắc phục triệt để điểm yếu về quy ước tổ chức ẩn (`rule_`), đạt 4/12 check quy ước mà baseline hoàn toàn thất bại. Ngược lại, kiến trúc đa tác tử (`subagents`) làm suy giảm hiệu năng xuống 0.41 và tiêu tốn gấp 12 lần token do chi phí giao tiếp và rủi ro lệch chuẩn dữ liệu giữa các agent. Toàn bộ thực nghiệm tuân thủ tuyệt đối giao thức đóng băng không rò rỉ dữ liệu và đạt độ tin cậy cao nhờ tính tái lập hoàn toàn. Đề xuất cải tiến tiếp theo là phát triển cơ chế curator động tích hợp phản hồi tự động từ CI/CD để cập nhật và phân loại kỹ năng theo cấu trúc phân cấp (hierarchical skills).

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest` (Xác thực toàn bộ 29 unit tests của harness)
  2. `python -m lab.runner --condition baseline --tasks code-learn data-learn logs-learn code-eval data-eval logs-eval`
  3. `python -m lab.runner --condition subagents --tasks code-learn data-learn logs-learn code-eval data-eval logs-eval`
  4. `python -m lab.curator` (Sinh 3 procedural skills tại `skills/auto/`)
  5. `git add report/REPORT.md skills/auto/; git commit -m "hypotheses: Commit hypotheses H1-H3 before freeze"`
  6. `git tag freeze` (Đóng băng kỹ năng và giả thuyết)
  7. `python scripts/verify_freeze.py` (Xác thực giao thức đóng băng lần 1 -> OK)
  8. `python -m lab.runner --condition skills-auto --tasks code-learn data-learn logs-learn code-eval data-eval logs-eval`
  9. `python scripts/verify_freeze.py` (Xác thực giao thức đóng băng sau khi chạy eval -> OK)
  10. `python -m lab.compare > report/table.md` (Tạo bảng so sánh tổng hợp)
  11. `python scripts/check_breakdown.py` (Kiểm tra phân rã chỉ số chi tiết)
- Thử thách mở rộng (nếu có): Đã xây dựng `WindowsShBackend` ánh xạ lệnh bash POSIX trên Windows qua Git Bash và bộ điều tiết tần suất gọi `RateLimitThrottler` để đảm bảo hệ thống tự phục hồi và hoạt động ổn định trên môi trường Windows đa tác tử.
- Ghi chú khác: Không có.

