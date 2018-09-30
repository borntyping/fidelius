def test_decrypt(invoke, secret):
    invoke(['decrypt'])
    assert secret.decrypted.exists()


def test_clean(invoke, secret):
    invoke(['decrypt'])
    assert secret.decrypted.exists()
    
    invoke(['clean'])
    assert not secret.decrypted.exists()
