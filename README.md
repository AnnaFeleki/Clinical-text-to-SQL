# Clinical Text to SQL Agent

An LLM agent that answers plain English questions from a clinical style SQL database. It writes its own SQL, executes it, fixes its own errors, and explains the results in plain language. Built with LangChain and a synthetic SQLite database.

![Python](https://img.shields.io/badge/python-3.10+-blue) ![LangChain](https://img.shields.io/badge/LangChain-0.3-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Why this matters

Most teams have valuable data locked in SQL databases that only analysts can query. This agent lets anyone ask questions like "How many female patients over 60 had an abnormal cholesterol result this year?" and get a correct, explained answer in seconds.

## Features

- Natural language to SQL over a realistic clinical schema (patients, visits, diagnoses, lab results)
- Self correction loop: if a query fails, the agent reads the error and rewrites the SQL (up to 3 attempts)
- Read only guard: only SELECT statements are ever executed
- Plain language summary of every result set
- 100 percent synthetic data, generated locally, no privacy concerns
- Streamlit chat interface plus a CLI

## Quickstart

```bash
git clone https://github.com/AnnaFeleki/clinical-text-to-sql-agent.git
cd clinical-text-to-sql-agent
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY

# 1. Create the synthetic clinical database
python setup_db.py

# 2. Ask from the command line
python agent.py "How many patients are in each department?"

# 3. Or launch the chat app
streamlit run app.py
```

## Example questions

- Which 5 patients had the most visits?
- What is the average glucose value by sex?
- List patients diagnosed with hypertension in 2025
- How many lab results were outside the reference range?

## Schema

```
patients     (patient_id, sex, birth_year)
visits       (visit_id, patient_id, visit_date, department)
diagnoses    (diagnosis_id, visit_id, icd10_code, description)
lab_results  (lab_id, visit_id, test_name, value, unit, ref_low, ref_high)
```

## Safety design

- SQL is validated before execution: SELECT only, single statement, no write keywords
- Query results are capped at 50 rows
- All data is synthetic; the generator is seeded and reproducible

## Disclaimer

Synthetic demo data only. Not for clinical use.

## License

MIT. Built by [Anna Feleki](https://github.com/AnnaFeleki).
