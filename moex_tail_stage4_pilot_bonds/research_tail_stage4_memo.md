# Stage 4 tail-index memo

## Configuration

- Table: `moex_total_return_daily`
- Markets: bonds
- Period: 2018-01-01 to end
- Tail side: `lower`
- Filter method: `raw`
- Windows: [504]; step=21
- Bootstrap reps: 100; block lengths=[5, 10, 15]
- Universe: core_liquid

## Data audit

- raw_rows: 1203538
- canonical_board_rows: 1201511
- n_securities_raw: 2039
- n_securities_canonical: 2039
- missing_log_return_raw: 2027
- nonfinite_model_return: 0
- multi_board_securities: 0
- audit_abs_return_gt_threshold: 680

## Universe

| market   |   securities |   core_liquid |   broad |   median_coverage |   median_zero_share |
|:---------|-------------:|--------------:|--------:|------------------:|--------------------:|
| bonds    |         2039 |            15 |      16 |          0.193959 |                   0 |

Selected securities:
| market   |   n |
|:---------|----:|
| bonds    |  15 |

## Estimation results

Total rolling estimates: 1153
Securities with estimates: 15
| market   |   window | tail_group                 |   n |
|:---------|---------:|:---------------------------|----:|
| bonds    |      504 | point_alpha_1_2_uncertain  | 562 |
| bonds    |      504 | point_alpha_gt_2_uncertain | 225 |
| bonds    |      504 | point_alpha_lt_1_uncertain |  16 |
| bonds    |      504 | strict_alpha_gt_2          | 350 |

Interpretation rule: strict_alpha_lt_1 and strict_alpha_gt_2 are the defensible groups for the main DQ-vs-DR hypothesis. Point-estimate uncertain groups should be used only for robustness or continuous-alpha tests.