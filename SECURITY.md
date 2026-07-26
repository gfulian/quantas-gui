# Security policy

Quantas GUI currently targets trusted local use. It is not yet presented as a
hardened public calculation service.

Please report security vulnerabilities through GitHub private vulnerability
reporting or a private draft security advisory for this repository. Do not put
credentials, private datasets, exploit details, or sensitive server paths in a
public issue.

Public or multi-user deployments must add authentication, upload validation,
resource limits, isolated workspaces, secure reverse-proxy configuration, and
worker isolation as described in `docs/deployment-roadmap.md`.
