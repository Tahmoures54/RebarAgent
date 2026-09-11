from utils.events import EventBus


def test_subscribe_and_emit():
    bus = EventBus()
    seen = []
    bus.subscribe("ping", lambda p: seen.append(p["x"]))
    bus.emit("ping", {"x": 1})
    assert seen == [1]


def test_batch_holds_until_end():
    bus = EventBus()
    seen = []
    bus.subscribe("ping", lambda p: seen.append(p["n"]))
    with bus:
        bus.emit("ping", {"n": 1})
        bus.emit("ping", {"n": 2})
        assert seen == []
    assert seen == [1, 2]


def test_once_unsubscribes():
    bus = EventBus()
    seen = []
    bus.once("ping", lambda p: seen.append(1))
    bus.emit("ping", {})
    bus.emit("ping", {})
    assert seen == [1]


def test_reentrant_emit_is_dropped():
    bus = EventBus()
    seen = []

    def boom(payload):
        seen.append("a")
        bus.emit("ping", {"nested": True})
        seen.append("b")

    bus.subscribe("ping", boom)
    bus.emit("ping", {})
    assert seen == ["a", "b"]
    assert bus.stats["dropped_reentrant"] >= 1
