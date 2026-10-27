# Build one new HR capability

Your deliverable is a working extension that handles one new intent end to end, plus a short design note. A worksheet alone is not completion.

## Choose your access route

- Codex / Claude Code with a subscription: use it to modify `starter/`, then test the resulting tools. You can also run the native HR route against your changed copy using the instructions below.
- An approved API or local tool-capable model: run your extension through the HR application and inspect its tool calls and state.
- Chat-only or no execution access: pair with an execution-enabled colleague. You can supply the specification and review results. If pairing is unavailable, do the design now and finish execution afterward. Mark the working-agent deliverable incomplete until an actual model run passes.

## Before class: prepare your starter copy

Copy `starter/` into your own working directory. In that copy:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

Windows activation: `.venv\Scripts\Activate.ps1`. The untouched starter has 22 passing offline tests. For API/local execution install `.[openai,dev]` instead; for Claude SDK use `.[claude,dev]`. Native Codex/Claude runtime use of the tools requires only Python; tests require pytest.

Open `codex` or `claude` in THIS starter copy for development. Use a separate native session after implementation, as described below. Do not overwrite the supplied completed reference while doing the exercise.

## Follow along during 09:43–10:05

Use the supplied `live_build/agent` workspace or your own copy of `exercise/starter`. Open the Claude Code extension in VS Code, or your approved coding assistant, in that development folder.

1. Read the acceptance contract and existing policy. The baseline suite has 22 passing tests.
2. Paste `prompts/brownfield/B1_RED.txt` (relative to the repository root). Review the generated tests and their intended failures before implementation.
3. Paste `prompts/brownfield/B2_GREEN.txt`. Let the assistant edit the files and run the tests.
4. Review the schema, handler, registration and routing instruction. Run the tests yourself.
5. From the repository root, run `python3 live_build.py run claude`, `python3 live_build.py run api` or `python3 live_build.py run local`. Confirm the printed code path points to your live copy. Ask the new intent, inspect the actual tool call and facts, then try an unsupported stage.
6. At 10:50, complete `exercise/DESIGN_NOTE.md`. Keep your real run transcript and test output with it. If you need more time, complete the implementation and real-model run after class.

The prompts assume the supplied folder layout and shared environment. If you copy the project elsewhere, replace their interpreter path with your own prepared Python environment. The time slot is a bounded attempt, not a guarantee that every participant will finish. Installation and model downloads happen before class.

The Greenfield demonstration at 10:09 teaches how to start a smaller agent. It is optional follow-up practice. Your required submission remains one working extension plus the note.

## Exact subscription-only run against your extension

Make a separate workspace with two sibling folders named `agent` and `native`. Copy your modified starter into `agent`. Copy the supplied `native` folder into `native`, excluding `state.json` and caches. Its hr.py imports tools from the sibling `agent` folder. Open Codex or Claude Code from `native`, then ask your new intent in natural language. Do not open the developer session and runtime session in the same directory.

Example terminal layout:

```text
my-extension/
  agent/       # your changed starter
  native/      # supplied runtime wrapper + AGENTS.md + CLAUDE.md
```

From `my-extension/native`: `python3 hr.py reset`, then `codex` or `claude`. For onboarding, ask: “Give me my week-one onboarding checklist, with each task separately and its policy source.” The transcript must call your NEW tool, not merely answer through the pre-existing search tool.

## Acceptance for the supplied onboarding capability

1. Week one returns laptop collection, security training within 5 working days, two-factor authentication, and onboarding buddy, grounded in Onboarding Checklist / Week one / v1.8 / 2026-05-01.
2. Unsupported stage returns a useful error or clarification; it never invents company requirements.
3. Leave requests and HR cases remain unchanged.
4. The agent selects get_onboarding_checklist when handling the new intent.

The supplied completed `agent/` is the reference solution. Your exercise starts from `exercise/starter/`, which intentionally does not contain that new tool.
