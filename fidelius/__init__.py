"""
Fidelius manages GPG encrypted secrets in a git repository.

Paths follow simple rules that are used to select files to decrypt and where the decrypted files
will be written. The gpg command is used to perform all encryption and decryption. It will check
that decrypted paths are excluded by a .gitignore file.

The rules used to pair filenames are:

\b
    * 'file.encrypted.ext.asc' is decrypted to 'file.decrypted.ext'.
    * 'dir.encrypted/file.ext.asc' is decrypted to 'dir/file.ext'.

Configure secret recipients (applies to all encryption commands):

\b
    $ export FIDELIUS_RECIPIENTS="fidelius@example.invalid"

Create a new encrypted secret:

\b
    $ mkdir "secrets.encrypted" && echo "hello world" > example.txt
    $ fidelius create "secrets.encrypted/example.txt.asc" "example.txt"

Decrypt an encrypted secret into a matching plaintext file:

\b
    $ fidelius decrypt "secrets.encrypted/example.txt.asc"
    $ cat "secrets/example.txt"

Encrypt a plaintext file into a matching encrypted secret:

\b
    $ vi "secrets/example.txt"
    $ fidelius encrypt "secrets.encrypted/example.txt.asc"

Decrypt all secrets, make changes, and encrypt changed secrets:

\b
    $ fidelius decrypt
    $ vi ...
    $ fidelius encrypt
"""

__author__ = 'Sam Clements'
__version__ = '4.1.0'
