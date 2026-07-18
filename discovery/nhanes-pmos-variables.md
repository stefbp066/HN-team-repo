# NHANES 2021-2023 Variables for PMOS (PCOS) Data Synthesis

This document outlines the key files, variables, and methodologies for identifying and synthesizing **Polyendocrine Metabolic Ovarian Syndrome (PMOS)** — formerly known as **Polycystic Ovary Syndrome (PCOS)** — using the National Health and Nutrition Examination Survey (NHANES) 2021-2023 cycle.

---

## 1. The 2026 PMOS Nomenclature Update
In **May 2026**, a 14-year global collaborative effort involving over 50 patient and professional organizations (including the [Endocrine Society](https://www.endocrine.org/) and the [American Medical Association (AMA)](https://www.ama-assn.org/)) officially renamed **Polycystic Ovary Syndrome (PCOS)** to **Polyendocrine Metabolic Ovarian Syndrome (PMOS)**. 
- **Rationale:** The original name "PCOS" focused too narrowly on ovarian "cysts" (which are actually immature follicles). The new name "PMOS" emphasizes that the condition is fundamentally a systemic, lifelong endocrine and metabolic disorder.

---

## 2. Methodology for Phenotyping PMOS in NHANES
Because NHANES does not contain a direct variable for a clinical diagnosis of PMOS, researchers construct PMOS cohorts by combining laboratory biomarkers of hyperandrogenism with self-reported reproductive symptoms from questionnaires.

### A. Laboratory Biomarkers: Sex Steroid Hormone Panel (`TST_L`)
The **Sex Steroid Hormone Panel — Serum (`TST_L`)** was published in October 2024 for the August 2021–August 2023 cycle. High-precision isotope dilution liquid chromatography-tandem mass spectrometry (ID-LC-MS/MS) is used to measure steroids.

- **Data File Page:** [NHANES 2021-2023 Sex Steroid Hormone Panel (TST_L)](https://wwwn.cdc.gov/Nchs/Nhanes/2021-2023/TST_L.htm)
- **Primary Data Link:** [NHANES 2021-2023 Laboratory Data Page](https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Laboratory&Cycle=2021-2023)

#### Key Laboratory Variables:
| Variable | Description | Units | Clinical Relevance to PMOS |
|---|---|---|---|
| **`LBXTST`** | Total Testosterone | ng/dL | Elevated levels indicate clinical/biochemical hyperandrogenism (core PMOS feature). |
| **`LBXSHBG`** | Sex Hormone-Binding Globulin | nmol/L | Decreased levels are strongly associated with PMOS, insulin resistance, and obesity. |
| **`LBXAMH`** | Anti-Müllerian Hormone (AMH) | ng/mL | Elevated levels indicate ovarian follicle excess/polycystic ovarian morphology. |
| **`LBXLUH`** | Luteinizing Hormone (LH) | mIU/mL | Evaluates gonadotropin ratios. High LH/FSH ratio is common in PMOS. |
| **`LBXFSH`** | Follicle-Stimulating Hormone (FSH) | mIU/mL | Used alongside LH to calculate the gonadotropin ratio. |
| **`LBXEST`** | Estradiol | pg/mL | Evaluates estrogenic status/balance. |
| **`LBXPG4`** | Progesterone | ng/dL | Identifies progesterone deficiency or anovulation. |
| **`LBXDHE`** | DHEA-S | µg/dL | Indicates adrenal androgen contribution. |
| **`LBXAND`** | Androstenedione | ng/dL | Key androgen precursor, often elevated in PMOS. |
| **`LBX17H`** | 17α-Hydroxyprogesterone | ng/dL | Excludes Late-Onset Congenital Adrenal Hyperplasia (LOCAH). |

#### Mathematical Formulas for Synthesis:
* **Free Androgen Index (FAI):** Used to estimate bioavailable/free testosterone levels:
  $$\text{FAI} = \left( \frac{\text{Total Testosterone (LBXTST) in nmol/L}}{\text{SHBG (LBXSHBG) in nmol/L}} \right) \times 100$$
  *Note: To convert Total Testosterone from ng/dL (`LBXTST`) to nmol/L (`LBDTSTSI`), multiply by 0.0347.*

---

### B. Reproductive Health Questionnaire (`RHQ_L`)
The **Reproductive Health Questionnaire (`RHQ_L`)** was published in September 2024 for the 2021-2023 cycle, administered via MEC ACASI.

- **Data File Page:** [NHANES 2021-2023 Reproductive Health Questionnaire (RHQ_L)](https://wwwn.cdc.gov/Nchs/Nhanes/2021-2023/RHQ_L.htm)
- **Primary Data Link:** [NHANES 2021-2023 Questionnaire Data Page](https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Questionnaire&Cycle=2021-2023)

#### Key Questionnaire Variables:
| Variable | Question / Description | Target Group | Relevance to PMOS |
|---|---|---|---|
| **`RHQ031`** | Had regular periods in past 12 months? | Females 12+ | Identifies oligomenorrhea or amenorrhea (ovulatory dysfunction). |
| **`RHD043`** | Reason for not having regular periods in past 12 months? | Females 12+ | Specifically looks for explanations like pregnancy, menopause, or medical conditions. |
| **`RHQ010`** | Age when first menstrual period occurred | Females 12+ | Assesses early-life reproductive onset/menarche. |
| **`RHD143`** | Are you pregnant now? | Females 12-44 | Rules out pregnancy-associated amenorrhea. |
| **`RHD280`** | Had a hysterectomy? | Females 12+ | Rules out surgical amenorrhea. |
| **`RHQ305`** | Had both ovaries removed? | Females 12+ | Rules out surgical menopause/oophorectomy. |
| **`RHQ078`** | Ever treated for a pelvic infection (PID)? | Females 12+ | Excludes pelvic inflammatory disease as a cause of pain/irregularity. |

---

## 3. Integrating PMOS with mcPHASES Dataset
To perform multi-dataset synthesis (e.g., combining cross-sectional NHANES population data with high-resolution longitudinal mcPHASES data):
1. **Targeting Common Hormonal Signatures:**
   - [mcPHASES](https://physionet.org/content/mcphases/) provides continuous wearables (heart rate, temperature, sleep) synchronized with daily urinary hormone metabolites: Estrone-3-glucuronide (E3G), Pregnanediol glucuronide (PdG), and Luteinizing Hormone (LH).
   - NHANES (`TST_L`) provides single-timepoint blood measurements of Estradiol (`LBXEST`), Progesterone (`LBXPG4`), and LH (`LBXLUH`).
   - Researchers can map the continuous urinary metabolites in mcPHASES to population serum distributions in NHANES using established urinary-serum translation models.
2. **Predicting Metabolic Dysregulation:**
   - Both datasets track glucose-related metrics. mcPHASES includes Continuous Glucose Monitoring (CGM) data. NHANES includes extensive fasting glucose, HbA1c, and insulin profiles. This enables mapping continuous glucose dynamics in menstruators to population-level metabolic syndrome biomarkers common in PMOS.
