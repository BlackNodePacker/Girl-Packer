import pytest
from utils.pro_verifier import verify_license

class DummyResp:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP Error")
    def json(self):
        return self._json

def test_verify_license_no_url():
    assert verify_license("abc123", verify_url=None) is False

def test_verify_license_mock(monkeypatch):
    def fake_post(url, json, timeout):
        return DummyResp({"valid": True}, status=200)
    monkeypatch.setattr('utils.pro_verifier.requests.post', fake_post)
    assert verify_license("abc123", verify_url="https://example.com/verify") is True
