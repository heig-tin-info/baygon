import math

from RestrictedPython import (
    compile_restricted,
    limited_builtins,
    safe_builtins,
    utility_builtins,
)

from .eval import iter, reset


class RestrictedEvaluator:
    def __init__(self):
        self.global_env = {
            "__builtins__": {**safe_builtins, **utility_builtins, **limited_builtins},
            "math": math,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "sqrt": math.sqrt,
            "pi": math.pi,
            "e": math.e,
            "exp": math.exp,
            "iter": iter,
            "reset": reset,
        }
        self.local_env = {}

    @property
    def error(self):
        return self.local_env.get("__exception__")

    def evaluate(self, code: str):
        compiled_code = compile_restricted(code, "<string>", "exec")
        exec(compiled_code, self.global_env, self.local_env)
        try:
            result = eval(code, self.global_env, self.local_env)
            return result
        except Exception as e:
            self.local_env["__exception__"] = e
            return None
