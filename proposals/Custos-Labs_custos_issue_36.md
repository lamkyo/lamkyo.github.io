# Bounty Proposal: Custos-Labs/custos#36 - [Bounty: $70] Broaden the secret scanner's credential names\n\n# Architecture & Code Fix: Custos-Labs/custos - [Bounty: $70] Broaden the secret scanner's credential names

## Architecture (Opus 5.5)
Proceed with surgical fix.

## Code Fix (SWE-2)
I don't have visibility into the `Custos-Labs/custos` repository contents — I can't produce an exact-line diff (line numbers, imports, file paths) without the actual source. Per the syntax-grounding invariant, I also can't mark anything verified without running it through a linter against the real tree.

**Status: unverified draft.** To produce the real surgical patch, please point me at:

- The scanner source file (e.g., `scanner.go`, `detectors/`, a regex/keyword list, or a YAML/JSON rules config)
- Its existing test file
- The repo language (Go? Python?)

In the meantime, here's the typical shape of this change (Go assumed — adapt as needed):

```diff
--- a/scanner/patterns.go
+++ b/scanner/patterns.go
@@
-var credentialNamePattern = regexp.MustCompile(`(?i)(api[_-]?key|secret|token|password)`)
+var credentialNamePattern = regexp.MustCompile(`(?i)\b(api[_-]?key|secret|token|password|passwd|private[_-]?key|access[_-]?key|client[_-]?secret|signing[_-]?key|encryption[_-]?key|connection[_-]?string|credentials?|bearer)\b`)
```

```go
func TestCredentialNameMatching(t *testing.T) {
	cases := []struct {
		name string
		want bool
	}{
		{"AWS_SECRET_ACCESS_KEY", true},
		{"STRIPE_API_KEY", true},
		{"DB_PASSWD", true},
		{"CLIENT_SECRET", true},
		{"SSH_PRIVATE_KEY", true},
		{"SIGNING_KEY", true},
		{"CONNECTION_STRING", true},
		{"MONKEY", false},
		{"TOKENIZER_VOCAB", false},
		{"PASSPORT_NUMBER", false},
	}
	for _, c := range cases {
		if got := credentialNamePattern.MatchString(c.name); got != c.want {
			t.Errorf("MatchString(%q) = %v, want %v", c.name, got, c.want)
		}
	}
}
```

**Caveat:** word boundaries matter here — substring matching on `pass` would false-positive on `PASSPORT_NUMBER`. Send me the actual scanner file and I'll write the real diff.\n