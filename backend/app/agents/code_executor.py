import sys
import json
import ast
import subprocess
import tempfile
import os
import time
from typing import Optional


def check_code_safety(code: str) -> tuple[bool, str]:
    dangerous_imports = [
        "os", "subprocess", "shutil", "sys", "importlib",
        "socket", "requests", "urllib", "pathlib",
        "ctypes", "multiprocessing", "threading",
    ]
    dangerous_builtins = [
        "eval", "exec", "compile", "__import__",
        "open", "input", "breakpoint",
    ]

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in dangerous_imports:
                        return False, f"Import of '{alias.name}' is not allowed for security reasons"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in dangerous_imports:
                    return False, f"Import from '{node.module}' is not allowed for security reasons"
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_builtins:
                        return False, f"Use of '{node.func.id}()' is not allowed for security reasons"
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["__import__", "open", "eval", "exec"]:
                        return False, f"Use of '{node.func.attr}()' is not allowed"
    except SyntaxError as e:
        return False, f"Syntax error in code: {e}"

    return True, ""


def _build_test_runner(code: str, test_cases: list[dict]) -> str:
    test_cases_json = json.dumps(test_cases)
    return f"""
import sys
import json
import ast
import traceback
import time

# User's code
{code}

# Test cases
test_cases = {test_cases_json}

results = []
passed = 0
start_time = time.time()

def _normalize_expected(expected_str):
    try:
        return json.loads(expected_str)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return ast.literal_eval(expected_str)
    except (ValueError, SyntaxError):
        pass
    return expected_str

for i, tc in enumerate(test_cases):
    result = {{"test_index": i}}
    try:
        input_str = tc["input"]
        expected_raw = tc["expected"]
        expected_val = _normalize_expected(expected_raw)

        try:
            parsed_input = eval(input_str) if isinstance(input_str, str) else input_str
        except:
            parsed_input = input_str

        func_name = None
        for key in dir():
            if not key.startswith('_') and callable(globals().get(key, None)):
                func_name = key
                break

        if func_name:
            if isinstance(parsed_input, tuple):
                actual = globals()[func_name](*parsed_input)
            else:
                actual = globals()[func_name](parsed_input)

            if isinstance(actual, bool):
                actual_repr = str(actual)
            elif actual is None:
                actual_repr = "None"
            elif isinstance(actual, (list, tuple)):
                actual_repr = repr(actual)
            elif isinstance(actual, dict):
                actual_repr = json.dumps(actual, sort_keys=True)
            else:
                actual_repr = str(actual)

            if isinstance(expected_val, bool):
                expected_repr = str(expected_val)
            elif expected_val is None:
                expected_repr = "None"
            elif isinstance(expected_val, (list, tuple)):
                expected_repr = repr(expected_val)
            elif isinstance(expected_val, dict):
                expected_repr = json.dumps(expected_val, sort_keys=True)
            else:
                expected_repr = str(expected_val)

            if actual == expected_val:
                passed += 1
                result["status"] = "passed"
                result["actual"] = actual_repr
            else:
                result["status"] = "failed"
                result["actual"] = actual_repr
                result["expected"] = expected_repr
        else:
            result["status"] = "error"
            result["error"] = "No callable function found"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()

    results.append(result)

elapsed_ms = int((time.time() - start_time) * 1000)

output = json.dumps({{
    "results": results,
    "passed": passed,
    "total": len(test_cases),
    "executionTimeMs": elapsed_ms,
}})
print(output)
"""


def run_code_with_test_cases(
    code: str, test_cases: list[dict], timeout: int = 10
) -> dict:
    is_safe, error_msg = check_code_safety(code)
    if not is_safe:
        return {
            "success": False,
            "error": error_msg,
            "results": [],
            "passed": 0,
            "total": len(test_cases),
        }

    test_runner = _build_test_runner(code, test_cases)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_runner)
            temp_path = f.name

        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={},
            cwd=tempfile.gettempdir(),
        )

        try:
            os.unlink(temp_path)
        except:
            pass

        if result.returncode != 0:
            stderr = result.stderr[:500] if result.stderr else "Unknown error"
            return {
                "success": False,
                "error": stderr,
                "results": [],
                "passed": 0,
                "total": len(test_cases),
            }

        try:
            output_data = json.loads(result.stdout.strip())
            return {
                "success": True,
                "error": None,
                "results": output_data["results"],
                "passed": output_data["passed"],
                "total": output_data["total"],
                "executionTimeMs": output_data.get("executionTimeMs", None),
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": f"Could not parse output: {result.stdout[:200]}",
                "results": [],
                "passed": 0,
                "total": len(test_cases),
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Code execution timed out after {timeout} seconds",
            "results": [],
            "passed": 0,
            "total": len(test_cases),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "passed": 0,
            "total": len(test_cases),
        }


def run_python_code(code: str, timeout: int = 5) -> dict:
    is_safe, error_msg = check_code_safety(code)
    if not is_safe:
        return {"success": False, "stdout": "", "stderr": error_msg}

    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={},
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Execution timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}


def run_code_with_hidden_tests(
    code: str,
    visible_tests: list[dict],
    hidden_tests: list[dict],
    timeout: int = 10,
) -> dict:
    all_tests = visible_tests + hidden_tests
    full_result = run_code_with_test_cases(code, all_tests, timeout)

    if full_result["results"]:
        visible_count = len(visible_tests)
        hidden_results = full_result["results"][visible_count:]
        hidden_passed = sum(1 for r in hidden_results if r.get("status") == "passed")
        full_result["visiblePassed"] = sum(
            1 for r in full_result["results"][:visible_count] if r.get("status") == "passed"
        )
        full_result["hiddenPassed"] = hidden_passed
        full_result["hiddenTotal"] = len(hidden_tests)
        full_result["results"] = full_result["results"][:visible_count]

    return full_result