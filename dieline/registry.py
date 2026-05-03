import importlib
import pkgutil

from dieline import templates
from dieline.base_template import BaseTemplate


class TemplateRegistry:
    def __init__(self):
        self._templates: dict[str, BaseTemplate] = {}
        self._discover()

    def _discover(self):
        for _, module_name, _ in pkgutil.iter_modules(templates.__path__):
            importlib.import_module(f"dieline.templates.{module_name}")

        def _all_subclasses(cls):
            result = []
            for sub in cls.__subclasses__():
                result.append(sub)
                result.extend(_all_subclasses(sub))
            return result

        for cls in _all_subclasses(BaseTemplate):
            if cls.TEMPLATE_ID:
                self._templates[cls.TEMPLATE_ID] = cls()

    def get(self, template_id: str) -> BaseTemplate | None:
        return self._templates.get(template_id)

    def all(self) -> list[BaseTemplate]:
        return list(self._templates.values())
