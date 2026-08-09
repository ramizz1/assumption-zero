# Security policy

## Reporting a vulnerability

Please do not open a public issue for a vulnerability involving API keys, server-side request forgery, data exposure, authentication, or remote code execution.

Use GitHub's private vulnerability reporting for this repository when available. Include:

- the affected component and version or commit;
- reproducible steps or a minimal proof of concept;
- the expected impact;
- any suggested mitigation.

Please allow reasonable time for investigation before public disclosure.

## Deployment expectations

Assumption Zero is an early-stage open-source project. Public operators are responsible for HTTPS, access control, rate limiting, secure secret handling, restricted CORS origins, protected persistence, and enabling SSRF protection for custom provider URLs.
