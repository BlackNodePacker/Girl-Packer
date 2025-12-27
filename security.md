# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by emailing: ahmedasker115@gmail.com

## Supported Versions

We currently support the latest stable release with Python 3.11.

## Security Best Practices

- Do not commit secrets, passwords, or API keys.
- Use `.env` files for sensitive configuration (though not currently implemented).
- Keep dependencies updated to avoid vulnerabilities.
- Handle media files securely; avoid processing untrusted inputs without validation.
- AI models and data should be reviewed for biases and security implications.
- Use HTTPS for any network requests (currently minimal).

## Known Security Considerations

- The application processes user-provided media files; ensure input validation.
- No authentication or authorization implemented; for local use only.
- Dependencies are pinned; monitor for CVEs in libraries like PyTorch, OpenCV.
- Avoid processing untrusted media files.
- The application processes media for adult content; ensure compliance with local laws.

## Known Issues

- No input validation for media files; potential for malicious files.
- AI models may have biases; use responsibly.
- Temporary files in `temp/` may contain sensitive data; clean up manually.

## Recommendations

- Run in isolated environment.
- Do not use on production systems without review.
- Regularly update dependencies.
