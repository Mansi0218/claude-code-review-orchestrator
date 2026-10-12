Submission Feedback
I'm not able to review this submission.

The Capstone asks you to run the four official solution/ packs from the course and answer the official reflection brief using the output of those runs. This submission contains neither. What I found instead is a separate Python project under project/python-harness/ that borrows the names of the four systems but is not the course code. It is also packaged inside the classroom repo for a different course (cd14715-claude-code-classroom).

More importantly, the "run evidence" in this pack was not produced by running anything against Claude:

System 1: src/agentic_loop/orchestrator.py says it runs on "simulated API responses", and every stop_reason in the traces comes from simulate_stop_reason(). The assistant turns just repeat "Analyzing claim data... (turn 1)", "(turn 2)" and so on. There are no tool-use IDs and no model calls. anthropic is never even imported.
The run IDs (*_20261009_120000) are hard-coded in generate_artifacts.py. They are not timestamps from a real run, and they don't match the trace filenames (080452).
System 2: the 73.2% reduction comes from repeating the same paragraph 50 and 25 times to inflate the baseline, then counting tokens as len(text) // 4. Your own test log fails on exactly this point (assert -2.13 > 0).
System 3: the brief cites .claude/CLAUDE.md, .claude/rules/python-style.md and .claude/skills/project-review/SKILL.md. None of these files are in the submission. The validator log you included ends with Status: FAILED, Exit Code: 1.
System 4: there is no shift run, no warm tier and no fork_for_hypothesis. It is three made-up defects filtered with one WHERE clause.
Tests: your logs show 31, 31 + 4 failed, 26 + 3 failed and 32 + 1 failed, from your own test files. Yet the brief's checklist marks every rubric item ✅ and calls the project "production-ready". That is not what your evidence shows.
Presenting simulated output as run evidence is not acceptable in this project, whatever tool generated it. The rubric exists to check that you ran the harnesses and understood what they did. A pack built to look like it passes the rubric defeats that purpose.

To get this reviewed, please:

Run the four official solution/ packs as described in the project instructions: the agentic loop, context strategy, Claude Code configuration and orchestrator. Include each pytest log (30 / 30 / 35 / 33) and the System 3 validator output.
Include the real artifacts those runs produce: traces, budget.json, eval and eval_control results, hot state, and the shift-run output.
Fill in the official reflection-brief-template.md (Q1–Q20). Keep each question as written and answer it from your own runs.
Remove python-harness/, the TypeScript starter and the lesson folders from the submission. Only submit the Capstone work.
Please don't submit generated or simulated artifacts again. A resubmission in the same form will be treated the same way.

This also falls under the Udacity Honor Code. https://www.udacity.com/en-US/legal/honor-code(opens in a new tab)

Its section on AI tools explicitly prohibits "allowing AI tools to complete coding projects, written assignments, or assessments on the student's behalf", "using AI tools to bypass learning objectives, grading criteria, or assessment safeguards" and "misrepresenting AI-generated output as the student's own work". You can use AI to help you learn, debug or polish your writing. You cannot use it to produce the work and the evidence that this project is meant to assess. Udacity treats violations seriously. Possible consequences include a failing grade, revoked credit and removal from the program. Please read the Honor Code before you resubmit.