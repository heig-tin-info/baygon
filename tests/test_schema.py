from io import StringIO
from textwrap import dedent
from unittest import TestCase

from pydantic import ValidationError

from baygon import Schema
from baygon.error import ConfigError, ConfigSyntaxError
from baygon.schema import (
    BaygonConfig,
    CaseCondition,
    EvalConfig,
    FiltersConfig,
    NegatedCondition,
    TestCaseModel,
    _coerce_match_list,
    _load_yaml,
)


class TestSchema(TestCase):
    def test_minimal(self):
        Schema({"version": 1, "tests": [{"exit": 0}]})

    def test_wrong_version(self):
        with self.assertRaises(ValidationError):
            Schema({"version": 3, "tests": [{"exit": 0}]})

    def test_filters(self):
        config = Schema(
            {
                "version": 1,
                "filters": {
                    "uppercase": True,
                    "ignorespaces": True,
                    "regex": ["foo", "bar"],
                    "replace": ("baz", "qux"),
                },
                "tests": [],
            }
        )
        self.assertEqual(config["filters"]["regex"], ["foo", "bar"])

    def test_filters_invalid_pairs(self):
        with self.assertRaises(ValidationError):
            Schema(
                {
                    "tests": [],
                    "filters": {"regex": ["only-one"]},
                }
            )

    def test_test_contains(self):
        config = Schema(
            {
                "tests": [
                    {
                        "stdout": [1, {"contains": "Version"}, True],
                        "stderr": {"regex": r"\d+"},
                    }
                ]
            }
        )
        stdout = config["tests"][0]["stdout"]
        self.assertEqual(stdout[0]["equals"], "1")
        self.assertEqual(stdout[-1]["equals"], "1")
        self.assertEqual(config["tests"][0]["stderr"][0]["regex"], r"\d+")

    def test_invalid_match_definition(self):
        with self.assertRaises(TypeError):
            Schema({"tests": [{"stdout": {1, 2, 3}}]})

    def test_empty_filters(self):
        s = Schema({"version": 1, "tests": []})
        self.assertIn("filters", s)

    def test_eval_bool_removes_delimiters(self):
        config = Schema(
            {
                "eval": True,
                "tests": [
                    {
                        "stdin": None,
                        "stdout": {"equals": True},
                        "exit": True,
                    }
                ],
            }
        )
        self.assertEqual(config["eval"], {"init": []})
        case = config["tests"][0]
        self.assertEqual(case["stdout"][0]["equals"], "1")

    def test_eval_init_string_coercion(self):
        config = EvalConfig.model_validate({"init": "value = 42"})
        self.assertEqual(config.init, ["value = 42"])

    def test_eval_none_defaults(self):
        config = Schema({"eval": None, "tests": [{"exit": 0}]})
        self.assertEqual(config["eval"], {"init": []})

    def test_points_weight_conflict_humanized(self):
        with self.assertRaises(ConfigError) as exc:
            Schema(
                {
                    "points": 2,
                    "weight": 1,
                    "tests": [{"exit": 0}],
                },
                humanize=True,
            )
        self.assertIn("points", str(exc.exception))

    def test_assign_ids_nested(self):
        config = Schema(
            {
                "tests": [
                    {
                        "name": "group",
                        "tests": [
                            {"name": "case-a", "exit": 0},
                            {"name": "case-b", "exit": 0},
                        ],
                    },
                    {"name": "root-case", "exit": 0},
                ]
            }
        )
        group = config["tests"][0]
        self.assertEqual(group["test_id"], [1])
        self.assertEqual(group["tests"][0]["test_id"], [1, 1])
        self.assertEqual(group["tests"][1]["test_id"], [1, 2])
        self.assertEqual(config["tests"][1]["test_id"], [2])

    def test_internal_coerce_match_list(self):
        self.assertEqual(_coerce_match_list(None), [])
        self.assertEqual(_coerce_match_list(True)[0]["equals"], "1")

    def test_negated_condition_validation(self):
        neg = NegatedCondition.model_validate({"equals": 10})
        self.assertEqual(neg.equals, "10")
        with self.assertRaises(ValidationError):
            NegatedCondition.model_validate({})

    def test_case_condition_validation(self):
        condition = CaseCondition.model_validate({"equals": 5})
        self.assertEqual(condition.equals, "5")
        with self.assertRaises(ValidationError):
            CaseCondition.model_validate({})

    def test_testcase_model_conversions(self):
        model = TestCaseModel.model_validate(
            {
                "args": [1, "2"],
                "env": {"A": 1},
                "stdin": 3.14,
                "stdout": [False],
                "stderr": None,
                "exit": False,
            }
        )
        self.assertEqual(model.args, ["1", "2"])
        self.assertEqual(model.env, {"A": "1"})
        self.assertEqual(model.stdin, "3.14")
        self.assertEqual(model.stdout[0].equals, "0")
        self.assertEqual(model.stderr, [])

    def test_testcase_model_invalid_inputs(self):
        with self.assertRaises(TypeError):
            TestCaseModel.model_validate({"args": "boom"})
        with self.assertRaises(TypeError):
            TestCaseModel.model_validate({"env": ["oops"]})

    def test_convert_eval_field_retains_mapping(self):
        config = BaygonConfig.model_validate({"eval": {"init": []}, "tests": []})
        self.assertEqual(config.eval.init, [])

    def test_load_yaml_helpers(self):
        self.assertEqual(_load_yaml(""), {})
        with self.assertRaises(ConfigError):
            _load_yaml("- 1")

    def test_filters_validator_none(self):
        config = FiltersConfig.model_validate({"regex": None})
        self.assertIsNone(config.regex)

    def test_eval_init_invalid_type(self):
        with self.assertRaises(TypeError):
            EvalConfig.model_validate({"init": 123})

    def test_eval_init_none_defaults(self):
        config = EvalConfig.model_validate({"init": None})
        self.assertEqual(config.init, [])

    def test_negated_condition_none(self):
        self.assertIsNone(NegatedCondition._convert_values(None))

    def test_case_condition_convert_none(self):
        self.assertIsNone(CaseCondition._convert_values(None))

    def test_testcase_model_none_inputs(self):
        model = TestCaseModel.model_validate({"args": None, "env": None})
        self.assertEqual(model.args, [])
        self.assertEqual(model.env, {})

    def test_baygon_config_version_none(self):
        config = BaygonConfig.model_validate({"version": None, "tests": []})
        self.assertEqual(config.version, 2)

    def test_schema_with_text_io(self):
        handle = StringIO("tests:\n  - exit: 0\n")
        config = Schema(handle)
        self.assertEqual(config["tests"][0]["exit"], 0)

    def test_non_mapping_raises(self):
        with self.assertRaises(ConfigError):
            Schema(["not-a-mapping"])

    def test_yaml_string(self):
        config = Schema(
            dedent("""
                version: 1
                tests:
                  - exit: 0
                """)
        )
        self.assertEqual(config["tests"][0]["exit"], 0)

    def test_yaml_syntax_error(self):
        with self.assertRaises(ConfigSyntaxError) as exc:
            Schema("tests:\n  - exit: [")
        self.assertIn("line", str(exc.exception))
