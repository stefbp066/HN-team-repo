# Pre-commit macOS SSL Fix

## Issue
`pre-commit run` fails with SSL verification error:
`URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate>`

## Fix
Run macOS Python certificate installation script:

```bash
bash "/Applications/Python 3.13/Install Certificates.command"
```
*(Replace `3.13` with your active Python version if different, e.g. `3.12`)*
