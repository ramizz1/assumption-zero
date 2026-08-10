# Startup Idea Validation Guide

Assumption Zero is most useful when it receives a concrete business hypothesis. It can work from a short prompt, but a detailed brief produces better searches, more relevant regional evidence, and a more specific founder plan.

No validator can promise 100% accuracy. Treat the report as decision support: inspect important citations and confirm demand, price, legal requirements, and buying behavior with real local customers.

## A strong brief

Describe these points:

1. **Product and solution**: what is the smallest useful outcome you will deliver?
2. **Customer and buyer**: who uses it, who pays, and which narrow segment comes first?
3. **Problem**: when does it occur, how often, and what does it cost today?
4. **Region**: country, city, or sub-market; also add the customer language and local currency.
5. **Business model and price**: subscription, transaction fee, service, license, or another model.
6. **Current alternatives**: named products, manual workflows, agencies, spreadsheets, or doing nothing.
7. **Founder reality**: skills, team, budget, runway, launch deadline, and first revenue goal.
8. **Distribution**: communities, partnerships, outbound lists, marketplaces, or audiences you can already reach.
9. **Constraints**: privacy, licensing, tax, safety, logistics, procurement, or operational requirements.
10. **Dangerous assumptions**: the one or two beliefs that would kill the business if false.

Example:

```text
Name: ClinicFlow
Description: Appointment and follow-up software for independent dental clinics.
Problem: Clinics lose repeat patients because booking and follow-up are manual.
Target customer: Independent dental clinics with 2-10 dentists
Geography: Azerbaijan
Market language: Azerbaijani and Russian
Currency: AZN
Business model: Monthly subscription
Price: 99 AZN per clinic per month
Competitors: Local clinic software, WhatsApp, spreadsheets
Founder skills: Full-stack development and two years working with clinics
Budget: 5,000 AZN and four months of runway
Channels: Dental association, direct outreach, equipment distributors
Goal: Five paid pilots in 30 days
Constraints: Patient data privacy and local invoicing requirements
Assumptions: Clinics will switch from WhatsApp and pay for automated follow-up
```

## Choose research depth

| Mode | Coverage | Perspectives | Use it when |
|---|---|---:|---|
| Standard | 1 query per evidence category | 3 | You need a fast first screen |
| Deep | 2 queries per category | 4 | You want the default regional validation |
| Exhaustive | Up to 4 queries per category | 5 | You want maximum research and customer scrutiny |

Exhaustive mode consumes more search-provider and AI capacity. More calls improve coverage, not certainty.

## Regional validation rules

The regional score includes only evidence tied to the requested geography. Global industry growth does not prove local demand. Review four separate groups in the report:

- demand and customer-pain signals;
- local prices and willingness-to-pay evidence;
- regulation, tax, privacy, and operating constraints;
- local distribution partners, directories, communities, and benchmarks.

If coverage is weak, use the listed research gaps as a queue. Interview buyers from at least two local sub-markets, ask about their last real experience, and request a commitment such as data access, a pilot, a deposit, or payment.

## Run it

```bash
# View this guide in the terminal
azero guide

# Guided detailed brief
azero analyze --depth deep

# Maximum research from a natural-language brief
azero prompt "your detailed idea" --depth exhaustive

# Structured input
azero analyze --file examples/sample-idea.json --depth deep

# Review and export results
azero list
azero show 1
azero export 1 --format markdown --output report.md
```

The CLI and web app use the same engine, research-depth controls, regional analysis, saved history, and export model.

## Make a decision

Do not build a large MVP because a score looks attractive. First define pass/fail thresholds, run the cheapest high-information experiments, and look for behavioral evidence. Compliments are weak; repeated usage, referrals, data access, pilot agreements, deposits, and payments are stronger.
