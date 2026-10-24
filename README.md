# Ambition

An agent skill for Claude, Codex, Cursor, Gemini CLI, Copilot and any other agent that reads `SKILL.md`. It finds the more ambitious version of a task, plan, research question or feature, using Felix Rieseberg's four types of ambition: Speed, Altitude, Depth and Range.

Give it a task and it returns the baseline, the more ambitious versions ranked by payoff against cost, a rewritten brief you can run, and what it needs from you. Each version comes with a judge other than the model that would prove it worked. Then it stops, and you pick.

The framework is from Felix Rieseberg's essay [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/) (2026-10-13). This packaging is independent and not endorsed by Felix or Anthropic.

## Install

```
npx skills add https://nickbeaird.com/ambition/ambition.zip
```

Or copy `skills/ambition/` into your agent's skills folder: `~/.claude/skills/` for Claude Code, or `.agents/skills/` in a repo for Codex, Cursor, Gemini CLI, Copilot and OpenCode. In the Claude app, upload `ambition.zip` as a custom skill. For an agent without skill support, save `SKILL.md` as `docs/ambition.md` and add this line to `AGENTS.md`: "When asked to make a task more ambitious, follow docs/ambition.md."

## Use

```
/ambition <task> [planning|research|feature] [light|full]
```

## Layout

- `skills/ambition/SKILL.md`: the skill
- `examples/`: unedited runs of the skill on three made-up tasks
- `site/`: the download page as served at nickbeaird.com (`site/ambition/` is `/ambition/`; `site/fonts/` mirrors the site's `/fonts/`)
- `scripts/build.py`: renders the examples into the page, writes `site/ambition/ambition.zip` and `site/ambition/SKILL.md`

## License

MIT for the skill file. The framework and quoted lines are Felix Rieseberg's.
