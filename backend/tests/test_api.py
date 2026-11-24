import uuid

from conftest import client


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def login(client, account="student", password="123456"):
    response = client.post("/api/auth/login", json={"account": account, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    return body["data"]["access_token"]


def test_health(client):
    response = client.get("/api/health")
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["database"] == "up"
    assert body["data"]["llm_mode"] == "mock"


def test_course_filter_sort(client):
    response = client.get(
        "/api/courses",
        params={"tech_system": "人工智能", "level": "beginner", "sort": "rating", "page_size": 10},
    )
    data = response.json()["data"]
    assert data["total"] >= 1
    assert all(item["tech_system"] == "人工智能" for item in data["items"])
    assert all(item["level"] == "beginner" for item in data["items"])
    ratings = [item["rating"] for item in data["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_course_search_by_teacher(client):
    response = client.get("/api/courses", params={"keyword": "王老师"})
    data = response.json()["data"]
    assert data["total"] >= 1


def test_course_search_by_title(client):
    response = client.get("/api/courses", params={"keyword": "Hadoop"})
    data = response.json()["data"]
    assert data["total"] == 1
    assert "Hadoop" in data["items"][0]["title"]


def test_register_and_login(client):
    username = f"stu_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@test.cn", "password": "abc123456"},
    )
    body = response.json()
    assert body["code"] == 0
    token = body["data"]["access_token"]
    me = client.get("/api/users/me", headers=auth(token)).json()["data"]
    assert me["username"] == username
    assert me["role"] == "student"


def test_register_duplicate(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "student", "email": "student@zhixueyun.cn", "password": "abc123456"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == 40901


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={"account": "student", "password": "wrong-pass"})
    assert response.status_code == 401
    assert response.json()["code"] == 40101


def test_course_detail(client):
    response = client.get("/api/courses/1")
    data = response.json()["data"]
    assert data["id"] == 1
    assert len(data["chapters"]) == 5
    assert len(data["objectives"]) >= 3


def test_favorite_and_progress(client):
    token = login(client)
    headers = auth(token)
    first = client.post("/api/courses/3/favorite", headers=headers).json()["data"]
    assert first["is_favorite"] is True
    second = client.post("/api/courses/3/favorite", headers=headers).json()["data"]
    assert second["is_favorite"] is False

    detail = client.get("/api/courses/2", headers=headers).json()["data"]
    chapter_id = detail["chapters"][0]["id"]
    response = client.put(
        "/api/courses/2/progress",
        json={"chapter_id": chapter_id, "minutes": 30},
        headers=headers,
    )
    data = response.json()["data"]
    assert data["progress"] == 20
    assert data["study_minutes"] >= 30

    progress = client.get("/api/courses/2/progress", headers=headers).json()["data"]
    assert progress["progress"] == 20


def test_ai_chat_mock(client):
    token = login(client)
    headers = auth(token)
    response = client.post(
        "/api/ai/chat",
        json={"message": "HDFS 的副本机制是什么？", "course_id": 2},
        headers=headers,
    )
    data = response.json()["data"]
    assert data["mode"] == "mock"
    assert "HDFS" in data["answer"]
    conversation_id = data["conversation_id"]

    follow = client.post(
        "/api/ai/chat",
        json={"message": "MapReduce 的 Shuffle 做了什么？", "conversation_id": conversation_id},
        headers=headers,
    )
    assert follow.json()["data"]["conversation_id"] == conversation_id
    assert "Shuffle" in follow.json()["data"]["answer"]

    conversations = client.get("/api/ai/conversations", headers=headers).json()["data"]
    assert conversations["total"] >= 1


def test_ai_chat_rag_citation(client):
    token = login(client)
    response = client.post(
        "/api/ai/chat",
        json={"message": "pandas 分组聚合怎么用？", "course_id": 1},
        headers=auth(token),
    )
    data = response.json()["data"]
    assert data["mode"] == "mock"
    assert "参考：" in data["answer"]
    assert "Python 数据分析实战" in data["answer"]
    assert "第 3 章" in data["answer"]


def test_ai_chat_rag_no_cross_course(client):
    token = login(client)
    response = client.post(
        "/api/ai/chat",
        json={"message": "pandas 分组聚合怎么用？", "course_id": 2},
        headers=auth(token),
    )
    answer = response.json()["data"]["answer"]
    assert "Python 数据分析实战" not in answer


def test_ai_chat_rag_without_course(client):
    token = login(client)
    response = client.post(
        "/api/ai/chat",
        json={"message": "pandas 分组聚合怎么用？"},
        headers=auth(token),
    )
    answer = response.json()["data"]["answer"]
    assert "参考：" not in answer


def test_rag_retrieval_scope(client):
    from app.database import SessionLocal
    from app.services.rag import format_materials, format_reference_line, retrieve_materials

    db = SessionLocal()
    try:
        items = retrieve_materials(db, 1, "pandas 分组聚合", top_k=3)
        assert items
        assert all(item["course_id"] == 1 for item in items)
        assert items[0]["score"] >= items[-1]["score"]
        assert retrieve_materials(db, 9999, "pandas", top_k=3) == []
        assert retrieve_materials(db, 1, "！！！", top_k=3) == []
        assert retrieve_materials(db, 2, "pandas 分组聚合", top_k=3) == []
    finally:
        db.close()
    assert format_materials([]) == "（无匹配资料）"
    assert "资料《资料A》" in format_reference_line(
        "课程A", [{"chapter_title": "", "title": "资料A", "chapter_sort": 0}]
    )


def test_ai_learning_path(client):
    token = login(client)
    response = client.post(
        "/api/ai/learning-path",
        json={"goal": "三个月拿下 HCIA-AI", "weekly_hours": 8, "weak_points": "深度学习"},
        headers=auth(token),
    )
    data = response.json()["data"]
    assert data["mode"] in {"mock", "online"}
    assert "阶段" in data["content"]


def test_ai_grade(client):
    token = login(client)
    response = client.post(
        "/api/ai/grade",
        json={
            "title": "两数之和",
            "language": "python",
            "code": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n",
        },
        headers=auth(token),
    )
    result = response.json()["data"]["result"]
    assert 0 <= result["score"] <= 100
    assert "dimension_scores" in result


def test_ai_study_report(client):
    token = login(client)
    response = client.post("/api/ai/study-report", json={"period": "week"}, headers=auth(token))
    data = response.json()["data"]
    assert data["stats"]["course_count"] >= 1
    assert "本周" in data["content"]


def test_admin_forbidden_for_student(client):
    token = login(client)
    response = client.get("/api/admin/users", headers=auth(token))
    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_admin_manages_users(client):
    token = login(client, "admin")
    response = client.get("/api/admin/users", headers=auth(token))
    data = response.json()["data"]
    assert data["total"] >= 4


def test_admin_course_status(client):
    token = login(client, "admin")
    headers = auth(token)
    response = client.patch("/api/admin/courses/18/status", json={"status": "offline"}, headers=headers)
    assert response.json()["data"]["status"] == "offline"
    assert client.get("/api/courses/18").status_code == 404
    client.patch("/api/admin/courses/18/status", json={"status": "published"}, headers=headers)


def test_jobs(client):
    response = client.get("/api/jobs", params={"keyword": "昂楷"})
    data = response.json()["data"]
    assert data["total"] >= 1
    token = login(client)
    job_id = data["items"][0]["id"]
    detail = client.get(f"/api/jobs/{job_id}", headers=auth(token)).json()["data"]
    assert detail["company"]
    applied = client.post(f"/api/jobs/{job_id}/apply", headers=auth(token))
    assert applied.json()["code"] == 0
    duplicated = client.post(f"/api/jobs/{job_id}/apply", headers=auth(token))
    assert duplicated.status_code == 409

def test_course_comments(client):
    token = login(client)
    headers = auth(token)
    before = client.get("/api/courses/3/comments").json()["data"]
    created = client.post(
        "/api/courses/3/comments",
        json={"content": "课程节奏合适，示例很实用。", "rating": 5},
        headers=headers,
    )
    assert created.json()["code"] == 0
    after = client.get("/api/courses/3/comments").json()["data"]
    assert after["total"] == before["total"] + 1
    assert after["items"][0]["user_name"]


def test_notifications_require_login(client):
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/notifications/unread-count").status_code == 401
    assert client.post("/api/notifications/read-all").status_code == 401


def test_notifications_stream_requires_token(client):
    response = client.get("/api/notifications/stream")
    assert response.status_code == 401
    assert response.json()["code"] == 40101


def test_notifications_stream_route_with_token(client):
    import asyncio
    from types import SimpleNamespace

    from app.routers.notifications import stream_notifications

    token = login(client)
    response = asyncio.run(stream_notifications(SimpleNamespace(), token))
    assert response.media_type == "text/event-stream"
    asyncio.run(response.body_iterator.aclose())


def test_notification_event_stream_stops_when_disconnected(client):
    import asyncio

    from app.routers.notifications import notification_event_stream

    class DisconnectedRequest:
        async def is_disconnected(self):
            return True

    async def collect():
        return [chunk async for chunk in notification_event_stream(DisconnectedRequest(), 4, interval=0)]

    assert asyncio.run(collect()) == []


def test_notification_event_stream_emits_events(client):
    import asyncio
    import json

    from app.routers.notifications import notification_event_stream

    class ConnectedRequest:
        async def is_disconnected(self):
            return False

    async def collect():
        events = []
        async for chunk in notification_event_stream(ConnectedRequest(), 4, interval=0):
            events.append(chunk)
            if len(events) >= 2:
                break
        return events

    events = asyncio.run(collect())
    assert len(events) == 2
    payload = json.loads(events[0][len("data: ") :].strip())
    assert payload["unread"] >= 0
    assert "ts" in payload


def test_notifications_stream_rejects_invalid_token(client):
    response = client.get("/api/notifications/stream", params={"token": "invalid-token"})
    assert response.status_code == 401


def test_notification_safe_generate_swallows_errors(client):
    from types import SimpleNamespace

    from app.routers.notifications import _safe_generate

    class BrokenDb:
        def rollback(self):
            return None

    _safe_generate(BrokenDb(), SimpleNamespace(id=999, username="broken"))


def test_notification_read_flow(client):
    headers = auth(login(client, "student"))

    first = client.get("/api/notifications", headers=headers).json()["data"]
    assert first["total"] >= 1
    assert {"id", "type", "title", "content", "link", "is_read", "created_at"} <= set(first["items"][0])

    # 幂等：重复拉取不应因为「学习提醒生成」而不断新增
    again = client.get("/api/notifications", headers=headers).json()["data"]
    assert again["total"] == first["total"]

    unread = client.get("/api/notifications/unread-count", headers=headers).json()["data"]["unread"]
    assert unread >= 1

    only_unread = client.get(
        "/api/notifications", params={"unread_only": "true"}, headers=headers
    ).json()["data"]
    assert only_unread["total"] == unread
    assert all(item["is_read"] is False for item in only_unread["items"])

    target = next(item for item in first["items"] if not item["is_read"])
    marked = client.post(f"/api/notifications/{target['id']}/read", headers=headers).json()
    assert marked["code"] == 0
    assert marked["data"]["is_read"] is True
    assert marked["data"]["unread"] == unread - 1

    all_read = client.post("/api/notifications/read-all", headers=headers).json()["data"]
    assert all_read["unread"] == 0
    assert client.get("/api/notifications/unread-count", headers=headers).json()["data"]["unread"] == 0


def test_notification_belongs_to_owner(client):
    student_headers = auth(login(client, "student"))
    admin_headers = auth(login(client, "admin"))

    student_items = client.get("/api/notifications", headers=student_headers).json()["data"]["items"]
    admin_ids = {
        item["id"] for item in client.get("/api/notifications", headers=admin_headers).json()["data"]["items"]
    }
    foreign = next((item for item in student_items if item["id"] not in admin_ids), None)
    assert foreign is not None
    response = client.post(f"/api/notifications/{foreign['id']}/read", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["code"] == 40401


def test_favorite_course_comment_notifies(client):
    student_headers = auth(login(client, "student"))
    admin_headers = auth(login(client, "admin"))

    favorited = client.post("/api/courses/5/favorite", headers=student_headers).json()["data"]
    assert favorited["is_favorite"] is True

    created = client.post(
        "/api/courses/5/comments",
        json={"content": "TEST 收藏通知用例评论", "rating": 5},
        headers=admin_headers,
    )
    assert created.json()["code"] == 0

    items = client.get("/api/notifications", headers=student_headers).json()["data"]["items"]
    hit = [item for item in items if item["link"] == "/courses/5" and "有新评价" in item["title"]]
    assert hit
    assert hit[0]["type"] == "course_update"
    assert hit[0]["is_read"] is False

    # 清理：取消收藏，避免影响后续用例
    client.post("/api/courses/5/favorite", headers=student_headers)


def test_comment_is_upsert_not_duplicate(client):
    headers = auth(login(client, "student"))
    before = client.get("/api/courses/3/comments").json()["data"]

    first = client.post(
        "/api/courses/3/comments",
        json={"content": "同一用户的第一次提交", "rating": 4},
        headers=headers,
    ).json()
    assert first["code"] == 0

    second = client.post(
        "/api/courses/3/comments",
        json={"content": "同一用户的第二次提交", "rating": 5},
        headers=headers,
    ).json()
    assert second["data"]["updated"] is True

    after = client.get("/api/courses/3/comments").json()["data"]
    assert after["total"] == before["total"]  # 同一用户同一课程不新增
    assert any(item["content"] == "同一用户的第二次提交" for item in after["items"])


def test_comment_replies_and_likes(client):
    headers = auth(login(client))
    comments = client.get("/api/courses/3/comments").json()["data"]["items"]
    assert comments
    comment = comments[0]

    reply = client.post(
        f"/api/courses/3/comments/{comment['id']}/replies",
        json={"content": "回复测试"},
        headers=headers,
    ).json()["data"]
    assert reply["comment_id"] == comment["id"]
    assert reply["parent_id"] is None

    child = client.post(
        f"/api/courses/3/comments/{comment['id']}/replies",
        json={"content": "楼中楼回复", "parent_id": reply["id"]},
        headers=headers,
    ).json()["data"]
    assert child["parent_id"] == reply["id"]

    replies = client.get(f"/api/courses/3/comments/{comment['id']}/replies").json()["data"]
    assert replies["total"] == 2
    assert any(item["parent_id"] == reply["id"] for item in replies["items"])

    bad_parent = client.post(
        f"/api/courses/3/comments/{comment['id']}/replies",
        json={"content": "bad", "parent_id": 99999},
        headers=headers,
    )
    assert bad_parent.status_code == 404

    liked = client.post(f"/api/courses/3/comments/{comment['id']}/like", headers=headers).json()["data"]
    assert liked["liked"] is True
    assert liked["likes_count"] == 1

    unliked = client.post(f"/api/courses/3/comments/{comment['id']}/like", headers=headers).json()["data"]
    assert unliked["liked"] is False
    assert unliked["likes_count"] == 0

    listed = client.get("/api/courses/3/comments", headers=headers).json()["data"]["items"]
    hit = next(item for item in listed if item["id"] == comment["id"])
    assert hit["replies_count"] >= 2
    assert hit["likes_count"] == 0
    assert hit["liked_by_me"] is False

    unauth = client.post(
        f"/api/courses/3/comments/{comment['id']}/replies",
        json={"content": "未登录回复"},
    )
    assert unauth.status_code == 401


def test_password_reset_flow(client):
    email = "student@zhixueyun.cn"
    sent = client.post("/api/auth/send-code", json={"email": email}).json()
    code = sent["data"]["demo_code"]
    assert len(code) == 6

    wrong = "000001" if code != "000001" else "000002"
    bad = client.post(
        "/api/auth/reset-password",
        json={"email": email, "code": wrong, "new_password": "newpass123"},
    )
    assert bad.status_code == 400

    done = client.post(
        "/api/auth/reset-password",
        json={"email": email, "code": code, "new_password": "newpass123"},
    )
    assert done.json()["code"] == 0
    assert client.post("/api/auth/login", json={"account": "student", "password": "newpass123"}).status_code == 200

    # 验证码用过即失效
    reused = client.post(
        "/api/auth/reset-password",
        json={"email": email, "code": code, "new_password": "another123"},
    )
    assert reused.status_code == 400

    # 还原演示密码，避免影响其他用例与手工演示
    sent_again = client.post("/api/auth/send-code", json={"email": email}).json()
    restored = client.post(
        "/api/auth/reset-password",
        json={"email": email, "code": sent_again["data"]["demo_code"], "new_password": "123456"},
    )
    assert restored.json()["code"] == 0
    assert client.post("/api/auth/login", json={"account": "student", "password": "123456"}).status_code == 200


def test_protected_endpoints_require_login(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/notifications").status_code == 401
    assert client.post("/api/ai/chat", json={"message": "hi"}).status_code == 401
    assert client.get("/api/admin/stats").status_code == 401


def test_pagination_validation(client):
    assert client.get("/api/courses", params={"page": 0}).status_code == 422
    assert client.get("/api/courses", params={"page_size": 51}).status_code == 422
    headers = auth(login(client))
    assert client.get("/api/notifications", params={"page_size": 51}, headers=headers).status_code == 422


def test_not_found_resources(client):
    headers = auth(login(client))
    assert client.get("/api/courses/999999", headers=headers).status_code == 404
    assert client.get("/api/jobs/999999", headers=headers).status_code == 404
    assert client.post("/api/notifications/999999/read", headers=headers).status_code == 404

    admin = auth(login(client, "admin"))
    response = client.patch("/api/admin/courses/999999/status", json={"status": "offline"}, headers=admin)
    assert response.status_code == 404


def test_teacher_cannot_manage_others_course(client):
    teacher = auth(login(client, "teacher_wang"))
    response = client.patch("/api/admin/courses/2/status", json={"status": "offline"}, headers=teacher)
    assert response.status_code == 403
    assert response.json()["code"] == 40301

    student = auth(login(client))
    assert client.get("/api/admin/courses", headers=student).status_code == 403
    assert client.get("/api/admin/users", headers=student).status_code == 403


def test_invalid_enum_payloads(client):
    admin = auth(login(client, "admin"))
    assert client.patch("/api/admin/courses/1/status", json={"status": "archived"}, headers=admin).status_code == 422
    assert client.patch("/api/admin/users/5/role", json={"role": "root"}, headers=admin).status_code == 422
    assert client.post("/api/auth/register", json={"username": "ab", "email": "a@b.cn", "password": "123456"}).status_code == 422


def test_favorite_toggle_is_idempotent(client):
    headers = auth(login(client))
    first = client.post("/api/courses/6/favorite", headers=headers).json()["data"]
    assert first["is_favorite"] is True
    try:
        second = client.post("/api/courses/6/favorite", headers=headers).json()["data"]
        assert second["is_favorite"] is False
    finally:
        detail = client.get("/api/courses/6", headers=headers).json()["data"]
        if detail["is_favorite"]:
            client.post("/api/courses/6/favorite", headers=headers)


def test_ai_fallback_when_llm_unavailable(client, monkeypatch):
    import httpx as httpx_module

    from app.config import settings

    class BoomClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            raise httpx_module.ConnectError("mock network down")

    monkeypatch.setattr(settings, "llm_api_key", "sk-test-key", raising=False)
    monkeypatch.setattr(httpx_module, "Client", BoomClient)

    headers = auth(login(client))
    response = client.post("/api/ai/chat", json={"message": "断网时应该降级"}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mode"] == "mock"
    assert data["answer"]


def test_ai_conversation_isolation(client):
    student = auth(login(client))
    admin = auth(login(client, "admin"))

    created = client.post("/api/ai/chat", json={"message": "会话隔离用例"}, headers=student).json()["data"]
    conversation_id = created["conversation_id"]

    response = client.post(
        "/api/ai/chat",
        json={"message": "越权续写", "conversation_id": conversation_id},
        headers=admin,
    )
    assert response.status_code == 404


def test_profile_and_personal_lists(client):
    headers = auth(login(client))
    me = client.get("/api/users/me", headers=headers).json()["data"]
    assert me["username"] == "student"

    updated = client.put(
        "/api/users/me",
        json={"nickname": "测试昵称", "major": "计算机科学与技术"},
        headers=headers,
    ).json()["data"]
    assert updated["nickname"] == "测试昵称"

    # 还原资料，避免影响演示
    client.put("/api/users/me", json={"nickname": me["nickname"], "major": me["major"]}, headers=headers)

    favorites = client.get("/api/users/me/favorites", headers=headers).json()["data"]
    assert "items" in favorites and "total" in favorites
    learning = client.get("/api/users/me/learning", headers=headers).json()["data"]
    assert "items" in learning and "total_minutes" in learning


def test_admin_lists_and_filters(client):
    admin = auth(login(client, "admin"))

    stats = client.get("/api/admin/stats", headers=admin).json()["data"]
    assert stats["courses"] >= 18

    users = client.get("/api/admin/users", params={"keyword": "teacher"}, headers=admin).json()["data"]
    assert users["total"] >= 2

    courses = client.get("/api/admin/courses", params={"keyword": "Python"}, headers=admin).json()["data"]
    assert courses["total"] >= 1

    orders = client.get("/api/admin/orders", headers=admin).json()["data"]
    assert orders["total"] >= 1

    applications = client.get("/api/admin/applications", headers=admin).json()["data"]
    assert applications["total"] >= 1


def test_course_offline_notifies_favorites(client):
    admin = auth(login(client, "admin"))
    student = auth(login(client))

    client.patch("/api/admin/courses/8/status", json={"status": "offline"}, headers=admin)
    try:
        items = client.get(
            "/api/notifications", params={"page_size": 50}, headers=student
        ).json()["data"]["items"]
        assert any(item["link"] == "/courses/8" and "下架" in item["title"] for item in items)
    finally:
        client.patch("/api/admin/courses/8/status", json={"status": "published"}, headers=admin)


def test_ai_learning_path_domain_branches(client):
    headers = auth(login(client))
    for goal in ("鸿蒙 ArkTS 应用开发", "转岗产品经理"):
        response = client.post(
            "/api/ai/learning-path",
            json={"goal": goal, "weekly_hours": 5},
            headers=headers,
        )
        data = response.json()["data"]
        assert "阶段" in data["content"]


def test_invalid_token_and_unknown_account(client):
    bad_headers = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/api/users/me", headers=bad_headers).status_code == 401
    assert client.post("/api/auth/login", json={"account": "no_such_user", "password": "123456"}).status_code == 401


def test_my_orders(client):
    headers = auth(login(client))
    data = client.get("/api/users/me/orders", headers=headers).json()["data"]
    assert data["total"] >= 1
    item = data["items"][0]
    assert {"order_no", "title", "amount", "status"} <= set(item)
    assert data["total_amount"] >= item["amount"]


def test_admin_cannot_update_own_status(client):
    admin = auth(login(client, "admin"))
    me = client.get("/api/users/me", headers=admin).json()["data"]
    response = client.patch(f"/api/admin/users/{me['id']}/status", json={"is_active": False}, headers=admin)
    assert response.status_code == 400


def test_admin_disable_user_blocks_login(client):
    admin = auth(login(client, "admin"))
    student = auth(login(client))
    me = client.get("/api/users/me", headers=student).json()["data"]

    disabled = client.patch(f"/api/admin/users/{me['id']}/status", json={"is_active": False}, headers=admin)
    assert disabled.json()["data"]["is_active"] is False
    try:
        blocked = client.post("/api/auth/login", json={"account": "student", "password": "123456"})
        assert blocked.status_code == 403
    finally:
        restored = client.patch(f"/api/admin/users/{me['id']}/status", json={"is_active": True}, headers=admin)
        assert restored.json()["data"]["is_active"] is True

    assert client.post("/api/auth/login", json={"account": "student", "password": "123456"}).status_code == 200


def test_admin_course_crud(client):
    admin = auth(login(client, "admin"))

    created = client.post(
        "/api/admin/courses",
        json={"title": "TEST 临时课程", "tech_system": "AI", "level": "beginner", "is_free": True},
        headers=admin,
    ).json()
    assert created["code"] == 0
    course_id = created["data"]["id"]

    detail = client.get(f"/api/admin/courses/{course_id}", headers=admin).json()["data"]
    assert detail["title"] == "TEST 临时课程"
    assert detail["chapters"] == []

    updated = client.put(
        f"/api/admin/courses/{course_id}",
        json={"title": "TEST 临时课程改", "price": 99, "is_free": False},
        headers=admin,
    )
    assert updated.json()["code"] == 0
    detail = client.get(f"/api/admin/courses/{course_id}", headers=admin).json()["data"]
    assert detail["title"] == "TEST 临时课程改"
    assert detail["price"] == 99.0

    chapter = client.post(
        f"/api/admin/courses/{course_id}/chapters",
        json={"title": "第 1 章", "duration_min": 20, "sort": 1},
        headers=admin,
    ).json()["data"]
    edited = client.put(f"/api/admin/chapters/{chapter['id']}", json={"title": "第 1 章 改"}, headers=admin).json()
    assert edited["data"]["title"] == "第 1 章 改"
    assert client.delete(f"/api/admin/chapters/{chapter['id']}", headers=admin).status_code == 200

    assert client.delete(f"/api/admin/courses/{course_id}", headers=admin).json()["code"] == 0
    assert client.get(f"/api/admin/courses/{course_id}", headers=admin).status_code == 404


def test_teacher_course_ownership(client):
    teacher = auth(login(client, "teacher_wang"))
    me = client.get("/api/users/me", headers=teacher).json()["data"]

    created = client.post(
        "/api/admin/courses", json={"title": "TEST 教师课程"}, headers=teacher
    ).json()["data"]
    course_id = created["id"]
    try:
        detail = client.get(f"/api/admin/courses/{course_id}", headers=teacher).json()["data"]
        assert detail["teacher_id"] == me["id"]

        other = auth(login(client, "teacher_li"))
        blocked = client.put(f"/api/admin/courses/{course_id}", json={"title": "越权改名"}, headers=other)
        assert blocked.status_code == 403

        student = auth(login(client))
        assert client.post("/api/admin/courses", json={"title": "学生课程"}, headers=student).status_code == 403
    finally:
        client.delete(f"/api/admin/courses/{course_id}", headers=teacher)


def test_delete_course_with_records_blocked(client):
    admin = auth(login(client, "admin"))
    response = client.delete("/api/admin/courses/1", headers=admin)
    assert response.status_code == 409


def test_admin_teachers_list(client):
    admin = auth(login(client, "admin"))
    data = client.get("/api/admin/teachers", headers=admin).json()["data"]
    assert data["total"] >= 2
    assert all("course_count" in item for item in data["items"])

    student = auth(login(client))
    assert client.get("/api/admin/teachers", headers=student).status_code == 403


def test_order_status_machine(client):
    admin = auth(login(client, "admin"))
    orders = client.get("/api/admin/orders", headers=admin).json()["data"]["items"]
    paid = next(item for item in orders if item["status"] == "paid")

    detail = client.get(f"/api/admin/orders/{paid['id']}", headers=admin).json()["data"]
    assert detail["course_title"]

    assert (
        client.patch(
            f"/api/admin/orders/{paid['id']}/status", json={"status": "pending"}, headers=admin
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/admin/orders/{paid['id']}/status", json={"status": "refunded"}, headers=admin
        ).json()["data"]["status"]
        == "refunded"
    )
    assert (
        client.patch(
            f"/api/admin/orders/{paid['id']}/status", json={"status": "paid"}, headers=admin
        ).status_code
        == 409
    )


def test_course_payload_validation(client):
    admin = auth(login(client, "admin"))
    assert client.post("/api/admin/courses", json={"title": "A"}, headers=admin).status_code == 422
    assert (
        client.post("/api/admin/courses", json={"title": "有效课程", "level": "expert"}, headers=admin).status_code
        == 422
    )


def test_operation_log_permissions(client):
    assert client.get("/api/admin/operation-logs").status_code == 401
    student = auth(login(client))
    assert client.get("/api/admin/operation-logs", headers=student).status_code == 403
    teacher = auth(login(client, "teacher_wang"))
    assert client.get("/api/admin/operation-logs", headers=teacher).status_code == 403


def test_operation_log_records_course_actions(client):
    admin = auth(login(client, "admin"))
    created = client.post(
        "/api/admin/courses", json={"title": "TEST 审计课程"}, headers=admin
    ).json()["data"]
    course_id = created["id"]
    try:
        client.put(
            f"/api/admin/courses/{course_id}",
            json={"title": "TEST 审计课程改"},
            headers=admin,
        )
    finally:
        client.delete(f"/api/admin/courses/{course_id}", headers=admin)

    data = client.get(
        "/api/admin/operation-logs",
        params={"action": "course.create", "page_size": 100},
        headers=admin,
    ).json()["data"]
    item = next(row for row in data["items"] if row["target_id"] == course_id)
    assert item["target_type"] == "course"
    assert item["actor_role"] == "admin"
    assert item["actor_name"]
    assert item["detail"]["title"] == "TEST 审计课程"

    updates = client.get(
        "/api/admin/operation-logs",
        params={"action": "course.update", "page_size": 100},
        headers=admin,
    ).json()["data"]
    update_item = next(row for row in updates["items"] if row["target_id"] == course_id)
    assert "title" in update_item["detail"]["fields"]

    deletes = client.get(
        "/api/admin/operation-logs",
        params={"action": "course.delete", "page_size": 100},
        headers=admin,
    ).json()["data"]
    assert any(row["target_id"] == course_id for row in deletes["items"])


def test_operation_log_records_user_role_change(client):
    admin = auth(login(client, "admin"))
    users = client.get("/api/admin/users", params={"keyword": "teacher_li"}, headers=admin).json()["data"]["items"]
    target = next(user for user in users if user["username"] == "teacher_li")
    original = target["role"]
    other = "admin" if original != "admin" else "teacher"
    client.patch(f"/api/admin/users/{target['id']}/role", json={"role": other}, headers=admin)
    try:
        data = client.get(
            "/api/admin/operation-logs",
            params={"action": "user.role", "page_size": 100},
            headers=admin,
        ).json()["data"]
        item = next(row for row in data["items"] if row["target_id"] == target["id"])
        assert item["detail"]["before"] == original
        assert item["detail"]["after"] == other
    finally:
        client.patch(f"/api/admin/users/{target['id']}/role", json={"role": original}, headers=admin)


def test_operation_log_filters_and_pagination(client):
    admin = auth(login(client, "admin"))
    data = client.get(
        "/api/admin/operation-logs",
        params={"target_type": "course", "page": 1, "page_size": 5},
        headers=admin,
    ).json()["data"]
    assert data["page"] == 1 and data["page_size"] == 5
    assert all(item["target_type"] == "course" for item in data["items"])
    assert (
        client.get("/api/admin/operation-logs", params={"page_size": 101}, headers=admin).status_code
        == 422
    )


def test_teacher_course_students_scope(client):
    teacher = auth(login(client, "teacher_wang"))
    data = client.get("/api/admin/teacher/courses/1/students", headers=teacher).json()["data"]
    assert data["course_id"] == 1
    assert data["course_title"]
    assert {"students", "avg_progress", "total_minutes"} <= set(data["summary"])
    for item in data["items"]:
        assert {"user_id", "user_name", "progress", "study_minutes"} <= set(item)
        assert "email" not in item
        assert "username" not in item

    assert client.get("/api/admin/teacher/courses/2/students", headers=teacher).status_code == 403

    student = auth(login(client))
    assert client.get("/api/admin/teacher/courses/1/students", headers=student).status_code == 403

    admin = auth(login(client, "admin"))
    assert client.get("/api/admin/teacher/courses/2/students", headers=admin).status_code == 200
    assert client.get("/api/admin/teacher/courses/999999/students", headers=admin).status_code == 404
    assert client.get("/api/admin/orders/999999", headers=admin).status_code == 404

def test_enroll_free_course_idempotent(client):
    headers = auth(login(client))
    first = client.post("/api/courses/2/enroll", headers=headers).json()["data"]
    assert first["enrolled"] is True
    second = client.post("/api/courses/2/enroll", headers=headers).json()["data"]
    assert second["enrolled"] is True
    detail = client.get("/api/courses/2", headers=headers).json()["data"]
    assert detail["is_enrolled"] is True
    assert detail["can_learn"] is True


def test_enroll_paid_course_rules(client):
    headers = auth(login(client))
    blocked = client.post("/api/courses/5/enroll", headers=headers)
    assert blocked.status_code == 403

    progress = client.put(
        "/api/courses/5/progress",
        json={"chapter_id": None, "minutes": 5},
        headers=headers,
    )
    assert progress.status_code == 403


def test_course_resources_access_and_crud(client):
    admin = auth(login(client, "admin"))
    created = client.post(
        "/api/admin/courses",
        json={"title": "TEST 资源课程", "is_free": True},
        headers=admin,
    ).json()["data"]
    course_id = created["id"]
    chapter = client.post(
        f"/api/admin/courses/{course_id}/chapters",
        json={"title": "第 1 章", "duration_min": 20, "sort": 1},
        headers=admin,
    ).json()["data"]
    chapter_id = chapter["id"]
    resource = client.post(
        f"/api/admin/chapters/{chapter_id}/materials",
        json={
            "title": "示例代码",
            "resource_type": "code",
            "url": "https://example.com/demo.py",
            "content": "print('hello')",
            "sort": 1,
        },
        headers=admin,
    ).json()["data"]
    try:
        assert resource["resource_type"] == "code"
        teacher = auth(login(client, "teacher_wang"))
        assert (
            client.get(f"/api/admin/chapters/{chapter_id}/materials", headers=teacher).status_code
            == 403
        )

        student = auth(login(client))
        assert client.get(f"/api/courses/{course_id}/materials", headers=student).status_code == 403
        client.post(f"/api/courses/{course_id}/enroll", headers=student)
        materials = client.get(f"/api/courses/{course_id}/materials", headers=student).json()["data"]
        assert materials["total"] == 1
        assert materials["items"][0]["chapter_title"] == "第 1 章"

        updated = client.put(
            f"/api/admin/materials/{resource['id']}",
            json={"title": "示例代码（更新）", "sort": 2},
            headers=admin,
        ).json()["data"]
        assert updated["title"] == "示例代码（更新）"
    finally:
        client.delete(f"/api/admin/courses/{course_id}", headers=admin)


def test_taxonomy_dictionary_maintenance(client):
    data = client.get("/api/meta/taxonomy").json()["data"]
    assert data["course_type"] and data["level"] and data["tech_system"]

    admin = auth(login(client, "admin"))
    code = f"test_kind_{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/admin/taxonomy",
        json={"kind": "course_type", "code": code, "name": "测试类型", "sort": 99},
        headers=admin,
    ).json()["data"]
    try:
        assert created["enabled"] is True
        duplicate = client.post(
            "/api/admin/taxonomy",
            json={"kind": "course_type", "code": code, "name": "重复", "sort": 99},
            headers=admin,
        )
        assert duplicate.status_code == 409
        updated = client.put(
            f"/api/admin/taxonomy/{created['id']}",
            json={"enabled": False},
            headers=admin,
        ).json()["data"]
        assert updated["enabled"] is False
        current = client.get("/api/meta/taxonomy").json()["data"]
        assert code not in [item["value"] for item in current["course_type"]]
    finally:
        client.put(f"/api/admin/taxonomy/{created['id']}", json={"enabled": True}, headers=admin)


def test_course_review_flow(client):
    teacher = auth(login(client, "teacher_wang"))
    admin = auth(login(client, "admin"))

    created = client.post(
        "/api/admin/courses",
        json={"title": "TEST 审核课程", "audience": "在校学生", "prerequisite": "Python 基础"},
        headers=teacher,
    ).json()["data"]
    course_id = created["id"]
    try:
        detail = client.get(f"/api/admin/courses/{course_id}", headers=teacher).json()["data"]
        assert detail["review_status"] == "pending"
        assert detail["audience"] == "在校学生"
        assert detail["prerequisite"] == "Python 基础"

        search = client.get("/api/courses", params={"keyword": "TEST 审核课程"}).json()["data"]
        assert search["total"] == 0

        approved = client.patch(
            f"/api/admin/courses/{course_id}/review",
            json={"review_status": "published", "comment": "内容完整"},
            headers=admin,
        ).json()["data"]
        assert approved["review_status"] == "published"
        search = client.get("/api/courses", params={"keyword": "TEST 审核课程"}).json()["data"]
        assert search["total"] == 1

        rejected = client.patch(
            f"/api/admin/courses/{course_id}/review",
            json={"review_status": "rejected", "comment": "缺少大纲"},
            headers=admin,
        ).json()["data"]
        assert rejected["review_status"] == "rejected"
        search = client.get("/api/courses", params={"keyword": "TEST 审核课程"}).json()["data"]
        assert search["total"] == 0

        resubmitted = client.patch(
            f"/api/admin/courses/{course_id}/submit-review", headers=teacher
        ).json()["data"]
        assert resubmitted["review_status"] == "pending"
    finally:
        client.delete(f"/api/admin/courses/{course_id}", headers=admin)

def test_learning_events_progress_and_resume(client):
    headers = auth(login(client))
    client.post("/api/courses/6/enroll", headers=headers)
    detail = client.get("/api/courses/6", headers=headers).json()["data"]
    chapter = detail["chapters"][0]

    result = client.post(
        "/api/courses/6/events",
        json={
            "events": [
                {"event_type": "enter_chapter", "chapter_id": chapter["id"], "position_sec": 120},
                {"event_type": "heartbeat", "chapter_id": chapter["id"], "duration_sec": 90, "position_sec": 120},
                {"event_type": "complete_chapter", "chapter_id": chapter["id"], "position_sec": 120},
            ]
        },
        headers=headers,
    ).json()["data"]
    assert result["progress"] >= 20
    assert result["effective_minutes"] == 2
    assert result["last_chapter_id"] == chapter["id"]
    assert result["last_position_sec"] == 120

    refreshed = client.get("/api/courses/6", headers=headers).json()["data"]
    assert refreshed["last_chapter_id"] == chapter["id"]
    assert refreshed["last_chapter_title"] == chapter["title"]
    assert refreshed["effective_minutes"] == 2
    assert refreshed["last_position_sec"] == 120

    progress = client.get("/api/courses/6/progress", headers=headers).json()["data"]
    assert progress["effective_minutes"] == 2
    assert progress["last_chapter_title"] == chapter["title"]


def test_learning_heartbeat_is_capped(client):
    headers = auth(login(client))
    client.post("/api/courses/3/enroll", headers=headers)
    detail = client.get("/api/courses/3", headers=headers).json()["data"]
    chapter_id = detail["chapters"][0]["id"]
    result = client.post(
        "/api/courses/3/events",
        json={
            "events": [
                {"event_type": "heartbeat", "chapter_id": chapter_id, "duration_sec": 600},
                {"event_type": "heartbeat", "chapter_id": chapter_id, "duration_sec": 600},
            ]
        },
        headers=headers,
    ).json()["data"]
    assert result["effective_minutes"] == 4


def test_learning_event_chapter_must_belong_to_course(client):
    headers = auth(login(client))
    response = client.post(
        "/api/courses/6/events",
        json={"events": [{"event_type": "enter_chapter", "chapter_id": 999999}]},
        headers=headers,
    )
    assert response.status_code == 400


def test_learning_events_require_enrollment(client):
    headers = auth(login(client))
    response = client.post(
        "/api/courses/5/events",
        json={"events": [{"event_type": "enter_chapter", "chapter_id": None}]},
        headers=headers,
    )
    assert response.status_code == 403


def test_learning_events_reject_teacher(client):
    teacher = auth(login(client, "teacher_wang"))
    response = client.post(
        "/api/courses/1/events",
        json={"events": [{"event_type": "enter_chapter", "chapter_id": None}]},
        headers=teacher,
    )
    assert response.status_code == 403