from __future__ import annotations

from typing import Any, Callable


class _FieldInfo:
    def __init__(self, default: Any = ..., default_factory: Callable[[], Any] | None = None) -> None:
        self.default = default
        self.default_factory = default_factory


def Field(*, default: Any = ..., default_factory: Callable[[], Any] | None = None) -> _FieldInfo:
    """Minimal replacement for pydantic.Field."""
    return _FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    """Very small subset of pydantic's BaseModel for tests."""

    def __init__(self, **data: Any) -> None:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, _FieldInfo):
                if name not in data:
                    if value.default is not ...:
                        setattr(self, name, value.default)
                    elif value.default_factory is not None:
                        setattr(self, name, value.default_factory())
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self) -> dict[str, Any]:
        return self.__dict__

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "BaseModel":
        return cls(**data)


PositiveInt = int

__all__ = ["BaseModel", "Field", "PositiveInt"]
