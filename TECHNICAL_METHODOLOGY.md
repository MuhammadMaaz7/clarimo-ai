# Clarimo AI Launch Planning: Technical Methodology

This document outlines the architectural and mathematical logic used by the Clarimo AI Launch Planning Assistant. This can be used to explain the backend logic to evaluation panels or stakeholders.

---

## 1. Core Architecture: The Hybrid Expert System
Unlike simple "Prompt Engineering" which can produce hallucinatory or unrealistic plans, Module 5 uses a **Hybrid Expert System** approach. 

- **Heuristic Engine (Backend Core):** Handles deterministic calculations (Budget, Timing, Scoring) using industry-standard startup benchmarks.
- **Large Language Model (Refinement Layer):** Synthesizes the numeric outputs into a cohesive, professional narrative while identifying nuanced risks specific to the startup's niche.

## 2. Scientific Principles Implemented

### A. Adaptive Launch Readiness Score
The readiness score is not just a random number; it is a weighted sum of three primary vectors:
1. **Product Maturity Gate (30%):** A hard floor based on the `ProductStage` (Idea -> Live).
2. **Validation Confidence (40%):** Directly pulls the `overall_score` from Module 2. High validation offsets low technical maturity.
3. **Competitive Pressure (30%):** Uses results from Module 3 to calculate market saturation. A crowded market requires a higher readiness score before a "Recommend Launch" signal is triggered.

### B. Timeline Generation & Management Laws
We apply two fundamental software engineering laws to ensure timelines are realistic, not optimistic:
- **Brooks's Law (Communication Overhead):** As team size increases, efficiency at the early stage slightly decreases due to communication tax. The engine adds pads for larger teams to account for coordination.
- **Hofstadter's Law (The Buffer Principle):** The system automatically applies a 15-20% "Realism Buffer" to all developer-estimated timelines.

### C. Domain-Specific Budgeting
Instead of flat percentages, we use a **Contextual Modifier Matrix**.
- **AI Startups:** Budget is shifted 20% toward "Tech & Infrastructure" to account for GPU/Token costs.
- **Fintech/Health:** Budget is shifted 50-80% toward "Legal & Compliance" to account for regulatory audits.
- **E-commerce:** Budget is shifted 30% toward "Go-to-Market" and "Operations" for logistics and high CAC (Customer Acquisition Cost).

## 3. Data-Driven Checklist Engine
The checklist is generated via **Baseline + Signal Injection**.
1. **Baseline:** Pulls critical "Must-Do" tasks from our validated Knowledge Base (containing 50+ standard startup milestones).
2. **Signal Injection:**
    - If **Competitor Count > 10**: Injects "Differentiation Mapping" tasks.
    - If **Validation Score < 3.5**: Injects "Hypothesis Re-verification" tasks.
    - If **Domain = AI**: Injects "Cost Monitoring & Ethics Review" tasks.

## 4. Why Heuristics Over Pure ML?
While training a model on "successful startup plans" is a theoretical goal, successful startup data is proprietary and noisy. A **Heuristic Expert System** provides:
- **Explainability:** We can tell exactly why a certain budget was recommended.
- **Reliability:** Prevents the system from suggesting a $1M marketing budget for a solo founder with $500.
- **Actionability:** Tasks are bound to real-world stage gates.
