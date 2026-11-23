#!/usr/bin/env python3
"""Browser Bridge - 本地桥服务

两个职责：
1. WebSocket 服务（默认 127.0.0.1:8765/ws?token=...）：供 Edge 扩展常驻连接；
2. HTTP 控制接口（默认 127.0.0.1:8766）：供脚本 / AI 下发命令。

只依赖 Python 标准库，不需要 pip 安装任何东西。
安全：两个端口都只绑定 127.0.0.1；WS 与 HTTP 都校验 token（自动生成到 .token）。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TOKEN_FILE = Path(__file__).resolve().with_name(".token")
MAX_FRAME = 64 * 1024 * 1024


# --------------------------------------------------------------------------- #
# WebSocket 基础帧协议
# --------------------------------------------------------------------------- #
def recv_exact(sock: socket.socket, size: int) -> bytes:
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("连接已被对端关闭")
        buf += chunk
    return buf


def recv_frame(sock: socket.socket) -> tuple[int, int, bytes]:
    head = recv_exact(sock, 2)
    fin = head[0] & 0x80
    opcode = head[0] & 0x0F
    masked = head[1] & 0x80
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", recv_exact(sock, 8))[0]
    if length > MAX_FRAME:
        raise ConnectionError(f"帧过大：{length} 字节")
    mask = recv_exact(sock, 4) if masked else None
    payload = recv_exact(sock, length) if length else b""
    if mask:
        payload = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
    return fin, opcode, payload


def send_frame(sock: socket.socket, payload: bytes | str, opcode: int = 0x1) -> None:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    length = len(payload)
    header = bytearray([0x80 | opcode])
    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header += struct.pack(">H", length)
    else:
        header.append(127)
        header += struct.pack(">Q", length)
    sock.sendall(bytes(header) + payload)


# --------------------------------------------------------------------------- #
# 连接与调度中心
# --------------------------------------------------------------------------- #
class ExtensionConn:
    def __init__(self, sock: socket.socket, addr):
        self.sock = sock
        self.addr = addr
        self.alive = True
        self.send_lock = threading.Lock()
        self.connected_at = time.time()

    def send_json(self, obj: dict) -> None:
        data = json.dumps(obj, ensure_ascii=False)
        with self.send_lock:
            send_frame(self.sock, data)

    def close(self) -> None:
        self.alive = False
        try:
            send_frame(self.sock, b"", opcode=0x8)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class Hub:
    def __init__(self, token: str, verbose: bool = False):
        self.token = token
        self.verbose = verbose
        self.conn: ExtensionConn | None = None
        self.pending: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.counter = {"commands": 0, "errors": 0}

    # ---- 连接管理 ----
    def attach(self, conn: ExtensionConn) -> None:
        with self.lock:
            old = self.conn
            self.conn = conn
        if old is not None and old is not conn:
            old.close()
        self.log(f"扩展已连接 {conn.addr[0]}:{conn.addr[1]}")

    def detach(self, conn: ExtensionConn) -> None:
        with self.lock:
            if self.conn is conn:
                self.conn = None
            slots = list(self.pending.values())
            self.pending.clear()
        for slot in slots:
            slot["result"] = {"ok": False, "error": "扩展连接已断开"}
            slot["event"].set()
        self.log("扩展连接已断开")

    def status(self) -> dict:
        with self.lock:
            conn = self.conn
            return {
                "extension_connected": bool(conn and conn.alive),
                "connected_seconds": round(time.time() - conn.connected_at, 1) if conn else 0,
                "pending": len(self.pending),
                "commands": self.counter["commands"],
                "errors": self.counter["errors"],
            }

    # ---- 消息处理 ----
    def on_message(self, obj: dict) -> None:
        msg_id = obj.get("id")
        if msg_id:
            with self.lock:
                slot = self.pending.get(msg_id)
            if slot is not None:
                slot["result"] = obj
                slot["event"].set()
            return
        if obj.get("type") == "hello":
            self.log(f"握手成功：{obj.get('name', 'extension')} v{obj.get('version', '?')}")
        elif obj.get("type") == "pong":
            pass

    # ---- 下发命令 ----
    def call(self, action: str, params: dict | None = None, timeout: float = 20.0):
        if action == "wait":
            seconds = float((params or {}).get("seconds", 1))
            time.sleep(max(0.0, min(seconds, 60)))
            return {"waited": seconds}

        with self.lock:
            conn = self.conn
        if conn is None or not conn.alive:
            raise RuntimeError("扩展未连接：请确认 Edge 已加载扩展，并在弹窗中点击「保存并重连」")

        msg_id = uuid.uuid4().hex
        slot = {"event": threading.Event(), "result": None}
        with self.lock:
            self.pending[msg_id] = slot
            self.counter["commands"] += 1

        try:
            conn.send_json({"id": msg_id, "action": action, "params": params or {}})
        except Exception as exc:
            with self.lock:
                self.pending.pop(msg_id, None)
                self.counter["errors"] += 1
            raise RuntimeError(f"命令发送失败：{exc}") from exc

        if not slot["event"].wait(timeout):
            with self.lock:
                self.pending.pop(msg_id, None)
                self.counter["errors"] += 1
            raise TimeoutError(f"命令超时（{timeout:g}s）：{action}")

        with self.lock:
            self.pending.pop(msg_id, None)

        result = slot["result"] or {"ok": False, "error": "空响应"}
        if not result.get("ok"):
            with self.lock:
                self.counter["errors"] += 1
            raise RuntimeError(result.get("error") or "扩展执行失败")
        return result.get("data")

    def log(self, message: str) -> None:
        print(f"[bridge] {time.strftime('%H:%M:%S')} {message}", flush=True)


# --------------------------------------------------------------------------- #
# WebSocket 服务
# --------------------------------------------------------------------------- #
def perform_handshake(sock: socket.socket, token: str) -> bool:
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = sock.recv(4096)
        if not chunk:
            return False
        raw += chunk
        if len(raw) > 65536:
            return False

    head = raw.split(b"\r\n\r\n", 1)[0].decode("latin1")
    lines = head.split("\r\n")
    request_line = lines[0] if lines else ""
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    parts = request_line.split(" ")
    path = parts[1] if len(parts) > 1 else "/"
    parsed = urlparse(path)
    query = parse_qs(parsed.query)

    def deny(status: str, reason: str) -> bool:
        body = json.dumps({"ok": False, "error": reason}).encode()
        sock.sendall(
            f"HTTP/1.1 {status}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body
        )
        return False

    if parsed.path != "/ws":
        return deny("404 Not Found", "只支持 /ws")
    if query.get("token", [""])[0] != token:
        return deny("403 Forbidden", "token 不正确")

    key = headers.get("sec-websocket-key")
    if not key:
        return deny("400 Bad Request", "缺少 Sec-WebSocket-Key")

    accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    sock.sendall(
        (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode()
    )
    return True


def serve_extension(conn: ExtensionConn, hub: Hub) -> None:
    hub.attach(conn)
    assembly = bytearray()
    assembly_opcode = None
    try:
        while conn.alive:
            fin, opcode, payload = recv_frame(conn.sock)
            if opcode == 0x8:  # close
                break
            if opcode == 0x9:  # ping
                with conn.send_lock:
                    send_frame(conn.sock, payload, opcode=0xA)
                continue
            if opcode == 0xA:  # pong
                continue

            # 大消息（如截图 base64）会被拆成首帧 + 若干 continuation 帧，必须拼装
            if opcode in (0x1, 0x2):
                assembly = bytearray(payload)
                assembly_opcode = opcode
                if not fin:
                    continue
            elif opcode == 0x0:
                if assembly_opcode is None:
                    continue
                assembly.extend(payload)
                if not fin:
                    continue
            else:
                continue

            raw = bytes(assembly)
            assembly = bytearray()
            assembly_opcode = None
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception:
                if hub.verbose:
                    hub.log(f"丢弃无法解析的消息（{len(raw)} 字节）")
                continue
            if isinstance(obj, dict):
                hub.on_message(obj)
    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()
        hub.detach(conn)


def ws_server_loop(server: socket.socket, hub: Hub) -> None:
    while True:
        try:
            client, addr = server.accept()
        except OSError:
            return
        client.settimeout(None)
        try:
            if not perform_handshake(client, hub.token):
                client.close()
                continue
        except Exception:
            try:
                client.close()
            except Exception:
                pass
            continue
        conn = ExtensionConn(client, addr)
        threading.Thread(target=serve_extension, args=(conn, hub), daemon=True).start()


# --------------------------------------------------------------------------- #
# HTTP 控制接口
# --------------------------------------------------------------------------- #
class ControlHandler(BaseHTTPRequestHandler):
    hub: Hub
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # 静默访问日志
        if getattr(self.hub, "verbose", False):
            sys.stderr.write("[http] " + (fmt % args) + "\n")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("X-Bridge-Token", "") == self.hub.token

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"ok": True, **self.hub.status()})
            return
        if path == "/":
            self._json(
                200,
                {
                    "name": "Browser Bridge",
                    "usage": {
                        "health": "GET /health",
                        "command": "POST /cmd  {action, params, timeout}  需 X-Bridge-Token 头",
                    },
                    **self.hub.status(),
                },
            )
            return
        self._json(404, {"ok": False, "error": "未知路径"})

    def do_POST(self):  # noqa: N802
        if urlparse(self.path).path != "/cmd":
            self._json(404, {"ok": False, "error": "未知路径"})
            return
        if not self._authorized():
            self._json(403, {"ok": False, "error": "token 不正确（X-Bridge-Token）"})
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > 8 * 1024 * 1024:
            self._json(400, {"ok": False, "error": "请求体为空或过大"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json(400, {"ok": False, "error": "请求体不是合法 JSON"})
            return

        action = (payload or {}).get("action")
        if not action:
            self._json(400, {"ok": False, "error": "缺少 action"})
            return
        params = payload.get("params") or {}
        timeout = float(payload.get("timeout") or 20)

        started = time.time()
        try:
            data = self.hub.call(action, params, timeout=timeout)
        except (RuntimeError, TimeoutError) as exc:
            self._json(200, {"ok": False, "error": str(exc), "elapsed": round(time.time() - started, 2)})
            return
        self._json(200, {"ok": True, "data": data, "elapsed": round(time.time() - started, 2)})


# --------------------------------------------------------------------------- #
# 启动
# --------------------------------------------------------------------------- #
def load_token(explicit: str | None) -> str:
    if explicit:
        return explicit
    if TOKEN_FILE.exists():
        saved = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    token = base64.urlsafe_b64encode(os.urandom(18)).decode().rstrip("=")
    TOKEN_FILE.write_text(token, encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description="Edge 浏览器本地桥")
    parser.add_argument("--ws-port", type=int, default=8765, help="扩展 WebSocket 端口")
    parser.add_argument("--http-port", type=int, default=8766, help="控制接口 HTTP 端口")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址，默认仅本机")
    parser.add_argument("--token", default=None, help="指定 token（默认读取/生成 .token）")
    parser.add_argument("--verbose", action="store_true", help="打印 HTTP 访问日志")
    args = parser.parse_args()

    token = load_token(args.token)
    hub = Hub(token, verbose=args.verbose)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.ws_port))
    server.listen(8)

    threading.Thread(target=ws_server_loop, args=(server, hub), daemon=True).start()

    ControlHandler.hub = hub
    httpd = ThreadingHTTPServer((args.host, args.http_port), ControlHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    print("=" * 66)
    print("  Browser Bridge 已启动")
    print(f"  WebSocket : ws://{args.host}:{args.ws_port}/ws")
    print(f"  控制接口  : http://{args.host}:{args.http_port}/cmd")
    print(f"  Token     : {token}")
    print(f"  Token 文件: {TOKEN_FILE}")
    print("-" * 66)
    print("  下一步：Edge → edge://extensions → 开发者模式 → 加载解压缩的扩展")
    print("          选择 tools/edge-bridge/extension，然后在弹窗填入上面的 Token")
    print("  按 Ctrl+C 退出")
    print("=" * 66)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[bridge] 正在关闭…")
        try:
            server.close()
        except Exception:
            pass
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
