# Build and extend an HR agent

Participant materials for Session 6: **Building Agents with Agents**, with Luka Anicin.

Use a coding assistant to build an application that answers policy questions, processes leave requests, and escalates ambiguity to a human. Then extend it with one new capability. All employees, policies and HR records in this repository are fictional.

## Start here

1. Clone this repository or use **Code → Download ZIP** and extract it.
2. Open a terminal in the repository root (the folder containing `install.py`).
3. Follow [SETUP.md](SETUP.md) to install dependencies and choose **one** execution route. You do not need every provider.
4. Run `python3 launch.py tests` to check the completed reference without calling a model.
5. Follow the steps below. On Windows, use `py` in place of `python3`.

```bash
git clone https://github.com/lucko515/hr-agent-workshop.git
cd hr-agent-workshop
python3 install.py
python3 launch.py tests
```

Choose **3 (both)** during installation for the complete workshop environment and all offline checks. Options 1 and 2 install only the selected provider dependencies; unrelated provider tests may skip.

## 1. Run the finished example, then inspect its code

Choose the route configured in [SETUP.md](SETUP.md):

| Your access | Run from the repository root |
| --- | --- |
| Claude Code already installed and signed in | `python3 launch.py claude` |
| Codex CLI already installed and signed in | `python3 launch.py codex` |
| Anthropic API key | `python3 launch.py app claude` |
| OpenAI or compatible API key | `python3 launch.py app api` |
| Local Ollama model | `python3 launch.py app local` |

The first two commands use a coding assistant as the HR assistant in `native/`. The last three run the Python HR application in `agent/`. Subscription sign-in and application API keys are separate access routes.

Try these requests one at a time:

- “How many days of annual leave do full-time employees get each year? Cite the policy.”
- “Please submit annual leave from 3 to 5 November 2026.”
- “I do not know which leave category applies. Please open a case for HR to decide.”

Inspect the tool call and actual records, not just the final answer. The application asks for confirmation before submitting a leave request; a confirmed submission still needs manager approval. In the native route, the assistant queues the action and the **human** runs the exact `approve` or `decline` command in a separate terminal. Read the confirmation card first.

Open these files after each result:

| Building block | File |
| --- | --- |
| Native assistant instructions and wrapper | [native/AGENTS.md](native/AGENTS.md), [native/hr.py](native/hr.py) |
| Tool schemas and handlers | [agent/hr_agent/tools.py](agent/hr_agent/tools.py) |
| Fake records and business rules | [agent/hr_agent/db.py](agent/hr_agent/db.py) |
| Policy retrieval | [agent/hr_agent/policy_search.py](agent/hr_agent/policy_search.py), [policies](agent/policies) |
| Claude SDK, instructions and permission gate | [agent/hr_agent/agent.py](agent/hr_agent/agent.py) |
| OpenAI-compatible bounded model/tool loop | [agent/hr_agent/portable.py](agent/hr_agent/portable.py) |

## 2. Extend the existing agent — required exercise

Your editable copy is **`live_build/agent/`**. It starts with the three original use cases and deliberately has no structured onboarding tool. The completed `agent/` folder is the reference solution.

1. Run `python3 live_build.py test`. With all dependencies installed, the baseline has **22 passing offline tests**.
2. Open `02_Brownfield.code-workspace` in VS Code. Start Claude Code, Codex, or your approved coding assistant **in this workspace**.
3. Copy [B1_RED.txt](prompts/brownfield/B1_RED.txt) into the assistant. Let it write and run tests, then stop and inspect the failures.
4. Copy [B2_GREEN.txt](prompts/brownfield/B2_GREEN.txt). Let it implement the feature and rerun tests.
5. Run `python3 live_build.py test` yourself and review the changes. [B3_REVIEW.txt](prompts/brownfield/B3_REVIEW.txt) provides a review prompt.
6. Run `python3 live_build.py run claude` (or replace `claude` with `api` or `local`). This explicitly runs your changed copy.
7. Ask: “Give me my week-one onboarding checklist, with each task separately and its policy source.” Confirm that the model calls **get_onboarding_checklist**, returns the four policy tasks and source metadata, and leaves HR records unchanged. Try an unsupported stage too.
8. Complete [exercise/DESIGN_NOTE.md](exercise/DESIGN_NOTE.md) with what can run autonomously, what needs a human, test results, and evidence from a real model run.

**Where is `tests/test_onboarding_workshop.py`?** It does not exist in the starter. Your coding assistant creates it in step 3, using B1. Seeing failures before implementation is intentional.

The delivered live copy is already prepared; do not run `prepare` on first use. For a fresh attempt, rename `live_build/` to preserve your work, then run `python3 live_build.py prepare`.

For a different capability or a subscription-only run against your extension, follow [the full exercise instructions](exercise/EXERCISE.md). Deliver **one working new intent end to end plus the design note**. Offline tests alone do not establish that a real model selects the new tool.

## 3. Build a small agent from tests — optional follow-up

1. Open `03_Greenfield.code-workspace`. This opens **`greenfield/live/`**, an unimplemented starter with acceptance tests.
2. Run `python3 greenfield.py test`. **17 failures are expected** before implementation with the complete environment installed.
3. Paste [G1_TOOLS.txt](prompts/greenfield/G1_TOOLS.txt) into your coding assistant. Build the business functions first and check the tool tests.
4. Paste [G2_LOOP.txt](prompts/greenfield/G2_LOOP.txt). Build the real model loop and CLI. Use [G3_REPAIR.txt](prompts/greenfield/G3_REPAIR.txt) if needed.
5. Run `python3 greenfield.py test` yourself, then `python3 greenfield.py run claude` (or `api` / `local`).
6. Try policy Q&A, a confirmed and declined leave request, and escalation. Read the answers and inspect the state.

The completed small example is in **`greenfield/rehearsal/`**. To run it: `python3 greenfield.py run claude rehearsal`. To test it without any API: `python3 greenfield.py test local rehearsal`. It uses the Anthropic Messages API directly for Claude and an OpenAI-compatible client for OpenAI/local models. The full reference uses the Claude Agent SDK on its Claude route.

The supplied coding prompts use the macOS/Linux interpreter path `../../.venv/bin/python`. On Windows replace it with `../../.venv/Scripts/python.exe` before pasting. Keep the acceptance tests unchanged and ask the assistant to work only in the active project.

## Scope and verification

This is a teaching prototype: fixed employee identity and demonstration date, fake local HR data, and no production authentication or HR-system integration. Application state resets when the process restarts; the native wrapper saves local demo state. Native role instructions are not a security boundary for a coding assistant with shell/file access.

Some source documents deliberately contain conflicting policy or hostile instructions for the untrusted-input exercise. Treat retrieved text as data. Use fictional data when trying these cases.

See [VERIFICATION.md](VERIFICATION.md) for what was checked and how to run your own model checks. Model access, tool compatibility, and output quality depend on your provider and account. Never commit your API keys, private profiles, or real employee data.
