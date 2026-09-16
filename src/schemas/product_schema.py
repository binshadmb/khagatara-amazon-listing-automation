from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductField:
    name: str
    required: bool = False
    value: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductSchema:
    product_type: str
    marketplace_id: str
    fields: list[ProductField] = field(default_factory=list)

    def required_fields(self) -> list[ProductField]:
        return [field for field in self.fields if field.required]

    def field_names(self) -> list[str]:
        return [field.name for field in self.fields]