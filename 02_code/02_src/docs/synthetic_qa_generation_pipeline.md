# EduGuard Synthetic QA Data Generation Pipeline

## 1. Purpose

This document explains how the synthetic data for EduGuard was created, organized, reviewed, and prepared for RAG retrieval, classifier training, and benchmark evaluation.

EduGuard uses synthetic data for two main parts:

1. RAG educational knowledge base
2. Guardrail classification dataset

All data was created for an educational support chatbot. No real student records, private university data, or real support conversations were used.

---

## 2. RAG Knowledge Base Generation

The RAG knowledge base was created synthetically to support SAFE academic and student-support questions.

First, common university support topics were researched using Google. The purpose of this research was to identify the main sections usually needed in an educational chatbot, such as academic policies, academic integrity, student services, exams, registration, graduation, and frequently asked educational questions.

After identifying the required sections, the content was written as a fictional educational knowledge base for EduGuard. The final content was not copied from any real university.

ChatGPT was used to help structure the sections and improve the wording. Claude Code was then used to generate and organize the RAG content step by step, section by section.

The final RAG knowledge base contains 200 synthetic chunks organized into six sections:

| Section                              | Number of Chunks |
| ------------------------------------ | ---------------: |
| Academic Policies                    |               50 |
| Academic Integrity & Responsible AI  |               50 |
| Student Academic Support Services    |               30 |
| Examination & Assessment Policies    |               30 |
| Registration & Graduation Procedures |               20 |
| Educational FAQ Dataset              |               20 |
| Total                                |              200 |

The RAG deliverable is:

`educational_knowledge_base.md`

This file is used by FAISS retrieval to provide trusted context only when the student request is classified as SAFE and requires academic, policy, or student-support information.

---

## 3. Guardrail Classification Dataset Generation

The guardrail classification dataset was also created synthetically.

First, educational chatbot risks and safety categories were researched using Google. This helped define realistic student scenarios such as safe academic questions, academic dishonesty attempts, sensitive wellbeing concerns, out-of-scope requests, and prompt injection attempts.

Hugging Face datasets were also reviewed to understand common safety classification structures, refusal patterns, prompt injection examples, and dataset formatting.

Google and Hugging Face were used for research and structure only. The final EduGuard dataset was not copied from these sources.

After the requirements were defined, ChatGPT was used to design and improve the data generation prompts. The prompts included:

* Safety labels
* Expected actions
* Severity levels
* Scenario types
* Realistic student message styles
* Boundary cases
* Prompt injection examples

Then, Claude Code was used to generate the dataset step by step, label by label and section by section.

---

## 4. Dataset Labels

The guardrail dataset uses five safety labels:

| Label            | Meaning                                                    | Expected Behavior           |
| ---------------- | ---------------------------------------------------------- | --------------------------- |
| SAFE             | Allowed academic or student-support request                | Answer using RAG and/or GPT |
| UNSAFE           | Cheating, plagiarism, harmful, or disallowed request       | Refuse and redirect         |
| SENSITIVE        | Student safety, distress, crisis, or policy-sensitive case | Support and escalate        |
| OUT_OF_SCOPE     | Not related to education or student support                | Politely redirect           |
| PROMPT_INJECTION | Attempts to bypass rules or reveal hidden instructions     | Block and alert admin       |

These are the safety classifier labels. They are different from the RAG knowledge base sections.

---

## 5. Main Guardrail Dataset

The final main guardrail dataset contains 800 synthetic records.

The dataset is balanced across the five safety labels:

| Label            | Samples |
| ---------------- | ------: |
| SAFE             |     160 |
| UNSAFE           |     160 |
| SENSITIVE        |     160 |
| OUT_OF_SCOPE     |     160 |
| PROMPT_INJECTION |     160 |
| Total            |     800 |

Each record includes fields such as:

* `id`
* `text`
* `label`
* `reason`
* `scenario_type`
* `difficulty`
* `expected_action`
* `severity`
* `human_review`

---

## 6. Train, Validation, and Test Split

The 800-sample dataset was split into three files:

| Split      | Samples | Purpose                                           |
| ---------- | ------: | ------------------------------------------------- |
| Train      |     560 | Used to train the DistilBERT safety classifier    |
| Validation |     120 | Used to monitor model performance during training |
| Test       |     120 | Used for final model testing                      |

The split keeps the five labels balanced.

---

## 7. Benchmark Dataset

A separate benchmark dataset was created to test boundary and safety-critical behavior.

The benchmark contains 100 synthetic samples:

| Label            | Samples |
| ---------------- | ------: |
| SAFE             |      20 |
| UNSAFE           |      20 |
| SENSITIVE        |      20 |
| OUT_OF_SCOPE     |      20 |
| PROMPT_INJECTION |      20 |
| Total            |     100 |

The benchmark tests:

* Safe in-domain questions
* Unsafe request refusal
* Sensitive case escalation
* Out-of-scope redirection
* Prompt injection blocking
* Ambiguous and boundary cases

---

## 8. Data Review and Cleaning

After generation, the dataset was reviewed and cleaned before training.

The review process included:

* Checking label balance
* Removing exact duplicates
* Reducing near-duplicate wording
* Reviewing label consistency
* Reviewing sensitive and critical cases
* Reviewing prompt injection examples
* Keeping all labels in English
* Keeping all text samples in English
* Separating train, validation, test, and benchmark files

This process helped create a clean and controlled synthetic dataset for the EduGuard DistilBERT safety classifier.

---

## 9. Dataset Files

The dataset files are stored in the `data/` folder.

Main dataset files:

* `eduguard_guardrail_clean_800.json`
* `eduguard_guardrail_clean_800.jsonl`
* `eduguard_guardrail_clean_800.xlsx`
* `eduguard_guardrail_clean_800_review.xlsx`

Training and evaluation split files:

* `train.jsonl`
* `validation.jsonl`
* `test.jsonl`

Benchmark files:

* `benchmark_boundary_100.jsonl`
* `benchmark_boundary_100.xlsx`

---

## 10. Use in EduGuard

The synthetic data is used for:

* Building the FAISS RAG knowledge base
* Training the DistilBERT guardrail classifier
* Testing the EduGuard safety pipeline
* Evaluating label prediction
* Checking refusal behavior
* Checking escalation behavior
* Testing prompt injection detection
* Supporting benchmark evaluation

---

## 11. Important Distinction

EduGuard has two different data parts:

| Part                        |       Count | Purpose                              |
| --------------------------- | ----------: | ------------------------------------ |
| Safety classifier labels    |    5 labels | Classify student requests            |
| RAG knowledge base sections |  6 sections | Retrieve trusted educational context |
| RAG chunks                  |  200 chunks | Support SAFE academic answers        |
| Guardrail dataset           | 800 records | Train the DistilBERT classifier      |
| Benchmark dataset           | 100 records | Evaluate safety behavior             |

The RAG knowledge base is not a classifier. It is used only after a request is classified as SAFE.

---

## 12. Limitations

The dataset and RAG knowledge base are synthetic and were created for an AI Engineering bootcamp prototype. They do not represent real student data, real university records, or official institutional policies.

Future improvements may include larger datasets, more human annotation, multilingual examples, stronger red-team testing, better benchmark scoring, and model calibration.

