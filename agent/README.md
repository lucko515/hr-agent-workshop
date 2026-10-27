# HR application code

Start with README.md and SETUP.md at the repository root. They contain the model profiles, launch commands and exercise sequence.

## Files to inspect
- hr_agent/portable.py: bounded compatible API loop, with tool results returned to the model.
- hr_agent/agent.py: system instructions, tier map, exact confirmation cards, gate and optional Claude SDK runner.
- hr_agent/tools.py: business capability schemas and handlers; identity comes from Session.
- hr_agent/db.py: fake HR data and business validation.
- hr_agent/policy_search.py and policies/: local source documents and simple search.
- tests/: offline business/gate/loop tests and opt-in real-model evals.

The workshop's live extension is structured onboarding lookup. SPEC.md describes that exercise. The completed reference has the tool; the starter and untouched live copy intentionally do not.

Use the delivery launch helpers so the correct environment, private profile and application copy are selected. The generic loop requires Chat Completions function-tool compatibility. Cloud/company/LM Studio access is not verified merely because the client library accepts its URL. See VERIFICATION.md at the repository root for verification scope.

This is a fictional local prototype with in-memory state, fixed demonstration identity and date. It is not a production HR service.
