from pyulog import ULog
from pyulog.trim import trim

def test_trim():
    trim("test/sample.ulg", "test/trimmed.ulg", 120, 170)

    ulg_trimmed = ULog("test/trimmed.ulg")

    assert ulg_trimmed.start_timestamp/1e6 >= 120
    assert ulg_trimmed.last_timestamp/1e6 <= 170
