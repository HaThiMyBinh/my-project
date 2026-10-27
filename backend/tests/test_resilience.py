# -*- coding: utf-8 -*-
"""Test độ ổn định: rate limiter, retry, circuit breaker, cache (thuần Python, không cần FastAPI)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services import ai_service as ai  # noqa: E402
from app.services.rate_limit import SlidingWindowLimiter  # noqa: E402

ai.RETRY_DELAY = 0          # test không chờ thật


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def scripted_client(script):
    """script: danh sách kết quả lần lượt: chuỗi = thành công, AIServiceError = lỗi."""
    calls = []

    def transport(url, headers, body, timeout):
        calls.append(1)
        item = script[min(len(calls) - 1, len(script) - 1)]
        if isinstance(item, Exception):
            raise item
        return {"candidates": [{"content": {"parts": [{"text": item}]}}]}

    return ai.GeminiClient(api_key="k", model="m", transport=transport), calls


PET = {"pet_name": "Bơ", "pet_type": "CHO"}


def test_limiter_blocks_after_limit_and_recovers():
    clk = Clock()
    lim = SlidingWindowLimiter(3, 60, clock=clk)
    assert [lim.check_and_hit("u")[0] for _ in range(3)] == [True, True, True]
    ok, wait = lim.check_and_hit("u")
    assert ok is False and 1 <= wait <= 61
    assert lim.check_and_hit("other")[0] is True            # khóa khác không bị ảnh hưởng
    clk.t += 61
    assert lim.check_and_hit("u")[0] is True                # hết cửa sổ -> được phép lại


def test_limiter_failure_counting_and_reset():
    lim = SlidingWindowLimiter(2, 900, clock=Clock())
    assert lim.retry_after("a") == 0
    lim.hit("a")
    lim.hit("a")
    assert lim.retry_after("a") > 0
    lim.reset("a")
    assert lim.retry_after("a") == 0


def test_retry_once_on_transient_error_then_succeed():
    ai.reset_state()
    client, calls = scripted_client([ai.AIServiceError("503", retryable=True), "Đã thành công"])
    res = ai.answer_question("Bao lâu nên tắm cho mèo?", client=client)
    assert res["source"] == "gemini" and res["content"] == "Đã thành công" and len(calls) == 2


def test_no_retry_on_permanent_error():
    ai.reset_state()
    client, calls = scripted_client([ai.AIServiceError("400 bad request", retryable=False)])
    res = ai.answer_question("Bao lâu nên tắm cho mèo?", client=client)
    assert res["source"] == "fallback" and len(calls) == 1


def test_circuit_breaker_opens_then_skips_gemini_then_recovers():
    ai.reset_state()
    clk = Clock()
    ai._now = clk
    try:
        client, calls = scripted_client([ai.AIServiceError("boom", retryable=False)])
        for i in range(ai.BREAKER_THRESHOLD):
            ai.answer_question(f"Câu hỏi chăm sóc số {i}?", client=client)
        assert len(calls) == ai.BREAKER_THRESHOLD
        res = ai.answer_question("Một câu hỏi chăm sóc khác?", client=client)
        assert res["source"] == "fallback" and len(calls) == ai.BREAKER_THRESHOLD   # mạch mở: không gọi Gemini nữa
        clk.t += ai.BREAKER_COOLDOWN + 1
        ok_client, ok_calls = scripted_client(["Đã phục hồi"])
        res = ai.answer_question("Câu hỏi sau khi phục hồi?", client=ok_client)
        assert res["source"] == "gemini" and len(ok_calls) == 1
    finally:
        ai._now = __import__("time").monotonic
        ai.reset_state()


def test_success_resets_failure_counter():
    ai.reset_state()
    bad, _ = scripted_client([ai.AIServiceError("x")])
    for i in range(ai.BREAKER_THRESHOLD - 1):
        ai.answer_question(f"Câu hỏi lỗi số {i}?", client=bad)
    good, _ = scripted_client(["ok"])
    ai.answer_question("Câu hỏi thành công?", client=good)
    for i in range(ai.BREAKER_THRESHOLD - 1):
        ai.answer_question(f"Câu hỏi lỗi tiếp số {i}?", client=bad)
    assert ai._breaker["open_until"] == 0.0               # chưa đủ lỗi LIÊN TIẾP nên chưa ngắt mạch
    ai.reset_state()


def test_identical_requests_are_cached():
    ai.reset_state()
    client, calls = scripted_client(["Tắm 3 tuần một lần."])
    a = ai.answer_question("Bao lâu nên tắm cho mèo?", PET, client=client)
    b = ai.answer_question("Bao lâu nên tắm cho mèo?", PET, client=client)
    assert a["content"] == b["content"] and len(calls) == 1
    c = ai.answer_question("Cắt móng cho mèo thế nào?", PET, client=client)
    assert len(calls) == 2 and c["source"] == "gemini"
    ai.reset_state()


def test_guardrail_answers_are_never_cached_or_sent():
    ai.reset_state()
    client, calls = scripted_client(["không được gọi"])
    ai.answer_question("Chó nhà em đang co giật", client=client)
    assert calls == []
