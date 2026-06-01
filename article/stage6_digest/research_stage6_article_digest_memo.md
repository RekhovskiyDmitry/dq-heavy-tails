# Stage 6 article digest

## Inputs
- Tail directory: `/home/openclaw/.openclaw/workspace/dq-coursework-work/moex_article_core_bundle_assetwise/moex_tail_stage4_main_shares_raw`
- Stage 2 directory: `/home/openclaw/.openclaw/workspace/dq-coursework-work/moex_article_core_bundle_assetwise/moex_stage2_alpha_windows_shares_parallel`
- Stage 5 directory: `/home/openclaw/.openclaw/workspace/dq-coursework-work/moex_article_core_bundle_assetwise/moex_stage5_alpha_windows_shares_assetwise`

## Tail-index status

The Stage 4 tail-index run contains **43,377 rolling estimates** for **142 equities**.

- Strict alpha < 1 observations: **0**
- Point alpha < 1 observations: **9**
- Strict alpha > 2 observations: **21,243**

### Tail alpha summary by window

|   window |   n_estimates |   n_securities |   alpha_mean |   alpha_median |   alpha_p10 |   alpha_p25 |   alpha_p75 |   alpha_p90 |   point_alpha_lt1 |   point_alpha_1_2 |   point_alpha_gt2 |   strict_alpha_lt1 |   strict_alpha_1_2 |   strict_alpha_gt2 |   mean_p_alpha_lt1 |   mean_p_alpha_gt2 |
|---------:|--------------:|---------------:|-------------:|---------------:|------------:|------------:|------------:|------------:|------------------:|------------------:|------------------:|-------------------:|-------------------:|-------------------:|-------------------:|-------------------:|
|      504 |         16163 |            142 |      5.21857 |        2.9924  |     1.8164  |     2.21099 |     4.53304 |     8.3726  |                 9 |              2733 |             13421 |                  0 |                  0 |               9023 |        0.00181904  |           0.834431 |
|      756 |         14459 |            142 |      4.0424  |        2.70044 |     1.86507 |     2.1455  |     3.81937 |     5.90099 |                 0 |              2476 |             11983 |                  0 |                  4 |               7046 |        0.000891386 |           0.821078 |
|     1008 |         12755 |            142 |      3.2751  |        2.52756 |     1.91537 |     2.14458 |     3.25277 |     4.80466 |                 0 |              1986 |             10769 |                  0 |                  0 |               5174 |        0.000434751 |           0.810313 |

### Latest group summary by window

|   window |   n_securities |   alpha_median |   alpha_p10 |   alpha_p25 |   alpha_p75 |   point_alpha_lt1 |   point_alpha_1_2 |   point_alpha_gt2 |   strict_alpha_lt1 |   strict_alpha_1_2 |   strict_alpha_gt2 |   point_alpha_1_2_uncertain |   point_alpha_gt_2_uncertain |   point_alpha_lt_1_uncertain |   mean_p_alpha_lt1 |   mean_p_alpha_gt2 |
|---------:|---------------:|---------------:|------------:|------------:|------------:|------------------:|------------------:|------------------:|-------------------:|-------------------:|-------------------:|----------------------------:|-----------------------------:|-----------------------------:|-------------------:|-------------------:|
|      504 |            142 |        4.80043 |     2.67033 |     3.22808 |     8.38703 |                 0 |                 3 |               139 |                  0 |                  0 |                125 |                           2 |                           15 |                            0 |         0.0031361  |           0.966495 |
|      756 |            142 |        3.71082 |     2.54488 |     3.10816 |     5.42749 |                 0 |                 5 |               137 |                  0 |                  0 |                120 |                           4 |                           18 |                            0 |         0.00353058 |           0.953074 |
|     1008 |            142 |        3.54313 |     2.28676 |     2.81036 |     4.66687 |                 0 |                 8 |               134 |                  0 |                  0 |                109 |                           8 |                           25 |                            0 |         0.00154231 |           0.930818 |

## Stage 2 DQ/DR horse-race summary

This table counts how often each signal is significant across the Stage 2 model grid.

| dependent         | spec_name        | param               |   n_models |   sig10 |   sig5 |   pos_sig10 |   neg_sig10 |   median_coef |   median_t_hac |   mean_r2 |
|:------------------|:-----------------|:--------------------|-----------:|--------:|-------:|------------:|------------:|--------------:|---------------:|----------:|
| future_tail_event | dq_only          | dq_es               |         24 |      10 |      4 |          10 |           0 |      0.426287 |       1.07917  | 0.0378732 |
| future_tail_event | dr_only          | dr_es_concentration |         24 |       7 |      5 |           0 |           7 |     -0.213702 |      -0.419692 | 0.0299523 |
| future_tail_event | dq_dr            | dq_es               |         24 |      17 |     13 |          17 |           0 |      1.29393  |       2.27003  | 0.126784  |
| future_tail_event | dq_dr            | dr_es_concentration |         24 |      15 |     12 |           0 |          15 |     -1.66312  |      -2.09931  | 0.126784  |
| future_tail_event | dq_dr_current_es | dq_es               |         24 |      14 |     12 |          14 |           0 |      1.64059  |       1.87298  | 0.156101  |
| future_tail_event | dq_dr_current_es | dr_es_concentration |         24 |       7 |      6 |           1 |           6 |     -0.692325 |      -0.375469 | 0.156101  |
| future_tail_event | full             | dq_es               |         24 |       9 |      8 |           9 |           0 |      1.92412  |       1.12521  | 0.260844  |
| future_tail_event | full             | dr_es_concentration |         24 |      16 |     14 |           0 |          16 |     -4.72407  |      -2.16876  | 0.260844  |

## Stage 5 alpha-interaction summary

This table counts significant DQ/DR × tail-heaviness interaction terms across the Stage 5 model grid.

| dependent         | spec                                         | param        |   n_models |   sig10 |   sig5 |   pos_sig10 |   neg_sig10 |   median_coef |   median_t_hac |   mean_r2 |   min_pvalue |
|:------------------|:---------------------------------------------|:-------------|-----------:|--------:|-------:|------------:|------------:|--------------:|---------------:|----------:|-------------:|
| future_tail_event | interact_alpha_heaviness_below2              | z_dq_x_heavy |         16 |       6 |      5 |           4 |           2 |    0.00810139 |      0.180724  |  0.157353 |  9.66079e-08 |
| future_tail_event | interact_alpha_heaviness_below2              | z_dr_x_heavy |         16 |       9 |      8 |           7 |           2 |    0.00720967 |      0.729415  |  0.157353 |  1.61764e-10 |
| future_tail_event | interact_alpha_heaviness_below2_controls     | z_dq_x_heavy |         16 |       2 |      1 |           2 |           0 |   -0.00409567 |     -0.084956  |  0.210724 |  8.74007e-05 |
| future_tail_event | interact_alpha_heaviness_below2_controls     | z_dr_x_heavy |         16 |       7 |      7 |           5 |           2 |   -0.0759617  |     -0.268853  |  0.210724 |  2.9925e-05  |
| future_tail_event | interact_alpha_heaviness_inv                 | z_dq_x_heavy |         24 |      10 |      5 |           0 |          10 |   -0.139713   |     -1.32044   |  0.234965 |  1.42472e-05 |
| future_tail_event | interact_alpha_heaviness_inv                 | z_dr_x_heavy |         24 |       5 |      4 |           4 |           1 |    0.0813261  |      0.649613  |  0.234965 |  9.48838e-10 |
| future_tail_event | interact_alpha_heaviness_inv_controls        | z_dq_x_heavy |         24 |       7 |      5 |           1 |           6 |   -0.135437   |     -0.927106  |  0.260073 |  1.06201e-16 |
| future_tail_event | interact_alpha_heaviness_inv_controls        | z_dr_x_heavy |         24 |       5 |      4 |           1 |           4 |   -0.00921932 |     -0.0419964 |  0.260073 |  0.000469174 |
| future_tail_event | interact_alpha_heaviness_q25_below2          | z_dq_x_heavy |         24 |       4 |      4 |           3 |           1 |    0.122757   |      0.875386  |  0.186172 |  0.000405814 |
| future_tail_event | interact_alpha_heaviness_q25_below2          | z_dr_x_heavy |         24 |       9 |      6 |           1 |           8 |   -0.252014   |     -1.37305   |  0.186172 |  0.00142346  |
| future_tail_event | interact_alpha_heaviness_q25_below2_controls | z_dq_x_heavy |         24 |       6 |      3 |           6 |           0 |    0.177512   |      0.756393  |  0.247341 |  1.1356e-12  |
| future_tail_event | interact_alpha_heaviness_q25_below2_controls | z_dr_x_heavy |         24 |      11 |      8 |           0 |          11 |   -0.491759   |     -1.53405   |  0.247341 |  4.22018e-11 |

## Key correlations

High correlations between DQ and alpha-heaviness indicate that interaction models are likely collinear and should be interpreted cautiously.

| period        |   window |   horizon |   tail_prob | var1   | var2                |      corr |   n_obs |
|:--------------|---------:|----------:|------------:|:-------|:--------------------|----------:|--------:|
| baseline_2018 |      504 |        21 |       0.025 | dq_es  | alpha_heaviness_inv |  0.8976   |      76 |
| baseline_2018 |      504 |        21 |       0.025 | dq_es  | alpha_median        | -0.800943 |      76 |
| baseline_2018 |      504 |        21 |       0.025 | dq_es  | dr_es_concentration |  0.561068 |      76 |
| baseline_2018 |      504 |        21 |       0.05  | dq_es  | alpha_heaviness_inv |  0.909602 |      76 |
| baseline_2018 |      504 |        21 |       0.05  | dq_es  | alpha_median        | -0.868146 |      76 |
| baseline_2018 |      504 |        21 |       0.05  | dq_es  | dr_es_concentration |  0.213482 |      76 |
| baseline_2018 |      504 |        63 |       0.025 | dq_es  | alpha_heaviness_inv |  0.898078 |      74 |
| baseline_2018 |      504 |        63 |       0.025 | dq_es  | alpha_median        | -0.810171 |      74 |
| baseline_2018 |      504 |        63 |       0.025 | dq_es  | dr_es_concentration |  0.571017 |      74 |
| baseline_2018 |      504 |        63 |       0.05  | dq_es  | alpha_heaviness_inv |  0.903193 |      74 |
| baseline_2018 |      504 |        63 |       0.05  | dq_es  | alpha_median        | -0.864461 |      74 |
| baseline_2018 |      504 |        63 |       0.05  | dq_es  | dr_es_concentration |  0.24518  |      74 |
| baseline_2018 |      756 |        21 |       0.025 | dq_es  | alpha_heaviness_inv |  0.912358 |      64 |
| baseline_2018 |      756 |        21 |       0.025 | dq_es  | alpha_median        | -0.882512 |      64 |
| baseline_2018 |      756 |        21 |       0.025 | dq_es  | dr_es_concentration |  0.694616 |      64 |
| baseline_2018 |      756 |        21 |       0.05  | dq_es  | alpha_heaviness_inv |  0.901231 |      64 |
| baseline_2018 |      756 |        21 |       0.05  | dq_es  | alpha_median        | -0.873141 |      64 |
| baseline_2018 |      756 |        21 |       0.05  | dq_es  | dr_es_concentration |  0.427638 |      64 |
| baseline_2018 |      756 |        63 |       0.025 | dq_es  | alpha_heaviness_inv |  0.904787 |      62 |
| baseline_2018 |      756 |        63 |       0.025 | dq_es  | alpha_median        | -0.873424 |      62 |
| baseline_2018 |      756 |        63 |       0.025 | dq_es  | dr_es_concentration |  0.716983 |      62 |
| baseline_2018 |      756 |        63 |       0.05  | dq_es  | alpha_heaviness_inv |  0.892122 |      62 |
| baseline_2018 |      756 |        63 |       0.05  | dq_es  | alpha_median        | -0.862013 |      62 |
| baseline_2018 |      756 |        63 |       0.05  | dq_es  | dr_es_concentration |  0.472433 |      62 |
| baseline_2018 |     1008 |        21 |       0.025 | dq_es  | alpha_heaviness_inv |  0.657355 |      52 |
| baseline_2018 |     1008 |        21 |       0.025 | dq_es  | alpha_median        | -0.685366 |      52 |
| baseline_2018 |     1008 |        21 |       0.025 | dq_es  | dr_es_concentration |  0.669291 |      52 |
| baseline_2018 |     1008 |        21 |       0.05  | dq_es  | alpha_heaviness_inv |  0.647919 |      52 |
| baseline_2018 |     1008 |        21 |       0.05  | dq_es  | alpha_median        | -0.676805 |      52 |
| baseline_2018 |     1008 |        21 |       0.05  | dq_es  | dr_es_concentration |  0.43514  |      52 |

## Suggested interpretation

1. Conservative EVT classification does not find defensible alpha < 1 regimes among liquid MOEX equities.
2. Stage 2 provides stronger evidence that DQ predicts future tail events than that DQ predicts continuous realized ES/VaR/RV/MDD.
3. Stage 5 interaction regressions should be treated as robustness rather than the core result because DQ is highly correlated with tail-heaviness measures.
4. The article should not claim that DQ outperforms DR specifically at alpha < 1 on MOEX equities; the data do not contain that regime.
5. A defensible contribution is: DQ has predictive content for future tail-event incidence in liquid MOEX equities, while ultra-heavy alpha < 1 regimes are empirically rare under conservative EVT inference.
