# Evaluation: six modes, ten questions

Every mode answered the same 10 questions, in 7 languages, some with typos or missing accents, plus an out-of-scope question and one whose answer is not in the manual. All models run locally with Ollama on the same laptop CPU, at temperature 0. Each model was loaded before its first question, so the times are answering time only.

Questions: [questions.json](questions.json). Every answer: [results/answers.md](results/answers.md). Re-run with `python evaluation/run.py`, then `python evaluation/report.py`.

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

## Summary

| Mode | Model | Score | Mean time | Median | Slowest | LLM calls / question | Verified | Errors |
|---|---|---|---|---|---|---|---|---|
| `qwen` | qwen2.5:3b | **80%** | 135 s | 103 s | 580 s | 3.8 | 10/10 | 0 |
| `llama` | llama3.2:3b | **80%** | 152 s | 165 s | 309 s | 4.1 | 10/10 | 0 |
| `gemma` | gemma3:4b | **89%** | 163 s | 171 s | 278 s | 4.5 | 10/10 | 0 |
| `deepseek` | deepseek-v2:16b | **80%** | 107 s | 115 s | 225 s | 3.8 | 10/10 | 0 |
| `auto` | qwen2.5:3b | **80%** | 66 s | 56 s | 194 s | 1.9 | 10/10 | 0 |
| `offline` | — | **54%** | <0.1 s | <0.1 s | <0.1 s | 0.0 | 10/10 | 0 |

*Score*: share of the applicable checks below that passed, over all ten questions. *Verified*: answers the mode's own verifier approved (it is not a measure of correctness). *LLM calls*: 2 in `auto` and 5 in the LLM modes, plus 1 or 2 when an answer is rewritten.

## Results by check

| Check | `qwen` | `llama` | `gemma` | `deepseek` | `auto` | `offline` |
|---|---|---|---|---|---|---|
| No error: the mode returned an answer | 100% | 100% | 100% | 100% | 100% | 100% |
| In-scope questions answered, out-of-scope refused | 90% | 100% | 100% | 100% | 90% | 90% |
| Triage found the right intent | 88% | 67% | 67% | 88% | 88% | 33% |
| Triage detected the question's language | 88% | 89% | 89% | 100% | 88% | 89% |
| The answer is written in the question's language | 88% | 100% | 89% | 88% | 75% | 33% |
| A correct cause is among the diagnosed causes | 80% | 0% | 100% | 60% | 80% | 0% |
| The first diagnosed cause is a correct one | 40% | 0% | 80% | 20% | 80% | 0% |
| The answer cites the page that has the answer | 62% | 75% | 88% | 75% | 50% | 12% |
| Every cited page is in the evidence (no made-up pages) | 88% | 100% | 88% | 88% | 88% | 75% |
| Disconnect-power warning present when electrical work is involved | 67% | 100% | 100% | 33% | 100% | 100% |
| The answer contains the key fact | 62% | 88% | 88% | 62% | 50% | 25% |
| No invented warranty period (the manual gives none) | 100% | 100% | 100% | 100% | 100% | 100% |

## Results by question

Score of each answer (checks passed / applicable) and its time.

| Question | Lang | Variant | `qwen` | `llama` | `gemma` | `deepseek` | `auto` | `offline` |
|---|---|---|---|---|---|---|---|---|
| q01: My pump makes a lot of noize and vibrats when… | en | typos | 10/10 · 102 s | 7/10 · 309 s | 10/10 · 278 s | 9/10 · 225 s | 10/10 · 33 s | 8/10 · <0.1 s |
| q02: La bomba no ceba y sale muy poca agua, ¿qué p… | es | clean | 9/10 · 103 s | 7/10 · 198 s | 9/10 · 174 s | 9/10 · 145 s | 8/10 · 79 s | 3/10 · <0.1 s |
| q03: El motor s'ha aturat i crec que salta la prot… | ca | missing accents | 9/11 · 127 s | 7/11 · 169 s | 9/11 · 157 s | 7/11 · 101 s | 6/11 · 30 s | 5/11 · <0.1 s |
| q04: Ma pompe ne démarre pas du tout, que dois-je … | fr | clean | 9/11 · 154 s | 8/11 · 168 s | 11/11 · 180 s | 9/11 · 151 s | 11/11 · 93 s | 5/11 · <0.1 s |
| q05: il motore fa un ronzio ma non parte, cosa faccio | it | no punctuation | 9/11 · 149 s | 8/11 · 256 s | 11/11 · 168 s | 8/11 · 106 s | 11/11 · 91 s | 5/11 · <0.1 s |
| q06: Wie oft muss man die Gleitringdichtung und di… | de | clean | 2/8 · 19 s | 8/8 · 99 s | 7/8 · 178 s | 7/8 · 123 s | 2/8 · 16 s | 2/8 · <0.1 s |
| q07: what shuold i do with the pump befor the wint… | en | typos | 6/8 · 88 s | 8/8 · 135 s | 5/8 · 146 s | 6/8 · 130 s | 6/8 · 95 s | 6/8 · <0.1 s |
| q08: Como faço o arranque da bomba pela primeira vez? | pt | clean | 7/8 · 580 s | 7/8 · 163 s | 6/8 · 174 s | 6/8 · 75 s | 7/8 · 194 s | 4/8 · <0.1 s |
| q09: ¿Me recomiendas un buen restaurante en Barcel… | es | out of scope | 2/2 · 15 s | 2/2 · 7.9 s | 2/2 · 16 s | 2/2 · 7.2 s | 2/2 · 12 s | 2/2 · <0.1 s |
| q10: How many years of warranty does the ASTRAL pu… | en | not in manual | 3/3 · 15 s | 6/6 · 15 s | 6/6 · 157 s | 3/3 · 6.7 s | 3/3 · 12 s | 6/6 · <0.1 s |

## Failed checks

- `qwen`: q02 facts, q03 language, q03 top_cause, q04 top_cause, q04 safety, q05 cause_found, q05 top_cause, q06 scope, q06 intent, q06 answer_language, q06 page_cited, q06 citations_valid, q06 facts, q07 page_cited, q07 facts, q08 page_cited
- `llama`: q01 intent, q01 cause_found, q01 top_cause, q02 cause_found, q02 top_cause, q02 facts, q03 intent, q03 language, q03 cause_found, q03 top_cause, q04 intent, q04 cause_found, q04 top_cause, q05 cause_found, q05 top_cause, q05 page_cited, q08 page_cited
- `gemma`: q02 top_cause, q03 language, q03 answer_language, q06 intent, q07 intent, q07 page_cited, q07 facts, q08 intent, q08 citations_valid
- `deepseek`: q01 top_cause, q02 facts, q03 intent, q03 answer_language, q03 cause_found, q03 top_cause, q04 top_cause, q04 safety, q05 cause_found, q05 top_cause, q05 safety, q06 facts, q07 page_cited, q07 facts, q08 page_cited, q08 citations_valid
- `auto`: q02 page_cited, q02 facts, q03 language, q03 answer_language, q03 cause_found, q03 top_cause, q03 facts, q06 scope, q06 intent, q06 answer_language, q06 page_cited, q06 citations_valid, q06 facts, q07 page_cited, q07 facts, q08 page_cited
- `offline`: q01 cause_found, q01 top_cause, q02 intent, q02 answer_language, q02 cause_found, q02 top_cause, q02 page_cited, q02 citations_valid, q02 facts, q03 intent, q03 language, q03 answer_language, q03 cause_found, q03 top_cause, q03 page_cited, q04 intent, q04 answer_language, q04 cause_found, q04 top_cause, q04 page_cited, q04 facts, q05 intent, q05 answer_language, q05 cause_found, q05 top_cause, q05 page_cited, q05 facts, q06 scope, q06 intent, q06 answer_language, q06 page_cited, q06 citations_valid, q06 facts, q07 page_cited, q07 facts, q08 intent, q08 answer_language, q08 page_cited, q08 facts
