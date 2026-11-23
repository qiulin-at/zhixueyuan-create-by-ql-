#!/usr/bin/env python3
"""Browser Bridge 命令行控制器

用法示例：
  python ctl.py health
  python ctl.py tabs
  python ctl.py goto http://127.0.0.1:5173/admin
  python ctl.py info
  python ctl.py text --limit 800
  python ctl.py click --text "登录"
  python ctl.py type "#username" student --clear-last
  python ctl.py shot out.png --width 1440 --height 900
  python ctl.py eval "document.title"
  python ctl.py call page.scroll --params '{"y": 600}'

只依赖标准库。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / ".token"
DEFAULT_URL = "http://127.0.0.1:8766"


def read_token(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("BRIDGE_TOKEN")
    if env:
        return env
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"找不到 token：{TOKEN_FILE}，请先启动 server.py 或用 --token 指定")


def request(url: str, token: str, payload: dict | None = None, timeout: float = 60) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if data is not None else "GET",
        headers={"Content-Type": "application/json", "X-Bridge-Token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"连不上本地桥（{url}）：{exc.reason}。请先运行 python bridge/server.py") from exc


def send(action: str, params: dict | None = None, timeout: float = 30, base: str = DEFAULT_URL, token: str = "") -> dict:
    return request(
        f"{base}/cmd",
        token,
        {"action": action, "params": params or {}, "timeout": timeout},
        timeout=timeout + 5,
    )


def print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="通过本地桥操控 Edge")
    p.add_argument("--base", default=DEFAULT_URL, help="控制接口地址")
    p.add_argument("--token", default=None, help="桥 token，默认读取 bridge/.token")
    p.add_argument("--raw", action="store_true", help="只输出 data 部分")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="查看桥与扩展连接状态")
    sub.add_parser("tabs", help="列出所有标签页")

    g = sub.add_parser("goto", help="打开网址")
    g.add_argument("url")
    g.add_argument("--tab", type=int, default=None)

    sub.add_parser("info", help="当前页 URL/标题/尺寸")
    t = sub.add_parser("text", help="读取页面纯文本")
    t.add_argument("--limit", type=int, default=4000)
    t.add_argument("--tab", type=int, default=None)
    h = sub.add_parser("html", help="读取页面 HTML")
    h.add_argument("--limit", type=int, default=8000)
    h.add_argument("--tab", type=int, default=None)

    c = sub.add_parser("click", help="点击元素")
    c.add_argument("selector", nargs="?", default="")
    c.add_argument("--text", default="", help="按可见文本匹配")
    c.add_argument("--tab", type=int, default=None)

    ty = sub.add_parser("type", help="向输入框输入")
    ty.add_argument("selector")
    ty.add_argument("value")
    ty.add_argument("--append", action="store_true", help="追加而非替换")
    ty.add_argument("--tab", type=int, default=None)

    s = sub.add_parser("scroll", help="滚动页面")
    s.add_argument("--y", type=int, default=0)
    s.add_argument("--selector", default="")
    s.add_argument("--tab", type=int, default=None)

    e = sub.add_parser("eval", help="在页面内执行 JS 表达式")
    e.add_argument("code")
    e.add_argument("--tab", type=int, default=None)

    sh = sub.add_parser("shot", help="截图（可视区）")
    sh.add_argument("path", nargs="?", default="screenshot.png")
    sh.add_argument("--tab", type=int, default=None)
    sh.add_argument("--width", type=int, default=None)
    sh.add_argument("--height", type=int, default=None)

    w = sub.add_parser("wait", help="等待若干秒")
    w.add_argument("seconds", type=float, nargs="?", default=1.0)

    ca = sub.add_parser("call", help="直接调用扩展命令")
    ca.add_argument("action")
    ca.add_argument("--params", default="{}")
    ca.add_argument("--timeout", type=float, default=30)
    return p


def main() -> int:
    args = build_parser().parse_args()
    token = read_token(args.token)

    if args.cmd == "health":
        data = request(f"{args.base}/health", token, timeout=10)
        print_json(data)
        return 0 if data.get("extension_connected") else 2

    if args.cmd == "tabs":
        result = send("tabs.list", {}, 15, args.base, token)
    elif args.cmd == "goto":
        result = send("nav.goto", {"url": args.url, "tabId": args.tab}, 30, args.base, token)
    elif args.cmd == "info":
        result = send("page.info", {}, 15, args.base, token)
    elif args.cmd == "text":
        result = send("page.text", {"limit": args.limit, "tabId": args.tab}, 15, args.base, token)
    elif args.cmd == "html":
        result = send("page.html", {"limit": args.limit, "tabId": args.tab}, 20, args.base, token)
    elif args.cmd == "click":
        if not args.selector and not args.text:
            raise SystemExit("click 需要 selector 或 --text")
        result = send("page.click", {"selector": args.selector, "text": args.text, "tabId": args.tab}, 20, args.base, token)
    elif args.cmd == "type":
        result = send(
            "page.type",
            {"selector": args.selector, "value": args.value, "clear": not args.append, "tabId": args.tab},
            20,
            args.base,
            token,
        )
    elif args.cmd == "scroll":
        result = send("page.scroll", {"y": args.y, "selector": args.selector, "tabId": args.tab}, 15, args.base, token)
    elif args.cmd == "eval":
        result = send("page.eval", {"code": args.code, "tabId": args.tab}, 20, args.base, token)
    elif args.cmd == "shot":
        params = {"tabId": args.tab}
        if args.width and args.height:
            params.update({"width": args.width, "height": args.height})
        result = send("shot.capture", params, 30, args.base, token)
    elif args.cmd == "wait":
        result = send("wait", {"seconds": args.seconds}, args.seconds + 5, args.base, token)
    elif args.cmd == "call":
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--params 不是合法 JSON：{exc}") from exc
        result = send(args.action, params, args.timeout, args.base, token)
    else:
        raise SystemExit(f"未知命令：{args.cmd}")

    if not result.get("ok"):
        print_json({"ok": False, "error": result.get("error"), "elapsed": result.get("elapsed")})
        return 1

    data = result.get("data")

    if args.cmd == "shot":
        data_url = (data or {}).get("dataUrl", "")
        if "," not in data_url:
            raise SystemExit("截图返回格式异常")
        out = Path(args.path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
        payload = {
            "ok": True,
            "file": str(out.resolve()),
            "bytes": out.stat().st_size,
            "title": data.get("title"),
            "url": data.get("url"),
        }
        print_json(payload)
        return 0

    if args.raw:
        print_json(data)
    else:
        print_json({"ok": True, "data": data, "elapsed": result.get("elapsed")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
