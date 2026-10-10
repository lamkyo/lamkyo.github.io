# Bounty Proposal: Custos-Labs/custos#50 - [Bounty: $55] Pin the Node and pnpm versions consistently\n\nIn `Custos-Labs/custos`: `$55 > $25` gate pass, `ci` label correct. Surgical fix:

### 1. Create `.nvmrc` - exact patch, no `v`

```txt
# .nvmrc
22.13.0
```

> Use `22.13.0` not `22.13`. `22.13` floats patch. `engines.node: >=22.13` allows float, `.nvmrc` must not. No `v` prefix for `fnm`/`setup-node` compat.

Do not also create `.node-version` separately - drift source. If needed: `ln -s .nvmrc .node-version`.

### 2. Replace all 5x `setup-node` pins

Find:
```bash
grep -rn "node-version:" .github/workflows/
# ci.yml: 3x, contributor-checks.yml: 2x
```

Before:
```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: 'pnpm'
```

After in both `.github/workflows/ci.yml` and `.github/workflows/contributor-checks.yml`:
```yaml
- uses: actions/setup-node@v4
  with:
    node-version-file: '.nvmrc'
    cache: 'pnpm'
```

Keep pnpm as-is for pnpm pin:
```yaml
- uses: pnpm/action-setup@v4
  # no `version:` input -> reads packageManager: pnpm@11.17.0 implicitly. Do not duplicate.
```

### 3. Add consistency guard step in `ci.yml`

Add as first step in `ci` job, before setup:
```yaml
- name: Check Node pin consistency (.nvmrc vs engines.node)
  run: |
    node --input-type=module -e "
      import fs from 'node:fs';
      const raw = fs.readFileSync('.nvmrc','utf8').trim();
      const nvmrc = raw.replace(/^v/, '');
      if (!/^\d+\.\d+\.\d+\$/.test(nvmrc)) { console.error(\`Invalid .nvmrc '\${raw}': expected MAJOR.MINOR.PATCH\`); process.exit(1); }
      const engines = JSON.parse(fs.readFileSync('package.json','utf8')).engines?.node ?? '';
      const m = engines.match(/>=\s*(\d+)\.(\d+)(?:\.(\d+))?/);
      if (!m) { console.error(\`Unsupported engines.node '\${engines}'\`); process.exit(1); }
      const floor = [Number(m[1]), Number(m[2]), Number(m[3] ?? 0)];
      const ver = nvmrc.split('.').map(Number);
      for (let i=0;i<3;i++) { if (ver[i] > floor[i]) break; if (ver[i] < floor[i]) { console.error(\`.nvmrc \${nvmrc} does not satisfy engines.node \${engines}\`); process.exit(1); } }
      console.log(\\n