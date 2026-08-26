"""
app/calculation/metrics.py

REGISTRY công thức ổn định (METRIC_FORMULAS) + bộ thực thi công thức AN
TOÀN. Toàn bộ phép TÍNH chạy bằng code (ast-based evaluator); LLM chỉ chọn
metric_key/operation và cung cấp operand hoặc sinh CalculationPlan.
"""
from __future__ import annotations
import ast, operator
from typing import Any
from app.models.calculation_schema import (
    CalculationOutput, CalculationPlan, CalculationStep, MetricFormulaSpec, OperandDetail,
)


class FormulaError(Exception):
    """Lỗi khi công thức không hợp lệ / thiếu operand / chia cho 0..."""

#Toán tử cộng, trừ, nhân, chia (2 ngôi)
_ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
}

#Toán tử 1 ngôi
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def _eval_node(node: ast.AST, variables: dict) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, variables)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        raise FormulaError(f"Giá trị hằng không hợp lệ trong công thức: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise FormulaError(f"Thiếu giá trị cho biến '{node.id}' trong công thức.")
        return float(variables[node.id])
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise FormulaError(f"Toán tử không được hỗ trợ: {op_type.__name__}")
        left, right = _eval_node(node.left, variables), _eval_node(node.right, variables)
        try:
            return _ALLOWED_BINOPS[op_type](left, right)
        except ZeroDivisionError:
            raise FormulaError("Công thức chia cho 0.")
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARYOPS:
            raise FormulaError(f"Toán tử một ngôi không được hỗ trợ: {op_type.__name__}")
        return _ALLOWED_UNARYOPS[op_type](_eval_node(node.operand, variables))
    raise FormulaError(f"Cú pháp không được hỗ trợ trong công thức: {type(node).__name__}")


def safe_eval_formula(expression: str, variables: dict) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"Công thức không hợp lệ: {expression!r} ({e})")
    return _eval_node(tree, variables)


METRIC_FORMULAS: dict[str, MetricFormulaSpec] = {
    "gross_margin": MetricFormulaSpec(
        formula="gross_profit / revenue", required_metrics=["gross_profit", "revenue"],
        unit="%", name_vi="Biên lợi nhuận gộp",
        aliases=["gross margin", "biên lợi nhuận gộp", "tỷ suất lợi nhuận gộp"]),
    "net_margin": MetricFormulaSpec(
        formula="net_income / revenue", required_metrics=["net_income", "revenue"],
        unit="%", name_vi="Biên lợi nhuận ròng",
        aliases=["net margin", "biên lợi nhuận ròng", "tỷ suất lợi nhuận sau thuế"]),
    "current_ratio": MetricFormulaSpec(
        formula="current_assets / current_liabilities",
        required_metrics=["current_assets", "current_liabilities"],
        unit="lần", name_vi="Hệ số thanh toán hiện hành",
        aliases=["current ratio", "khả năng thanh toán hiện hành", "hệ số thanh toán ngắn hạn"]),
    "debt_to_equity": MetricFormulaSpec(
        formula="total_liabilities / total_equity",
        required_metrics=["total_liabilities", "total_equity"],
        unit="lần", name_vi="Hệ số nợ trên vốn chủ sở hữu",
        aliases=["debt to equity", "debt-to-equity", "d/e", "hệ số nợ/vốn chủ sở hữu"]),
    "yoy_growth": MetricFormulaSpec(
        formula="(current_value - prior_year_value) / prior_year_value",
        required_metrics=["current_value", "prior_year_value"],
        unit="%", name_vi="Tăng trưởng so với cùng kỳ năm trước (YoY)",
        aliases=["yoy", "year over year", "tăng trưởng cùng kỳ", "so với cùng kỳ năm trước"]),
    "qoq_growth": MetricFormulaSpec(
        formula="(current_value - prior_quarter_value) / prior_quarter_value",
        required_metrics=["current_value", "prior_quarter_value"],
        unit="%", name_vi="Tăng trưởng so với quý trước (QoQ)",
        aliases=["qoq", "quarter over quarter", "so với quý trước"]),
    "cagr": MetricFormulaSpec(
        formula="(ending_value / beginning_value) ** (1 / num_years) - 1",
        required_metrics=["beginning_value", "ending_value", "num_years"],
        unit="%", name_vi="Tốc độ tăng trưởng kép hàng năm (CAGR)",
        aliases=["cagr", "tăng trưởng kép", "compound annual growth rate"]),
    # ROE/ROA cần bước trung gian (vốn/tài sản BÌNH QUÂN 2 kỳ) -> dùng 'steps'.
    "roe": MetricFormulaSpec(
        steps=[
            CalculationStep(label="average_shareholders_equity",
                             expression="(shareholders_equity_t + shareholders_equity_t_minus_1) / 2"),
            CalculationStep(label=None, expression="net_income / average_shareholders_equity"),
        ],
        required_metrics=["net_income", "shareholders_equity_t", "shareholders_equity_t_minus_1"],
        unit="%", name_vi="Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE)",
        aliases=["roe", "return on equity"]),
    "roa": MetricFormulaSpec(
        steps=[
            CalculationStep(label="average_total_assets",
                             expression="(total_assets_t + total_assets_t_minus_1) / 2"),
            CalculationStep(label=None, expression="net_income / average_total_assets"),
        ],
        required_metrics=["net_income", "total_assets_t", "total_assets_t_minus_1"],
        unit="%", name_vi="Tỷ suất lợi nhuận trên tổng tài sản (ROA)",
        aliases=["roa", "return on assets"]),
}


def get_metric_spec(metric_key: str):
    return METRIC_FORMULAS.get(metric_key)


def compute_metric_from_operands(metric_key: str, operands: dict[str, OperandDetail]) -> CalculationOutput:
    spec = get_metric_spec(metric_key)
    if spec is None:
        raise FormulaError(f"Không tìm thấy công thức cho chỉ số '{metric_key}'.")

    missing = [m for m in spec.required_metrics if m not in operands]
    if missing:
        raise FormulaError(f"Thiếu operand: {', '.join(missing)}")

    values = {name: op.value for name, op in operands.items()}

    if spec.formula:
        # formula gốc trong registry là tỷ lệ thuần -- nhân 100 khi unit="%"
        # để result trả về là số phần trăm (38.0), không phải 0.38.
        expanded_formula = f"({spec.formula}) * 100" if spec.unit == "%" else spec.formula
        result = safe_eval_formula(expanded_formula, values)
        display_formula = expanded_formula
    else:
        namespace = dict(values)
        result, step_exprs = None, []
        for step in spec.steps:
            step_value = safe_eval_formula(step.expression, namespace)
            label = step.label or "result"
            namespace[label] = step_value
            step_exprs.append(f"{label} = {step.expression}")
            result = step_value
        if spec.unit == "%":
            result *= 100
        display_formula = "; ".join(step_exprs) + (" ; result * 100" if spec.unit == "%" else "")

    return CalculationOutput(formula=display_formula, operands=operands, result=round(result, 4))


def execute_plan(plan: CalculationPlan, operand_values: dict[str, float]) -> dict[str, Any]:
    """Thực thi 1 CalculationPlan AD-HOC do LLM sinh (vd so sánh 2 kỳ) --
    LLM chỉ sinh operation + steps, KHÔNG tự tính ra số."""
    namespace = dict(operand_values)
    step_results, final_value = [], None
    for i, step in enumerate(plan.steps, start=1):
        value = safe_eval_formula(step.expression, namespace)
        label = step.label or f"step_{i}"
        namespace[label] = value
        step_results.append({"label": label, "expression": step.expression, "value": value})
        final_value = value
    return {"operation": plan.operation, "steps": step_results, "result": final_value}