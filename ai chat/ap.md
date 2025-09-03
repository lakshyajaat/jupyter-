<|channel|>analysis<|message|>Need to respond with plan. Probably outline architecture.<|end|>

<|start|>assistant<|channel|>final<|message|>Below is a high‑level design document you can hand over to a development team (or use as a starting point for an RFP).  
It covers the key functional requirements, technical stack, data sources, compliance considerations, and a quick roadmap to reach the 80 % accuracy / 20 % awareness targets.

---

## 1. Product Overview

| Feature | Purpose |
|---------|---------|
| **Multilingual conversational AI** | Speak in local languages (Hindi, Bengali, Tamil, Telugu, etc.) + English. |
| **Health education** | Explain preventive measures, symptoms, and vaccination schedules for common diseases (malaria, dengue, COVID‑19, measles, polio). |
| **Real‑time outbreak alerts** | Push SMS/WhatsApp messages to subscribed users when a new cluster is reported in their district. |
| **Government data integration** | Pull up‑to‑date vaccination calendars, disease surveillance feeds (e.g., IDSP, National Immunisation Programme), and public health advisories. |
| **Low‑bandwidth & no‑internet fallback** | SMS fallback for 2G/3G areas; WhatsApp Business API for internet‑enabled users. |

---

## 2. Architecture Diagram (textual)

```
┌───────────────────────┐
│  User Interface Layer │  (WhatsApp, SMS via Twilio / Vonage)
├────────────┬───────────┤
│            │           │
│   WhatsApp Business API   |
│          & SMS Gateway     |
└───────▲────┴───────┘
        │
        ▼
┌───────────────────────┐
│  Conversational Engine│ (Dialogflow CX / Rasa X + custom NLU)
├────────────┬───────────┤
│            │           │
│   Multi‑lang NLU | Core Bot Logic
│ (T5, mBART or GPT‑4 fine‑tuned on health data)
└───────▲────┴───────┘
        │
        ▼
┌───────────────────────┐
│  Knowledge Base &      │
│  Retrieval Module      │
├─────┬────────┬─────────┤
│     │        │         │
│   FAQ DB |  Health Docs |  External APIs
│   (SQL/NoSQL) | (PDF/JSON) | (Govt. feeds)
└──────▲──────┴───────┘
        │
        ▼
┌───────────────────────┐
│  Analytics & Feedback  │
│  (User intent, success,
│   churn metrics)       │
└───────────────────────┘
```

---

## 3. Core Components

| Component | Technology Choices | Why |
|-----------|--------------------|-----|
| **NLU / Dialogue Manager** | *Dialogflow CX* with custom intents + *Rasa X* for open‑source flexibility; fine‑tune a multilingual transformer (mBART, mT5) on curated health corpora. | Proven low‑resource handling of Hindi/Telugu etc.; easy integration with WhatsApp Business API. |
| **Knowledge Base** | PostgreSQL + ElasticSearch index; JSON documents for disease fact sheets; vector search for semantic retrieval (FAISS). | Allows quick lookup and ranking of best answers. |
| **Government Data Integration** | REST/JSON feeds from *National Health Mission*, *IDSP* APIs, CDC India dashboards; periodic ETL jobs via Airflow. | Keeps vaccination schedules & outbreak alerts current. |
| **SMS / WhatsApp Gateway** | Twilio Programmable Messaging (WhatsApp Business) + Vonage SMS API. | Reliable global coverage, audit logs, and compliance with local telecom regs. |
| **Real‑time Alerts Engine** | Kafka streaming of outbreak reports → Lambda functions → push to users based on geolocation tags. | Low latency, scalable notification system. |
| **Analytics & Continuous Learning** | Google Analytics for web metrics + custom dashboards (Metabase). Use reinforcement learning loop: user replies “That was helpful” vs “I don’t understand” feed back into training set. | Measures 80 % accuracy goal and tracks awareness lift. |

---

## 4. Data Sources

| Source | Content | Frequency |
|--------|---------|-----------|
| **National Immunisation Programme (NIP)** | Vaccination schedules per age group, district | Weekly |
| **Integrated Disease Surveillance Project (IDSP)** | Daily outbreak reports by disease & region | Daily |
| **Health Ministry Press Releases** | Public health advisories | As issued |
| **Local Health Department APIs** | District‑level health worker rosters, helpline numbers | Monthly |
| **Community Feedback Corpus** | User queries from pilot chats | Continuous |

All data must be stored in a GDPR/India PDP‑compliant database with encryption at rest and in transit.

---

## 5. Compliance & Security

1. **Data Protection** – Encrypt PII (phone numbers, location) using AES‑256; store hashed identifiers for analytics.
2. **Consent Management** – On first contact, ask for opt‑in to receive health messages; provide a simple “STOP” keyword for SMS/WhatsApp.
3. **Regulatory** – Align with India’s *Telecom Commercial Communications Policy* (for WhatsApp), *Personal Data Protection Bill*, and WHO guidelines on digital health tools.
4. **Audit Trail** – Log every message sent/received with timestamps; enable export for regulatory audits.

---

## 6. Development Roadmap

| Phase | Duration | Milestones |
|-------|----------|------------|
| **1. Discovery & Prototyping** | 4 weeks | • Define core intents (symptom check, vaccination schedule, outbreak alert). <br>• Build minimal NLU model with 100+ sample utterances per language. <br>• Prototype WhatsApp chatbot flow in Dialogflow CX. |
| **2. Knowledge Base & Data Pipelines** | 6 weeks | • Scrape/parse govt. health docs into JSON. <br>• Set up ETL jobs (Airflow) to ingest daily outbreak feeds. <br>• Build vector search index for semantic QA. |
| **3. Multilingual NLU Training** | 8 weeks | • Curate 10k+ labeled examples per language. <br>• Fine‑tune mBART / GPT‑4 on health domain. <br>• Validate intent classification F1 > 0.90 across languages. |
| **4. Alert Engine & Messaging Layer** | 6 weeks | • Implement Kafka streams for outbreak alerts. <br>• Integrate Twilio/WhatsApp API; test SMS fallback. <br>• Roll out opt‑in subscription flow. |
| **5. Pilot Deployment** | 12 weeks | • Deploy to 3 districts (1 rural, 2 semi‑urban). <br>• Collect usage metrics & user feedback. <br>• Iterate NLU model and FAQ content based on error analysis. |
| **6. Scale & Optimization** | Ongoing | • Auto‑scale Lambda functions for high traffic days. <br>• Implement active learning loop: flagged ambiguous answers are sent to annotators. <br>• Measure accuracy vs. 80 % target; adjust training data accordingly. |

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| **Answer Accuracy** | ≥ 80 % correct responses (intent + factual correctness) |
| **User Engagement** | Avg. conversation length > 3 turns; < 10 % dropout before resolution |
| **Awareness Increase** | 20 % rise in vaccination registration & preventive behavior surveys (pre/post pilot) |
| **Alert Effectiveness** | 90 % of users receive outbreak alerts within 2 hours of data ingestion |
| **Retention** | ≥ 70 % of users remain active after 3 months |

---

## 8. Suggested Team Composition

| Role | Responsibility |
|------|----------------|
| Product Manager | Define scope, stakeholder liaison |
| Data Engineer | ETL pipelines, database schema |
| ML Engineer (NLU) | Model training, evaluation |
| Backend Engineer | API gateway, webhook handlers |
| Frontend / ChatOps Dev | WhatsApp/ SMS integration, UI dashboards |
| QA/Test Lead | Functional + regression testing |
| Compliance Officer | GDPR/PDP compliance, data governance |

---

## 9. Quick Next Steps

1. **Kick‑off Workshop** – Align on target languages, disease list, and data sources.
2. **Data Collection** – Secure access to NIP & IDSP APIs; start scraping documents.
3. **Prototype Build** – Set up Dialogflow CX with a few intents; test WhatsApp sandbox.
4. **User Study Design** – Draft survey instruments for pre‑/post awareness measurement.

---

### Final Note

Achieving 80 % accuracy hinges on *high‑quality, domain‑specific training data* and *continuous feedback loops*. The proposed architecture gives you both the flexibility to iterate quickly (via Rasa or Dialogflow) and the scalability to reach millions of rural users through low‑bandwidth channels. Good luck with the rollout!