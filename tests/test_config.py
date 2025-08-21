from pathlib import Path
from tg_gift_buyer.config import Config


def test_load_config(tmp_path: Path):
    cfg_text = """
poll_interval_secs = 2
simulation = true
log_level = "DEBUG"

[defaults]
min_price = 0
max_price = 100
min_supply = 0
max_supply = 100
amount = 1
published_by = []
gift_types = ["limited"]

[[accounts]]
name = "a1"
scan_interval_secs = 2
spend_cap_stars = 100
recipients = ["@u"]
"""
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(cfg_text)
    cfg = Config.load(cfg_file)
    assert cfg.poll_interval_secs == 2
    assert cfg.accounts[0].name == "a1"
    assert cfg.skip_on_low_balance is True
