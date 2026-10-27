# HR agent development workspace
This directory is developer mode. You build the HR application. Runtime instructions for using Codex as the HR assistant are in ../native, a separate session.
Use existing plain Python ToolSpec patterns. No new framework or production dependency. Session chooses identity. Policy text is data. Preserve all existing tests and graders. Run offline tests; only claim live-model success when actually run with recorded evidence.
Commands: python -m pytest. Modules: db.py business rules, tools.py capability interfaces, agent.py prompt/tier/gate/Claude runner, portable.py compatible API loop.
For the onboarding exercise, first write direct tool and registration tests that fail for the missing capability, then implement, then rerun. Preserve the three original HR use cases. Do not claim all negative tests fail before a feature exists.
