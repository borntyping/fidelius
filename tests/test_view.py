def test_view(invoke, secret):
    decrypted = invoke(['view', secret.encrypted])
    plaintext = secret.decrypted.read_text().splitlines()
    assert decrypted == plaintext
