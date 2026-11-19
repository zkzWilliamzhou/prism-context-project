---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions red-green-refactor, or wants integration tests.
category: engineering-core
source_repo: mattpocock/skills
source_path: skills/engineering/tdd/SKILL.md
source_url: https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md
metadata:
  license: MIT (reported by catalogs)
  status: condensed-reconstruction
---

# Test-Driven Development

TDD is the RED → GREEN → REFACTOR loop. The reference makes that loop produce
tests worth keeping.

## Core principle

Tests verify behavior through public interfaces, not implementation details.
Code can change entirely; tests should not. A good test reads like a
specification: "user can checkout with valid cart" tells you exactly what
capability exists, and it survives refactors because it does not care about
internal structure.

## Seams

A seam is the public boundary you test at: the interface where you observe
behavior without reaching inside. Before writing a test, write down the seams
under test and confirm them. No test is written at an unconfirmed seam.

## Anti-patterns

- **Implementation-coupled:** mocks internal collaborators, tests private
  methods, or verifies through a side channel. The tell: the test breaks when
  you refactor but behavior has not changed.
- **Tautological:** the assertion recomputes the expected value the way the code
  does, so it passes by construction. Expected values must come from an
  independent source: a known-good literal, a worked example, or the spec.
- **Horizontal slicing:** writing all tests first, then all implementation.
  Work in vertical slices: one test → one implementation → repeat.

## Rules of the loop

1. Red before green: write the failing test first, then only enough code to
   pass.
2. One slice at a time: one seam, one test, one minimal implementation.
3. Refactoring is not part of the loop; it follows a green suite and needs its
   own behavior-preservation gate.

See [references/REFERENCE.md](references/REFERENCE.md) for examples and mocking
guidance.
