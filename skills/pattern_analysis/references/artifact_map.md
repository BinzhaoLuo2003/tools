# Artifact Map

Use this map to decide which file proves which kind of claim.

| Artifact | Primary use | Typical questions |
|---|---|---|
| Task spec | Task contract | What had to be done? What is the reference answer? What rubric gates are explicit? |
| Execution summary | Run shape | Did the run ever start? How long was it? How many turns and tool calls? Which tool families dominated? |
| Tool trace | Temporal behavior | Was the first exploration sensible? Where did the run pivot? Was there repetition or blind scanning? |
| Reconstructed code | Actual experiment chain | Did the system produce logic that could generate the required evidence? Was the analysis pipeline structurally valid? |
| Reviewer context | Compressed evidence timeline | Where were the main turning points? Which facts mattered to the reviewer or judge? |
| Final response | Claim surface | What did the system say it did? Does the conclusion overclaim beyond the evidence? |
| Grader report | Rubric delta | Which elements were present, missing, or explicitly wrong? |
| Technical analysis | Analyst bootstrap | What did the reviewer-side code analysis notice? Which methods were or were not present? |
| Raw trajectory | Fine-grained chronology | What happened at exact turn resolution when the summary files are ambiguous? |
| Executed notebook or raw logs | Ground truth execution | What code actually ran, what failed, and what outputs existed in the live environment? |

## Common failure to avoid

Do not let the technical analysis or grader report fully substitute for primary evidence. They are useful summaries, but they are downstream interpretations.

## Quick routing hints

- If the execution summary shows very low tool count and no meaningful code, this may be a startup failure.
- If tool count is high but reconstructed code is incoherent, this is often an experiment-chain failure rather than a pure timeout issue.
- If code is structurally valid but the final response contradicts the evidence, the bottleneck is often evidence integration or reporting logic.
- If the run repeatedly hits contract errors around a single primitive, inspect whether a stronger run used a different abstraction layer entirely.
