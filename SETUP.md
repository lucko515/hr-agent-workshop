# Setup — start here

**Use a terminal, keep the whole repository together, and choose ONE model route. No virtual-environment activation is needed.** You do not need Claude, Codex, OpenAI and Ollama all at once.

## 1. Download and open the correct folder

Use **Code → Download ZIP**, then **extract** it. Open the extracted folder in VS Code and choose **Terminal → New Terminal**. The terminal folder must contain `install.py`, `launch.py`, `configure.py`, and `agent/`. Do not run from inside the ZIP, `agent/`, or `live_build/agent/`.

If you use Git instead:

```text
git clone https://github.com/lucko515/hr-agent-workshop.git
cd hr-agent-workshop
```

If you already worked on an earlier download, keep that folder. Download the corrected version into a **separate folder** and transfer your exercise changes deliberately; do not overwrite your work or paste private profiles into GitHub.

## 2. Pick the Python command for YOUR computer

Python **3.10+** is required. Python **3.12** is a straightforward choice. Use a 64-bit installation. Install from [python.org](https://www.python.org/downloads/) or your organization's approved software source, then restart the terminal.

| System | First try | If that command is missing or older than 3.10 |
| --- | --- | --- |
| Windows PowerShell | `py -3.12 --version` | Install Python 3.12 with the Python launcher, reopen PowerShell. If using another supported version, use `py -3 --version`. |
| macOS | `python3 --version` | Apple's Python can be 3.9. Install a newer Python, then try `python3.12 --version`. |
| Linux | `python3 --version` | Install Python 3.10+ and its matching `venv` package using your approved package manager. |

**Below, `python` means the command that passed this check.** Replace it everywhere with `py -3.12`, `python3.12`, or `python3` as appropriate. This is a command placeholder, not an instruction to change your system Python.

For example, on Windows run `py -3.12 install.py --engine local`; on macOS/Linux run `python3 install.py --engine local` if `python3` is new enough.

## 3. Install and check — no keys yet

Choose one installation command:

| What you will use | Command |
| --- | --- |
| Local Ollama, OpenAI, or a compatible company API | `python install.py --engine local` |
| Claude API | `python install.py --engine claude` |
| All routes / complete offline test coverage | `python install.py` |

The installer creates `.venv` inside this repository and installs dependencies there. It is safe to rerun to add another provider. It never modifies your exercise code or model profiles. Internet access to your approved Python package index is required.

```text
python doctor.py
python launch.py tests
```

`doctor.py` must say **PASS**. It makes no paid API calls and prints no keys. With all dependencies, the completed full agent has **31 passing offline tests**. With a limited install, the Claude-specific tests may skip; that is expected. Do not run plain `pytest` from the repository root: it would mix completed projects with deliberately failing starters.

## 4A. Local Ollama — no API key

1. Install [Ollama](https://ollama.com/download) using the approved installer. Reopen your terminal afterward.
2. **Start the server first:** open the Ollama app, or run `python local_server.py` in a separate terminal and leave it running.
3. In the workshop terminal, download and confirm the model:

```text
ollama pull qwen3:4b
ollama list
python configure.py local
```

Press Enter at the model prompt to use `qwen3:4b`, or enter the exact installed tool-capable model name from `ollama list`.

```text
python doctor.py local
python launch.py app local
```

Type: **How many annual leave days do full-time employees get? Cite the policy.**

The model runs locally. The initial package/model downloads need internet access and disk space. A smaller model may choose tools incorrectly or write unsupported claims; inspect the tool trace and actual state. If your computer cannot run this model, use an approved API route or pair with someone who can execute it.

## 4B. Claude API

```text
python configure.py claude
```

Enter your **Anthropic API key** at the hidden prompt, then an exact Claude model ID enabled on your account. Nothing appears while typing the key; that is expected. Use Terminal/PowerShell, not VS Code's Output or Debug Console.

```text
python doctor.py claude
python launch.py app claude
```

A Claude Code subscription does not by itself configure this API profile. The full application uses Claude Agent SDK, including its bundled Claude runtime. On Windows, [Git for Windows](https://git-scm.com/downloads/win) / Git Bash is recommended for Bash tools; restart the terminal after installation. See the [official platform setup notes](https://code.claude.com/docs/en/setup). Package availability can also depend on OS/CPU and the approved package mirror.

## 4C. OpenAI or a compatible company API

```text
python configure.py api
```

Enter the base URL, API key at the hidden prompt, and model ID. For OpenAI you can accept the displayed URL/model defaults if that model is enabled on your account. For company models, use the values supplied by your administrator. The endpoint must support **Chat Completions function tools**; a chat-only interface is insufficient.

```text
python doctor.py api
python launch.py app api
```

`doctor` validates local setup; it does not prove your key, account credit, endpoint or model works. The first model request verifies those. Do not put a key in a URL, chat prompt, screenshot, or issue.

For LM Studio, start its local server with a tool-capable model and configure the `api` profile with its local URL and exact loaded model name. Use a non-secret placeholder key only if the local server does not require authentication.

## 4D. Subscription-only Claude Code or Codex

With the chosen coding CLI already installed and signed in, run **one** of:

```text
python launch.py claude
python launch.py codex
```

This opens the native HR role in `native/`. It does not use the Python application's API profile. A VS Code extension alone does not necessarily install the CLI command used by this launcher. If you have only the extension, open the `native/` folder directly in VS Code and use the extension there. For development, open the exercise workspace instead.

The native assistant queues leave requests. Read the confirmation card and run the displayed approve/decline command yourself in a separate terminal. The assistant must not approve on your behalf.

## 5. Run your exercise, not the finished reference

All commands below run from the repository root. Replace `local` with `claude` or `api` for your configured route.

```text
python live_build.py test
python live_build.py run local
```

The untouched brownfield starter has **22 passing tests** with all dependencies installed. `tests/test_onboarding_workshop.py` is created by your assistant during B1; it is not missing from the download.

For the small greenfield project:

```text
python greenfield.py test
python greenfield.py run local
```

The untouched greenfield starter has **17 intentional failures** and no `main.py` until you build it. To run the already completed small example instead:

```text
python greenfield.py test local rehearsal
python greenfield.py run local rehearsal
```

Read [README.md](README.md) for the build prompts and [exercise/EXERCISE.md](exercise/EXERCISE.md) for the deliverable.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `python` / `python3` / `py` not found, or Python 3.9 | Follow step 2 and use the same working command for every helper. |
| `can't open file install.py` | You are in the wrong folder or have not extracted the ZIP. Open the folder containing `install.py`. |
| `No module named venv` / `ensurepip` | On Debian/Ubuntu install the matching `python3-venv` package; otherwise repair your Python installation. |
| `.venv` cannot start / `dyld` / wrong Python version | Close running agents. Rename `.venv` to `.venv-old`, then run the installer with a supported Python. Keep your code and `.env.*` profiles. |
| PowerShell refuses `Activate.ps1` | Do not activate. The root launchers use `.venv` directly; no execution-policy change is needed. |
| No matching dependency / certificate / proxy error | Check the organization's package mirror and proxy with IT. Do not disable certificate checks. Local/API-only installation avoids the large Claude SDK download. |
| `ModuleNotFoundError` for a provider | Rerun `install.py` with the needed `--engine` value, then `doctor.py PROFILE`. Use the root launchers, not a different environment's Python. |
| `ollama` not found | Install Ollama and reopen the terminal; confirm it is on PATH. |
| Cannot connect to Ollama | Start the Ollama app or `local_server.py` first; keep the server running. |
| Local model not found | Run `ollama list`, pull the intended model, then configure that exact name. |
| Profile missing / malformed / wrong provider | Rerun `configure.py local`, `api`, or `claude`; use the same profile name in the launch command. |
| `AuthenticationError` / HTTP 401 | Re-enter the correct provider key privately; subscription login is separate. |
| HTTP 403 / 404 | Confirm endpoint, permissions and exact model ID with your provider/admin. |
| `RateLimitError` / HTTP 429 | Check account quota, API credit or concurrent requests with your provider/admin. |
| `APIConnectionError` / timeout | Check the approved endpoint/network; for local models check the server and available memory. |
| Greenfield missing `main.py` / failing tests | This is the unimplemented exercise. Follow G1/G2, or append `local rehearsal` to run the completed example. |

Still stuck? Share your OS, Python version, command, and **error type/text with keys removed**. `doctor.py PROFILE` output is designed to be shareable; raw provider errors, profiles and pip logs may contain private details.

## Credentials and verification

Keys stay in ignored local `.env.api` / `.env.claude` files. `.env.local` uses a non-secret placeholder. Do not `source` these files or upload them. Never run `git add -f` on credential files. `.env.example` is a template only.

Offline tests do not call models. Optional `launch.py verify PROFILE` checks use actual inference, including API credit for cloud models, and predetermined approvals for fictional HR actions. Reports remain ignored in `evidence/`. See [VERIFICATION.md](VERIFICATION.md) for tested scope and limitations.
