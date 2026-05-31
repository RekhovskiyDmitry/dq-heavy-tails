# Stage 2 robustness memo

## Outputs
- `01_stage2_universes.csv`: selected universes by market and period.
- `02_stage2_rolling_metrics.csv`: rolling DQ/DR and future risk metrics.
- `04_stage2_regressions_hac.csv`: nested HAC regressions.
- `06_stage2_vif.csv`: multicollinearity diagnostics.
- `08_tail_group_tests.csv`: test of tail-index-sorted portfolio groups.
- `09_focus_summary_dq_dr.csv`: compact DQ/DR coefficient table.

## Rolling observations by market/period

| market   | period          |   window |   horizon |   tail_prob |   n |
|:---------|:----------------|---------:|----------:|------------:|----:|
| bonds    | baseline_2018   |      252 |        21 |       0.025 |  88 |
| bonds    | baseline_2018   |      252 |        21 |       0.05  |  88 |
| bonds    | baseline_2018   |      252 |        63 |       0.025 |  86 |
| bonds    | baseline_2018   |      252 |        63 |       0.05  |  86 |
| bonds    | baseline_2018   |      504 |        21 |       0.025 |  76 |
| bonds    | baseline_2018   |      504 |        21 |       0.05  |  76 |
| bonds    | baseline_2018   |      504 |        63 |       0.025 |  74 |
| bonds    | baseline_2018   |      504 |        63 |       0.05  |  74 |
| bonds    | covid_2020_2021 |      252 |        21 |       0.025 |  12 |
| bonds    | covid_2020_2021 |      252 |        21 |       0.05  |  12 |
| bonds    | covid_2020_2021 |      252 |        63 |       0.025 |  10 |
| bonds    | covid_2020_2021 |      252 |        63 |       0.05  |  10 |
| bonds    | full_2015       |      252 |        21 |       0.025 | 113 |
| bonds    | full_2015       |      252 |        21 |       0.05  | 113 |
| bonds    | full_2015       |      252 |        63 |       0.025 | 111 |
| bonds    | full_2015       |      252 |        63 |       0.05  | 111 |
| bonds    | full_2015       |      504 |        21 |       0.025 | 103 |
| bonds    | full_2015       |      504 |        21 |       0.05  | 103 |
| bonds    | full_2015       |      504 |        63 |       0.025 | 102 |
| bonds    | full_2015       |      504 |        63 |       0.05  | 102 |
| bonds    | post_2024       |      252 |        21 |       0.025 |  16 |
| bonds    | post_2024       |      252 |        21 |       0.05  |  16 |
| bonds    | post_2024       |      252 |        63 |       0.025 |  14 |
| bonds    | post_2024       |      252 |        63 |       0.05  |  14 |
| bonds    | post_2024       |      504 |        21 |       0.025 |   4 |
| bonds    | post_2024       |      504 |        21 |       0.05  |   4 |
| bonds    | post_2024       |      504 |        63 |       0.025 |   2 |
| bonds    | post_2024       |      504 |        63 |       0.05  |   2 |
| bonds    | shock_2022_2023 |      252 |        21 |       0.025 |  12 |
| bonds    | shock_2022_2023 |      252 |        21 |       0.05  |  12 |
| bonds    | shock_2022_2023 |      252 |        63 |       0.025 |  10 |
| bonds    | shock_2022_2023 |      252 |        63 |       0.05  |  10 |
| shares   | baseline_2018   |      252 |        21 |       0.025 |  88 |
| shares   | baseline_2018   |      252 |        21 |       0.05  |  88 |
| shares   | baseline_2018   |      252 |        63 |       0.025 |  86 |
| shares   | baseline_2018   |      252 |        63 |       0.05  |  86 |
| shares   | baseline_2018   |      504 |        21 |       0.025 |  76 |
| shares   | baseline_2018   |      504 |        21 |       0.05  |  76 |
| shares   | baseline_2018   |      504 |        63 |       0.025 |  74 |
| shares   | baseline_2018   |      504 |        63 |       0.05  |  74 |
| shares   | covid_2020_2021 |      252 |        21 |       0.025 |  12 |
| shares   | covid_2020_2021 |      252 |        21 |       0.05  |  12 |
| shares   | covid_2020_2021 |      252 |        63 |       0.025 |  10 |
| shares   | covid_2020_2021 |      252 |        63 |       0.05  |  10 |
| shares   | full_2015       |      252 |        21 |       0.025 | 124 |
| shares   | full_2015       |      252 |        21 |       0.05  | 124 |
| shares   | full_2015       |      252 |        63 |       0.025 | 122 |
| shares   | full_2015       |      252 |        63 |       0.05  | 122 |
| shares   | full_2015       |      504 |        21 |       0.025 | 112 |
| shares   | full_2015       |      504 |        21 |       0.05  | 112 |
| shares   | full_2015       |      504 |        63 |       0.025 | 110 |
| shares   | full_2015       |      504 |        63 |       0.05  | 110 |
| shares   | post_2024       |      252 |        21 |       0.025 |  16 |
| shares   | post_2024       |      252 |        21 |       0.05  |  16 |
| shares   | post_2024       |      252 |        63 |       0.025 |  14 |
| shares   | post_2024       |      252 |        63 |       0.05  |  14 |
| shares   | post_2024       |      504 |        21 |       0.025 |   4 |
| shares   | post_2024       |      504 |        21 |       0.05  |   4 |
| shares   | post_2024       |      504 |        63 |       0.025 |   2 |
| shares   | post_2024       |      504 |        63 |       0.05  |   2 |
| shares   | shock_2022_2023 |      252 |        21 |       0.025 |  12 |
| shares   | shock_2022_2023 |      252 |        21 |       0.05  |  12 |
| shares   | shock_2022_2023 |      252 |        63 |       0.025 |  10 |
| shares   | shock_2022_2023 |      252 |        63 |       0.05  |  10 |

## Significant DQ/DR coefficients at 10% level

| market   | period        |   window |   horizon |   tail_prob | dependent         | spec_name        | param               |        coef |    t_hac |   pvalue_hac |         r2 |   n_obs |
|:---------|:--------------|---------:|----------:|------------:|:------------------|:-----------------|:--------------------|------------:|---------:|-------------:|-----------:|--------:|
| bonds    | baseline_2018 |      252 |        21 |       0.025 | future_tail_event | dq_dr            | dq_es               |  0.974977   |  1.74076 |  0.081725    | 0.0299511  |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.025 | future_tail_event | dq_dr_current_es | dq_es               |  0.987311   |  1.73947 |  0.0819518   | 0.0419437  |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.025 | future_tail_event | full             | dq_es               |  1.9772     |  2.29234 |  0.0218861   | 0.126125   |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -2.72844    | -1.67664 |  0.0936124   | 0.126125   |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.05  | future_var        | full             | dr_es_concentration | -0.0818662  | -2.04059 |  0.0412914   | 0.210203   |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.05  | future_tail_event | full             | dq_es               |  2.44546    |  2.77916 |  0.00544994  | 0.17018    |      88 |
| bonds    | baseline_2018 |      252 |        21 |       0.05  | future_tail_event | full             | dr_es_concentration | -8.47441    | -2.79137 |  0.00524858  | 0.17018    |      88 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_es         | dq_dr            | dq_es               | -0.0382001  | -1.71855 |  0.0856962   | 0.0447076  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_es         | dq_dr_current_es | dq_es               | -0.0382432  | -1.74206 |  0.0814979   | 0.0447379  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_var        | dq_only          | dq_es               | -0.0103123  | -2.02686 |  0.0426765   | 0.0693349  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_var        | dq_dr            | dq_es               | -0.0201328  | -2.23215 |  0.0256051   | 0.0886463  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0205851  | -2.45618 |  0.0140424   | 0.105349   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_rv_ann     | dq_dr_current_es | dq_es               | -0.129831   | -1.65753 |  0.0974129   | 0.0473386  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.115127   | -1.87126 |  0.0613089   | 0.0673675  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.113452   | -1.85702 |  0.0633083   | 0.0743367  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | dq_only          | dq_es               |  0.707934   |  1.86413 |  0.0623034   | 0.0498092  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | dq_dr            | dq_es               |  2.0621     |  3.19697 |  0.00138877  | 0.105782   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | dq_dr            | dr_es_concentration | -3.38886    | -2.36611 |  0.017976    | 0.105782   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | dq_dr_current_es | dq_es               |  2.13861    |  3.45608 |  0.000548102 | 0.178615   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | full             | dq_es               |  2.30651    |  2.76932 |  0.00561733  | 0.344843   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.05  | future_var        | dq_only          | dq_es               | -0.00574591 | -1.81974 |  0.0687982   | 0.0492377  |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.05  | future_tail_event | full             | dq_es               |  1.50261    |  1.88022 |  0.0600785   | 0.221497   |      86 |
| bonds    | baseline_2018 |      252 |        63 |       0.05  | future_tail_event | full             | dr_es_concentration | -6.49848    | -2.08823 |  0.0367772   | 0.221497   |      86 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_es         | dq_only          | dq_es               | -0.0206062  | -2.425   |  0.0153083   | 0.0566113  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_es         | dr_only          | dr_es_concentration | -0.056764   | -2.2081  |  0.0272375   | 0.0390653  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_es         | full             | dq_es               | -0.352826   | -3.29227 |  0.000993837 | 0.521433   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_es         | full             | dr_es_concentration |  0.488955   |  2.53253 |  0.0113242   | 0.521433   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_var        | dq_only          | dq_es               | -0.016338   | -2.75057 |  0.00594917  | 0.0912531  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0482046  | -2.55154 |  0.0107248   | 0.0722384  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_var        | full             | dq_es               | -0.20093    | -3.04244 |  0.00234671  | 0.517307   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_var        | full             | dr_es_concentration |  0.252863   |  2.07986 |  0.0375381   | 0.517307   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_rv_ann     | dq_only          | dq_es               | -0.104342   | -2.57795 |  0.00993874  | 0.0897939  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration | -0.331712   | -2.51685 |  0.0118409   | 0.0825265  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_rv_ann     | full             | dq_es               | -1.13522    | -3.20299 |  0.00136011  | 0.553587   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_mdd        | dq_only          | dq_es               | -0.0354833  | -2.27281 |  0.0230373   | 0.0772037  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_mdd        | dr_only          | dr_es_concentration | -0.106615   | -2.27652 |  0.0228152   | 0.0633822  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_mdd        | full             | dq_es               | -0.39071    | -2.7582  |  0.00581208  | 0.439236   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.025 | future_mdd        | full             | dr_es_concentration |  0.45166    |  1.67504 |  0.0939263   | 0.439236   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_es         | dq_only          | dq_es               | -0.0215672  | -2.65295 |  0.00797917  | 0.0880212  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_es         | dr_only          | dr_es_concentration | -0.0515414  | -1.97801 |  0.0479278   | 0.0491507  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_var        | dq_only          | dq_es               | -0.0148409  | -3.28188 |  0.00103119  | 0.157311   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_var        | dr_only          | dr_es_concentration | -0.0446735  | -2.17993 |  0.0292623   | 0.139365   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_rv_ann     | dq_only          | dq_es               | -0.143036   | -2.8646  |  0.00417535  | 0.0934057  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration | -0.398461   | -2.13091 |  0.0330965   | 0.0708713  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_mdd        | dq_only          | dq_es               | -0.0464809  | -2.25485 |  0.0241429   | 0.0733308  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_mdd        | dr_only          | dr_es_concentration | -0.124172   | -1.89571 |  0.0579989   | 0.0511681  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dq_only          | dq_es               | -0.917534   | -2.3049  |  0.0211721   | 0.0568578  |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -4.01861    | -3.00885 |  0.00262238  | 0.106639   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dq_dr            | dr_es_concentration | -4.59867    | -1.80536 |  0.0710186   | 0.107919   |      76 |
| bonds    | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | full             | dq_es               | -4.63101    | -1.97664 |  0.0480819   | 0.246854   |      76 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_es         | dq_only          | dq_es               | -0.028557   | -2.21135 |  0.0270117   | 0.120981   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_es         | dr_only          | dr_es_concentration | -0.0813232  | -2.46617 |  0.0136565   | 0.086886   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_es         | full             | dq_es               | -0.179776   | -2.25387 |  0.0242046   | 0.29713    |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_var        | dq_only          | dq_es               | -0.0188975  | -3.34855 |  0.000812358 | 0.278097   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0618617  | -3.56733 |  0.000360631 | 0.263915   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_rv_ann     | dq_only          | dq_es               | -0.120323   | -2.63701 |  0.00836408  | 0.160196   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration | -0.392231   | -3.05121 |  0.00227919  | 0.150753   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_rv_ann     | full             | dq_es               | -0.550941   | -1.94905 |  0.0512899   | 0.388539   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dq_only          | dq_es               | -0.0719885  | -1.87682 |  0.0605422   | 0.116943   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dr_only          | dr_es_concentration | -0.221498   | -1.94817 |  0.051394    | 0.0980434  |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_es         | dq_only          | dq_es               | -0.0274244  | -2.75277 |  0.00590927  | 0.15835    |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_es         | dr_only          | dr_es_concentration | -0.0605251  | -2.34345 |  0.0191063   | 0.0724119  |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_var        | dq_only          | dq_es               | -0.0153355  | -4.13545 |  3.54266e-05 | 0.272294   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_var        | dr_only          | dr_es_concentration | -0.0479195  | -2.55164 |  0.0107217   | 0.249611   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_rv_ann     | dq_only          | dq_es               | -0.157029   | -2.80691 |  0.00500185  | 0.14855    |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration | -0.418716   | -2.55861 |  0.0105093   | 0.0991632  |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_mdd        | dq_only          | dq_es               | -0.0803136  | -1.70958 |  0.087344    | 0.079248   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -3.32167    | -2.38485 |  0.0170863   | 0.0880016  |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dq_dr            | dr_es_concentration | -5.83385    | -2.29128 |  0.0219474   | 0.117332   |      74 |
| bonds    | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | full             | dq_es               | -4.49643    | -1.95266 |  0.0508594   | 0.246024   |      74 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_es         | full             | dr_es_concentration | -0.0626622  | -1.90193 |  0.0571806   | 0.0958042  |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_var        | full             | dr_es_concentration | -0.0346003  | -1.65631 |  0.0976587   | 0.124582   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_rv_ann     | full             | dr_es_concentration | -0.353899   | -2.37978 |  0.0173229   | 0.170285   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_mdd        | full             | dr_es_concentration | -0.0840883  | -1.99951 |  0.0455529   | 0.112492   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_tail_event | dq_dr            | dr_es_concentration | -1.2855     | -1.69256 |  0.0905394   | 0.022477   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_tail_event | full             | dq_es               |  1.21032    |  2.21193 |  0.0269716   | 0.134281   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -3.26738    | -3.23535 |  0.00121495  | 0.134281   |     113 |
| bonds    | full_2015     |      252 |        21 |       0.05  | future_var        | dq_dr            | dq_es               | -0.00821858 | -1.78282 |  0.0746151   | 0.0312776  |     113 |
| bonds    | full_2015     |      252 |        21 |       0.05  | future_tail_event | full             | dr_es_concentration | -4.17271    | -2.25596 |  0.0240732   | 0.154658   |     113 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_es         | full             | dq_es               |  0.033365   |  1.72338 |  0.0848196   | 0.226982   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_es         | full             | dr_es_concentration | -0.0951309  | -2.57551 |  0.0100092   | 0.226982   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_var        | dq_only          | dq_es               | -0.0131173  | -2.56035 |  0.0104568   | 0.133366   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0216824  | -1.64956 |  0.0990331   | 0.0618369  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_var        | dq_dr            | dq_es               | -0.0145237  | -2.36507 |  0.0180266   | 0.134595   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0138225  | -2.31951 |  0.0203676   | 0.158536   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_var        | full             | dr_es_concentration | -0.0300227  | -1.65161 |  0.0986133   | 0.319817   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | full             | dr_es_concentration | -0.433341   | -2.96244 |  0.00305214  | 0.278624   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | dr_only          | dr_es_concentration | -1.4015     | -1.66003 |  0.096908    | 0.0514877  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr            | dq_es               |  0.763048   |  1.70717 |  0.0877913   | 0.091511   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr            | dr_es_concentration | -2.78143    | -2.22393 |  0.0261532   | 0.091511   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr_current_es | dq_es               |  0.74139    |  1.68291 |  0.0923931   | 0.0960638  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr_current_es | dr_es_concentration | -2.57208    | -2.09179 |  0.0364577   | 0.0960638  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | full             | dq_es               |  2.0731     |  3.87971 |  0.00010458  | 0.245006   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.025 | future_tail_event | full             | dr_es_concentration | -6.45547    | -4.8601  |  1.17324e-06 | 0.245006   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_es         | dq_dr            | dq_es               | -0.0182623  | -2.00445 |  0.0450217   | 0.0627521  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_es         | dq_dr_current_es | dq_es               | -0.0171634  | -1.66306 |  0.0963012   | 0.0631869  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_var        | dq_only          | dq_es               | -0.00806768 | -2.13869 |  0.0324609   | 0.0742336  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_var        | dq_dr            | dq_es               | -0.0121434  | -2.4659  |  0.013667    | 0.0950165  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_var        | dq_dr_current_es | dq_es               | -0.00924089 | -1.6696  |  0.0949976   | 0.105215   |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_tail_event | dq_only          | dq_es               | -0.397866   | -1.67934 |  0.0930867   | 0.0277855  |     111 |
| bonds    | full_2015     |      252 |        63 |       0.05  | future_tail_event | full             | dr_es_concentration | -3.6238     | -2.42508 |  0.0153051   | 0.215937   |     111 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_es         | dq_only          | dq_es               | -0.0153989  | -2.35807 |  0.0183703   | 0.040705   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_es         | dr_only          | dr_es_concentration | -0.0632941  | -2.14745 |  0.0317578   | 0.0398718  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_es         | full             | dq_es               | -0.11397    | -3.55793 |  0.000373796 | 0.431943   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_var        | dq_only          | dq_es               | -0.0113513  | -2.62664 |  0.00862314  | 0.0572241  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0478804  | -2.32518 |  0.0200622   | 0.0590298  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_var        | full             | dq_es               | -0.068863   | -3.48583 |  0.000490606 | 0.436051   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | dq_only          | dq_es               | -0.0815353  | -2.75151 |  0.00593207  | 0.0636303  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration | -0.346374   | -2.38569 |  0.017047    | 0.0665787  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | full             | dq_es               | -0.421576   | -3.27065 |  0.001073    | 0.437522   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_mdd        | dq_only          | dq_es               | -0.0160986  | -1.80609 |  0.070905    | 0.0258568  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_mdd        | dr_only          | dr_es_concentration | -0.065845   | -1.65159 |  0.0986181   | 0.0250794  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.025 | future_mdd        | full             | dq_es               | -0.140207   | -2.78265 |  0.00539171  | 0.355237   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_es         | dq_only          | dq_es               | -0.0216299  | -2.53262 |  0.0113213   | 0.0654127  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_es         | dq_dr            | dq_es               | -0.0269473  | -2.12981 |  0.033187    | 0.0730836  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_var        | dq_only          | dq_es               | -0.0137324  | -3.05373 |  0.00226017  | 0.092595   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_var        | dq_dr            | dq_es               | -0.015542   | -2.68616 |  0.00722783  | 0.0957152  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | dq_only          | dq_es               | -0.145078   | -2.63058 |  0.00852398  | 0.0634232  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | dq_dr            | dq_es               | -0.161932   | -1.93047 |  0.0535485   | 0.065084   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | full             | dr_es_concentration | -1.61268    | -1.77281 |  0.0762595   | 0.333293   |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_mdd        | dq_only          | dq_es               | -0.0283032  | -1.75535 |  0.0791996   | 0.0251619  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_tail_event | dq_only          | dq_es               | -0.943219   | -2.27961 |  0.022631    | 0.0451919  |     103 |
| bonds    | full_2015     |      504 |        21 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -3.16541    | -1.81596 |  0.0693764   | 0.0461791  |     103 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_es         | dq_only          | dq_es               | -0.0180682  | -2.13404 |  0.0328396   | 0.068607   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_es         | dr_only          | dr_es_concentration | -0.0902516  | -2.72605 |  0.00640968  | 0.0975404  |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_es         | dq_dr_current_es | dr_es_concentration | -0.133759   | -2.08663 |  0.0369219   | 0.116668   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_var        | dq_only          | dq_es               | -0.0154337  | -3.8853  |  0.000102202 | 0.228161   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0701812  | -4.06409 |  4.82195e-05 | 0.268832   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_var        | dq_dr_current_es | dr_es_concentration | -0.0716602  | -1.97441 |  0.0483348   | 0.287242   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_var        | full             | dq_es               | -0.0266736  | -1.67514 |  0.0939059   | 0.451909   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dq_only          | dq_es               | -0.0854072  | -2.61925 |  0.00881244  | 0.106073   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration | -0.443081   | -3.34738 |  0.000815807 | 0.162675   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration | -0.559643   | -1.82834 |  0.0674986   | 0.166059   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dq_dr_current_es | dr_es_concentration | -0.635778   | -2.15933 |  0.0308246   | 0.174074   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dr_es_concentration | -0.32255    | -1.85184 |  0.0640489   | 0.0638562  |     102 |
| bonds    | full_2015     |      504 |        63 |       0.025 | future_tail_event | full             | dr_es_concentration | -9.9616     | -3.03905 |  0.00237322  | 0.329      |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_es         | dq_only          | dq_es               | -0.03155    | -3.23889 |  0.00119998  | 0.160813   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_es         | dq_dr            | dq_es               | -0.035658   | -2.31657 |  0.0205273   | 0.16592    |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_var        | dq_only          | dq_es               | -0.018723   | -4.1895  |  2.79564e-05 | 0.215244   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_var        | dr_only          | dr_es_concentration | -0.0436964  | -1.88484 |  0.0594509   | 0.0962297  |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_var        | dq_dr            | dq_es               | -0.01739    | -2.87419 |  0.00405066  | 0.217287   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | dq_only          | dq_es               | -0.175614   | -3.1552  |  0.00160388  | 0.14072    |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | dq_dr            | dq_es               | -0.170105   | -1.86588 |  0.0620586   | 0.14098    |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | full             | dr_es_concentration | -1.22476    | -2.29147 |  0.0219364   | 0.409471   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_mdd        | full             | dq_es               |  0.277944   |  1.97644 |  0.0481049   | 0.378844   |     102 |
| bonds    | full_2015     |      504 |        63 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -3.0756     | -1.6795  |  0.0930546   | 0.0570453  |     102 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_es         | dr_only          | dr_es_concentration |  0.0219316  |  1.994   |  0.0461521   | 0.0104465  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_es         | dq_dr            | dr_es_concentration |  0.0439038  |  2.38449 |  0.0171027   | 0.0235173  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_es         | dq_dr_current_es | dq_es               | -0.0529242  | -1.8193  |  0.0688659   | 0.0278497  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_var        | dr_only          | dr_es_concentration |  0.0177815  |  1.87724 |  0.0604854   | 0.0147935  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_var        | dq_dr            | dr_es_concentration |  0.0358141  |  2.7802  |  0.00543257  | 0.0337595  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0495088  | -2.23032 |  0.0257265   | 0.0441257  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration |  0.210005   |  2.88302 |  0.00393887  | 0.0561134  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration |  0.303771   |  4.04811 |  5.16325e-05 | 0.0700589  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_rv_ann     | dq_dr_current_es | dq_es               | -0.296216   | -1.89228 |  0.0584538   | 0.0823851  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.0702192  | -2.22775 |  0.0258969   | 0.0507352  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration |  0.0928563  |  3.10125 |  0.00192708  | 0.0507352  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.151058   | -2.74275 |  0.00609267  | 0.0689075  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_mdd        | full             | dq_es               | -0.301027   | -1.79602 |  0.0724917   | 0.167646   |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -2.52929    | -3.12627 |  0.00177041  | 0.161678   |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_es         | dq_dr            | dr_es_concentration |  0.0240399  |  1.91947 |  0.0549245   | 0.0149885  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_var        | dq_dr            | dr_es_concentration |  0.0234585  |  2.17113 |  0.0299211   | 0.0374178  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration |  0.224175   |  2.90678 |  0.00365174  | 0.0540142  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_rv_ann     | dq_dr            | dr_es_concentration |  0.261714   |  3.2599  |  0.00111451  | 0.0565458  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_mdd        | dq_dr            | dr_es_concentration |  0.0759189  |  2.0194  |  0.0434458   | 0.0304123  |      88 |
| shares   | baseline_2018 |      252 |        21 |       0.05  | future_tail_event | full             | dr_es_concentration | -2.34422    | -1.93458 |  0.0530413   | 0.174737   |      88 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_es         | full             | dr_es_concentration | -0.156445   | -2.04885 |  0.0404769   | 0.175784   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0373099  | -1.7832  |  0.0745536   | 0.0417692  |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_var        | full             | dr_es_concentration | -0.0777048  | -2.26814 |  0.0233208   | 0.194377   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_rv_ann     | dq_dr_current_es | dq_es               | -0.317882   | -2.00413 |  0.0450565   | 0.04208    |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_rv_ann     | full             | dr_es_concentration | -0.553178   | -1.98111 |  0.0475793   | 0.216799   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.121941   | -1.94642 |  0.0516043   | 0.0481542  |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.283249   | -2.81609 |  0.00486128  | 0.0771463  |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_mdd        | full             | dr_es_concentration | -0.424218   | -2.06601 |  0.0388271   | 0.208332   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.025 | future_tail_event | full             | dr_es_concentration | -2.6288     | -3.69953 |  0.000215998 | 0.383962   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_es         | full             | dr_es_concentration | -0.130355   | -2.27065 |  0.0231679   | 0.170723   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_var        | dq_dr_current_es | dq_es               | -0.019343   | -1.70455 |  0.0882784   | 0.061005   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_var        | full             | dr_es_concentration | -0.076164   | -2.07887 |  0.0376289   | 0.22448    |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_rv_ann     | full             | dr_es_concentration | -0.708968   | -2.15095 |  0.0314799   | 0.194284   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_mdd        | dq_dr            | dq_es               | -0.113259   | -1.95187 |  0.0509541   | 0.0460594  |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_mdd        | dq_dr_current_es | dq_es               | -0.144156   | -2.02681 |  0.042682    | 0.0494371  |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_mdd        | full             | dr_es_concentration | -0.505479   | -1.93954 |  0.0524354   | 0.194821   |      86 |
| shares   | baseline_2018 |      252 |        63 |       0.05  | future_tail_event | full             | dr_es_concentration | -1.78025    | -1.7016  |  0.088831    | 0.148533   |      86 |
| shares   | baseline_2018 |      504 |        21 |       0.025 | future_tail_event | dq_dr            | dq_es               |  0.844935   |  2.8018  |  0.00508188  | 0.0760108  |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.025 | future_tail_event | dq_dr            | dr_es_concentration | -2.39137    | -4.44259 |  8.88806e-06 | 0.0760108  |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.025 | future_tail_event | dq_dr_current_es | dq_es               |  0.901497   |  1.88107 |  0.059962    | 0.0764313  |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.025 | future_tail_event | dq_dr_current_es | dr_es_concentration | -2.24043    | -2.39047 |  0.0168269   | 0.0764313  |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -2.68666    | -1.8618  |  0.0626316   | 0.185779   |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -1.37603    | -3.04802 |  0.00230356  | 0.0446603  |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dq_dr            | dq_es               |  0.777957   |  2.61885 |  0.0088228   | 0.120455   |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dq_dr            | dr_es_concentration | -1.93849    | -3.88888 |  0.000100709 | 0.120455   |      76 |
| shares   | baseline_2018 |      504 |        21 |       0.05  | future_tail_event | dq_dr_current_es | dq_es               |  1.15538    |  3.24613 |  0.00116985  | 0.147347   |      76 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_es         | dr_only          | dr_es_concentration | -0.0749303  | -2.30351 |  0.02125     | 0.0197329  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_es         | dq_dr            | dr_es_concentration | -0.115186   | -2.41903 |  0.015562    | 0.0251674  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration | -0.0531863  | -2.32726 |  0.0199515   | 0.0651212  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_var        | dq_dr            | dr_es_concentration | -0.0766985  | -2.78145 |  0.00541171  | 0.0772648  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_var        | dq_dr_current_es | dr_es_concentration | -0.116082   | -2.48156 |  0.0130808   | 0.105719   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dq_only          | dq_es               | -0.107892   | -1.92264 |  0.0545257   | 0.0571279  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dr_only          | dr_es_concentration | -0.426598   | -3.37466 |  0.000739058 | 0.122943   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration | -0.447647   | -2.29719 |  0.0216081   | 0.123229   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dr_es_concentration | -0.716348   | -2.61103 |  0.00902701  | 0.162099   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_tail_event | dq_dr            | dq_es               |  0.78979    |  2.18664 |  0.0287685   | 0.0675628  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.025 | future_tail_event | dq_dr            | dr_es_concentration | -1.59914    | -2.60643 |  0.00914918  | 0.0675628  |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dq_only          | dq_es               |  0.527239   |  2.11386 |  0.0345274   | 0.103242   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dq_dr            | dq_es               |  0.660912   |  2.40128 |  0.0163381   | 0.159712   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dq_dr            | dr_es_concentration | -0.968215   | -2.57406 |  0.0100514   | 0.159712   |      74 |
| shares   | baseline_2018 |      504 |        63 |       0.05  | future_tail_event | dq_dr_current_es | dq_es               |  0.806224   |  2.96227 |  0.00305384  | 0.171213   |      74 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_es         | dr_only          | dr_es_concentration |  0.0265676  |  2.72576 |  0.00641532  | 0.0212227  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_es         | dq_dr            | dq_es               | -0.0324757  | -1.68407 |  0.0921673   | 0.0384443  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_es         | dq_dr            | dr_es_concentration |  0.0500603  |  2.66208 |  0.00776584  | 0.0384443  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_es         | dq_dr_current_es | dq_es               | -0.0594989  | -2.44075 |  0.0146566   | 0.0434662  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_var        | dr_only          | dr_es_concentration |  0.022267   |  2.90698 |  0.0036494   | 0.0318115  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_var        | dq_dr            | dq_es               | -0.0276978  | -1.99719 |  0.0458043   | 0.0585424  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_var        | dq_dr            | dr_es_concentration |  0.0423034  |  3.31673 |  0.000910792 | 0.0585424  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0531298  | -2.94035 |  0.00327841  | 0.0680335  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration |  0.208634   |  3.7931  |  0.000148776 | 0.0688262  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_rv_ann     | dq_dr            | dq_es               | -0.190166   | -2.31726 |  0.0204893   | 0.09988    |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration |  0.346199   |  4.32032 |  1.55802e-05 | 0.09988    |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_rv_ann     | dq_dr_current_es | dq_es               | -0.371005   | -2.94618 |  0.00321721  | 0.111707   |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_mdd        | dr_only          | dr_es_concentration |  0.054099   |  2.48849 |  0.0128286   | 0.0363039  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.0789192  | -2.39756 |  0.0165048   | 0.0782607  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration |  0.111189   |  3.76087 |  0.000169321 | 0.0782607  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.154393   | -3.23296 |  0.00122515  | 0.0944214  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_mdd        | full             | dq_es               | -0.230218   | -1.70082 |  0.0889769   | 0.188957   |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_tail_event | dq_only          | dq_es               | -0.582845   | -3.04644 |  0.00231572  | 0.0472846  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_tail_event | dr_only          | dr_es_concentration | -0.643122   | -2.66674 |  0.00765905  | 0.0539871  |     124 |
| shares   | full_2015     |      252 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -2.42941    | -3.29147 |  0.000996641 | 0.1713     |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_es         | dr_only          | dr_es_concentration |  0.0240686  |  3.15055 |  0.00162962  | 0.0339632  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_es         | dq_dr            | dq_es               | -0.0180485  | -1.7732  |  0.0761963   | 0.0466794  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_es         | dq_dr            | dr_es_concentration |  0.0369779  |  3.75471 |  0.000173545 | 0.0466794  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_var        | dr_only          | dr_es_concentration |  0.020407   |  3.16995 |  0.00152465  | 0.0650044  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_var        | dq_dr            | dq_es               | -0.0173661  | -2.07387 |  0.0380911   | 0.0963484  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_var        | dq_dr            | dr_es_concentration |  0.0328281  |  4.34967 |  1.3634e-05  | 0.0963484  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_var        | dq_dr_current_es | dq_es               | -0.0208504  | -2.00796 |  0.0446474   | 0.0979141  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration |  0.228277   |  4.21168 |  2.53478e-05 | 0.0752929  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_rv_ann     | dq_dr            | dq_es               | -0.133357   | -2.00524 |  0.0449379   | 0.0924021  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_rv_ann     | dq_dr            | dr_es_concentration |  0.323661   |  4.95065 |  7.39665e-07 | 0.0924021  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_rv_ann     | dq_dr_current_es | dr_es_concentration |  0.293837   |  1.89322 |  0.0583288   | 0.0927658  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_mdd        | dr_only          | dr_es_concentration |  0.0606488  |  2.68269 |  0.00730335  | 0.0416931  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_mdd        | dq_dr            | dq_es               | -0.0560894  | -1.9415  |  0.052198    | 0.0654368  |     124 |
| shares   | full_2015     |      252 |        21 |       0.05  | future_mdd        | dq_dr            | dr_es_concentration |  0.100767   |  3.57694 |  0.000347638 | 0.0654368  |     124 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_es         | dq_dr            | dr_es_concentration |  0.0309965  |  1.71988 |  0.0854539   | 0.0134848  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_es         | dq_dr_current_es | dq_es               | -0.0620417  | -2.28496 |  0.0223154   | 0.0239378  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_es         | full             | dr_es_concentration | -0.174369   | -2.65208 |  0.00799978  | 0.252994   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration |  0.0189592  |  1.66836 |  0.0952434   | 0.0512968  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_var        | dq_dr            | dr_es_concentration |  0.0288501  |  2.44753 |  0.0143838   | 0.0655381  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_var        | dq_dr_current_es | dq_es               | -0.0486164  | -2.7392  |  0.00615896  | 0.105403   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_var        | full             | dr_es_concentration | -0.0843589  | -2.48121 |  0.0130936   | 0.38495    |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration |  0.133613   |  1.78016 |  0.07505     | 0.0344466  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | dq_dr            | dq_es               | -0.16157    | -2.20675 |  0.0273312   | 0.0614619  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration |  0.250771   |  3.04527 |  0.00232471  | 0.0614619  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | dq_dr_current_es | dq_es               | -0.365534   | -2.81553 |  0.00486966  | 0.0797914  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_rv_ann     | full             | dr_es_concentration | -0.653509   | -2.63655 |  0.00837534  | 0.327002   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.148453   | -2.55417 |  0.0106441   | 0.0680902  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration |  0.15886    |  2.34571 |  0.0189908   | 0.0680902  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.30055    | -3.24941 |  0.00115644  | 0.0929942  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_mdd        | full             | dr_es_concentration | -0.484645   | -2.49319 |  0.0126602   | 0.365513   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_only          | dq_es               | -0.787578   | -1.81728 |  0.0691739   | 0.0913702  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_tail_event | dr_only          | dr_es_concentration | -0.698654   | -1.76571 |  0.0774439   | 0.0676962  |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr_current_es | dq_es               | -1.83168    | -2.52626 |  0.0115284   | 0.142712   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_tail_event | dq_dr_current_es | dr_es_concentration | -1.31516    | -1.67114 |  0.0946944   | 0.142712   |     122 |
| shares   | full_2015     |      252 |        63 |       0.025 | future_tail_event | full             | dr_es_concentration | -1.8561     | -2.06275 |  0.039136    | 0.275625   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_es         | dq_dr            | dr_es_concentration |  0.0317209  |  2.45538 |  0.0140736   | 0.0352587  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_es         | full             | dr_es_concentration | -0.0939342  | -1.69896 |  0.089326    | 0.288813   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_var        | dr_only          | dr_es_concentration |  0.0174485  |  2.05524 |  0.0398556   | 0.0880411  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_var        | dq_dr            | dq_es               | -0.0155036  | -1.81686 |  0.0692389   | 0.133319   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_var        | dq_dr            | dr_es_concentration |  0.0286317  |  3.10561 |  0.00189884  | 0.133319   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_var        | dq_dr_current_es | dq_es               | -0.0195899  | -1.91981 |  0.0548816   | 0.137305   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration |  0.161679   |  2.09467 |  0.0362002   | 0.0460023  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_rv_ann     | dq_dr            | dq_es               | -0.156938   | -2.02976 |  0.0423808   | 0.0742365  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_rv_ann     | dq_dr            | dr_es_concentration |  0.274883   |  3.53135 |  0.000413447 | 0.0742365  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_rv_ann     | dq_dr_current_es | dq_es               | -0.195744   | -1.96889 |  0.0489653   | 0.0764243  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_rv_ann     | full             | dr_es_concentration | -0.56235    | -1.94142 |  0.052207    | 0.319003   |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_mdd        | dq_dr            | dq_es               | -0.144897   | -2.60727 |  0.00912686  | 0.0820013  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_mdd        | dq_dr            | dr_es_concentration |  0.177966   |  2.91084 |  0.00360456  | 0.0820013  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_mdd        | dq_dr_current_es | dq_es               | -0.163689   | -2.5514  |  0.0107292   | 0.0832549  |     122 |
| shares   | full_2015     |      252 |        63 |       0.05  | future_tail_event | dr_only          | dr_es_concentration | -0.512804   | -2.08613 |  0.036967    | 0.0590105  |     122 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_es         | dq_only          | dq_es               |  0.0166537  |  1.76392 |  0.0777456   | 0.00928005 |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_es         | dr_only          | dr_es_concentration |  0.0397195  |  2.02778 |  0.0425825   | 0.0285584  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_es         | dq_dr            | dr_es_concentration |  0.0510339  |  1.70759 |  0.0877133   | 0.0304465  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_var        | dr_only          | dr_es_concentration |  0.0316312  |  2.32778 |  0.0199239   | 0.0388733  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_var        | dq_dr            | dr_es_concentration |  0.0455592  |  2.15673 |  0.0310264   | 0.045014   |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | dq_only          | dq_es               |  0.109625   |  2.00646 |  0.0448074   | 0.0213025  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration |  0.286168   |  3.14757 |  0.00164634  | 0.0785328  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration |  0.390975   |  2.78725 |  0.00531579  | 0.0871151  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_mdd        | dr_only          | dr_es_concentration |  0.0725711  |  2.16842 |  0.0301265   | 0.0397463  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration |  0.122168   |  2.36455 |  0.018052    | 0.0548714  |     112 |
| shares   | full_2015     |      504 |        21 |       0.025 | future_tail_event | full             | dr_es_concentration | -4.85688    | -3.74524 |  0.00018022  | 0.18456    |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_es         | dq_only          | dq_es               |  0.0165918  |  1.77658 |  0.0756381   | 0.0183197  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_es         | dr_only          | dr_es_concentration |  0.0361069  |  2.7091  |  0.00674654  | 0.0465077  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_es         | dq_dr            | dr_es_concentration |  0.0376085  |  2.58922 |  0.00961942  | 0.0466104  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_var        | dr_only          | dr_es_concentration |  0.0288404  |  3.22823 |  0.00124558  | 0.0798903  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_var        | dq_dr            | dr_es_concentration |  0.0362018  |  3.06844 |  0.00215182  | 0.0865333  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_var        | dq_dr_current_es | dr_es_concentration |  0.0471486  |  1.79299 |  0.0729752   | 0.0890583  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | dq_only          | dq_es               |  0.148755   |  2.24344 |  0.0248683   | 0.0363465  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration |  0.327532   |  3.64046 |  0.000272153 | 0.0944587  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_rv_ann     | dq_dr            | dr_es_concentration |  0.343984   |  3.17039 |  0.00152235  | 0.0947628  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_mdd        | dr_only          | dr_es_concentration |  0.0883651  |  2.57493 |  0.010026    | 0.0541074  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_mdd        | dq_dr            | dr_es_concentration |  0.110342   |  2.52808 |  0.0114687   | 0.058379   |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_tail_event | dq_only          | dq_es               |  0.519696   |  2.0011  |  0.045382    | 0.0389123  |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_tail_event | dq_dr            | dq_es               |  0.886819   |  2.83868 |  0.00453005  | 0.063696   |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_tail_event | dq_dr            | dr_es_concentration | -0.756522   | -1.75623 |  0.0790485   | 0.063696   |     112 |
| shares   | full_2015     |      504 |        21 |       0.05  | future_tail_event | dq_dr_current_es | dq_es               |  1.19996    |  3.78013 |  0.000156747 | 0.0995372  |     112 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_es         | dr_only          | dr_es_concentration |  0.0434576  |  1.6588  |  0.0971559   | 0.0319287  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_var        | dr_only          | dr_es_concentration |  0.0315155  |  2.25282 |  0.0242706   | 0.0883093  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_var        | dq_dr            | dr_es_concentration |  0.0429176  |  2.22485 |  0.0260913   | 0.0969743  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dr_only          | dr_es_concentration |  0.262502   |  2.51355 |  0.0119523   | 0.0814251  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_rv_ann     | dq_dr            | dr_es_concentration |  0.394401   |  2.42477 |  0.0153181   | 0.0968354  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_mdd        | dq_dr            | dq_es               | -0.125273   | -1.89031 |  0.058716    | 0.073351   |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_mdd        | dq_dr            | dr_es_concentration |  0.241679   |  2.17916 |  0.02932     | 0.073351   |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_mdd        | dq_dr_current_es | dq_es               | -0.165162   | -1.75549 |  0.0791754   | 0.0788061  |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_mdd        | full             | dr_es_concentration | -0.511909   | -2.04782 |  0.0405778   | 0.408741   |     110 |
| shares   | full_2015     |      504 |        63 |       0.025 | future_tail_event | full             | dr_es_concentration | -3.38856    | -2.36158 |  0.0181972   | 0.17712    |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_es         | dr_only          | dr_es_concentration |  0.0388604  |  2.27726 |  0.0227708   | 0.0580229  |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_es         | dq_dr            | dr_es_concentration |  0.0392069  |  2.07631 |  0.0378652   | 0.0580281  |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_var        | dr_only          | dr_es_concentration |  0.0267366  |  2.59491 |  0.00946158  | 0.130092   |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_var        | dq_dr            | dr_es_concentration |  0.0348167  |  2.56135 |  0.0104265   | 0.143445   |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | dq_only          | dq_es               |  0.131658   |  1.82882 |  0.0674264   | 0.0346132  |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | dr_only          | dr_es_concentration |  0.306089   |  3.09187 |  0.001989    | 0.100776   |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_rv_ann     | dq_dr            | dr_es_concentration |  0.345824   |  2.68805 |  0.00718711  | 0.102685   |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_mdd        | dr_only          | dr_es_concentration |  0.154075   |  1.99856 |  0.0456564   | 0.0628845  |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_mdd        | dq_dr            | dr_es_concentration |  0.230178   |  2.48933 |  0.0127984   | 0.0801277  |     110 |
| shares   | full_2015     |      504 |        63 |       0.05  | future_tail_event | dq_dr_current_es | dq_es               |  0.559919   |  1.76524 |  0.0775228   | 0.0760454  |     110 |
