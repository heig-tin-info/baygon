import math
import random
import statistics

from RestrictedPython import (
    compile_restricted,
    limited_builtins,
    safe_builtins,
    utility_builtins,
)


class RestrictedEvaluator:
    def __init__(self):
        # Note: iter and reset are added dynamically when used from eval module
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
            "rand": random.random,
            "randint": random.randint,
            "uniform": random.uniform,
            "choice": random.choice,
            "mean": statistics.mean,
            "median": statistics.median,
            "mode": statistics.mode,
            "stdev": statistics.stdev,
            "variance": statistics.variance,
        }
        self.local_env = {}

    @property
    def error(self):
        return self.local_env.get("__exception__")

    def __call__(self, code: str):
        return self.evaluate(code)

    def evaluate(self, code: str):
        try:
            compiled_code = compile_restricted(code, "<string>", "exec")
            exec(compiled_code, self.global_env, self.local_env)

            # Extract the last variable assigned (if it's an assignment)
            # Split the code into lines, and check for assignment
            lines = code.strip().split("\n")
            last_line = lines[-1].strip()

            # Check if the last line is an assignment like `a = 42`
            if "=" in last_line:
                var_name = last_line.split("=")[0].strip()
                if var_name in self.local_env:
                    return self.local_env[var_name]
                elif var_name in self.global_env:
                    return self.global_env[var_name]

            # If it's an expression, we return its evaluated result
            result = eval(code, self.global_env, self.local_env)
            return result
        except Exception as e:
            self.local_env["__exception__"] = e
            return None
