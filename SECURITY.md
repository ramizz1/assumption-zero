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

The included Compose stack provides non-root containers, a private backend network, same-origin proxying, request throttling, browser security headers, and SSRF protection by default. It is designed for a trusted single user or team; it does not provide user accounts or multi-tenant authorization.

Public operators must place it behind HTTPS and access control, protect and back up the `azero_data` volume, keep secrets out of source control, retain the default SSRF protection, and apply equivalent CORS and rate-limit controls if the API is exposed outside the included proxy. Browser-entered provider keys live only for the current browser session.
