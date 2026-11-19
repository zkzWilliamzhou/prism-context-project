"""Declarative rule metadata.

Kept separate from the executable checks so a rule's ID, rationale and remedy
can be listed (`prism explain`), exported to SARIF, or overridden without
touching detection logic.
"""

RULES_CATALOG: dict[str, tuple[str, str, str]] = {
    "PF001": ("Unparsed frontmatter", "Unsupported YAML syntax was skipped, so metadata-driven rules may be blind.", "Use the documented frontmatter subset (scalars, simple lists/maps, block scalars)."),
    "PF002": ("Unreadable instruction file", "A source could not be read within the size/containment limits and is excluded from every context.", "Check permissions, size, and symlinks."),
    "PF010": ("Weak skill metadata", "The description is the routing signal an agent sees first; a vague or missing one causes under- or over-triggering.", "State what the skill does AND when to use it, with concrete trigger phrases."),
    "PF020": ("Broken or unsafe @import", "An @import that does not resolve (or escapes the repo) silently drops instructions.", "Fix the path, keep it inside the repo, and keep it out of fenced code blocks."),
    "PF021": ("Dead local reference", "A relative link in an instruction file points at a missing path, so the agent cannot follow it.", "Fix or remove the link."),
    "PF030": ("Shadowed instruction file", "Two competing files in one directory mean only one reaches the agent, with no warning from the harness.", "Keep a single source of truth per directory."),
    "PF040": ("Contradictory directives", "Opposite rules reach the same effective context; prose gives no precedence.", "Delete one rule or qualify its scope."),
    "PF041": ("Cross-harness divergence", "Different harnesses receive different (or contradictory) instructions for the same file.", "Consolidate into one portable instruction file and verify with `prism diff`."),
    "PF050": ("Duplicated directive", "The same rule appears in several co-loaded files, wasting context budget.", "Deduplicate into one source."),
    "PF060": ("Context token budget exceeded", "Always-loaded instructions crowd out code and increase the chance rules are ignored.", "Move detail into referenced files and shorten always-on rules."),
    "PF070": ("Possible embedded secret", "Instruction files are frequently committed and widely copied; a credential here leaks broadly.", "Remove the value, rotate it, and use an environment variable."),
    "PF071": ("Risky shell command in instructions", "Agents execute commands listed in instruction files; some patterns are destructive or execute remote code.", "Replace with a pinned, reviewed local command."),
    "PF072": ("Prompt-injection phrasing", "Instruction text that overrides other instructions or hides actions is a supply-chain risk.", "Remove the phrasing and review the file's provenance."),
    "PF073": ("Wildcard tool permission", "A skill that pre-approves every tool removes a useful safety boundary.", "List the specific tools the skill needs."),
    "PF080": ("Stale command", "An instruction references a package script that no longer exists, so the agent will run a failing command.", "Update the instruction or restore the script."),
    "PF090": ("Discovery limit hit", "The scan was bounded, so some files were not inspected.", "Raise `max_targets`/`ignore` deliberately, or narrow the scan root."),
}
