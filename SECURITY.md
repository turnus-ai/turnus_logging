# Security Policy

## Protecting Against Supply Chain Attacks

### Branch Protection Rules

This repository uses the following protections:

1. **No Direct Pushes to Main**
   - All changes must go through Pull Requests
   - Even repository admins cannot bypass

2. **Required Reviews**
   - Minimum 2 approvals required
   - At least 1 from code owners
   - Reviews dismissed when new commits pushed

3. **Required Status Checks**
   - All tests must pass
   - Code linting must pass
   - Security scans must pass

4. **Signed Commits Required**
   - All commits must be GPG signed
   - Verifies identity of committer

### Code Owners

Changes to critical files require approval from specific maintainers:

```
# CODEOWNERS file
* @turnus-ai/security-team
/turnus_logging/ @turnus-ai/core-maintainers
/setup.py @turnus-ai/release-managers
/pyproject.toml @turnus-ai/release-managers
```

### Dependency Management

- **Zero Core Dependencies** - Reduces attack surface
- Optional dependencies (`sentry-sdk`) are from trusted sources
- Pin versions in production: `sentry-sdk==2.35.0` (not `>=2.35.0`)

### Version Pinning in Services

**DO THIS in your services:**

```bash
# Pin to specific commit hash (most secure)
pip install git+https://github.com/turnus-ai/turnus_logging.git@515e86d

# Pin to specific tag (secure)
pip install git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0

# DON'T do this in production (less secure):
pip install git+https://github.com/turnus-ai/turnus_logging.git  # Gets latest
```

### Access Control

**Repository Access Levels:**
- **Read**: Team members (can view, can't modify)
- **Write**: Trusted developers (can create PRs, can't merge)
- **Admin**: 2-3 senior engineers only (can merge PRs)

**Two-Factor Authentication (2FA):**
- Required for all contributors
- Required for all admin accounts

### Security Monitoring

1. **GitHub Security Alerts**
   - Enabled for dependency vulnerabilities
   - Email notifications to security team

2. **Audit Log Review**
   - Weekly review of all repository changes
   - Alert on unexpected access patterns

3. **Signed Release Tags**
   - All releases must be GPG signed
   - Verify signature before deploying

### Incident Response

If you suspect malicious code:

1. **Immediately** revert to last known-good version
2. Contact security team: security@turnus.ai
3. Review git history for unauthorized changes
4. Audit all services using the library

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Email: security@turnus.ai with:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 24 hours.

### Security Best Practices for Users

1. **Pin versions in production:**
   ```txt
   # requirements.txt
   turnus-logging @ git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0
   ```

2. **Review changes before upgrading:**
   ```bash
   # Check what changed
   git log v0.1.0..v0.2.0
   ```

3. **Use private fork for critical services:**
   ```bash
   # Fork to your org, review all changes
   pip install git+https://github.com/your-org/turnus_logging.git@v0.1.0
   ```

4. **Monitor for unexpected network activity:**
   - Library should NEVER make outbound calls (except Sentry if configured)
   - Alert on any unexpected network connections

### Security Checklist for Maintainers

Before merging any PR:

- [ ] Code reviewed by 2+ maintainers
- [ ] No new dependencies added without approval
- [ ] No hardcoded credentials or secrets
- [ ] No unexpected network calls
- [ ] Tests cover new code
- [ ] Security implications discussed
- [ ] Commit is GPG signed

### Verified Releases

All official releases include:
- GPG-signed git tag
- Changelog with all changes
- Security impact assessment
- Migration guide (if breaking changes)

Verify signature:
```bash
git verify-tag v0.1.0
```

## License

This security policy is part of the turnus-logging project, licensed under MIT.
