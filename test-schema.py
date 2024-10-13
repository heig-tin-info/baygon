from typing import Optional
from pydantic import BaseModel, model_validator, ValidationError
from baygon.helpers import to_pcre, parse_pcre_flags
from baygon.filters import FilterFactory, Filters


class FilterConfigRegex(BaseModel):
    pattern: str
    replace: str
    flags: Optional[str] = ""

    @model_validator(mode="before")
    def validate_regex(cls, values):
        if isinstance(values, str):
            return to_pcre(values)
        if isinstance(values, list):
            pattern, replace = values[0], values[1]
            flags = parse_pcre_flags(values[2] if len(values) > 2 else "")
            return {"pattern": pattern, "replace": replace, "flags": flags}
        if isinstance(values, dict):
            pattern = values.get("pattern")
            replace = values.get("replace")
            flags = parse_pcre_flags(values.get("flags", ""))
            return {"pattern": pattern, "replace": replace, "flags": flags}
        raise ValueError(f"Invalid regex entry: {values}")


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


class FiltersConfig(BaseModel):
    uppercase: Optional[bool] = None
    lowercase: Optional[bool] = None
    trim: Optional[bool] = None
    join: Optional[bool] = None
    regex: Optional[FilterConfigRegex] = None
    replace: Optional[FilterConfigReplace] = None


class FilterMixin:
    filters_config: FiltersConfig = FiltersConfig()  # Renommé pour éviter le conflit

    @model_validator(mode="after")
    def apply_filters(self):
        """Generate enabled filters based on the configuration."""
        enabled_filters = []
        filters = self.filters_config  # Accéder aux filtres via self

        for filter_name in ["uppercase", "lowercase", "trim", "join"]:
            if getattr(filters, filter_name):
                enabled_filters.append(FilterFactory(filter_name))

        if filters.regex:
            enabled_filters.append(FilterFactory("regex", **filters.regex.model_dump()))

        if filters.replace:
            enabled_filters.append(
                FilterFactory("replace", **filters.replace.model_dump())
            )

        self.filters_config = Filters(*enabled_filters)  # Remplacer par l'objet Filters


config = FiltersConfig(
    uppercase=True,
    regex={
        "pattern": "foo",
        "replace": "bar",
        "flags": "g",
    },
    replace={"search": "old", "replace": "new"},
)


# FilterMixin est maintenant un vrai mixin, pas de conflit d'attributs
class MyFilterClass(FilterMixin, BaseModel):
    filters_config: FiltersConfig  # Utiliser filters_config au lieu de filters


mixin_instance = MyFilterClass(filters_config=config)
mixin_instance.apply_filters()  # Appliquer la validation et générer les filtres
print(mixin_instance.filters_config)
