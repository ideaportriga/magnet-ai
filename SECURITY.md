# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Magnet AI team takes security bugs seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

### Where to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing:

📧 **security@ideaportriga.com**

Alternatively, you can use GitHub's private vulnerability reporting feature:

1. Go to the repository's "Security" tab
2. Click "Report a vulnerability"
3. Fill out the form with details

### What to Include

To help us better understand the nature and scope of the possible issue, please include as much of the following information as possible:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

### What to Expect

After you submit a report, you can expect:

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
2. **Assessment**: We will assess the vulnerability and determine its impact and severity
3. **Updates**: We will keep you informed of the progress towards a fix
4. **Resolution**: We will notify you when the vulnerability is fixed
5. **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Response Timeline

- **Critical vulnerabilities**: Patch released within 7 days
- **High vulnerabilities**: Patch released within 14 days
- **Medium vulnerabilities**: Patch released within 30 days
- **Low vulnerabilities**: Patch released within 60 days

## Security Update Process

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new security patch versions as soon as possible

## Security Advisories

Security advisories will be published on:

- GitHub Security Advisories
- Repository releases page
- Project website (if applicable)

## Automated Security Checks

This project uses automated security scanning:

### GitHub Actions

- **Dependency Scanning**: Checks for known vulnerabilities in dependencies
- **Secret Scanning**: Detects accidentally committed secrets

### Python Security

- **pip-audit**: Checks Python dependencies for known security vulnerabilities

### JavaScript Security

- **npm audit**: Checks npm dependencies for known vulnerabilities

## Security Best Practices

### For Contributors

1. **Never commit secrets**: Use environment variables for sensitive data
2. **Keep dependencies updated**: Regularly update to latest secure versions
3. **Run security checks locally**: Use pre-commit hooks before pushing
4. **Review security alerts**: Check GitHub security tab regularly
5. **Follow secure coding practices**: See our contribution guidelines

### For Deployments

1. **Use environment variables**: Never hardcode credentials
2. **Enable HTTPS**: Always use SSL/TLS in production
3. **Regular updates**: Keep all dependencies up to date
4. **Access control**: Implement proper authentication and authorization
5. **Database security**: Use strong passwords, enable SSL connections
6. **Network security**: Use firewalls, restrict port access
7. **Logging and monitoring**: Enable security logging and alerts

## Vulnerability Disclosure Policy

We believe in coordinated disclosure of security vulnerabilities. We request that:

1. You give us reasonable time to fix the vulnerability before public disclosure
2. You make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our service
3. You do not exploit a security issue for purposes other than verification
4. You do not access or modify other users' data
5. You do not perform any attack that could harm the reliability or integrity of our services

## Security Hall of Fame

We would like to thank the following security researchers for responsibly disclosing vulnerabilities:

<!-- Add researchers who report vulnerabilities -->
- [Your Name] - [Vulnerability Type] - [Date]

## Compliance

### Licenses

All dependencies must be compatible with Apache License 2.0.

### Data Protection

- GDPR compliant data handling
- No collection of personal data without consent
- Right to deletion of personal data

## Contact

For any security-related questions or concerns:

- **Email**: security@ideaportriga.com
- **GPG Key**: [Link to public key if available]

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated**: November 2025

**Version**: 1.0.0
