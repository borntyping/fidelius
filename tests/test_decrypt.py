def test_decrypt(invoke, secret):
    invoke(['decrypt'])
    assert secret.decrypted.exists()
