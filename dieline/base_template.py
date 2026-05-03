from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .svg_builder import SVGBuilder


@dataclass
class ParameterSpec:
    name: str
    label: str
    type: str           # "float" | "int" | "bool" | "select"
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    unit: str | None = "mm"
    options: list[str] | None = None
    group: str | None = None


@dataclass
class ValidationError:
    field: str
    message: str


class BaseTemplate(ABC):
    """
    All packaging templates inherit from this class.
    Subclasses must:
      1. Set TEMPLATE_ID and TEMPLATE_NAME class attributes
      2. Implement generate(params) -> SVGBuilder
    """

    TEMPLATE_ID: str = ""
    TEMPLATE_NAME: str = ""
    DESCRIPTION: str = ""

    def __init__(self):
        self._config = self._load_yaml_config()

    def _load_yaml_config(self) -> dict:
        config_path = Path(__file__).parent.parent / "configs" / f"{self.TEMPLATE_ID}.yaml"
        with config_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    def parameter_specs(self) -> list[ParameterSpec]:
        return [ParameterSpec(**p) for p in self._config.get("parameters", [])]

    def validate(self, params: dict) -> list[ValidationError]:
        errors = []
        for spec in self.parameter_specs():
            val = params.get(spec.name)
            if val is None:
                errors.append(ValidationError(spec.name, "Required field missing"))
                continue
            if spec.type in ("float", "int"):
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    errors.append(ValidationError(spec.name, "Must be a number"))
                    continue
                if spec.min is not None and v < spec.min:
                    errors.append(ValidationError(spec.name, f"Minimum value is {spec.min}"))
                if spec.max is not None and v > spec.max:
                    errors.append(ValidationError(spec.name, f"Maximum value is {spec.max}"))
        return errors

    @abstractmethod
    def generate(self, params: dict) -> SVGBuilder:
        """Implement geometry here. Must return a populated SVGBuilder."""
        ...

    def render(self, params: dict) -> tuple[str, list[ValidationError]]:
        errors = self.validate(params)
        if errors:
            return ("", errors)
        builder = self.generate(params)
        return (builder.to_svg_string(), [])

    def metadata(self) -> dict:
        return {
            "id": self.TEMPLATE_ID,
            "name": self.TEMPLATE_NAME,
            "description": self.DESCRIPTION,
            "thumbnail": f"/static/thumbnails/{self.TEMPLATE_ID}.svg",
        }

    def default_params(self) -> dict:
        return {spec.name: spec.default for spec in self.parameter_specs()}
