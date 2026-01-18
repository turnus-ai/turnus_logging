# How to Securely Use turnus-logging in Your Services

## 🔒 Protect Against Supply Chain Attacks

### 1. Pin to Specific Versions (Critical!)

**❌ DON'T do this:**
```txt
# requirements.txt - Gets latest code (dangerous!)
git+https://github.com/turnus-ai/turnus_logging.git
```

**✅ DO this:**
```txt
# requirements.txt - Pin to specific tag
git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0

# OR even better - pin to specific commit hash
git+https://github.com/turnus-ai/turnus_logging.git@515e86d
```

### 2. Review Changes Before Upgrading

```bash
# See what changed between versions
git clone https://github.com/turnus-ai/turnus_logging.git
cd turnus_logging
git log v0.1.0..v0.2.0 --oneline

# Review actual code changes
git diff v0.1.0..v0.2.0

# Only upgrade after review!
```

### 3. Use Private Fork (For Critical Services)

```bash
# 1. Fork to your organization
# Go to: https://github.com/turnus-ai/turnus_logging
# Click "Fork" → Select your organization

# 2. Install from your fork
pip install git+https://github.com/your-org/turnus_logging.git@v0.1.0

# 3. Update your fork only after reviewing upstream changes
```

### 4. Hash Verification (Advanced)

```bash
# Generate hash of the installed package
pip hash turnus-logging

# Store in requirements.txt
turnus-logging @ git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0 \
    --hash=sha256:abc123...
```

### 5. Monitor for Unexpected Behavior

**Set up alerts for:**
- Unexpected outbound network connections
- New dependencies being installed
- Changes to core logging behavior
- Suspicious environment variable access

**Example monitoring:**
```python
import logging
import socket

# Patch socket to detect unexpected connections
original_connect = socket.socket.connect

def monitored_connect(self, address):
    # turnus_logging should ONLY connect to Sentry (if configured)
    host = address[0]
    if 'sentry.io' not in host:
        logging.warning(f"Unexpected connection to {host}")
    return original_connect(self, address)

socket.socket.connect = monitored_connect
```

### 6. Dependency Scanning

```bash
# Scan for known vulnerabilities
pip install safety
safety check

# Or use GitHub Dependabot (automatic)
```

### 7. Code Review Your Installation

```bash
# After installing, inspect the actual code
python -c "import turnus_logging; print(turnus_logging.__file__)"
# Go to that directory and review the code
```

### 8. Use Separate Environments

```bash
# Dev - can use latest
pip install git+https://github.com/turnus-ai/turnus_logging.git

# Staging - pin to tag
pip install git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0

# Production - pin to commit hash + verification
pip install git+https://github.com/turnus-ai/turnus_logging.git@515e86d
```

### 9. Vendor the Library (Most Secure)

```bash
# Copy library directly into your service
mkdir -p vendor/
cd vendor/
git clone https://github.com/turnus-ai/turnus_logging.git
cd turnus_logging
git checkout v0.1.0

# In your service:
import sys
sys.path.insert(0, '/path/to/vendor/turnus_logging')
import turnus_logging
```

### 10. Audit Log Review

**What to check:**
- Who has access to the GitHub repo?
- Who merged the last PR?
- Were commits GPG signed?
- Any unexpected changes to core files?

```bash
# View repo access audit log
# Go to: https://github.com/turnus-ai/turnus_logging/settings/audit-log

# Verify GPG signatures
git verify-tag v0.1.0
git log --show-signature
```

## 🚨 Red Flags (Security Warnings)

**Immediately investigate if you see:**

1. ❌ Unexpected network connections
2. ❌ New dependencies added without announcement
3. ❌ Changes to core context/logging code without documentation
4. ❌ Requests for environment variables beyond `SENTRY_DSN`
5. ❌ File system operations (reading unexpected files)
6. ❌ Subprocess execution
7. ❌ Base64 encoded strings (could hide malicious code)
8. ❌ `eval()` or `exec()` calls
9. ❌ Dynamic imports from URLs

## ✅ Current Safety Checks

turnus_logging v0.1.0 is safe because:
- ✅ Zero core dependencies
- ✅ No network calls (except Sentry SDK if configured)
- ✅ No file system writes
- ✅ No subprocess execution
- ✅ No dynamic code execution
- ✅ No base64/encoding tricks
- ✅ All code is readable Python
- ✅ MIT licensed (transparent)

## 📞 Emergency Response

If you detect malicious code:

1. **Immediately downgrade:**
   ```bash
   pip install git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0
   ```

2. **Isolate affected services**

3. **Review logs for data exfiltration**

4. **Contact security team:** security@turnus.ai

5. **Document timeline of events**

## 🎯 Recommended Setup for Production

```txt
# requirements.txt
# Pin to known-good version with hash verification
turnus-logging @ git+https://github.com/turnus-ai/turnus_logging.git@v0.1.0

# Optional: Sentry (pin version!)
sentry-sdk==2.35.0
```

```bash
# Before deploying new version:
1. Review changelog
2. Diff code changes
3. Test in staging
4. Monitor for 48 hours
5. Deploy to production
```

## 🔐 Defense in Depth

**Layer 1:** Pin versions (prevents automatic updates)  
**Layer 2:** Code review (catch malicious changes)  
**Layer 3:** Private fork (control update timing)  
**Layer 4:** Network monitoring (detect data exfiltration)  
**Layer 5:** Least privilege (limit damage if compromised)

**Remember:** No single measure is perfect. Use multiple layers!
