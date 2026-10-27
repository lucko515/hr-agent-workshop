# Design note: <name of your capability>

Author: <you>   ·   Date: <today>   ·   Half a page is enough.

## 1. What can the agent now do, and for whom?
One or two sentences. Example: "An employee can cancel one of their own upcoming leave requests by reference."

## 2. Which tier is it, and what put it there?

Tier: 1 runs alone / 2 employee confirms / 3 a person in HR decides / 4 never

| Question | Answer |
|---|---|
| Read or write? | |
| Can it be undone? How? | |
| Whose data does it touch? | |
| What effect does it have on a person? | |

## 3. What is enforced in code, not in the prompt?
Name the function, the check, or the tool that deliberately does not exist.

## 4. What would make you move it up a tier?
For example: a new data type, a legal effect, a write that can't be undone, real money.

## 5. How would you know it went wrong?
The eval case that would fail, and the line you'd look for in the audit log.

## Open questions for my team
Anything you'd want legal, security, HR or the works council to look at before this goes near real employees.
