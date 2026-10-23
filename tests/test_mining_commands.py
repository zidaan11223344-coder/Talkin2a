import copy
import threading
from pathlib import Path

import bot as bot_module
from treasure_mining import DAY_SECONDS, MiningStore


def test_mining_commands_use_stable_id_and_redeem_inventory_idempotently(tmp_path, monkeypatch):
    state = {
        "version": 1,
        "players": {},
        "diamond_schedule": {"cycle_end": 1_000.0 + DAY_SECONDS, "times": [1_000.0]},
    }
    store = MiningStore(
        tmp_path / "mining_game.json",
        load_json=lambda _path, default: copy.deepcopy(state),
        save_json=lambda _path, data: state.update(copy.deepcopy(data)),
        chooser=lambda: None,
        diamond_chooser=lambda: "diamond_blue",
        clock=lambda: 1_000.0,
    )
    bot = bot_module.TalkinBot.__new__(bot_module.TalkinBot)
    bot._mining_cooldown_lock = threading.RLock()
    bot._mining_last_dig = {}
    sent = []
    media = []
    transactions = []
    bot.send_room_text = lambda room, text: sent.append((room, text))
    bot.send_room_media = lambda room, url, media_type: media.append((room, url, media_type))
    bot._game_public_image = lambda path, route="games": f"https://assets.example/{route}/{path.name}"
    bot.log = lambda *args, **kwargs: None

    monkeypatch.setattr(bot_module, "MINING_STORE", store)
    monkeypatch.setattr(bot_module, "_record_game", lambda *args: None)
    monkeypatch.setattr(
        bot_module,
        "_apply_points_delta_once",
        lambda username, points, txid, reason: (
            transactions.append((username, points, txid, reason)) or {"ok": True}
        ),
    )
    monkeypatch.setattr(bot_module.time, "sleep", lambda _seconds: None)

    assert bot_module._looks_like_bot_command("diamond")
    assert bot_module._looks_like_bot_command("mine")
    assert bot_module._looks_like_bot_command("dig")
    assert bot_module._looks_like_bot_command("treasure store")
    assert bot_module._looks_like_bot_command("top diamonds")
    assert bot_module._looks_like_bot_command("sv inventory")
    assert bot._execute_mining_command_with_id("Hall", "diamond", "Ahmed", "3456782")
    assert state["players"]["3456782"]["inventory"]["diamond_blue"] == 1
    assert any("Ahmed عثرت على:" in text and "قيمة الاستبدال: 1,000,000 نقطة" in text for _room, text in sent)
    assert media == [("Hall", "https://assets.example/assets/treasures/diamond_blue.jpg", "image")]

    sent.clear()
    assert bot._execute_mining_command_with_id("Hall", "inventory", "NewName", "3456782")
    assert any("الألماس الأزرق: 1" in text for _room, text in sent)

    sent.clear()
    assert bot._execute_mining_command_with_id("Hall", "top diamonds", "NewName", "3456782")
    assert any("@NewName — 1 ألماسة" in text for _room, text in sent)

    sent.clear()
    assert bot._execute_mining_command_with_id("Hall", "Rdem الماس", "NewName", "3456782")
    assert len(transactions) == 1
    assert transactions[0][0] == "NewName"
    assert transactions[0][1] == 1_000_000
    assert transactions[0][3] == "treasure mining redemption"
    assert transactions[0][2].startswith("mining-redemption:")
    assert state["players"]["3456782"]["inventory"]["diamond_blue"] == 0
    assert state["players"]["3456782"].get("pending_redemption") is None
    assert any("1,000,000 نقطة" in text for _room, text in sent)

    # R is the short alias for any item and must redeem copper through the
    # same points ledger, without touching another user's inventory.
    state["players"]["3456782"]["inventory"]["copper"] = 1
    store._save_state(state)
    sent.clear()
    assert bot._execute_mining_command_with_id("Hall", "R نحاس", "NewName", "3456782")
    assert transactions[1][1] == 25_000
    assert transactions[1][3] == "treasure mining redemption"
    assert state["players"]["3456782"]["inventory"]["copper"] == 0
    assert any("25,000 نقطة" in text for _room, text in sent)

    sent.clear()
    assert bot._execute_mining_command_with_id("Hall", "treasure store", "NewName", "3456782")
    catalog = sent[-1][1]
    packet = bot_module.encode_query("room_message", room="Hall", body=catalog)
    assert len(packet) <= 1008


def test_compressed_treasure_asset_is_served_as_jpeg():
    handler = bot_module._MediaHandler.__new__(bot_module._MediaHandler)
    compressed_jpeg = Path(bot_module.ASSETS_DIR) / "treasures" / "diamond_clear.jpg"
    assert compressed_jpeg.is_file()
    assert handler._ctype(compressed_jpeg) == "image/jpeg"


def test_media_type_uses_image_signature_when_extension_is_wrong(tmp_path):
    handler = bot_module._MediaHandler.__new__(bot_module._MediaHandler)
    mislabeled = tmp_path / "image.jpg"
    mislabeled.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    assert handler._ctype(mislabeled) == "image/png"


def test_mining_and_cricket_messages_follow_the_saved_room_language():
    bot = bot_module.TalkinBot.__new__(bot_module.TalkinBot)
    bot._effective_room_language = lambda room: "en" if room == "EnglishHall" else "ar"
    inventory = (
        "🎒 مخزون @Player\n🔷 الألماس الأزرق: 2\n"
        "🔴 ألماسة نادرة RED: 0 — الاستبدال: red 0 (4,000,000 نقطة للقطعة)\n"
        "💎 إجمالي الألماس الذي عثرت عليه: 2\n"
        "🔁 للاستبدال: red رمز أو اسم أي كنز العدد — مثال: red ⚙️ 3 أو red ♦️ 3"
    )
    english_inventory = bot._localize_room_text("EnglishHall", inventory)
    arabic_inventory = bot._localize_room_text("ArabicHall", inventory)
    assert not any("\u0600" <= char <= "\u06ff" for char in english_inventory)
    assert arabic_inventory == inventory

    cricket_setup = (
        "🏏 إعداد مباراة ضد البوت\n"
        "اختر عدد اللاعبين: 1 أو 2 أو 3 أو 4.\n"
        "بعد اختيار العدد، يرسل كل لاعب Join من هذه الغرفة فقط.\n"
        "🤖 الخصم هو بوت Talkin2."
    )
    english_setup = bot._localize_room_text("EnglishHall", cricket_setup)
    assert not any("\u0600" <= char <= "\u06ff" for char in english_setup)

    cricket_samples = [
        "⛔ يوجد لاعب مسجل بالفعل؛ أرسل Join بحسابه أو انتظر الغرفة الأخرى.",
        "لاعب في الغرفة.\n🔗 بعد اكتمال الفريق الأول، ترسل الغرفة الثانية Join؛ وعند تعدد القوائم يُقرن بأقدم فريق مكتمل. أو أكمل العدد هنا للعب ضد BotName.",
        "🔄 استؤنفت مباراة الكركيت بعد إعادة تشغيل البوت.\nPrompt",
        "🔄 استؤنفت مباراة الكركيت. ترسل غرفة الإعداد 1 للهجوم أو 2 للدفاع؛ ويُعيّن دور الغرفة الثانية تلقائيًا.",
        "🔄 استؤنف إعداد مباراة الكريكيت. اختر عدد اللاعبين من 1 إلى 4.",
    ]
    for message in cricket_samples:
        localized = bot._localize_room_text("EnglishHall", message)
        assert not any("\u0600" <= char <= "\u06ff" for char in localized), localized
    assert bot._localize_room_text("ArabicHall", cricket_samples[1]) == cricket_samples[1]
