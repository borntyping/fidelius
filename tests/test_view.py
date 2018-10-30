def test_view(invoke, secret):
    invoke(['decrypt'])
    decrypted = invoke(['view', secret.encrypted.as_posix()])
    plaintext = secret.decrypted.read_text().splitlines()
    assert decrypted == plaintext
