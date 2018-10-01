Fidelius
--------

Fidelius is a tool for managing GPG encrypted secrets in a git repository.

The `gpg` command is used to perform all encryption and decryption. Fidelius 
is a simple wrapper that makes working with multiple encrypted files easy, and
follows some simple rules that define which files are decrypted and where the
plaintext is written.

* Paths like `file.encrypted.ext.asc` are decrypted to `file.decrypted.ext`,
* Paths like `directory.encrypted/file.ext.asc` are decrypted to
`directory/file.ext`.

These rules ensure decrypted files have the correct extension for their
contents, are easy to exclude from version control with `.gitignore` rule 
(`fidelius` will check they are excluded!) and that decrypted files are
placed where you want in your directory structure. 

The last of these is partially useful when working with tools like [Helm] which
may crash if they encounter encrypted files in their directory structure, so it
can be useful to keep the encrypted files in a separate directory.

Usage
-----

You'll need Python 3.7, [Pip] and GPG installed.

You can then install `fidelius` via `pip`:

```bash
pip install fidelius
```

This will install `fidelius` executable. Run `fidelius --help` for full usage
information. 

```bash
fidelius new -r 'fidelius@example.invalid' 'example.encrypted.txt.asc'
fidelius edit -r 'fidelius@example.invalid' 'example.encrypted.txt.asc'
fidelius view 'example.encrypted.txt.asc'
fidelius decrypt 'example.encrypted.txt.asc' && cat 'example.decrypted.txt'
```

Rules
-----

All files with `.encrypted` anywhere in the name and a `.asc` or `.gpg` suffix
are decrypted into the same directory. The `.asc` or `.gpg` suffix is removed
and `.encrypted` is replaced with `.decrypted`.

```
one.encrypted.json.asc -> one.decrypted.json
```

All files with a `.asc` or `.gpg` suffix in a directory named `%.encrypted` are
decrypted into `%`, keeping the same relative path. Filenames have the `.asc` or
`.gpg` suffix removed, and `.encrypted` is replaced with `.decrypted`. Encrypted
files without `.encrypted` in their name have a `.decrypted` suffix added before
the last suffix in the filename.

```
directory.encrypted/two.json.gpg -> directory/two.decrypted.json
directory.encrypted/three.encrypted.json.gpg -> directory/three.decrypted.json
```

Alternatives
------------

Fidelius is built to fit my own use cases perfectly, but there are several other
far more mature projects for managing encrypted secrets in git repositories.

* [blackbox](https://github.com/StackExchange/blackbox)
* [git-crypt](https://github.com/AGWA/git-crypt)
* [git-secret](https://github.com/sobolevn/git-secret)
* [sops](https://github.com/mozilla/sops)
* [transcrypt](https://github.com/elasticdog/transcrypt)

License
-------

Licensed under the [MIT License].

Author
------

Written by [Sam Clements].

[Pip]: https://packaging.python.org/tutorials/installing-packages/
[Helm]: https://helm.sh/
[MIT License]: ./README.md
[Sam Clements]: https://github.com/borntyping
