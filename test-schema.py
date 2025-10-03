from typing import Optional

from pydantic import BaseModel, Field, model_validator

from baygon.filters import FilterFactory, Filters
from baygon.helpers import to_pcre


class RegexDictFormat(BaseModel):
    pattern: str
    replace: str
    flags: Optional[str] = Field(
        None, pattern=r"^[gims]*$", description="PCRE flags (g, i, m, s)"
    )

    class Config:
        json_schema_extra = {
            "regex": {"pattern": "foo(bar?)", "replace": "bar", "flags": "gim"}
        }


class RegexListFormat(BaseModel):
    pattern: str
    replace: str
    flags: Optional[str]

    @model_validator(mode="before")
    def validate_list(cls, values):
        if len(values) < 2:
            raise ValueError(
                "List format should contain at least two elements: [pattern, replace]."
            )
        pattern, replace = values[0], values[1]
        flags = values[2] if len(values) > 2 else ""
        return {"pattern": pattern, "replace": replace, "flags": flags}

    class Config:
        json_schema_extra = {"regex": ["foo", "bar", "gim"]}


class RegexStringFormat(BaseModel):
    pattern: str
    replace: str
    flags: Optional[str]

    @model_validator(mode="before")
    def validate_string(cls, value):
        return to_pcre(value)

    class Config:
        json_schema_extra = {"regex": "s/foo/bar/g"}


class FilterConfigRegex(BaseModel):
    pattern: Optional[str]
    replace: Optional[str]
    flags: Optional[str]

    @model_validator(mode="before")
    def validate_regex(cls, values):
        """Validate input and select the correct format based on input type."""
        if isinstance(values, dict):
            return RegexDictFormat(**values).dict()
        elif isinstance(values, list):
            return RegexListFormat.validate_list(values)
        elif isinstance(values, str):
            return to_pcre(values)  # For string format like s/.../.../...
        else:
            raise ValueError(f"Invalid regex format: {values}")

    class Config:
        json_schema_extra = {
            "stdout": {
                "regex": {"pattern": "foo", "replace": "bar", "flags": "gim"},
                "regex": ["foo", "bar", "gim"],
                "regex": "s/foo/bar/g",
            }
        }


class FilterConfigReplace(BaseModel):
    search: str
    replace: str

    @model_validator(mode="before")
    def validate_replace(cls, values):
        if isinstance(values, list) and len(values) == 2:
            return {"search": values[0], "replace": values[1]}
        if isinstance(values, dict) and "search" in values and "replace" in values:
            return values
        raise ValueError(f"Invalid replace entry: {values}")

    class Config:
        json_schema_extra = {
            "stdout": {
                "replace": {"search": "foo", "replace": "bar"},
                "regex": ["foo", "bar"],
            }
        }


# Configuration class for filters
class FiltersConfig(BaseModel):
    uppercase: Optional[bool] = None
    lowercase: Optional[bool] = None
    trim: Optional[bool] = None
    join: Optional[bool] = None
    regex: Optional[FilterConfigRegex] = None
    replace: Optional[FilterConfigReplace] = None


# Mixin for handling filter application
class FilterMixin:
    filters_config: FiltersConfig = FiltersConfig()

    @model_validator(mode="after")
    def apply_filters(self):
        """Generate enabled filters based on the configuration."""
        enabled_filters = []
        filters = self.filters_config  # Access filters via self

        print("NON DE DIEU")
        # Check for basic filters
        for filter_name in ["uppercase", "lowercase", "trim", "join"]:
            if getattr(filters, filter_name):
                enabled_filters.append(FilterFactory(filter_name))

        # Handle regex filter
        if filters.regex:
            enabled_filters.append(FilterFactory("regex", **filters.regex.model_dump()))

        # Handle replace filter
        if filters.replace:
            enabled_filters.append(
                FilterFactory("replace", **filters.replace.model_dump())
            )

        # Update filters_config with generated Filters object
        self.filters_config = Filters(enabled_filters)


# Example usage
config = FiltersConfig(
    uppercase=True,
    regex={
        "pattern": "foo",
        "replace": "bar",
        "flags": "g",
    },
    replace={"search": "old", "replace": "new"},
)


class MyFilterClass(FilterMixin, BaseModel):
    filters_config: FiltersConfig


mixin_instance = MyFilterClass(filters_config=config)
mixin_instance.apply_filters()  # Apply validation and generate filters
print(mixin_instance.filters_config)
