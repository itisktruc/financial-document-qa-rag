from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class OperandDetail(BaseModel):
    """1 số liệu thô dùng làm operand, kèm ĐẦY ĐỦ nguồn trích dẫn. 'source'
    CHỈ là tên file (khớp cơ chế citation đã sửa -- không kèm đường dẫn)."""
    value: float
    source: str
    page: Optional[int] = None
    table: Optional[str] = None


class CalculationOutput(BaseModel):
    formula: str
    operands: dict[str, OperandDetail]
    result: float

class CalculationToolResult(BaseModel):
    calculation: CalculationOutput

class CalculationStep(BaseModel):
    """'label': tên biến lưu kết quả bước này để bước SAU tham chiếu (vd
    "result_2025") -- None nếu là bước cuối. 'expression': chỉ chứa toán
    tử số học cơ bản (+ - * / ** %), số, dấu ngoặc và tên biến (operand
    gốc hoặc label bước trước) -- tính bằng safe_eval_formula(), không
    dùng eval() trần trụi."""
    label: Optional[str] = None
    expression: str

class CalculationPlan(BaseModel):
    operation: str
    steps: list[CalculationStep]

class MetricFormulaSpec(BaseModel):
    """vd:
    {
      "current_ratio": {"formula": "current_assets / current_liabilities", "required_metrics": [...]},
      "roe": {"formula": "net_income / average_shareholders_equity", "required_metrics": ["net_income", "shareholders_equity_t", "shareholders_equity_t_minus_1"]}
    }

    Chỉ số cần bước trung gian (vd ROE cần tính vốn CSH BÌNH QUÂN trước khi
    chia -- formula tham chiếu 1 biến không có sẵn trực tiếp trong
    required_metrics) dùng 'steps' THAY 'formula' đơn. Đúng 1 trong 2 field
    phải được khai báo.
    """
    formula: Optional[str] = None
    steps: Optional[list[CalculationStep]] = None
    required_metrics: list[str]
    unit: str = ""
    name_vi: str = ""
    aliases: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_formula_or_steps(self):
        has_formula, has_steps = bool(self.formula), bool(self.steps)
        if has_formula == has_steps:
            raise ValueError(
                "MetricFormulaSpec phải khai báo ĐÚNG 1 trong 2: "
                "'formula' (đơn bước) hoặc 'steps' (nhiều bước)."
            )
        return self
    
    def display_json(self, metric_key: str) -> dict:
        """Trả về đúng 2 giá trị cần hiển thị lên UI khi vào nhánh
        Calculation: công thức thực sự dùng (formula HOẶC steps -- KHÔNG
        rút gọn ROE/ROA thành 1 formula giả vì sẽ che giấu bước tính bình
        quân) + required_metrics (những số liệu thô hệ thống cần tra cứu).
        Dạng: {"<metric_key>": {"formula"|"steps": ..., "required_metrics": [...]}}.
        """
        if self.formula:
            body = {"formula": self.formula, "required_metrics": self.required_metrics}
        else:
            body = {
                "steps": [s.model_dump() for s in self.steps],
                "required_metrics": self.required_metrics,
            }
        return {metric_key: body}

class CalculationIntent(BaseModel):
    # "metric_key"/"metric_keys": kể từ khi hỗ trợ multi-metric (1 câu hỏi
    # có thể cần tính NHIỀU chỉ số, hoặc chỉ số được suy luận GIÁN TIẾP từ
    # ngữ cảnh câu hỏi thay vì gọi tên trực tiếp -- xem
    # CalculationService.extract_intent()), "metric_keys" là NGUỒN SỰ THẬT
    # ĐẦY ĐỦ. "metric_key" (số ít) LUÔN = metric_keys[0] (hoặc None nếu
    # rỗng) -- giữ lại CHỈ để tương thích ngược với bất kỳ code cũ nào còn
    # đọc field đơn số này trực tiếp (vd log/debug, hoặc client cũ).
    metric_key: Optional[str] = None
    metric_keys: list[str] = Field(default_factory=list)
    ticker: Optional[str] = None
    year: Optional[int] = None
    quarter: Optional[int] = None
    compare_year: Optional[int] = None
    compare_quarter: Optional[int] = None
    report_scope: Optional[str] = None  # "parent" | "consolidated" | None
    raw_query: str = ""


class CalculationResponse(BaseModel):
    answer: str
    calculation: Optional[CalculationOutput] = None
    calculations: list[CalculationOutput] = Field(default_factory=list)
    citations: list = Field(default_factory=list)
    intent: Optional[dict] = None
    metric_spec: Optional[dict] = None
    metric_specs: list[dict] = Field(default_factory=list)