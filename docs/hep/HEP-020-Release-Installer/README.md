# Release & Installer

## Version Management

Current version: **1.0.0**

```yaml
# version.yaml
version: 1.0.0
build: 1
channel: stable
release_date: 2026-07-13
```

## Release Checklist

- [ ] All tests pass (pnpm -r exec vitest run)
- [ ] TypeScript compiles clean (pnpm -r exec tsc --noEmit)
- [ ] All packages build (pnpm -r exec tsc --outDir dist)
- [ ] CHANGELOG updated
- [ ] Version bumped in root package.json
- [ ] Docker image built and tagged
- [ ] Release notes written

## Build Process

```bash
# 1. Clean
pnpm -r exec rm -rf dist

# 2. Install
pnpm install

# 3. Type check
pnpm -r exec tsc --noEmit

# 4. Test
pnpm -r exec vitest run

# 5. Build
pnpm -r exec tsc --outDir dist

# 6. Package
cd dist && tar -czf ../hermes-agent-os-1.0.0.tar.gz .
```

## Installer

### Windows (NSIS)
- Bundles Node.js runtime
- Creates desktop shortcut
- Adds to PATH

### macOS (DMG)
- .app bundle with embedded runtime
- Code signed

### Linux (AppImage)
- Portable AppImage
- deb/rpm packages

## Upgrade Mechanism

1. Check for updates: `GET /api/upgrade/check`
2. Download package: `GET /api/upgrade/download/{version}`
3. Verify checksum
4. Backup current installation
5. Extract new version
6. Migrate configuration
7. Restart service
