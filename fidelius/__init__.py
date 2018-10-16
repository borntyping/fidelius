"""
Fidelius manages GPG encrypted secrets in a git repository.

Paths follow simple rules that are used to select files to decrypt and where
the decrypted files will be written.

\b
The gpg command is used to perform all encryption and decryption.
Paths like 'file.encrypted.ext.asc' are decrypted to 'file.decrypted.ext'.
Paths like 'dir.encrypted/file.ext.asc' are decrypted to 'dir/file.ext'.

It will also check that decrypted paths are excluded by a .gitignore file.
"""

__author__ = 'Sam Clements'
__version__ = '2.0.1'
