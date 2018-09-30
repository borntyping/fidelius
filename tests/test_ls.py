def test_ls(invoke, secret):
    assert f'{secret.enc} -> {secret.dec}' in invoke(['ls'])


def test_ls_decrypted(invoke, secret):
    assert f'{secret.dec}' in invoke(['ls-decrypted'])


def test_ls_encrypted(invoke, secret):
    assert f'{secret.enc}' in invoke(['ls-encrypted'])
