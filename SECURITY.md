# Security policy

Quantas GUI is still in alpha. Its supported use is local or within a controlled
laboratory environment; it is not presented as an already hardened public
service.

## Supported versions

Security fixes are applied to the main branch and the newest alpha artifact.
Older development snapshots are not maintained as supported release lines.

## Reporting a vulnerability

Use GitHub's private Security Advisory channel:

https://github.com/gfulian/quantas-gui/security/advisories/new

Do not open a public issue containing credentials, private data, tokens, exploit details or
sensitive server paths.

A useful report includes, where possible:

- Quantas GUI and Quantas versions;
- operating system and Python version;
- affected component or workflow;
- reproduction steps using non-sensitive data;
- expected impact and any known workaround.

## Deployment boundary

A multi-user or public service needs authentication, workspace ownership and
expiry, upload validation, quotas, secure reverse-proxy configuration and worker
isolation. The planned path is described in `docs/deployment-roadmap.md` and
`docs/server-deployment.md`.
