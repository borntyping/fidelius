Fidelius
--------

Fidelius is a tool for managing GPG encrypted secrets in a git repository.

It uses a couple of rules to rename files when they are decrypted so that they
have the correct extension and placed in the directory structure you want.

It's partially useful when working with tools like [Helm] which will crash if
they encounter encrypted files in their directory structure.

Rules
-----

All files with `.encrypted` anywhere in the name and a `.asc` or `.gpg` suffix
are decrypted into the same directory. The `.asc` or `.gpg` suffix is removed
and `.encrypted` is replaced with `.decrypted`.

```
examples/example-1.encrypted.json.asc
examples/example-1.decrypted.json
```


All files with a `.asc` or `.gpg` suffix in a directory named `%.encrypted` are
decrypted into `%`, keeping the same relative path. Filenames have the `.asc` or
`.gpg` suffix removed, and `.encrypted` is replaced with `.decrypted`. Encrypted
files without `.encrypted` in their name have a `.decrypted` suffix added before
the last suffix in the filename.

```
examples/directory.encrypted/example-2.json.gpg
examples/directory/example-2.decrypted.json
```

```
examples/directory.encrypted/example-3.encrypted.json.gpg
examples/directory/example-3.decrypted.json
```
