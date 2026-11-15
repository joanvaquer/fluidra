# Evaluation: six modes, ten questions

Every mode answered the same 10 questions, in 5 languages, some with typos or missing accents, plus an out-of-scope question and one whose answer is not in the manual. All models run locally with Ollama on the same laptop CPU, at temperature 0. Each model was loaded before its first question, so the times are answering time only.

Questions: [questions.json](questions.json). Every answer: [results/answers.md](results/answers.md). Re-run with `python evaluation/run.py`, then `python evaluation/report.py`.

## Findings

**Recommendation:** use `auto` as the everyday mode and `gemma` when quality matters more than
waiting. `auto` uses gemma only for triage and the writer, and gets almost the same score (86%
against 88%) in less than half the time (75 s against 181 s). Its rule checks never let an answer
through without the safety warning or with a made-up page.

- **`gemma` is the most accurate.** It found a correct cause for every troubleshooting question
  (and ranked it first 60% of the time), always added the safety warning and cited the right page
  most often. It is also the slowest: 181 s on average, and up to 5 minutes for one answer.
- **`auto` gets almost `gemma`'s quality in less than half the time.** It uses the same model but
  makes 2 LLM calls per question instead of 4–5, so it takes 75 s on average and never more than
  94 s. It cited the right page as often as `gemma` (88%) and never cited a page outside the
  evidence. Its weak spot is triage: it took the Catalan question for French (and answered in
  French, with the wrong cause), and for the humming motor (q05) it matched "will not start"
  instead of "hums", so it ranked wrong voltage first.
- **`qwen` is the weakest at triage.** It refused the German question as out of scope and ranked
  the right cause first in only 2 of the 5 troubleshooting questions.
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
  `qwen` and `deepseek` refused the warranty question; `llama`, `gemma` and `auto` said the manual
  doesn't give it; `offline` is the only mode that answered it badly.
- **Times vary a lot.** The same mode took from 7 s (a refusal) to almost 10 minutes (qwen, q08,
  where the writer produced a long answer and the verifier asked for a rewrite).

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

## Summary

| Mode | Model | Score | Mean time | Median | Slowest | LLM calls / question | Verified | Errors |
|---|---|---|---|---|---|---|---|---|
| `qwen` | qwen2.5:3b | **80%** | 148 s | 103 s | 580 s | 4.0 | 10/10 | 0 |
| `llama` | llama3.2:3b | **83%** | 148 s | 157 s | 309 s | 4.1 | 10/10 | 0 |
| `gemma` | gemma3:4b | **88%** | 181 s | 174 s | 302 s | 4.5 | 10/10 | 0 |
| `deepseek` | deepseek-v2:16b | **80%** | 134 s | 127 s | 327 s | 3.8 | 10/10 | 0 |
| `auto` | gemma3:4b | **86%** | 75 s | 79 s | 94 s | 1.9 | 10/10 | 0 |
| `offline` | — | **65%** | <0.1 s | <0.1 s | <0.1 s | 0.0 | 10/10 | 0 |

*Score*: share of the applicable checks below that passed, over all ten questions. *Verified*: answers the mode's own verifier approved (it is not a measure of correctness). *LLM calls*: 2 in `auto` and 5 in the LLM modes, plus 1 or 2 when an answer is rewritten.

## Results by check

| Check | `qwen` | `llama` | `gemma` | `deepseek` | `auto` | `offline` |
|---|---|---|---|---|---|---|
| No error: the mode returned an answer | 100% | 100% | 100% | 100% | 100% | 100% |
| In-scope questions answered, out-of-scope refused | 90% | 100% | 100% | 100% | 100% | 90% |
| Triage found the right intent | 88% | 67% | 67% | 88% | 67% | 56% |
| Triage detected the question's language | 88% | 89% | 89% | 100% | 89% | 89% |
| The answer is written in the question's language | 88% | 100% | 89% | 88% | 89% | 44% |
| A correct cause is among the diagnosed causes | 80% | 20% | 100% | 60% | 60% | 40% |
| The first diagnosed cause is a correct one | 40% | 20% | 60% | 40% | 60% | 40% |
| The answer cites the page that has the answer | 62% | 75% | 88% | 62% | 88% | 38% |
| Every cited page is in the evidence (no made-up pages) | 88% | 100% | 88% | 75% | 100% | 75% |
| Disconnect-power warning present when electrical work is involved | 100% | 100% | 100% | 100% | 100% | 100% |
| The answer contains the key fact | 50% | 88% | 88% | 50% | 75% | 38% |
| No invented warranty period (the manual gives none) | 100% | 100% | 100% | 100% | 100% | 100% |
| Says the manual doesn't give the warranty period, if it answers | — | 100% | 100% | — | 100% | 0% |

## Results by question

Score of each answer (checks passed / applicable) and its time.

| Question | Lang | Variant | `qwen` | `llama` | `gemma` | `deepseek` | `auto` | `offline` |
|---|---|---|---|---|---|---|---|---|
| q01: My pump makes a lot of noize and vibrats when… | en | typos | 10/10 · 102 s | 7/10 · 309 s | 10/10 · 278 s | 9/10 · 225 s | 10/10 · 65 s | 8/10 · <0.1 s |
| q02: La bomba no ceba y sale muy poca agua, ¿qué p… | es | clean | 9/10 · 103 s | 7/10 · 198 s | 9/10 · 174 s | 9/10 · 145 s | 10/10 · 90 s | 3/10 · <0.1 s |
| q03: El motor s'ha aturat i crec que salta la prot… | ca | missing accents | 9/11 · 127 s | 7/11 · 169 s | 9/11 · 157 s | 7/11 · 101 s | 6/11 · 80 s | 5/11 · <0.1 s |
| q04: mi bomba no arranca que tengo que revisar | es | no accents or punctuation | 8/11 · 322 s | 7/11 · 234 s | 11/11 · 224 s | 9/11 · 327 s | 11/11 · 94 s | 9/11 · <0.1 s |
| q05: The motor hums but the pump won't start. What… | en | clean | 10/11 · 111 s | 11/11 · 151 s | 10/11 · 302 s | 8/11 · 204 s | 9/11 · 71 s | 11/11 · <0.1 s |
| q06: Wie oft muss man die Gleitringdichtung und di… | de | clean | 2/8 · 19 s | 8/8 · 99 s | 7/8 · 178 s | 7/8 · 123 s | 7/8 · 78 s | 2/8 · <0.1 s |
| q07: what shuold i do with the pump befor the wint… | en | typos | 6/8 · 88 s | 8/8 · 135 s | 5/8 · 146 s | 6/8 · 130 s | 5/8 · 78 s | 6/8 · <0.1 s |
| q08: Como faço o arranque da bomba pela primeira vez? | pt | clean | 7/8 · 580 s | 7/8 · 163 s | 6/8 · 174 s | 6/8 · 75 s | 7/8 · 92 s | 4/8 · <0.1 s |
| q09: ¿Me recomiendas un buen restaurante en Barcel… | es | out of scope | 2/2 · 15 s | 2/2 · 7.9 s | 2/2 · 16 s | 2/2 · 7.2 s | 2/2 · 18 s | 2/2 · <0.1 s |
| q10: How many years of warranty does the ASTRAL pu… | en | not in manual | 3/3 · 15 s | 7/7 · 15 s | 7/7 · 157 s | 3/3 · 6.7 s | 7/7 · 84 s | 6/7 · <0.1 s |

## Failed checks

- `qwen`: q02 facts, q03 language, q03 top_cause, q04 cause_found, q04 top_cause, q04 facts, q05 top_cause, q06 scope, q06 intent, q06 answer_language, q06 page_cited, q06 citations_valid, q06 facts, q07 page_cited, q07 facts, q08 page_cited
- `llama`: q01 intent, q01 cause_found, q01 top_cause, q02 cause_found, q02 top_cause, q02 facts, q03 intent, q03 language, q03 cause_found, q03 top_cause, q04 intent, q04 cause_found, q04 top_cause, q04 page_cited, q08 page_cited
- `gemma`: q02 top_cause, q03 language, q03 answer_language, q05 top_cause, q06 intent, q07 intent, q07 page_cited, q07 facts, q08 intent, q08 citations_valid
- `deepseek`: q01 top_cause, q02 facts, q03 intent, q03 answer_language, q03 cause_found, q03 top_cause, q04 page_cited, q04 citations_valid, q05 cause_found, q05 top_cause, q05 facts, q06 facts, q07 page_cited, q07 facts, q08 page_cited, q08 citations_valid
- `auto`: q03 language, q03 answer_language, q03 cause_found, q03 top_cause, q03 facts, q05 cause_found, q05 top_cause, q06 intent, q07 intent, q07 page_cited, q07 facts, q08 intent
- `offline`: q01 cause_found, q01 top_cause, q02 intent, q02 answer_language, q02 cause_found, q02 top_cause, q02 page_cited, q02 citations_valid, q02 facts, q03 intent, q03 language, q03 answer_language, q03 cause_found, q03 top_cause, q03 page_cited, q04 answer_language, q04 facts, q06 scope, q06 intent, q06 answer_language, q06 page_cited, q06 citations_valid, q06 facts, q07 page_cited, q07 facts, q08 intent, q08 answer_language, q08 page_cited, q08 facts, q10 says_not_in_manual
