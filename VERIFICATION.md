# Verification scope

The public participant export was checked on 27 October 2026 with the prepared workshop Python environment and all provider dependencies installed:

| Project | Offline result |
| --- | --- |
| Completed full agent (`agent/`) | 31 passed; 24 live cases deselected |
| Brownfield starter (`live_build/agent/`) | 22 passed; 21 live cases deselected |
| Completed small agent (`greenfield/rehearsal/`) | 17 passed |

These tests cover business rules, permission gates, tool registration, grading, and model/tool protocol handling with scripted clients. They do **not** call paid cloud models. The greenfield starter intentionally fails until implemented; B1 intentionally adds failing onboarding tests to the brownfield starter.

Earlier workshop preparation exercised native Claude/Codex routes and the local Qwen model. Those observations are sample runs, not a reliability benchmark. Some final answers contained unsupported implications even when actions and state checks passed. Always read the answer as well as checking the tool trace.

Cloud API routes are provided in the code but were not verified with a live paid API key during preparation. Company endpoints and LM Studio were not independently verified. Configure your own approved route and run its checks before relying on it.

From the repository root:

```bash
python3 launch.py tests
python3 live_build.py test
python3 greenfield.py test local rehearsal
```

For actual inference after private configuration:

```bash
python3 launch.py verify claude
python3 greenfield.py verify claude rehearsal
```

Replace `claude` with `api` or `local` as appropriate. These commands use fictional data and predetermined confirmation decisions. Reports are saved locally in `evidence/` and excluded from Git. They check selected facts and actions, not every property of the answer.

The exercise is complete only after your changed agent handles the new intent through a real model, the underlying tool result and state are correct, and you have written your autonomy/design note. See [exercise/EXERCISE.md](exercise/EXERCISE.md).
