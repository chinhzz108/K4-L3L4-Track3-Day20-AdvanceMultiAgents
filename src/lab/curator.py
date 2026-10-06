"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    out_dir = Path(out_dir)

    source_path = Path(results_dir) / source_condition
    runs = []

    for run_file in sorted(source_path.glob("*/run.json")):
        try:
            r = json.loads(run_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if r.get("role") != "learn":
            continue

        failed = [
            (c.get("name"), c.get("detail", ""))
            for c in r.get("checks", [])
            if not c.get("passed")
        ]

        if not failed:
            continue

        trace_file = run_file.parent / "trace.md"
        trace_text = ""
        if trace_file.exists():
            try:
                trace_text = trace_file.read_text(encoding="utf-8")[-6000:]
            except Exception:
                trace_text = ""

        runs.append({
            "task": r.get("task", run_file.parent.name),
            "failed": failed,
            "trace": trace_text,
        })

    if not runs:
        print("Warning: no failed checks found in learning task runs.")
        return []

    runs_blocks = []
    for run in runs:
        checks_text = "\n".join(f"- Check: {name} | Feedback: {detail}" for name, detail in run["failed"])
        block = f"### Task: {run['task']}\nFailed Checks and Evaluator Feedback:\n{checks_text}\n"
        if run["trace"]:
            block += f"\nRecent Execution Trace:\n```\n{run['trace']}\n```\n"
        runs_blocks.append(block)

    runs_summary = "\n\n".join(runs_blocks)

    prompt = (
        f"You write reusable engineering and data analysis SKILLS for an autonomous agent.\n"
        f"Below are the failed checks (check names and evaluator feedback notes) and execution traces "
        f"from previous runs on learning tasks.\n"
        f"Identify common procedural mistakes (NOT specific answers or hardcoded numbers) and write up to {max_skills} concise skills "
        f"that help prevent these mistakes on new tasks of the same type.\n\n"
        f"Rules:\n"
        f"- Skills must be general: do not mention specific task IDs, specific one-off filenames, or hardcoded answers/numbers.\n"
        f"- Each skill must have YAML frontmatter with `name` (lowercase alphanumeric and hyphens only, max 64 chars) "
        f"and `description` (one concise sentence stating WHEN to use this skill, max 1024 chars), "
        f"followed by max 40 lines of clear imperative checklist items.\n"
        f"- Output format must strictly follow:\n"
        f"=== SKILL: <name> ===\n"
        f"---\n"
        f"name: <name>\n"
        f"description: <when to use>\n"
        f"---\n"
        f"<body instructions in markdown>\n"
        f"=== END ===\n\n"
        f"{runs_summary}\n"
    )

    if model is None:
        model = make_model()

    response = model.invoke(prompt)
    if hasattr(response, "content"):
        if isinstance(response.content, str):
            reply_content = response.content
        elif isinstance(response.content, list):
            reply_content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in response.content
            )
        else:
            reply_content = str(response.content)
    else:
        reply_content = str(response)

    blocks = parse_skill_blocks(reply_content)
    written = []

    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(text + "\n", encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
