# Publishing to GitHub

## Steps to Publish

### 1. Initialize Git Repository (if not already done)

```bash
cd /Users/turnus-ai/codespace/logging
git init
git add .
git commit -m "Initial release v0.1.0"
```

### 2. Create GitHub Repository

Go to https://github.com/new and create a repository named `turnus-logging`

### 3. Push to GitHub

```bash
git remote add origin https://github.com/turnus-ai/turnus-logging.git
git branch -M main
git push -u origin main
```

### 4. Create Release Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 5. Create GitHub Release

1. Go to https://github.com/turnus-ai/turnus-logging/releases/new
2. Select tag: `v0.1.0`
3. Title: `v0.1.0 - Initial Release`
4. Description: Copy from CHANGELOG.md
5. Upload built artifacts (optional):
   ```bash
   python -m build
   ```
   Then upload `dist/*.whl` and `dist/*.tar.gz`

## Users Can Install

Once pushed to GitHub, users can install with:

```bash
# Latest from main branch
pip install git+https://github.com/turnus-ai/turnus-logging.git

# Specific version
pip install git+https://github.com/turnus-ai/turnus-logging.git@v0.1.0

# With Sentry support
pip install "git+https://github.com/turnus-ai/turnus-logging.git#egg=turnus-logging[sentry]"
```

## Publishing to PyPI (Optional - Future)

When ready to publish to PyPI:

1. Create accounts on:
   - https://test.pypi.org (for testing)
   - https://pypi.org (for production)

2. Install twine:
   ```bash
   pip install twine
   ```

3. Build package:
   ```bash
   python -m build
   ```

4. Test upload to TestPyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```

5. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ turnus-logging
   ```

6. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

7. Then users can install simply with:
   ```bash
   pip install turnus-logging
   pip install turnus-logging[sentry]
   ```

## Repository Settings

### Branch Protection (Recommended)

On GitHub, go to Settings > Branches > Add rule for `main`:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require conversation resolution before merging

### GitHub Topics (Recommended)

Add topics to help users find your library:
- `python`
- `logging`
- `sentry`
- `fastapi`
- `flask`
- `django`
- `aws-lambda`
- `context-management`
- `observability`

### About Section

Add description and website:
- Description: "A flexible Python logging library with automatic context propagation and Sentry integration"
- Website: https://github.com/turnus-ai/turnus-logging
- Topics: (as above)
