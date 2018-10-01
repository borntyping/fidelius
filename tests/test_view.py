def test_view(invoke, secret):
    invoke(['decrypt'])
    decrypted = invoke(['view', str(secret.encrypted)])
    plaintext = secret.decrypted.read_text().splitlines()
    assert decrypted == plaintext
