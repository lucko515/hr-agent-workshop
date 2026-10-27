# Workshop extension: onboarding checklist

The existing application answers policy questions, validates and submits leave after confirmation, and records unresolved cases for HR. Preserve those behaviors.

Add get_onboarding_checklist(stage), with before_day_one, week_one and first_month as supported values. Retrieve the exact section from the existing onboarding policy. Return its text and title, section, version and effective date. Do not invent employee completion status. Use a stage-only schema and validate it in Python. Register the tool as tier 1 and explain its routing in the system prompt.

Invalid stages and missing sections must return useful errors. The lookup must not change leave requests or HR cases. Tests should cover exact facts/source, invalid inputs, nonmutation and tool/tier registration. First run them red, then implement and run the full offline suite. Afterwards run a real model and verify that the new intent actually calls the new tool.

The exact staged prompts are in delivery/prompts/brownfield. This is a read-only policy capability. Recording HR cases is a different automatic operation in this demonstration, and its safety/authorization must be assessed separately for a real deployment.

