from pathlib import Path

import yaml
from pydantic import BaseModel

class AxisOption(BaseModel):
    value: str | int | float
    label: str | None = None
    citation: str

class MethodologyAxis(BaseModel):
    id: str
    description: str
    options: list[AxisOption]

    def option_values(self) -> list:
        return [o.value for o in self.options]

class MethodologySpace(BaseModel):
    methodology_space: str
    version: str
    description: str = ""
    axes: list[MethodologyAxis]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MethodologySpace":
        with open(path) as p:
            data = yaml.safe_load(p)
        return cls(**data)
    def axis(self, axis_id: str) -> MethodologyAxis:
        for ax in self.axes:
            if ax.id == axis_id:
                return ax
        raise KeyError(f"No axis of {axis_id!r} in methodology space")
    def axis_ids(self) -> list[str]:
        return [ax.id for ax in self.axes]
    def grid_size(self) -> int:
        size = 1
        for ax in self.axes:
            size *= len(ax.options)
        return size