import json
import os
import subprocess
import tempfile
from pathlib import Path

SANDBOX_MODE = os.getenv("SANDBOX_MODE", "auto")
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")
SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "6"))

RUNNER_SOURCE = """
import json
import sys
import traceback

from solution import solve


def main():
    with open("cases.json", "r", encoding="utf-8") as handle:
        cases = json.load(handle)
    results = []
    for case in cases:
        args = case.get("args", [])
        expected = case.get("expected")
        try:
            actual = solve(*args) if isinstance(args, list) else solve(args)
            results.append({"passed": actual == expected, "output": repr(actual), "error": ""})
        except Exception:
            results.append({"passed": False, "output": "", "error": traceback.format_exc(limit=2)})
    print(json.dumps({"status": "ok", "cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
""".strip()


def docker_available(timeout: int = 2) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _unavailable(reason: str) -> dict:
    return {
        "status": "not_executed",
        "available": False,
        "reason": reason,
        "cases": [],
    }


def run_python_tests(code: str, cases: list[dict], timeout: int = SANDBOX_TIMEOUT) -> dict:
    """在一次性 Docker 容器中执行 solve(*args)；不可用时明确降级，不在宿主机执行。"""
    if SANDBOX_MODE == "disabled":
        return _unavailable("沙箱已关闭（SANDBOX_MODE=disabled）")
    if not docker_available():
        return _unavailable("Docker 未运行，未执行代码；仅做静态分析")
    if not cases:
        return _unavailable("未配置测试用例，未执行代码")
    try:
        with tempfile.TemporaryDirectory(prefix="zx-sandbox-") as tmp:
            work = Path(tmp)
            (work / "solution.py").write_text(code, encoding="utf-8")
            (work / "cases.json").write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
            (work / "runner.py").write_text(RUNNER_SOURCE, encoding="utf-8")
            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                "128m",
                "--cpus",
                "0.5",
                "-v",
                f"{work}:/work",
                "-w",
                "/work",
                SANDBOX_IMAGE,
                "python",
                "runner.py",
            ]
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout + 8,
            )
            if proc.returncode != 0:
                stderr = (proc.stderr or "")[-500:]
                return {
                    "status": "compile_error" if "SyntaxError" in stderr else "runtime_error",
                    "available": True,
                    "reason": stderr or "容器执行失败",
                    "cases": [],
                }
            payload = json.loads((proc.stdout or "").strip() or "{}")
            checked = payload.get("cases", [])
            passed = sum(1 for item in checked if item.get("passed"))
            return {
                "status": "passed" if checked and passed == len(checked) else "failed",
                "available": True,
                "reason": "",
                "cases": checked,
                "passed": passed,
                "total": len(checked),
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "available": True,
            "reason": f"执行超时（>{timeout}s），容器已终止",
            "cases": [],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "runtime_error",
            "available": False,
            "reason": f"沙箱调用失败：{exc}",
            "cases": [],
        }