### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Root Cause:**
The issue stems from **dependency drift** and **dead code accumulation**. The `@fortawesome/*` packages were likely added during an initial UI prototype phase or as a "just-in-case" library for future icon needs. However, the development team subsequently adopted a lightweight, custom SVG component approach (as seen in `Navbar.tsx` with `SparkleIcon`, `StarIcon`, etc.). The original dependencies were never removed from `package.json`.

**Architectural Impact:**
1.  **CI/CD Bloat:** Every CI run executes `npm ci`, downloading and installing these unused packages, increasing build time and disk I/O.
2.  **Security Surface:** Unused dependencies still have their own dependency trees, potentially introducing CVEs or vulnerabilities that do not affect the runtime but clutter security scans.
3.  **Maintenance Debt:** Without a mechanism to detect unused dependencies, this pattern will repeat with other libraries.

**Solution Strategy:**
1.  **Remove** the three specific `@fortawesome/*` entries from `frontend/package.json`.
2.  **Regenerate** `package-lock.json` to ensure consistency.
3.  **Add a Guardrail:** Implement a script (e.g., `npm run check-deps`) that scans `package.json` dependencies against the codebase to fail CI if a dependency has zero imports. This prevents future silent accumulation.

---

### 2. SURGICAL CODE SOLUTION

#### Step 1: Modify `frontend/package.json`

Remove the three lines containing `@fortawesome`.

```json
// frontend/package.json
{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "check-deps": "node scripts/check-unused-deps.js"
  },
  "dependencies": {
    "next": "14.2.5",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "lucide-react": "0.400.0",
    "clsx": "2.1.1",
    "tailwind-merge": "2.4.0"
  },
  "devDependencies": {
    "@types/node": "20.14.10",
    "@types/react": "18.3.3",
    "@types/react-dom": "18.3.0",
    "typescript": "5.5.3",
    "eslint": "8.57.0",
    "eslint-config-next": "14.2.5",
    "jest": "29.7.0",
    "ts-jest": "29.2.3",
    "@testing-library/react": "16.0.0",
    "@testing-library/jest-dom": "6.4.6"
  }
}
```

#### Step 2: Create `frontend/scripts/check-unused-deps.js`

This script scans `package.json` dependencies and checks if any file in `lib`, `components`, `pages`, `utils`, or `hooks` imports them.

```javascript
// frontend/scripts/check-unused-deps.js
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Directories to scan for imports
const SCAN_DIRS = ['lib', 'components', 'pages', 'utils', 'hooks'];
const ROOT = path.join(__dirname, '..');

// Read package.json
const pkgPath = path.join(ROOT, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
const deps = Object.keys(pkg.dependencies || {});

// Helper to get all files in a directory recursively
function getFiles(dir, files = []) {
  if (!fs.existsSync(dir)) return files;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      getFiles(fullPath, files);
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

// Collect all source files
let sourceFiles = [];
for (const dir of SCAN_DIRS) {
  const dirPath = path.join(ROOT, dir);
  sourceFiles = sourceFiles.concat(getFiles(dirPath));
}

// Check each dependency
const unusedDeps = [];
for (const dep of deps) {
  // Normalize dependency name for import matching (e.g., @fortawesome/react-fontawesome)
  // We check if the package name appears in any import statement
  const isUsed = sourceFiles.some(file => {
    const content = fs.readFileSync(file, 'utf8');
    // Look for import statements containing the package name
    // This is a simple heuristic; for complex scopes, a proper AST parser is better,
    // but for this specific case, string matching is sufficient and fast.
    return content.includes(dep);
  });

  if (!isUsed) {
    unusedDeps.push(dep);
  }
}

if (unusedDeps.length > 0) {
  console.error('❌ Unused dependencies detected:');
  unusedDeps.forEach(dep => console.error(`   - ${dep}`));
  process.exit(1);
} else {
  console.log('✅ All dependencies are used.');
  process.exit(0);
}
```

#### Step 3: Update `.github/workflows/ci.yml`

Add the `check-deps` step to the frontend job.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Use Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      - name: Check for unused dependencies
        working-directory: frontend
        run: npm run check-deps
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Test
        working-directory: frontend
        run:

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.21s • $0.00)</i>