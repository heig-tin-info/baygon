from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, ValidationError

Value = Union[str, int, float, bool]


class EvaluateConfig(BaseModel):
    start: str = "{{"
    end: str = "}}"
    init: Optional[List[str]] = None


class MinPointsMixin(BaseModel):
    min_points: float = Field(0.1, alias="min-points")


class FiltersConfig(BaseModel):
    uppercase: Optional[bool] = None
    lowercase: Optional[bool] = None
    trim: Optional[bool] = None
    ignorespaces: Optional[bool] = Field(None, alias="ignore-spaces")
    regex: Optional[List[str]] = None
    replace: Optional[List[str]] = None


class CaseConfig(BaseModel):
    filters: FiltersConfig = FiltersConfig()
    equals: Optional[Value] = None
    regex: Optional[Value] = None
    contains: Optional[Value] = None
    not_: Optional[List[Dict[str, Value]]] = Field(None, alias="not")
    expected: Optional[Value] = None

    @field_validator("not_", mode="before")
    def rename_not(cls, v):
        return v


class CommonConfig(MinPointsMixin, BaseModel):
    name: str = ""
    executable: Optional[str] = None
    points: Optional[float] = None
    weight: Optional[float] = None

    @field_validator("points")
    def check_points_weight(cls, v, values):
        weight = values.get("weight")
        if weight is not None and v is not None:
            raise ValueError("Cannot specify both 'points' and 'weight'")
        return v


class TestConfig(CommonConfig):
    args: List[Value] = []
    env: Dict[str, Value] = {}
    stdin: Optional[Value] = ""
    stdout: Optional[List[Union[Value, "CaseConfig"]]] = []
    stderr: Optional[List[Union[Value, "CaseConfig"]]] = []
    repeat: int = 1
    exit: Optional[Union[int, str, bool]] = None


class GroupConfig(CommonConfig):
    tests: List[Union["GroupConfig", TestConfig]]

    class Config:
        arbitrary_types_allowed = True


GroupConfig.model_rebuild()


class CLIConfig(BaseModel):
    """CLI configuration that can be overridden by CLI arguments"""

    verbose: Optional[int] = 0
    report: Optional[str] = None
    format: Optional[Literal["json", "yaml"]] = "json"
    table: bool = False


class SchemaConfig(MinPointsMixin, CLIConfig, BaseModel):
    name: Optional[str] = None
    version: int = 2
    filters: FiltersConfig = FiltersConfig()
    tests: List[Union[GroupConfig, TestConfig]]
    points: Optional[float] = None
    evaluate: Optional[EvaluateConfig] = None

    @field_validator("version")
    def _check_version(cls, v):
        if v > 2:
            raise ValidationError(
                "Only version up to 2 is accepted, you may used a newer schema"
            )
        return v

    class Config:
        populate_by_name = True
