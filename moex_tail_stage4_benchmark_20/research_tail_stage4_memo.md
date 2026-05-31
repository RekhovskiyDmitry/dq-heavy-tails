# Stage 4 tail-index memo

## Configuration

- Table: `moex_total_return_daily`
- Markets: shares
- Period: 2015-01-01 to end
- Tail side: `lower`
- Filter method: `raw`
- Windows: [504, 756, 1008]; step=21
- Bootstrap reps: 100; block lengths=[5, 10, 15, 21]
- Universe: core_liquid

## Data audit

- raw_rows: 610766
- canonical_board_rows: 610696
- n_securities_raw: 259
- n_securities_canonical: 259
- missing_log_return_raw: 70
- nonfinite_model_return: 0
- multi_board_securities: 0
- audit_abs_return_gt_threshold: 21

## Universe

| market   |   securities |   core_liquid |   broad |   median_coverage |   median_zero_share |
|:---------|-------------:|--------------:|--------:|------------------:|--------------------:|
| shares   |          259 |           142 |     158 |                 1 |           0.0602158 |

Selected securities:
| market   |   n |
|:---------|----:|
| shares   |  20 |

## Estimation results

Total rolling estimates: 6120
Securities with estimates: 20
| market   |   window | tail_group                 |    n |
|:---------|---------:|:---------------------------|-----:|
| shares   |      504 | point_alpha_1_2_uncertain  |  374 |
| shares   |      504 | point_alpha_gt_2_uncertain |  567 |
| shares   |      504 | strict_alpha_gt_2          | 1339 |
| shares   |      756 | point_alpha_1_2_uncertain  |  326 |
| shares   |      756 | point_alpha_gt_2_uncertain |  626 |
| shares   |      756 | strict_alpha_gt_2          | 1088 |
| shares   |     1008 | point_alpha_1_2_uncertain  |  266 |
| shares   |     1008 | point_alpha_gt_2_uncertain |  694 |
| shares   |     1008 | strict_alpha_gt_2          |  840 |

Interpretation rule: strict_alpha_lt_1 and strict_alpha_gt_2 are the defensible groups for the main DQ-vs-DR hypothesis. Point-estimate uncertain groups should be used only for robustness or continuous-alpha tests.