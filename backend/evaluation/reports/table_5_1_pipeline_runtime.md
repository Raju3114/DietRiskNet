**Table 5.1 - Pipeline Runtime**

| Stage | Mean (ms) | Median (ms) | P95 (ms) |
|---|---|---|---|
| yolo_detection | 0.002 | 0.002 | 0.003 |
| efficientnet_classification | 10.386 | 10.386 | 10.422 |
| nutrition_lookup | 0.43 | 0.43 | 0.559 |
| dci | 1.422 | 1.422 | 1.777 |
| nis | 0.022 | 0.022 | 0.025 |
| disease_prediction | 51.438 | 51.438 | 52.831 |
| risk_fusion | 0.005 | 0.005 | 0.006 |
| rule_recommendations | 0.003 | 0.003 | 0.003 |
| Total (pipeline stages) | 63.708 |  |  |