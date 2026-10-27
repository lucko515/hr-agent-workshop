# Build one new HR capability

Your deliverable is a working extension that handles one new intent end to end, plus a short design note. A worksheet alone is not completion.

## Choose your access route

- Codex / Claude Code with a subscription: use it to modify `starter/`, then test the resulting tools. You can also run the native HR route against your changed copy using the instructions below.
- An approved API or local tool-capable model: run your extension through the HR application and inspect its tool calls and state.
- Chat-only or no execution access: pair with an execution-enabled colleague. You can supply the specification and review results. If pairing is unavailable, do the design now and finish execution afterward. Mark the working-agent deliverable incomplete until an actual model run passes.

## Before class: prepare once

Follow [SETUP.md](../SETUP.md) from the repository root. Use the included `live_build/agent/` working copy and the root `live_build.py` launcher. No activation or second environment is needed. Do not move the starter elsewhere for the standard workshop path: the coding prompts use the shared environment two folders above the project.

Run `python3 live_build.py test` from the repository root (Windows: `py -3.12 live_build.py test`). With all dependencies, the untouched starter has 22 passing tests. Then open `02_Brownfield.code-workspace` for development. Keep runtime sessions separate.

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
