"""
app/generation/calculation_formatter.py

Chuyển CalculationOutput (metrics.py) + operands (OperandDetail) thành
markdown hiển thị trên Streamlit, giống mẫu:
  1. Bảng "Thành phần | Giá trị | Nguồn"
  2. Khối "Toán học" -- công thức ký hiệu -> công thức đã thay số -> kết quả,
     render bằng LaTeX ($$...$$, Streamlit hỗ trợ sẵn qua st.write/st.markdown).
"""
from __future__ import annotations

import ast
from typing import Optional

from app.calculation.metrics import safe_eval_formula
from app.models.calculation_schema import CalculationOutput, MetricFormulaSpec, OperandDetail
from app.generation.citation import clean_source_filename

# ---------------------------------------------------------------------------
# Định dạng số kiểu Việt Nam: 56890567 -> "56.890.567", 38.0055 -> "38,01"
# ---------------------------------------------------------------------------

def _fmt_number(x: float) -> str:
    if x == int(x):
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.4f}".replace(",", "#").replace(".", ",").replace("#", ".")


# ---------------------------------------------------------------------------
# AST -> LaTeX (chỉ để HIỂN THỊ, không dùng để tính -- phép tính thật vẫn
# chạy qua safe_eval_formula() trong metrics.py)
# ---------------------------------------------------------------------------

_PRECEDENCE = {ast.Add: 1, ast.Sub: 1, ast.Mult: 2, ast.Div: 2, ast.Mod: 2, ast.Pow: 3}
_OP_SYMBOL = {ast.Add: "+", ast.Sub: "-", ast.Mult: "\\times", ast.Mod: "\\bmod"}


def _ast_to_latex(node: ast.AST, resolve, parent_prec: int = 0) -> str:
    """resolve(name:str) -> str: trả về LaTeX cho 1 biến -- tuỳ resolve mà
    ra tên ký hiệu (bản 'symbolic') hay số đã format (bản 'substituted')."""
    if isinstance(node, ast.Expression):
        return _ast_to_latex(node.body, resolve, parent_prec)
    if isinstance(node, ast.Constant):
        return _fmt_number(float(node.value))
    if isinstance(node, ast.Name):
        return resolve(node.id)
    if isinstance(node, ast.BinOp):
        prec = _PRECEDENCE.get(type(node.op), 0)
        if isinstance(node.op, ast.Div):
            left = _ast_to_latex(node.left, resolve, 0)
            right = _ast_to_latex(node.right, resolve, 0)
            return f"\\frac{{{left}}}{{{right}}}"
        if isinstance(node.op, ast.Pow):
            base = _ast_to_latex(node.left, resolve, prec + 1)
            exp = _ast_to_latex(node.right, resolve, 0)
            return f"{base}^{{{exp}}}"
        left = _ast_to_latex(node.left, resolve, prec)
        right = _ast_to_latex(node.right, resolve, prec + 1)
        s = f"{left} {_OP_SYMBOL[type(node.op)]} {right}"
        return f"({s})" if prec < parent_prec else s
    if isinstance(node, ast.UnaryOp):
        operand = _ast_to_latex(node.operand, resolve, 3)
        return f"{'-' if isinstance(node.op, ast.USub) else '+'}{operand}"
    raise ValueError(f"Không hỗ trợ render LaTeX: {type(node).__name__}")


def _formula_to_latex(expression: str, resolve) -> str:
    return _ast_to_latex(ast.parse(expression, mode="eval"), resolve)


# ---------------------------------------------------------------------------
# Bảng thành phần
# ---------------------------------------------------------------------------
def clean_source_display(raw_source: str) -> str:
    """Chỉ giữ tên file (bỏ toàn bộ đường dẫn), và đổi đuôi '_extracted.txt'
    thành '.pdf' -- khớp đúng cách format_citation_label() trong
    app/generation/citation.py hiển thị ở khối "Nguồn tham khảo" phía dưới,
    để 2 chỗ nhất quán với nhau."""
    name = clean_source_filename(raw_source)
    return name.replace("_extracted.txt", ".pdf")

def format_operand_table(operands: dict[str, OperandDetail], field_labels: dict[str, str]) -> str:
    lines = ["| Thành phần | Giá trị (VND) | Nguồn |", "|---|---:|---|"]
    for key, op in operands.items():
        label = field_labels.get(key, key)
        source = clean_source_display(op.source) 
        if op.page:
            source += f", trang {op.page}"
        if op.table:
            source += f" — {op.table}"
        lines.append(f"| {label} | {_fmt_number(op.value)} | {source} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Khối "Toán học"
# ---------------------------------------------------------------------------

def format_math_block(
    output: CalculationOutput,
    spec: MetricFormulaSpec,
    field_labels: dict[str, str],
    metric_label: str = "",
) -> str:
    values = {k: op.value for k, op in output.operands.items()}
    resolve_symbol = lambda n: f"\\text{{{field_labels.get(n, n)}}}"
    resolve_number = lambda n: _fmt_number(values.get(n, 0.0))
    lhs = f"\\text{{{metric_label}}}" if metric_label else "KQ"

    tex: list[str] = []

    if spec.formula:
        symbolic = _formula_to_latex(spec.formula, resolve_symbol)
        substituted = _formula_to_latex(spec.formula, resolve_number)
        if spec.unit == "%":
            symbolic = f"\\left({symbolic}\\right) \\times 100"
            substituted = f"\\left({substituted}\\right) \\times 100"
        tex.append(f"{lhs} &= {symbolic} \\\\")
        tex.append(f"&= {substituted} \\\\")
        tex.append(f"&= {_fmt_number(output.result)}\\ {spec.unit}")
    else:
        # Multi-step (vd ROE/ROA): hiển thị lần lượt từng bước trung gian
        namespace = dict(values)
        for step in spec.steps:
            symbolic = _formula_to_latex(step.expression, resolve_symbol)
            substituted = _formula_to_latex(
                step.expression, lambda n: _fmt_number(namespace.get(n, 0.0))
            )
            step_value = None
            try:
                step_value = safe_eval_formula(step.expression, namespace)
            except Exception:
                pass
            label = step.label or "KQ"
            step_label_tex = field_labels.get(label, label)
            tex.append(f"\\text{{{step_label_tex}}} &= {symbolic} \\\\")
            if step_value is not None:
                tex.append(f"&= {substituted} = {_fmt_number(step_value)} \\\\")
                namespace[label] = step_value
            else:
                tex.append(f"&= {substituted} \\\\")
        unit_tex = "\\%" if spec.unit == "%" else spec.unit
        tex.append(f"{lhs} &= {_fmt_number(output.result)}\\ {unit_tex}")

    body = "\n".join(tex)
    return f"$$\n\\begin{{aligned}}\n{body}\n\\end{{aligned}}\n$$"


# ---------------------------------------------------------------------------
# Ghép toàn bộ answer
# ---------------------------------------------------------------------------

def format_calculation_answer(
    metric_label: str,
    period_label: str,
    ticker: Optional[str],
    output: CalculationOutput,
    spec: MetricFormulaSpec,
    field_labels: dict[str, str],
) -> str:
    ticker_part = f" của {ticker}" if ticker else ""
    title = f"**{metric_label}{ticker_part} {period_label}**".strip()
    table = format_operand_table(output.operands, field_labels)
    math_block = format_math_block(output, spec, field_labels, metric_label=metric_label)

    return (
        f"{title}\n\n"
        f"{table}\n\n"
        f"**{_fmt_number(output.result)} {spec.unit}**\n\n"
        f"Toán học:\n\n"
        f"{math_block}"
    )