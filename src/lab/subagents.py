"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when you need to inspect files, understand workspace code structure, read README or docstrings, "
                "or examine data schemas and error logs before making modifications. Reports factual findings."
            ),
            "system_prompt": (
                "You are an exploratory subagent. Your role is to examine files, search code or data, inspect error traces, "
                "and report factual findings accurately without modifying or deleting any files. "
                "Report exact file paths, line numbers, and concise summaries."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when you need to write or edit code or data files, run scripts, execute tests, and implement required changes."
            ),
            "system_prompt": (
                "You are an implementation subagent. Your role is to make precise edits, create or update files, "
                "and execute commands or tests to verify your implementation. Report your changes and test outcomes clearly."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use when you need an independent verification of task requirements, test pass/fail status, edge cases, "
                "and output format before finishing. Does not modify files."
            ),
            "system_prompt": (
                "You are a review and verification subagent. Your role is to verify that all task requirements are satisfied, "
                "check file outputs, validate format and edge cases, and run tests to report any discrepancies without editing files."
            ),
        },
    ]
