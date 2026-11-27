@AGENTS.md

# Claude Code specifics

- Before committing, run and keep clean:
  - `claude plugin validate .` and `claude plugin validate . --profile directory`
  - `python3 scripts/build_skills_index.py --check`
- Try the plugin in a session with `claude --plugin-dir .` (skills appear as `github-ninja:<name>`).
- Cloud sessions can't push tags or delete remote branches: ask the maintainer.
