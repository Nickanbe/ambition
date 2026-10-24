# Ambition eval: does the Recommended brief beat the original task?

The skill's one rule is that every upgrade names a judge that is not the model. This eval holds the skill to the same rule.

## Arms

For each task:

- **A (baseline):** an agent receives `prompt` verbatim and works in a fresh copy of `fixture/`.
- **B (ambition):** an agent runs the skill on `prompt` (light unless the task says otherwise) with read access to the fixture, then a fresh agent receives only the skill's Recommended brief and works in a fresh copy of `fixture/`. Items under "Needs from you" are answered with: "Use only what is in the working directory; no network."

Both arms use the same model and have no network. Neither sees `judge/`.

## Task layout

```
tasks/<id>/
  task.json    {"id", "mode": "feature|research|planning", "size": "light", "prompt", "judge": "auto|human", "control": bool, "notes"}
  fixture/     copied to the arm's working directory
  judge/
    judge.py   python3 -I judge/judge.py <workdir>  ->  prints one JSON line {"score": 0..1, "checks": {...}}
    reference/ a reference solution used to validate the judge (never shown to arms)
```

## Judge rules

1. Score the outcome the person asking actually needs, not literal compliance. The literal request is always part of the score, so a correct literal answer never scores 0.
2. Hidden checks must be things a field-leading expert would cover without being told (edge cases a senior engineer tests, the confound an analyst checks). No mind-reading gotchas.
3. Judges read only files the arm writes in `<workdir>` plus their own data in `judge/`.
4. Every judge is validated: untouched fixture scores low, `judge/reference/` applied over the fixture scores high (>= 0.9). Record both numbers in `notes`.
5. Control tasks (`control: true`) are trivial. The skill should say so and do the task; the judge also penalizes scope creep (extra files, changed behavior).
6. `judge: human` tasks (planning) are blind-ranked by Nick: arm outputs are shuffled and labeled X/Y. A rubric in `judge/rubric.md` is shown to him.

## Scoring

Per task: `B - A` on the judge score, plus agent wall time and tokens for each arm. Headline: B wins on at least 10 of 12 tasks, with control tasks counted as wins only if B did not inflate scope.
