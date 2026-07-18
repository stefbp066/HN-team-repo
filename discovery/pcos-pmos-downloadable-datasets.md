# Public Raw Downloadable Datasets for PMOS (PCOS) Research

This document compiles the verified, raw, publicly downloadable datasets on the internet for **Polyendocrine Metabolic Ovarian Syndrome (PMOS)** — formerly known as **Polycystic Ovary Syndrome (PCOS)**. 

Unlike medical registry descriptions or closed clinical trials (e.g., GEMS-PCOS), these datasets contain raw files (tabular, genomic, and imaging) that are openly accessible and can be downloaded immediately to train and validate machine learning models.

---

## 1. Tabular Clinical Datasets

### A. [Kaggle PCOS Tabular Clinical Dataset](https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos)
* **Description:** The most widely used benchmark dataset in PCOS machine learning literature. 
* **Data Source:** Collected from 10 different hospitals in Kerala, India.
* **Size:** 541 patient records (177 PMOS cases, 364 healthy/non-PMOS controls).
* **Format:** CSV / Excel (also mirrored on [GitHub PCOS_EDA Repo](https://github.com/powellsarahbeth/PCOS_EDA)).
* **Parameters Included (43-44 features):**
  - **Demographics & Physical:** Age, BMI, waist-to-hip ratio, blood pressure, cycle length, cycle regularity, weight gain, hair growth (hirsutism), skin darkening, hair loss.
  - **Hormonal & Biochemical:** FSH (mIU/mL), LH (mIU/mL), LH/FSH ratio, Total Testosterone (ng/dL), Sex Hormone-Binding Globulin (SHBG) (nmol/L), AMH (ng/mL), TSH (µIU/mL), Prolactin (ng/mL), Fasting Insulin (µIU/mL).
  - **Cardiometabolic:** Fasting Blood Glucose (mg/dL), cholesterol levels.
  - **Ovarian Imaging Metrics:** Follicle count (left & right ovary), average follicle size (mm), endometrium thickness (mm).

---

## 2. Genomic & Transcriptomic Datasets

### A. [Figshare GEO Gene Expression Dataset of PCOS Patients](https://figshare.com/articles/dataset/GEO_dataset_of_PCOS_patients_/20303110)
* **Description:** Transcriptomic profile matrices curated from the NCBI Gene Expression Omnibus (GEO).
* **Format:** Raw expression matrix (.txt / .csv format).
* **Data:** High-throughput RNA-Seq / microarray gene expression profiles extracted from granulosa cells, ovarian tissue, and peripheral blood of PMOS patients compared to healthy controls.
* **Relevance:** Enables identification of upregulated and downregulated molecular pathways, key receptor expressions (e.g., insulin receptors, androgen receptors), and gene-level biomarkers for systemic PMOS pathology.

---

## 3. Medical Ovarian Imaging Datasets

### A. [Figshare Large-Scale PCOS Ultrasound Image Dataset](https://figshare.com/articles/dataset/PCOS_Dataset/27491112)
* **Description:** A massive collection of ultrasound images designed to support Computer Vision models and Explainable AI (XAI) in gynaecological diagnostics.
* **Format:** Structured image directories (JPEG/PNG).
* **Size:** 12,680 ovarian ultrasound frames (segmented into PMOS-positive ovaries displaying polycystic follicle excess vs. normal healthy ovaries).
* **Relevance:** Perfect for training Convolutional Neural Networks (CNNs) to automate follicle counts and verify Polycystic Ovarian Morphology (PCOM) — one of the cornerstones of the Rotterdam diagnostic criteria.

### B. [Zenodo PCOSGen-test Dataset](https://doi.org/10.5281/zenodo.14591782)
* **Description:** A highly curated, benchmark test dataset developed for the Auto-PCOS classification challenge.
* **Format:** PNG images.
* **Size:** 1,468 high-quality ultrasound frames extracted from transvaginal ultrasound videos.
* **Labels:** General classification (normal vs. abnormal ovaries) and specific classification (polycystic ovary visible vs. not visible).

---

## 4. Multi-Dataset Synthesis Strategy
To create a high-impact, reusable AI infrastructure for the hackathon, we recommend synthesizing these public assets with **[mcPHASES](https://physionet.org/content/mcphases/)**:

1. **Feature Alignment:**
   - Map mcPHASES daily urinary hormone tracking (LH, Estradiol, Progesterone) and daily symptom scores to the clinical population benchmarks in the [Kaggle PCOS Dataset](https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos) (which has single-point serum LH, FSH, Estradiol, and cycle lengths).
2. **Phenotype Classification:**
   - Train an unsupervised clustering or supervised classification model on the Kaggle dataset to define the optimal biomarker thresholds for PMOS. 
   - Apply this classifier to the mcPHASES participants' median hormone levels to identify which of the 42 naturally cycling participants have "Likely PMOS" vs. "Normal Controls."
3. **Physiological & Wearable Characterization:**
   - Extract the continuous Fitbit wearables data (heart rate variability, skin temperature) and Dexcom continuous glucose monitoring (CGM) data for the predicted PMOS subgroup in mcPHASES to analyze sleep and glucose dynamics under the influence of PMOS-related metabolic dysfunction.
