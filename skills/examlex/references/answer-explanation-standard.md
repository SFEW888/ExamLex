# Comprehensive Answer Explanation Standard

Use this contract whenever ExamLex generates a mock paper, explains a practice
set, reviews errors, or supplies an answer key with teaching notes. It applies to
`CET4`, `CET6`, `POSTGRADUATE_ENGLISH`, `TEM4`, and `TEM8`, and to every supported
module: `vocabulary`, `listening`, `reading`, `translation`, `writing`, `cloze`,
`language-knowledge`, `proofreading`, and `dictation`.

## Purpose and evidence boundary

An explanation must teach the learner how to understand the task, reach the
answer, reject alternatives, and verify the result. A bare key, a one-sentence
conclusion, or one generic paragraph for several questions is incomplete.

Commercial practice-book answer pages or operator-supplied annotated examples
may inform presentation structure only. Treat them as `R`-level teaching-method references,
not as official papers, official answer banks, fixed question banks,
or direct sources for new questions. Do not copy their questions, passages,
scripts, model answers, translations, or explanation prose into generated
material. Their layout does not raise the evidence level of any source.

## Default depth and learner language

`detailed` is the default for every learner and every complete mock paper. Do not
silently reduce explanation depth for `基础偏弱`, `中等基础`, `基础较好`, a high
target band, or any exam type. A learner may explicitly request a concise key for
one output, but that does not change the stored default.

Use the learner's chosen support language. For the default Chinese-learner
profile, supply Chinese translations and explanations. Stronger learners still
receive every required field; compact wording may replace elementary glosses,
but evidence, translations, distractor analysis, error diagnosis, and transfer
guidance remain mandatory.

For `基础偏弱`, keep the same complete contract and add more scaffolding:

- define essential words and grammar terms in plain language;
- split long sentences and reasoning into smaller numbered steps;
- show the relation between the question, evidence, and answer explicitly;
- distinguish literal meaning from contextual meaning;
- finish with one short retry or transfer task.

## Core output contract

### Objective or selective-response items

Give every item its own explanation. Use these field names as the conceptual
contract even when the learner-facing answer book uses natural Markdown:

| Field | Required content |
|---|---|
| `answer_key` | Question number and one unambiguous answer. |
| `tested_skill` | Question type and the ability being tested. |
| `question_translation` | Faithful support-language translation of the stem or statement, preserving negation, modality, comparison, number, time, and scope. |
| `option_translation` | Translation of every option, including every wrong option. Preserve qualifiers such as *only*, *mainly*, *may*, *all*, and *except*. |
| `evidence_anchor` | Exact transcript line or timestamp, paragraph and sentence, blank, or language rule that supports the answer. Never invent an anchor. |
| `evidence_scope` | State whether the conclusion comes from the same sentence, adjacent context, paragraph synthesis, whole-text structure, or a grammar/usage rule. |
| `evidence_translation` | Translate the decisive evidence sentence or short evidence span and resolve pronouns or omitted information when needed. |
| `reasoning_steps` | Numbered path from task wording to evidence, inference, and conclusion. |
| `paraphrase_map` | Synonym, reformulation, logical relation, reference chain, or sound-to-text mapping between evidence and answer. |
| `key_language` | Vocabulary, collocation, grammar, pronunciation, or long-sentence point needed by the learner. |
| `distractor_analysis` | Explain every wrong option separately: contradicted, not mentioned, scope shifted, concept swapped, over-inferred, grammatically impossible, or contextually unsuitable. |
| `error_tag` | Best matching ExamLex error tag when the item diagnoses a learner mistake. |
| `learner_retry` | One actionable retry: relocate evidence, replay a chunk, reparse a sentence, translate an option, or answer a parallel micro-item. |

Do not write only “the text mentions B.” Quote a short decisive span, translate
it, name its scope, and show the inference. Use only short evidence excerpts. If
two options remain defensible after review, revise the item instead of forcing a
unique answer.

### Constructed-response items

Writing, translation, and other open responses use this shared contract:

| Field | Required content |
|---|---|
| `task_analysis` | Genre, audience, purpose, topic, required content, stance or communicative goal, constraints, and scoring focus. |
| `answer_plan` | Ordered paragraph or clause plan showing how the response will be built. |
| `reference_answer` | Original, exam-aligned model response; never present it as the only acceptable wording. |
| `reference_translation` | Accurate support-language translation aligned by sentence or paragraph with the model response. |
| `scoring_points` | Dimension-by-dimension rubric notes and an explicit statement that the score is an estimate, not official scoring. |
| `language_notes` | Useful structures, vocabulary, collocations, cohesion, tense, voice, or register choices. |
| `acceptable_alternatives` | Other accurate wording, structures, arguments, or organizations that should receive credit. |
| `common_errors` | Likely omissions, mistranslations, grammar failures, weak logic, or register problems and how to repair them. |
| `learner_revision` | A concrete rewrite, self-check, or comparison task. |

## Shared reading and listening package

For each reading passage or listening script in a complete detailed answer book:

1. provide the complete copyright-safe passage or script used by the simulation;
2. provide a readable support-language translation, paragraph by paragraph;
3. list focused `core_vocabulary` with contextual meanings, useful collocations,
   and difficult long-sentence structures;
4. number paragraphs, sentences, or transcript lines so every
   `evidence_anchor` can be checked;
5. translate every question and every option before the item explanation;
6. state `evidence_scope`, translate the evidence, show the paraphrase or
   inference chain, and eliminate every distractor.

For a copyrighted user-supplied paper, do not reproduce protected text beyond
what the user is authorized to use. Explain from the supplied material and use
short excerpts or location references where full reproduction is not permitted.

## Module playbooks

### Vocabulary `vocabulary`

- State the tested contextual meaning, part of speech, inflection, word family,
  and support-language meaning.
- Give pronunciation or sound recognition when relevant, high-value
  collocations, and one exam-context example.
- Explain why competing senses or near-synonyms do not fit this context.
- Map the mistake to recognition, spelling, audio recognition, or contextual-use
  error tags.

### Listening `listening`

- For an original simulation, provide the complete readable script and its
  paragraph-by-paragraph translation after the timed attempt. Number or
  timestamp all question evidence.
- Translate each question and all options before explaining the answer.
- Identify the question type, signal words, speaker attitude, turn, number,
  date, contrast, or causal relation that controls the answer.
- Quote and translate the decisive line, name whether the answer comes from one
  turn, adjacent turns, a whole conversation, or a full passage, then show the
  sound-to-text and paraphrase chain.
- Explain linking, weak forms, reductions, homophones, reference words, and
  number traps when relevant. Analyze every distractor against the recording,
  including “not mentioned” options.
- End with a precise replay range and a listening target, not a generic request
  to listen again.

### Reading `reading`

- Provide the complete passage translation and a focused core-vocabulary list.
- Identify the item type, translate the stem and all options, locate paragraph
  and sentence, translate the evidence, name the evidence scope, map the
  paraphrase, and parse any decisive long sentence.
- State explicitly whether the answer is directly restated, inferred from local
  context, synthesized from a paragraph, or derived from whole-text structure.
- Eliminate every wrong option separately and identify the exact failure:
  reversed logic, unsupported detail, wrong subject, changed time, narrowed or
  expanded scope, extreme wording, or plausible-but-unmentioned content.

### CET-4-specific playbook `CET4-specific-playbook`

A complete `CET4` detailed answer book must contain writing, listening, Reading
Section A/B/C, and Chinese-to-English translation packages whenever those
sections appear in the active exam profile. Apply every shared translation,
evidence, distractor, writing, and translation-construction field above. Calibrate
vocabulary, sentence complexity, inference depth, script speed, length, and
timing to the active `CET4` profile; simpler language never permits a shorter
explanation. End with the source/evidence-role statement and an explicit notice
that the simulation is not an official paper.

### CET-6-specific playbook `CET6-specific-playbook`

A complete `CET6` detailed answer book must contain writing, listening, Reading
Section A/B/C, and Chinese-to-English translation packages whenever those
sections appear in the active exam profile. Apply every shared translation,
evidence, distractor, writing, and translation-construction field above. Calibrate
for the active `CET6` profile's denser paraphrase, more abstract argument,
longer-sentence logic, speaker qualification, and inference burden without
inventing complexity unsupported by the paper. End with the source/evidence-role
statement and an explicit notice that the simulation is not an official paper.

### CET word-bank gap filling: Reading Section A

For `CET4` and `CET6` Section A, the detailed answer must include:

1. an option-bank table with letter, word, part of speech, inflected form,
   support-language meaning, and useful collocation; classify noun singular or
   plural, verb base or tense/participle, adjective, adverb, and other forms;
2. the completed passage, full passage translation, and core vocabulary;
3. for every blank, the local sentence translation, required grammatical form,
   `grammar_analysis`, `semantic_judgment`, collocation and discourse logic;
4. a comparison with other grammatically possible candidates and the reason
   each fails semantically or contextually;
5. the final answer and one reusable decision rule.

### CET paragraph matching: Reading Section B

For `CET4` and `CET6` Section B, include the full paragraph translation, then for
every statement provide its translation, keywords, matched paragraph and exact
sentence, evidence translation, paraphrase map, and reasoning. Explain why a
nearby or topically similar paragraph is only a partial match or changes the
claim. Do not rely on a shared keyword alone.

### CET multiple-choice reading: Reading Section C

For `CET4` and `CET6` Section C, include the full passage translation and core
vocabulary. For every item translate the stem and all four options; give the
paragraph/sentence location, evidence scope, evidence translation, reasoning,
paraphrase map, and separate elimination of A, B, C, and D as applicable.

### Postgraduate English-specific playbook `postgraduate-playbook-contract`

For `POSTGRADUATE_ENGLISH`:

- Use of English must give every option's meaning and relevant part of speech,
  the completed passage and full translation, core vocabulary, and per-blank
  grammar, collocation, semantic, reference, and discourse analysis.
- Reading Part A must give the full passage translation, core vocabulary,
  question and all-option translations, exact location, evidence scope and
  translation, long-sentence parsing, reasoning, and every distractor's failure.
- Reading Part B must translate the passage and every heading, sentence, or
  option in the bank; show structural signals, location, paraphrase mapping, and
  why nearby choices do not connect logically.
- Reading/Translation Part C must split each underlined sentence into clauses,
  resolve reference and logic, deliberate key words, build a literal skeleton,
  and produce a natural aligned translation.

### TEM-4-specific playbook `TEM4-specific-playbook`

For `TEM4`, apply the shared detailed contract and add the following section
requirements. Follow the active exam profile for timing, word count, and section
presence; do not invent a section that is absent from the target paper.

- `TEM4 dictation`: after the timed attempt, give the complete script and full
  translation, divide it into numbered sense groups, and mark punctuation,
  capitalization, function words, morphology, linking, weak forms, and spelling
  traps. For every missed span, distinguish hearing, segmentation, grammar,
  spelling, memory, and punctuation errors, then give an exact replay-and-write
  task.
- `TEM4 listening`: provide the full transcript and translation for each
  conversation or passage; translate every question and all options; identify
  speaker role, attitude, turn, transition, number, cause, and inference; give
  the exact evidence line and eliminate every distractor.
- `TEM4 language knowledge`: translate the stem and all options, name the tested
  grammar, usage, collocation, or lexical distinction, parse the trigger
  structure, explain each option, state any register or exception boundary, and
  give a minimal-pair transfer example.
- `TEM4 cloze`: provide an option table with meanings and parts of speech, the
  completed passage, full translation, core vocabulary, and per-blank grammar,
  collocation, semantic, reference, and discourse analysis. Compare every
  plausible candidate rather than explaining only the correct word.
- `TEM4 reading`: provide the full passage translation and core vocabulary;
  translate each question and all options; give location, evidence scope and
  translation, paraphrase or inference chain, decisive long-sentence parsing,
  and separate distractor rejection.
- `TEM4 writing`: apply the full writing contract, including genre and prompt
  analysis, at least three angles, paragraph plan, original model and aligned
  translation, common and advanced topic vocabulary, reusable slot-based
  templates, rubric estimate, and revision task.

### TEM-8-specific playbook `TEM8-specific-playbook`

For `TEM8`, apply the shared detailed contract and add the following section
requirements. Follow the active exam profile for timing, word count, and section
presence; if a profile marks a section as optional, explain it only when it is
actually included.

- `TEM8 mini-lecture`: provide the complete lecture script and translation,
  reconstruct its outline and signposting, translate every note-completion or
  question prompt, locate each answer line, explain the required grammatical
  form and paraphrase, and distinguish content-hearing errors from note-taking,
  spelling, and form errors.
- `TEM8 interview listening`: provide the complete interview transcript and
  translation; translate every question and all options; track speaker,
  attitude, agreement or qualification, cross-turn inference, and evidence
  scope; eliminate every distractor against the transcript.
- `TEM8 reading`: provide the full passage translation and core vocabulary;
  translate stems and all choices; identify paragraph/sentence location,
  evidence scope, evidence translation, author stance, discourse structure,
  long-sentence logic, and every distractor's failure. Constructed responses
  must also show content points and acceptable alternatives.
- `TEM8 language knowledge`, when present, follows the all-option translation,
  rule-trigger, structural parsing, option contrast, register-boundary, and
  transfer-example contract used for advanced language knowledge.
- `TEM8 bidirectional translation`: for both English-to-Chinese and
  Chinese-to-English tasks, give sentence-intent analysis, a clause map,
  reference and logic resolution, keyword deliberation, literal skeleton,
  restructuring choices, polished aligned translation, acceptable alternatives,
  scoring points, and common-error repairs. English-to-Chinese explanations must
  prioritize accurate long-sentence logic and natural Chinese; Chinese-to-English
  explanations must prioritize precise collocation, register, cohesion, and
  idiomatic restructuring.
- `TEM8 proofreading`: provide the corrected complete passage and full
  translation, then a line-by-line table containing the original span,
  correction, error category, governing rule, contextual reason, and acceptable
  alternative if any. Cover articles, number, agreement, tense, non-finite
  forms, reference, conjunctions, prepositions, collocation, redundancy, and
  discourse logic as applicable; never explain only the replacement word.
- `TEM8 writing`: apply the full writing contract at the target profile's
  advanced level. When the task is source-based, separate source summary from
  the learner's position, analyze the supplied viewpoints or data, develop at
  least three defensible angles, and provide an original model with aligned
  translation, advanced topic language, reusable slot-based templates, rubric
  estimate, and revision task. Do not invent facts or source claims.

### Cloze `cloze`

- Translate the completed passage and list core vocabulary.
- Translate all choices or give their contextual meanings before each item.
- Establish the required part of speech and grammar form around each blank.
- Check collocation, semantic fit, pronoun/reference relations, and discourse
  logic across sentences, and contrast all plausible alternatives.
- Summarize the passage's argument or narrative logic after item explanations.

### Language knowledge `language-knowledge`

- Translate the stem and all options when translation aids comprehension.
- Name the tested grammar, usage, collocation, or lexical distinction; point out
  the trigger and show the structure compactly.
- Explain exceptions or register limits and contrast each option.
- Give one minimal pair or corrected example for transfer.

### Translation `translation`

Every translation response must include:

1. `sentence_intent_analysis`: what each source sentence is saying and its
   relation to the preceding and following ideas;
2. `clause_map`: subject, predicate, objects or complements, modifiers, embedded
   clauses, logic, tense, voice, reference, and connector choices;
3. `keyword_deliberation`: two or more plausible renderings for important terms
   when useful, with differences in meaning, collocation, register, and why the
   selected wording is stronger;
4. `translation_build`: a literal clause skeleton, necessary restructuring, and
   the polished sentence;
5. an original `reference_answer` aligned sentence by sentence with the source,
   plus acceptable alternatives;
6. scoring points for information, grammar, word choice, cohesion, and sentence
   variety, followed by common mistranslations and a repair task.

Do not merely list a reference translation. Explain why it is accurate and
natural, and do not treat an `R`-level textbook or corpus as an official fixed
translation bank.

### Writing `writing`

Every writing response must include all of the following:

1. `task_analysis`: classify the genre (argumentative essay, report, email,
   letter, notice, proposal, chart/picture essay, or other), audience, purpose,
   topic, required points, stance, word range, and scoring priorities;
2. `idea_bank`: at least three plausible angles the learner could choose, with
   claim, reason, example or consequence, and suitability for the prompt;
3. `answer_plan`: paragraph functions, topic sentences, supporting logic,
   examples, transitions, and conclusion before the model;
4. an original `reference_answer` and a sentence-aligned or paragraph-aligned
   `reference_translation`;
5. `topic_vocabulary`: common and advanced words or phrases with meanings,
   collocations, register notes, and short usable examples;
6. `reusable_templates`: function-based sentence or paragraph frames with
   clearly labeled replaceable slots such as `[TOPIC]`, `[REASON]`, `[EXAMPLE]`,
   and `[ACTION]`; explain where each frame fits, its limitations, and show at
   least one substitution for a different topic;
7. paragraph annotations, cohesion and grammar notes, acceptable alternative
   arguments, rubric estimate, common failure modes, and a learner rewrite
   checklist.

Templates are tools for organizing thought, not universal sentences. Never
encourage memorized off-topic content, fabricated data, or a template whose
register conflicts with the task.

For `POSTGRADUATE_ENGLISH` Writing Part A, distinguish email, letter, notice,
memo, and other practical genres and specify salutations, purpose, required
points, tone, and closing. For Part B, first analyze the picture, chart, caption,
or proposition; separate description, interpretation, causes or implications,
and response. Both parts still require model translations, topic vocabulary,
and reusable slot-based templates.

### Proofreading `proofreading`

- Show the original form, corrected form, support-language sentence meaning,
  error span, and error category.
- Explain the governing grammar, collocation, reference, or discourse rule in
  the full sentence, not only the corrected word.
- State whether alternative corrections are valid, contrast misleading forms,
  and give one parallel example.
- Map the error to the relevant proofreading or language-accuracy tag.

### Dictation `dictation`

- Provide the correct script and translation only after the attempt, divided
  into meaningful chunks with punctuation and sentence boundaries.
- Explain linking, reduction, stress, homophones, function words, morphology,
  spelling cues, and sentence meaning for each missed chunk.
- Distinguish hearing failure from spelling, grammar, punctuation, or memory
  failure and assign the matching error tag.
- Give a replay-and-write sequence rather than asking the learner to memorize
  the full script.

## Full-paper packaging

For a complete mock paper, present material in this order:

1. compact answer key for checking;
2. writing task analysis, idea bank, plan, model, model translation, vocabulary,
   reusable templates, annotations, and rubric estimate;
3. complete listening scripts and translations, followed by item-by-item
   translated questions/options, evidence, reasoning, and distractors;
4. completed reading/cloze texts, full translations, core vocabulary, and
   section-specific item explanations;
5. translation sentence analysis, clause maps, keyword deliberation,
   construction steps, aligned reference translation, and scoring points;
6. proofreading, dictation, or language explanations required by the exam;
7. error-tag summary and a prioritized retry plan;
8. source and evidence-role statement making clear that the simulation is not an
   official paper.

Keep the answer key, explanation, transcript, passage, and source item numbering
aligned. Do not merge questions into one generic paragraph to shorten the paper.

## Quality gate

Before delivery, verify all of the following:

- every question number has exactly one matching `answer_key` entry and one
  explanation;
- every objective item includes `question_translation`, translation of every
  option, truthful `evidence_anchor`, `evidence_scope`, `evidence_translation`,
  reasoning, paraphrase mapping, and every-wrong-option analysis;
- every reading passage or listening script in a complete detailed answer book
  has a full support-language translation and core vocabulary where required;
- CET Section A contains option classification, completed text, full
  translation, grammar analysis, and semantic judgment for every blank;
- CET Section B contains item translation, exact paragraph/sentence location,
  paraphrase mapping, and nearby-paragraph rejection;
- CET Section C and Postgraduate Reading Part A contain stem/all-option
  translations, evidence location and scope, and separate distractor rejection;
- CET-4 and CET-6 complete answers each apply their named exam-specific playbook,
  active-profile calibration, full section packages, and non-official notice;
- TEM-4 answers contain the dedicated dictation, listening, language-knowledge,
  cloze, reading, and writing packages required by the active profile;
- TEM-8 answers contain the dedicated mini-lecture/interview, reading,
  bidirectional-translation, proofreading, and writing packages required by the
  active profile;
- every writing task contains genre/audience/purpose analysis, three or more
  usable angles, a plan, original model and model translation, common and
  advanced topic vocabulary, and reusable slot-based templates;
- every translation task contains sentence-intent analysis, a clause map,
  keyword deliberation, construction steps, an aligned reference answer,
  alternatives, and scoring points;
- answer, evidence, paraphrase, translation, and explanation agree;
- no quote, title, page, timestamp, rule, source level, or publication fact was
  invented;
- model answers and simulations are original or copyright-safe adaptations;
- scoring is labeled as training guidance, and the material is explicitly not
  an official paper or official fixed answer bank.

If any check fails, repair the explanation or the item before delivery. Missing
mandatory sections may not be excused by a learner's foundation level.
