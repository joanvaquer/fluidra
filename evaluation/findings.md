## Findings

**Recommendation:** use `auto` as the everyday mode and `gemma` when quality matters more than
waiting. `auto` matches the full-LLM modes on score (80%) in about half the time, and its rule
checks never let an answer through without the safety warning. `gemma` gives the best answers
(89%) but is the slowest, at almost 3 minutes per question.

- **`gemma` is the most accurate.** It found a correct cause for every troubleshooting question
  (top cause right 80% of the time), always added the safety warning and cited the right page
  most often. It is also the slowest: 163 s on average.
- **`auto` costs half as much as `qwen` for the same score.** Both use qwen2.5:3b and score 80%,
  but `auto` makes 2 LLM calls per question instead of 4–5: 66 s on average against 135 s. It
  ranks the right cause first more often (80% against 40%), because its diagnosis comes from the
  table rows of the symptoms triage found instead of a second LLM guess. It shares qwen's
  weaknesses in triage, though: both refused the German question as out of scope.
- **`llama` writes well but diagnoses badly.** Its answers were always in the right language and
  usually had the key fact (88%), but its triage never mapped a fault to the right symptom, so it
  diagnosed no correct cause at all (0%).
- **`deepseek` is the fastest full-LLM mode (107 s) but the least safe:** it left out the
  disconnect-power warning in 2 of the 3 electrical questions, and twice cited a page that was
  not in the evidence.
- **`offline` answers instantly but only works in English without typos.** It answered in English
  every time, missed every fault described with typos ("noize", "vibrats") or in another language,
  and took the German question as out of scope. It never invents anything: it scored 100% on safety
  and on the warranty trap.
- **The verifiers approve almost everything.** Every LLM-mode answer was "verified" (10/10), yet
  1 in 5 checks failed. The models also wrote citations like "(p. 11)" or "page 97", which no
  verifier recognises. A verified answer is not a correct answer.
- **Catalan is the weakest language.** Most modes took the Catalan question for Spanish or French,
  and some answered in those languages. `offline` has no Catalan detection at all.
- **Every mode passed both traps.** All of them refused the restaurant question, and none invented
  a warranty period (the manual gives none).
- **Times vary a lot.** The same mode took from 7 s (a refusal) to almost 10 minutes (qwen, q08,
  where the writer produced a long answer and the verifier asked for a rewrite).

### Bug found and fixed during the evaluation

The rule that checks the safety warning (`DISCONNECT_WORDS` in `agents/common.py`) did not
recognise French *déconnectez* or Italian *disconnettere*. So `auto` rejected correct French and
Italian answers, rewrote them and flagged them as unverified. After the fix, those two `auto`
answers were re-run: both were verified on the first draft, in about 90 s instead of about 160 s.

### Limits of this study

Ten questions and one run per mode, on one laptop CPU (8 cores, no GPU): enough to see clear
differences, not to rank modes that are a few points apart. The checks are automatic: they look
for causes, pages, safety words and key facts, and don't judge how clear or complete an answer
is. Read [results/answers.md](results/answers.md) for that.
