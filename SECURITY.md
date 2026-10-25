# Security

This repository is a set of instructions that agents load and follow, so a change to `SKILL.md` can change what someone's agent does. Treat it like code.

## Reporting

Report anything that could make an agent act against its user (hidden instructions, a tampered download, a lookalike copy of this skill) through GitHub's private vulnerability reporting: the **Security** tab, then **Report a vulnerability**. Please don't open a public issue for it.

## What you install

- `skills/ambition/SKILL.md` on `main` is the skill. It has no scripts, no network calls and no tool permissions of its own.
- The zip at https://nickbeaird.com/ambition/ambition.zip is built from the same file by `scripts/build.py`.
- Read `SKILL.md` before you install it. It is short, and nothing else gets loaded.
