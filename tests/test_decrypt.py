import pytest


@pytest.fixture(autouse=True)
def decrypt(invoke):
    invoke(['decrypt'])
    yield
    invoke(['clean'])


def test_decrypt(secret):
    assert secret.decrypted.exists()
