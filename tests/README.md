Development
-----------

Creating encrypted files:

```bash
gpg --armour --local-user "fidelius@example.invalid" --recipient "fidelius@example.invalid" --encrypt "examples/example-1.encrypted.json"
gpg --armour --local-user "fidelius@example.invalid" --recipient "fidelius@example.invalid" --encrypt "examples/directory.encrypted/example-2.json"
gpg --armour --local-user "fidelius@example.invalid" --recipient "fidelius@example.invalid" --encrypt "examples/directory.encrypted/example-3.encrypted.json"
```

Manually decrypted for editing:

```bash
gpg --armour --local-user "fidelius@example.invalid" --output "examples/example-1.encrypted.json" --decrypt "examples/example-1.encrypted.json.asc"
gpg --armour --local-user "fidelius@example.invalid" --output "examples/directory.encrypted/example-2.json" --decrypt "examples/directory.encrypted/example-2.json.asc"
gpg --armour --local-user "fidelius@example.invalid" --output "examples/directory.encrypted/example-3.encrypted.json" --decrypt "examples/directory.encrypted/example-3.encrypted.json.asc"
```
