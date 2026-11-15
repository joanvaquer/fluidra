## Findings

**Recommendation:** use `auto` as the everyday mode and `gemma` when quality matters more than
waiting. `auto` scores like the full-LLM modes (80%) in less than half the time, and its rule
checks never let an answer through without the safety warning. `gemma` gives the best answers
(88%) but is the slowest, at 3 minutes per question.

- **`gemma` is the most accurate.** It found a correct cause for every troubleshooting question
  (and ranked it first 60% of the time), always added the safety warning and cited the right page
  most often. It is also the slowest: 181 s on average.
- **`auto` costs half as much as `qwen` for the same score.** Both use qwen2.5:3b and score 80%,
  but `auto` makes 2 LLM calls per question instead of 4–5: 66 s on average against 148 s. It
  ranks the right cause first more often (80% against 40%), because its diagnosis comes from the
  table rows of the symptoms triage found instead of a second LLM guess. It shares qwen's
  weaknesses in triage, though: both refused the German question as out of scope.
- **`llama` writes well but diagnoses badly.** Its answers were always in the right language and
  usually had the key fact (88%), but its triage rarely mapped a fault to the right symptom: it
  found a correct cause in only 1 of the 5 troubleshooting questions.
- **`deepseek` is the fastest full-LLM mode (134 s) but cites least reliably.** Two of its answers
  cited a page that was not in the evidence, and it often left out the page that has the answer.
  For the humming motor (q05) it listed four causes, none of them the blocked motor.
- **`offline` answers instantly but only works in English without typos.** It answered in English
  every time, missed the faults described with typos ("noize", "vibrats"), in Catalan and in one
  of the two Spanish questions, and took the German question as out of scope. On clean
  English it is as good as any mode (11/11 on q05). It never invents a value, but it can't tell
  when the manual has no answer: for the warranty question it pasted the replacement table
  ("Capacitor 1 year, Bearings 1 year…"), which reads like a warranty period.
- **The verifiers approve almost everything.** Every LLM-mode answer was "verified" (10/10), yet
  1 in 6 checks failed. The models also wrote citations like "(p. 11)" or "page 97", which no
  verifier recognises, and one `qwen` answer still contains the verifier's feedback ("Fix these
  problems: …"). A verified answer is not a correct answer.
- **Catalan is the weakest language.** Most modes took the Catalan question for Spanish or French,
  and some answered in those languages. `offline` has no Catalan detection at all.
- **The traps.** All modes refused the restaurant question, and none invented a warranty period.
  `qwen`, `deepseek` and `auto` refused the warranty question; `llama` and `gemma` said the manual
  doesn't give it; `offline` is the only mode that answered it badly.
- **Times vary a lot.** The same mode took from 7 s (a refusal) to almost 10 minutes (qwen, q08,
  where the writer produced a long answer and the verifier asked for a rewrite).

### Changes to the question set

The first run had a French and an Italian question (q04, q05). They were replaced by a Spanish and
an English question about the same two faults (the pump won't start; the motor hums but won't
start), so the set is now mostly English and Spanish, with one Catalan, one German and one
Portuguese question. Only those two questions, in every mode, and all the `offline` answers were
re-run; the other answers are from the first run, with the same code.

A check was also added for the warranty question: an answer that doesn't refuse it must say the
manual doesn't give the period. Not inventing a number is not enough, as the `offline` answer
shows.

### Bug found and fixed during the evaluation

The rule that checks the safety warning (`DISCONNECT_WORDS` in `agents/0_common.py`) did not
recognise French *déconnectez* or Italian *disconnettere*. So in the first run `auto` rejected
correct French and Italian answers, rewrote them and flagged them as unverified. After the fix,
those answers were verified on the first draft, in about 90 s instead of about 160 s.

### Limits of this study

Ten questions and one run per mode, on one laptop CPU (8 cores, no GPU): enough to see clear
differences, not to rank modes that are a few points apart. The checks are automatic: they look
for causes, pages, safety words and key facts, and don't judge how clear or complete an answer
is. Read [results/answers.md](results/answers.md) for that.

The answers are not graded by an LLM. The local models are small and, as verifiers, approved
every answer, so they would be lenient judges; a judge from the same family as a mode tends to
favour it; and an LLM grade changes with the prompt and gives no reason that can be checked. Rule
checks are repeatable and say exactly what failed. A stronger external model could judge
clarity, but its grades would first need checking against an expert.
