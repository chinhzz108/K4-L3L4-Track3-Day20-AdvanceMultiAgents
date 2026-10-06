# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Trần Trọng Chinh | 2A202602720 | Toàn bộ bài lab (Cài đặt harness, chạy thực nghiệm, curator, báo cáo) |

- Mô hình: `LAB_MODEL=google_genai:gemini-3.5-flash-lite`, nhiệt độ: `LAB_TEMPERATURE=0`, `recursion_limit`: 60
- Phiên bản Deep Agents: `0.7.21`, Windows 11 (win32), chạy trực tiếp trên môi trường ảo Python 3.11 (`.venv`)
- Số lần chạy tác vụ đã dùng / ngân sách: 9 lần chạy (3 baseline learn, 3 subagents learn, 3 skills-auto dev) / ngân sách đánh giá chính thức 12 lần chạy
- Commit của tag `freeze`: Sẽ được cập nhật sau khi gắn tag `freeze`

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
