# Managed ML Platforms vs Self-Hosted EKS

Comparing **SageMaker**, **Databricks**, **Vertex AI**, and a **self-hosted EKS + CNCF/ML OSS** stack against 7 use cases.  
Sized for ~2 FTE platform owners + 5–7 ML engineers, mid scale, modest 12-month growth.

> **The real comparison is lock-in vs ops cost.** All four options can technically handle every use case. The decision isn't "what's possible" — it's how much exit cost vs platform-team headcount you'd rather pay.

---

## Exit Cost — Estimated Months to Migrate Out

| Platform | Estimate |
|---|---|
| SageMaker | 4–6 months |
| Databricks | 4–6 months |
| Vertex AI | 5–8 months |
| EKS / OSS | 1–2 months |

---

## Capability Matrix

**Legend:** `Full` = managed primitive · `DIY` = capable, you assemble & operate · `Partial` = works with friction · `Gap` = not native to platform

| Use Case | SageMaker | Databricks | Vertex AI | EKS / OSS |
|---|:---:|:---:|:---:|:---:|
| Ephemeral dev / EDA (Okteto-like) | Partial | Partial | Partial | DIY |
| Snowflake → S3 dataset exports | Partial | Full | Partial | DIY |
| Automated evals against endpoints | Full | Full | Full | DIY |
| Model serving / inference | Full | Full | Full | DIY |
| Hosted MLflow / Langfuse | Partial | Partial | Gap | DIY |
| Migrate enrichment task off core-api | Full | Full | Full | DIY |
| Feature store | Full | Full | Full | DIY |

### Notes per use case

**Ephemeral dev / EDA (Okteto-like)**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Partial | Studio Spaces & Code Editor — cloud IDE, not a local→cloud sync loop. |
| Databricks | Partial | Notebooks + Databricks Connect / Asset Bundles. Better than SM, still notebook-centric. |
| Vertex AI | Partial | Workbench instances. Same shape as SM/DBX, no sync-style dev loop. |
| EKS / OSS | DIY | Okteto / Coder / DevPod / JupyterHub on K8s — this is exactly what they're built for. |

**Snowflake → S3 dataset exports**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Partial | Processing Jobs run it; orchestration lives in Step Functions / Airflow. |
| Databricks | Full | Workflows + Snowflake connector is a tight fit; this is bread-and-butter. |
| Vertex AI | Partial | Possible via Pipelines / Workflows; cross-cloud egress hurts. |
| EKS / OSS | DIY | Argo Workflows / Airflow + Snowflake operator. Standard pattern. |

**Automated evals against endpoints**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Full | Pipelines + Clarify + FMEval. Native. |
| Databricks | Full | MLflow Evaluate + Workflows. Native. |
| Vertex AI | Full | Vertex AI Evaluation Service. Native, LLM-leaning. |
| EKS / OSS | DIY | Argo Workflows + KServe + your eval framework of choice. |

**Model serving / inference**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Full | Real-time / Async / Serverless / Batch. Their flagship. |
| Databricks | Full | Mosaic Model Serving — real-time + batch. |
| Vertex AI | Full | Online / Batch prediction endpoints. |
| EKS / OSS | DIY | KServe / Seldon / BentoML / Triton / Ray Serve. Mature but you operate it. |

**Hosted MLflow / Langfuse**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Partial | Managed MLflow is GA. Langfuse → ECS/EKS sidecar. |
| Databricks | Partial | MLflow native (they ship it). Langfuse → external. |
| Vertex AI | Gap | No managed MLflow. Both → external hosting. |
| EKS / OSS | DIY | `helm install langfuse` / MLflow chart. Trivial. |

**Migrate enrichment task off core-api**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Full | Async Inference is built for queue-driven enrichment. |
| Databricks | Full | Jobs / Model Serving handle this cleanly. |
| Vertex AI | Full | Custom Jobs / Online Prediction. |
| EKS / OSS | DIY | It's just a deployment + queue (SQS/Kafka). Simplest integration with the rest of your stack. |

**Feature store**
| Platform | Fit | Note |
|---|:---:|---|
| SageMaker | Full | SageMaker Feature Store, online + offline. |
| Databricks | Full | Feature Engineering in Unity Catalog. |
| Vertex AI | Full | Vertex AI Feature Store (BigQuery-backed). |
| EKS / OSS | DIY | Feast on K8s. OSS, but you operate the online store (Redis/DynamoDB). |

---

## The Three Axes That Actually Decide This

### 1. Lock-in Surface

| Platform | Proprietary (cost to leave) | Portable (free to leave) |
|---|---|---|
| SageMaker *(4–6mo exit)* | Feature Store API · Pipelines DSL · Endpoint container contract · Clarify / Model Monitor configs | Managed MLflow (it's MLflow) · S3 data · Training container images |
| Databricks *(4–6mo exit)* | Unity Catalog · Workflows / Jobs · Mosaic Model Serving endpoints · Notebook %magic commands | Delta tables (OSS) · MLflow tracking · PySpark code |
| Vertex AI *(5–8mo exit)* | Feature Store · Endpoints · Vertex Pipelines · Cross-cloud data egress tax | KFP pipelines (with rewrite) · GCS data (with egress cost) |
| EKS / OSS *(1–2mo exit)* | Karpenter / AWS LBC / EBS CSI configs · IAM-for-ServiceAccounts wiring | All workloads (Helm/manifests) · All OSS components · Container images |

### 2. Operational Burden

| Platform | Steady-state ops | What that covers |
|---|:---:|---|
| SageMaker | ~0.25 FTE | IAM, networking glue, occasional support tickets. |
| Databricks | ~0.5 FTE | Workspace admin, UC governance, cost guardrails. |
| Vertex AI | ~0.25 FTE | Project/IAM, cross-cloud data plumbing. |
| EKS / OSS | 1.5–2 FTE | Cluster lifecycle, upgrades, CNI/CSI, observability, security, cost. Sized for your 2 FTE — plausible but tight. |

### 3. Dev UX — the Okteto-style loop the team actually wants

| Platform | Quality | Reality |
|---|:---:|---|
| SageMaker | Partial | Studio is a UI. The team explicitly wants to skip it. |
| Databricks | Partial | Best of the managed three; still notebook-shaped. |
| Vertex AI | Partial | Workbench instances. Notebook-shaped. |
| EKS / OSS | **Full** | Okteto / Coder / DevPod give you "edit on laptop, run in cloud" verbatim. This is the only way to actually deliver the stated dev UX. |

---

## Per-Platform Summary

**SageMaker** — exit: 4–6mo  
Strongest AWS-native fit. 4 use cases full, 3 partial. Heaviest lock-in surface is Feature Store + Pipelines + endpoint contract — that's the migration cost if you ever leave.

**Databricks** — exit: 4–6mo  
Best overall managed-ML breadth. Lock-in concentrates in UC + Workflows + Mosaic Serving; data layer (Delta) is portable. Cross-cloud-friendly but a separate billing/identity surface from AWS.

**Vertex AI** — exit: 5–8mo  
Capability parity with SM/DBX, but cross-cloud data gravity is real. No managed MLflow. Probably the worst fit purely because your data is in AWS.

**EKS / OSS** — exit: 1–2mo  
Capability-complete via OSS (KServe, Feast, MLflow, Argo, Okteto, Langfuse). Lowest lock-in and only platform that delivers the Okteto-style dev loop. Cost is real platform-engineering work — 1.5–2 FTE for your scale.

---

## Recommendation

> Sized for: 2 FTE platform + 4–5 partial · 5–7 ML engineers · ECS shop · mid scale · lock-in-averse.

### The honest hybrid

Stand up **EKS as the platform spine** — it's the only way to deliver the Okteto-style dev UX, host Langfuse cleanly, and keep lock-in low. Use **SageMaker selectively** for the bits with the worst ops gap on K8s relative to effort: real-time autoscaling endpoints and Feature Store while you're small. Migrate inward to KServe + Feast as the team and traffic grow.

### Why not pure managed

The team's stated goals — Okteto-style dev UX, Langfuse hosting, avoiding multi-month exit cost — are *structurally* unsolved by SageMaker, Databricks, or Vertex. You'd buy ops relief and re-buy the dev-UX problem and the lock-in problem.

### Why not pure EKS today

2 FTE running KServe + Feast + Argo + JupyterHub + Langfuse + MLflow + ingress + observability + cost is doable but tight, and the bus factor is brutal. Buying the parts that are hardest to operate (online feature store, autoscaling endpoints) for the first 12 months is the cheap insurance.

### What to decide first

1. Are you OK with SageMaker as a temporary inference + FS host, knowing the 4–6mo exit if you ever leave?
2. Is the 1.5–2 FTE ongoing cost of the EKS platform funded?

Both yes → hybrid. Only (1) → SageMaker-led with EKS for dev/services. Only (2) → pure EKS, accept slower time-to-first-model.

> **The trap to avoid:** Don't pick the managed platform that scores best on the capability matrix and discover 18 months in that the dev UX never landed and the migration out is a year of work. The capability matrix is the easy part — lock-in and dev UX are why this decision is hard.
