# Mental-Disorder-TS: Klasyfikacja szeregów czasowych

The project aimed to compare time series classification methods for diagnosing neurological and mental disorders based on patients' daily activity data. It was based on the article “Comparison of Manual and Automated Feature Engineering for Daily Activity Classification in Mental Disorder Diagnosis” by J. Adamczyk and F. Malawski.

Used approaches:

* Classification based on the entire time series (complete patient data).
* Multiple Instance Learning (MIL), where data is split into shorter segments (e.g., days), and diagnosis is based on aggregating predictions for these segments (voting).

The effect of dividing data into time windows of varying lengths (whole day, daytime, nighttime) was also studied to identify which data segments provide more diagnostic value.

## Datasets
Three datasets were utilized:
* **Depresjon:** 55 patients (23 with depression, 32 controls).
* **Psykose:** 54 patients (22 with schizophrenia, 32 controls).
* **HYPERAKTIV:** 103 patients (51 with ADHD, 52 controls).


A total of 24 features were extracted as in the reference article. In the traditional method, features were derived from the entire time series, while in MIL, they were extracted from daily segments.

![img.png](plots/img.png)
*Table 1. Manually extracted features \
“Comparison of Manual and Automated Feature Engineering for Daily Activity Classification in Mental Disorder Diagnosis” by J. Adamczyk and F. Malawski.*

## Training and evaluation

Four models were tested:
* Logistic regression
* SVM
* Random Forest
* LightGBM

**Evaluation:**
* Entire time series: Nested CV.
* MIL: Nested CV ensuring patient days were not in both training and test sets.

**Metrics:**
* accuracy
* balanced accuracy
* f1-score
* precision
* recall
* specificity
* ROC AUC
* MCC


## Results
### Classical
#### Hyperaktiv

![img_1.png](plots/img_1.png)

![img.png](plots/img3.png)


Analyzing the classification results on the HYPERAKTIV dataset, several interesting patterns emerge. Most notably, the best results were achieved during the night-time window (21:00-8:00). This may be due to the nature of ADHD, as individuals with this disorder often exhibit increased activity at night, have trouble falling asleep, and experience restless and interrupted sleep.

The highest accuracy (90.7%) was achieved by Random Forest and LightGBM in the 21:00–8:00 window. These models also performed best during the daytime window (6:00–22:00) with accuracies of 85% and 83%, respectively. For 8:00–21:00, Random Forest (81%) and Logistic Regression (80%) were most effective, while LightGBM performed poorly at 68.5%. For the full-day classification, Logistic Regression was the most effective, achieving 81% accuracy.


#### Depresjon

![img_2.png](plots/img_2.png)

![img_3.png](plots/img_3.png)

For depression data, unlike ADHD, the highest accuracy was achieved using full-day classification. However, Random Forest and SVM performed better on daytime data, while nighttime classification yielded the poorest results. The best accuracy was achieved by LightGBM (79%) and Logistic Regression (76%) on full-day data, whereas Random Forest and SVM only reached ~60%.

On daytime data (8:00–21:00), Random Forest achieved 74% accuracy, and SVM 69%. Random Forest excelled in the 6:00–22:00 range with 76% accuracy, outperforming other models, which scored 70–71%. All models struggled on nighttime data, with none exceeding 71%.

Overall, the Depresjon dataset produced lower classification accuracy than HYPERAKTIV, likely due to the less pronounced deviations in activity patterns among patients with depression and the smaller dataset size (half as many patients).




#### Psykose

![img_4.png](plots/img_4.png)

![img_5.png](plots/img_5.png)

For the Psykose dataset, the best results were also achieved during nighttime windows, similar to ADHD, likely due to disrupted circadian rhythms in schizophrenia. Symptoms like delusions, hallucinations, and sleep disturbances increase nighttime activity compared to healthy individuals.

Random Forest and LightGBM achieved the highest accuracy (90.7%) for nighttime data, regardless of the time window (21:00–8:00/22:00–6:00). For daytime classification, Random Forest and Logistic Regression performed best (~80%). Logistic Regression was most accurate for full-day data (81%).

Overall, Psykose achieved the highest results across all datasets, likely because schizophrenia, being rarer and more behaviorally distinct, is easier to classify.

Across all datasets, disorder characteristics significantly influenced results. Nighttime data performed better for ADHD and schizophrenia due to increased nocturnal activity, while depression was better classified using full-day data.

### MIL
#### Hyperactiv

![img_6.png](plots/img_6.png)

![img_7.png](plots/img_7.png)

Using MIL resulted in significantly worse performance compared to the classical approach, where accuracy and balanced accuracy reached ~90%. With MIL, all models fell below 70%, often below 50% or worse. Only SVM performed reasonably well for the 8:00–21:00 window, achieving positive MCC and a recall of 87% (notably higher than precision at 64%). Interestingly, a small shift in the day window (8:00–21:00 to 6:00–22:00) sharply degraded SVM’s performance.

Logistic Regression consistently performed the worst, except for nighttime datasets, where Random Forest usually had the lowest results. However, for 6:00–22:00, Random Forest identified negative cases more effectively (specificity). SVM, despite its relative success, often struggled with specificity.

For the 6:00–22:00 nighttime dataset, LightGBM achieved the best balanced accuracy and tied for accuracy, with a slight edge due to its better specificity.

#### Depresjon

![img_8.png](plots/img_8.png)

![img_9.png](plots/img_9.png)

For depression, MIL results were closer to those of the classical method, with accuracy/balanced accuracy around 80%. The best results were slightly lower than the classical approach (e.g., full LightGBM: 0.78 vs. full Logistic Regression MIL: 0.782). For some windows, like 8:00–21:00, results slightly improved, typically equating to one more patient being correctly classified.

All models performed best on full-day data and worst on nighttime data, with MIL results consistently below the classical approach by ~5 percentage points. Logistic Regression excelled on full-day and daytime data, while LightGBM and Random Forest performed best for nighttime data. SVM lagged, staying below 60% accuracy.

SVM prioritized positive case classification (higher recall at the expense of specificity), whereas other models favored higher specificity over recall. This tradeoff allowed SVM to occasionally achieve the best f1-score.

Unlike HYPERAKTIV, MCC values were consistently positive. The lowest MCCs (<0.6) were observed for Logistic Regression and SVM on nighttime data.


#### Psykose

![img_10.png](plots/img_10.png)

![img_11.png](plots/img_11.png)


For the Psykose dataset, MIL performed best, with LightGBM achieving the highest accuracy for full-day data. Every dataset had at least one model reaching ≥83% accuracy. LightGBM, Random Forest, and Logistic Regression showed similar results, with slight variations favoring LightGBM for full-day data and Logistic Regression for nighttime data. Accuracy across different time splits (e.g., 21:00–8:00 vs. 22:00–6:00) was consistent.

SVM struggled with specificity but had better recall, though it's F1-scores were the lowest due to other models outperforming it in recall. Balanced accuracy for SVM was sometimes higher than accuracy due to its focus on positive cases. MCC values for Psykose were the highest across datasets, nearing 0.8 for LightGBM and RF.

Unlike the classical approach, MIL excelled with full-day or daytime data, while nighttime data consistently produced the worst results. Despite some improvements, MIL generally underperformed compared to the classical method. SVM consistently lagged but surprisingly excelled in the challenging HYPERAKTIV dataset, where MCC values for MIL models were generally poor (~<0.5).

Comparison with the Article: MIL did not outperform the classical method, aligning with the article's findings of ~80% accuracy for Depresjon and ~90% for Psykose. The HYPERAKTIV dataset was not analyzed in the article.



