https://doi.org/10.13026/5b8h-jx61

Abstract
Individuals who menstruate are frequently led to believe that there is a standard menstrual cycle, typically characterized as 28 days in length with predictable and uniform patterns. This framing often emphasizes cycle dates as the only relevant metric, overlooking the broader physiological and emotional fluctuations throughout the cycle driven by complex hormonal interactions. Consequently, when individuals encounter menstrual experiences that do not align with calendar-based metrics, they are often left without adequate frameworks for understanding their menstrual health, which can result in distress or delays in seeking care. Our work advocates for a new definition of menstrual health that encompasses a wider range of physiological signals in order to acknowledge its connection to overall wellbeing, establish realistic expectations for menstruators, and build better health management systems. However, historical stigmatization has led to a dearth of datasets suitable for pursuing these aims.

mcPHASES (menstrual cycle Physiological, Hormonal, and Self-Reported Events and Symptoms) is a comprehensive dataset consisting of multimodal physiological, hormonal, and self-reported measures collected to support holistic menstrual health research. Data from 42 Canadian young adult menstruators was collected across two 3-month periods. Participants wore Fitbit Sense smartwatches and Dexcom G6 continuous glucose monitors to measure physiological signals, and they used Mira Plus Starter Kits to track their hormone levels. Additionally, participants self-reported daily experiences like cramps, sleep quality, and stress levels. The dataset contains 23 structured tables organized by signal category so that researchers can examine relationships between physiological signals and hormonal fluctuations, analyze the impacts of lifestyle factors on the menstrual cycle, and develop better algorithms for menstrual cycle prediction. More broadly, mcPHASES supports research in women's health, digital health technologies, and personalized care by providing unprecedented multimodal data for building a more accurate understanding of menstrual health patterns.

Background
The menstrual cycle is a complex interplay of hormonal, physiological, and behavioral processes that profoundly impacts overall wellbeing. It influences and is influenced by factors like stress, activity, nutrition, and sleep, leading many to recognize menstrual health as a key health indicator akin to a “fifth vital sign” [1,2]. Despite its clinical significance, menstrual health remains under-researched due to historical neglect [3], thereby perpetuating narrow perspectives linked strictly to reproduction [4,5]. Resulting misconceptions about cycle consistency and regularity contribute to delayed healthcare seeking, inadequate symptom management, and the development of tracking technologies that fail to account for the natural variations in menstrual experiences [4,5,6,7].

The rise of wearable technologies has created unprecedented opportunities to continuously track physiological data that can address these gaps. However, most studies lack ground-truth hormone data necessary to account for the menstrual cycle; the few that have hormone data are rarely longitudinal or ambulatory [8], limiting their validity and generalizability. These shortcomings prevent research communities from studying the nuanced relationships between hormonal fluctuations and the wide array of physiological and behavioral changes that occur throughout the menstrual cycle [9,10,11,12].

In response to the calls for more inclusive and longitudinal menstrual datasets [13], we release a dataset called mcPHASES. This comprehensive dataset includes multimodal data from 42 menstruating young adults in Canada over two 3-month intervals. They collected smartwatch-derived physiological metrics, continuous glucose monitoring, daily symptom diaries, and daily hormone measurements from urinalysis. By providing synchronized hormonal and physiological data during everyday living, mcPHASES enables menstrual health research that has previously been challenging to conduct. Specifically, it provides a valuable resource for studying the dynamic interplay between hormonal cycles and systemic health, supporting investigations that lead to more accurate menstrual phase detection and broader health insights.

Methods
mcPHASES was created using a three-step process involving participant recruitment, multimodal data collection, and deidentification.

Recruitment and Enrollment.
Participants were recruited through women's health advocacy groups in the Greater Toronto Area. Eligibility criteria included being a menstruating adult over 18 years of age with no recent hormonal contraceptive use or diabetes diagnosis. A total of 50 participants enrolled for a three-month interval in 2022, and 42 consented to have their data publicly released. Of these, 20 completed a second three-month interval of data collection in 2024.

Data Collection.
Data were collected using commercially available devices and self-report methods:

Hormone analyzer: The Mira Plus Starter Kit was used to measure daily levels of luteinizing hormone (LH), as well as urinary metabolites of estrogen (estrone-3-glucuronide, E3G) and progesterone (pregnanediol glucuronide, PdG).
Fitness tracker: The Fitbit Sense smartwatch passively captured physiological data including heart rate, temperature, sleep quality, and activity.
Glucose monitor: The Dexcom G6 CGM continuously tracked blood glucose (used only in Interval 1).
Daily diary: A custom smartphone diary app collected self-reported menstrual symptoms and menstruation status (optional in Interval 2).

Interval 1 included all modalities, requiring daily manual reporting and device use for compensation. Round 2 excluded glucose tracking and made diaries optional to reduce participant burden. Each device was registered with anonymized credentials, and data was extracted directly from manufacturer portals or participant input.

Deidentification and Processing.
To protect participant privacy, all collected data were deidentified following HIPAA standards. Personal identifiers such as names, emails, and device IDs were removed. Absolute calendar dates were replaced with relative “day-in-study” values, and a weekday/weekend indicator was added. Mira’s proprietary hormone interpretation was used to label four cycle phases: menstruation, late-follicular, ovulation, and luteal. Data from both rounds were stacked, with fields left blank when data were not collected in a specific round. No imputation or additional cleaning was applied, preserving the real-world nature of the dataset.

Data Description
The mcPHASES dataset is organized into 23 structured tables linked by a shared participant identifier (id) and a relative timeline variable (day_in_study). For events spanning more than one day, such as sleep, additional fields like sleep_start_day_in_study and sleep_end_day_in_study are included to capture full event durations. Each participant's timeline begins on Day 1 of their Round 1 participation; for those who returned in Round 2, data resumes around Day 905 to reflect the elapsed real-world time.

The dataset includes the following tables:

Demographic Table: Contains static information such as age, education, employment, and age at menarche.
Self-Report and Hormone Table: Includes daily entries from a custom survey app, including symptoms (e.g., cramps, mood, menstrual flow) and manually entered hormone levels (LH, E3G, PdG).
Glucose Table: Provides high-frequency continuous glucose monitoring data.
Fitbit-Derived Tables (20 total): Include high-resolution physiological and behavioral data such as heart rate, activity levels, sleep stages and scores, respiratory rate, temperature, VO₂ max, oxygen variation, and stress scores.
All data are preserved in a form close to the original device outputs to maintain authenticity.

Usage Notes
The mcPHASES dataset provides a unique resource not only for menstrual health research but also for topics that span physiology, machine learning, and digital health. Key areas of potential analysis include the following:

Mapping wearable signals to menstrual phases
Researchers can examine how physiological signals such as skin temperature, heart rate variability, and glucose levels track with hormone-defined menstrual phases. Such explorations may lead to the development of non-invasive predictors of ovulation and hormonal state [9,10,11].
Characterizing cycle variability and influencing factors
mcPHASES enables analysis of both inter- and intra-individual variation in cycle length, phase duration, and symptom patterns. Researchers can also study how contextual factors like stress, sleep, and physical activity influence menstrual dynamics [2,13].
Studying hormone-physiology interactions
By jointly modeling hormone levels with continuous sensor data, researchers can explore how hormonal fluctuations modulate broader physiological systems [8,11].
Developing predictive models for menstrual tracking
mcPHASES provides hormone-verified ground truth labels for machine learning models designed to predict ovulation, fertile windows, and symptom onset more accurately than traditional calendar- or self-report–based approaches [14,15].
Ethics
The study protocol for data collection and public release was reviewed and approved by the Research Ethics Board at the University of Toronto (Protocol #41568), which granted approval for the study and the sharing of de-identified data.

Acknowledgements
This work was supported in part by NSERC Discovery Grants RGPIN-2021-03457 and RGPIN-2021-04268, a Google PhD Fellowship, and an unrestricted research gift from Google.

Conflicts of Interest
The Authors declare no competing financial or non-financial interests.

References
Bobel C. Beyond the managed body: putting menstrual literacy at the center. In: The Managed Body: Developing Girls and Menstrual Health in the Global South. 2018 Oct 20. p. 281-321. Cham: Springer International Publishing.
Vollmar AK, Mahalingaiah S, Jukic AM. The menstrual cycle as a vital sign: a comprehensive review. F&S Reviews. 2025 Jun 1;6(1):100081.
Critchley HO, Babayev E, Bulun SE, Clark S, Garcia-Grau I, Gregersen PK, Kilcoyne A, Kim JY, Lavender M, Marsh EE, Matteson KA. Menstruation: science and society. American Journal of Obstetrics and Gynecology. 2020 Nov 1;223(5):624-64.
Eschler J, Menking A, Fox S, Backonja U. Defining menstrual literacy with the aim of evaluating mobile menstrual tracking applications. CIN: Computers, Informatics, Nursing. 2019 Dec 1;37(12):638-46.
Zwingerman R, Chaikof M, Jones C. A critical appraisal of fertility and menstrual tracking apps for the iPhone. Journal of Obstetrics and Gynaecology Canada. 2020 May 1;42(5):583-90.
Lin GE, Mynatt ED, Kumar N. Investigating culturally responsive design for menstrual tracking and sharing practices among individuals with minimal sexual education. In: Proceedings of the 2022 CHI Conference on Human Factors in Computing Systems. 2022 Apr 29. p. 1-15.
Epstein DA, Lee NB, Kang JH, Agapie E, Schroeder J, Pina LR, Fogarty J, Kientz JA, Munson S. Examining menstrual tracking to inform the design of personal informatics tools. In: Proceedings of the 2017 CHI Conference on Human Factors in Computing Systems. 2017 May 2. p. 6876-6888.
Baker FC, Siboza F, Fuller A. Temperature regulation in women: effects of the menstrual cycle. Temperature. 2020 Jul 2;7(3):226-62.
Goodale BM, Shilaih M, Falco L, Dammeier F, Hamvas G, Leeners B. Wearable sensors reveal menses-driven changes in physiology and enable prediction of the fertile window: observational study. Journal of Medical Internet Research. 2019 Apr 18;21(4):e13404.
Lin G, Siddiqui R, Lin Z, Blodgett JM, Patel SN, Truong KN, Mariakakis A. Blood glucose variance measured by continuous glucose monitors across the menstrual cycle. npj Digital Medicine. 2023 Aug 11;6(1):140.
Lin G, Li JY, Christofferson K, Patel SN, Truong KN, Mariakakis A. Understanding wrist skin temperature changes to hormone variations across the menstrual cycle. npj Women's Health. 2024 Oct 4;2(1):35.
Shilaih M, Van der Clerck D, Falco L, Kübler F, Leeners B. Pulse rate measurement during sleep using wearable sensors, and its correlation with the menstrual cycle phases, a prospective observational study. Scientific Reports. 2017 May 2;7(1):1294.
Bull JR, Rowland SP, Scherwitzl EB, Scherwitzl R, Danielsson KG, Harper J. Real-world menstrual cycle characteristics of more than 600,000 menstrual cycles. NPJ Digital Medicine. 2019 Aug 27;2(1):83.
Jasinski SR, Presby DM, Grosicki GJ, Capodilupo ER, Lee VH. A novel method for quantifying fluctuations in wearable-derived daily cardiovascular parameters across the menstrual cycle. NPJ Digital Medicine. 2024 Dec 23;7(1):373.
Maijala A, Kinnunen H, Koskimäki H, Jämsä T, Kangas M. Nocturnal finger skin temperature in menstrual cycle tracking: ambulatory pilot study using a wearable Oura ring. BMC Women's Health. 2019 Nov 29;19(1):150.