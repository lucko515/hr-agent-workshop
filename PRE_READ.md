# Before Session 6: the agent design loop

A useful agent starts with a bounded job. In this workshop, the job is to help an employee with company HR policy, leave requests and unresolved questions.

The model receives instructions, a request and descriptions of allowed tools. It may answer or propose a tool call. The application checks that proposal, runs a permitted function, and returns the result. The model can use that result in its next step. The application also needs a limit so the loop cannot continue indefinitely.

A policy search reads data. A leave submission changes data. Those operations deserve different controls. Our code checks dates and employee identity, and asks the employee to confirm the exact proposed write. The manager still decides whether to approve the leave. If the situation is ambiguous, the agent records a case for HR rather than inventing a decision.

We will use a coding agent to build and extend this application. That development tool can edit code and run tests. The HR application used by employees exposes a much smaller set of business operations. Keep those roles separate.

Before class, choose one approved coding assistant and one execution route. Install dependencies and, if using a local model, download it in advance. Follow SETUP.md. Do not bring real employee data or put credentials in an AI prompt.

Come with one small idea for an additional capability. Write one successful request, one unsupported request, and the state that must remain unchanged. Those examples become your acceptance criteria.
