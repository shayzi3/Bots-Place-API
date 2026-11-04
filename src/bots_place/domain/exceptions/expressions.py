class UnknownFieldError(Exception):
    """Raised when an expression references a field absent on the model."""

    def __init__(self, model_name: str, field: str) -> None:
        super().__init__(f"Model {model_name} has no field {field!r}")
        self.model_name = model_name
        self.field = field


class UnknownOperatorError(Exception):
    """Raised when an expression uses an operator the parser does not support."""

    def __init__(self, operator: str) -> None:
        super().__init__(f"Unsupported operator {operator!r}")
        self.operator = operator
