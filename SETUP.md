# Participant setup

Run commands from the repository root. Use Python 3.10 or newer. On Windows replace `python3` with `py`; the launchers select the correct virtual-environment executable automatically.

## Install once

```bash
python3 install.py
```

Select **3** for both provider clients and all workshop tests. Select **1** for OpenAI-compatible/local only or **2** for Claude only. Installation needs internet access; download local models before class. No shell activation is required for the root launchers.

## Choose one model route

### Claude API

```bash
python3 configure.py claude
python3 launch.py app claude
```

The setup asks for your Anthropic API key at a hidden prompt and the exact model ID enabled on your account. It saves `.env.claude` locally. No OpenAI key is needed. The full application uses Claude Agent SDK; the smaller greenfield example uses the Anthropic Messages API directly.

### OpenAI or an approved compatible endpoint

```bash
python3 configure.py api
python3 launch.py app api
```

Enter your base URL, API key at the hidden prompt, and model ID. For OpenAI the default URL is `https://api.openai.com/v1` and the offered default model is `gpt-4.1-mini`; choose a model enabled on your account. A company endpoint must support Chat Completions function tools, not just chat text. The configuration is stored in `.env.api`.

### Local Ollama

Install Ollama from its official distribution. In a terminal:

```bash
ollama pull qwen3:4b
python3 local_server.py
```

Leave the server terminal open if it starts a server. In another terminal at this repository root:

```bash
python3 configure.py local
python3 launch.py app local
```

Use `qwen3:4b` or enter another installed tool-capable model. The profile uses `http://127.0.0.1:11434/v1/` and a non-secret placeholder key. Model downloads and suitable memory are required. Smaller models can be inconsistent about tools and final answers; inspect what actually happened.

For LM Studio or another compatible local server, use `python3 configure.py api`, enter its local base URL and loaded model ID, then use the `api` commands. Enter the server's required key, or a non-secret placeholder if authentication is disabled. The label `api` can point to a local endpoint.

### Claude Code or Codex subscription access

With the chosen CLI already installed and signed in:

```bash
python3 launch.py claude
```

or:

```bash
python3 launch.py codex
```

These launch the native HR role in `native/`. They do not configure the Python application's API route. A coding assistant can also build the exercises; open it in the appropriate **development** folder, not `native/`.

To inspect/reset fictional native records, use a separate terminal:

```bash
cd native
python3 hr.py state
python3 hr.py reset
```

Reset only when you want to discard your local demo records. For leave requests, read the queued card and run the displayed approval/decline command yourself; the assistant must not approve on your behalf.

## Keys and profiles

Use the configuration script, not a chat prompt, to enter keys. `.env.claude`, `.env.api`, and `.env.local` are excluded from Git. They contain JSON-quoted values loaded by the helpers; do not `source` them as shell scripts. `.env.example` contains placeholders only.

Use explicit profile names when launching: `claude`, `api`, or `local`. The loader clears the previous provider settings when switching profiles. Existing subscriptions and API billing are separate; use your organization's approved access.

## Verify your setup

```bash
python3 launch.py tests
python3 live_build.py test
python3 greenfield.py test local rehearsal
```

With all dependencies installed, expect 31, 22 and 17 passing offline tests respectively. The unimplemented `greenfield/live` has intentional failures until you build it. Tests marked `live` are excluded from the default full-agent suite.

Optional real-model checks (cloud requests use API credit):

```bash
python3 launch.py verify claude
python3 greenfield.py verify claude rehearsal
```

Replace `claude` with `api` or `local`. These checks automatically approve or refuse **fictional** test actions according to each case. Read generated reports in `evidence/` and the final answers; a passing assertion is not a guarantee of reliable prose. Do not share reports containing private prompts or paths.

Return to [README.md](README.md) for the workshop sequence. If a client reports authentication or model errors, check your selected profile, approved endpoint, and enabled model ID. If the live exercise seems unchanged, check that the launcher prints `live_build/agent` as its code path.
