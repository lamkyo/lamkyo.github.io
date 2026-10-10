## 1️⃣ ROOT CAUSE & TECHNICAL ANALYSIS  

| Problem | Why it exists | What must change |
|---------|---------------|------------------|
| **No automated reviewer** – the repository only has human reviewers. | The current CI pipeline does not invoke any LLM‑based analysis, so every PR is reviewed manually. | Add a **Claude‑Code sub‑agent** that (1) fetches the PR diff, (2) sends it to Anthropic’s Claude model, (3) receives a structured Markdown review, and (4) posts the comment back to GitHub (or prints it for CLI use). |
| **Missing CLI / Action entry‑point** – there is no executable that can be called from a terminal or a GitHub Action. | The code base does not expose a command‑line interface nor a reusable GitHub Action. | Implement a tiny `claude-review` entry‑point (Python console script) and a minimal GitHub Action (`.github/workflows/claude-review.yml`). |
| **No deterministic output format** – reviewers need a consistent structure (summary, risks, suggestions, confidence). | Claude can be prompted to return free‑form text; without a strict prompt the output varies. | Define a **system prompt** that forces Claude to return a Markdown block with the four required sections. |
| **No test coverage** – we must prove the tool works on real PRs. | Without tests the bounty cannot be verified. | Write unit tests that mock the GitHub and Claude APIs, feed a sample diff, and assert that the generated Markdown contains the required headings. |

**Key architectural decisions**

1. **Language** – Python 3.10+ (widely available on GitHub Actions, easy to package).  
2. **Dependencies** – `requests` (GitHub API), `anthropic` (Claude client), `click` (CLI ergonomics), `pydantic` (typed config), `pytest` + `responses` (mock HTTP).  
3. **Design pattern** – a single `ClaudeReviewer` class that encapsulates:  
   - fetching the diff (`GitHubClient`)  
   - calling Claude (`ClaudeClient`)  
   - formatting the response (`MarkdownFormatter`).  
4. **Security** – All external calls are wrapped in `try/except`; secrets (GitHub token, Anthropic API key) are read only from environment variables.  
5. **Extensibility** – The CLI can be used directly (`claude-review --pr <url>`) **or** invoked from a GitHub Action that runs on `pull_request_target`.  

---

## 2️⃣ SURGICAL CODE SOLUTION  

Below is a **complete, production‑ready** implementation that can be dropped into a fresh repo.  
All files are shown in full and wrapped in `<pre><code>` blocks so you can copy‑paste them directly.

### 2.1 `pyproject.toml` (project metadata & dependencies)

```html
<pre><code>[project]
name = "claude-review"
version = "0.1.0"
description = "Claude‑Code sub‑agent that reviews a PR and posts a structured comment"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Antigravity Team"}]

[project.urls]
Homepage = "https://github.com/your-org/claude-review"

[project.scripts]
claude-review = "claude_review.__main__:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"*" = ["*.yaml"]

[project.dependencies]
click = "^8.1"
requests = "^2.31"
anthropic = "^0.5.0"
pydantic = "^2.5"
</code></pre>
```

### 2.2 Directory layout  

```
claude-review/
├─ src/
│  └─ claude_review/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ config.py
│     ├─ github_client.py
│     ├─ claude_client.py
│     ├─ formatter.py
│     └─ reviewer.py
├─ tests/
│  ├─ conftest.py
│  └─ test_reviewer.py
├─ .github/
│  └─ workflows/
│     └─ claude-review.yml
├─ README.md
└─ pyproject.toml
```

### 2.3 Core modules  

#### `src/claude_review/config.py`

```html
<pre><code>import os
from pydantic import BaseSettings, Field, SecretStr

class Settings(BaseSettings):
    github_token: SecretStr = Field(..., env="GITHUB_TOKEN")
    anthropic_api_key: SecretStr = Field(..., env="ANTHROPIC_API_KEY")
    model: str = Field("claude-3-5-sonnet-20240620", env="CLAUDE_MODEL")
    max_tokens: int = Field(1024, env="CLAUDE_MAX_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
</code></pre>
```

#### `src/claude_review/github_client.py`

```html
<pre><code>import requests
from urllib.parse import urlparse
from typing import Tuple

class GitHubClient:
    API_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review-agent"
        })

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        """
        Extract owner, repo and PR number from a full Git

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.43s • $0.00)</i>