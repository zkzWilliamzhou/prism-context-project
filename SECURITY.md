# Security policy

## Reporting

Open a GitHub issue with a minimal reproduction. Do not paste real credentials,
private instruction files, or proprietary repository contents. If the issue is
sensitive, contact the maintainers privately first.

## Threat model

`prism` reads untrusted Markdown/YAML from a repository and renders it into
terminals, JSON, Markdown, and SARIF. It is designed to fail closed:

| Risk | Mitigation |
|---|---|
| Path traversal via `@import`, links, config, or target | Every path is resolved and containment-checked against the scan root |
| Symlink escape on `init` / `snapshot` writes | `safe_write()` refuses symlinks and out-of-root targets |
| Terminal escape injection | `sanitize()` removes ANSI, C0/C1, bidi controls, and truncates |
| Credential exfiltration through reports | `redact_obj()` is applied at `Report.to_dict()`; secrets are also stripped before directive tokenization |
| Unbounded reads / decompression-style DoS | Per-file 2 MB cap, 32 MB total cap, 5,000 file cap, depth 12 |
| Arbitrary code execution | No `eval`, `exec`, `pickle`, `subprocess`, `socket`, `urllib`, or HTTP imports |
| Malformed UTF-8 | Decoded with `errors="replace"`; a bad byte never aborts the audit |
| Untrusted frontmatter | A small, explicit YAML-subset parser warns on unsupported syntax instead of guessing |
| Import cycles / hop bombs | Bounded BFS with explicit `circular` and `depth` findings |

## What this is not

`prism` is **not** a malware scanner, a secret scanner, a policy engine, or a
live-agent evaluator. Its secret and injection rules are high-precision
heuristics. A clean result is not a security certification.

## Runtime guarantees

- No network sockets are opened.
- No child processes are spawned.
- No telemetry is emitted.
- No files outside the repository are read.
- No file is written unless the user passes `--write`.
