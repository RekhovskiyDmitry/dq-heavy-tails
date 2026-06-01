# Literature and Formulas for DQ / DR / Heavy Tails

Date: 2026-06-01

Purpose: зафиксировать проверенную теоретическую базу для курсовой, отдельно от переписывания репозитория. Формулы ниже даны в соглашении авторов DQ: \(X_i\) - потери, \(\alpha\in(0,1)\) - малая хвостовая вероятность, например \(0.025\), а не доверительный уровень \(0.975\).

## 1. Проверенные источники

### DQ

1. Han, X., Lin, L., Wang, R. (2025). "Diversification quotients: Quantifying diversification via risk measures". *Management Science*, 71(9), 7990-8006. DOI: https://doi.org/10.1287/mnsc.2023.00513. Препринт: https://arxiv.org/abs/2206.13679.  
   Это первоисточник DQ. Проверены определение DQ, аксиомы, связь с VaR/ES, диапазоны и интерпретация.

2. Han, X., Lin, L., Wang, R. (2023). "Diversification quotients based on VaR and ES". *Insurance: Mathematics and Economics*, 113, 185-197. DOI: https://doi.org/10.1016/j.insmatheco.2023.08.006. Препринт: https://arxiv.org/abs/2301.03517.  
   Удобный источник для формул DQ на VaR/ES, специальных значений, больших портфелей, эллиптических и MRV-моделей.

3. Han, X., Lin, L., Zhao, M. (2025). "Empirical estimator of diversification quotient". arXiv: https://arxiv.org/abs/2506.20385.  
   Это не первоисточник DQ, а свежий препринт по эмпирическим оценкам DQ. Полезен для проверки, что простая plug-in/эмпирическая оценка DQ должна быть сформулирована аккуратно.

Важно: для самого определения DQ правильная ссылка - Han-Lin-Wang (2025). Han-Lin-Zhao (2025) относится к эмпирическим оценкам и может использоваться только как источник для будущего улучшения estimator-части.

### DR и риск-меры

4. Choueifaty, Y., Coignard, Y. (2008). "Toward Maximum Diversification". *The Journal of Portfolio Management*, 35(1), 40-45. DOI: https://doi.org/10.3905/jpm.2008.35.1.40.  
   Классический источник по volatility Diversification Ratio.

5. Artzner, P., Delbaen, F., Eber, J.-M., Heath, D. (1999). "Coherent Measures of Risk". *Mathematical Finance*, 9(3), 203-228. DOI: https://doi.org/10.1111/1467-9965.00068.  
   База для когерентных риск-мер; нужна для ES и субаддитивности.

6. Acerbi, C., Tasche, D. (2002). "On the coherence of expected shortfall". *Journal of Banking & Finance*, 26(7), 1487-1503. DOI: https://doi.org/10.1016/S0378-4266(02)00283-2.  
   Источник по ES как когерентной альтернативе VaR.

### EVT, POT, heavy tails

7. Hill, B. M. (1975). "A Simple General Approach to Inference About the Tail of a Distribution". *The Annals of Statistics*, 3(5), 1163-1174. DOI: https://doi.org/10.1214/aos/1176343247.  
   Первоисточник Hill-estimator.

8. Pickands, J. (1975). "Statistical Inference Using Extreme Order Statistics". *The Annals of Statistics*, 3(1), 119-131. DOI: https://doi.org/10.1214/aos/1176343003.  
   Источник Pickands estimator и EVT-логики через экстремальные порядковые статистики.

9. Balkema, A. A., de Haan, L. (1974). "Residual Life Time at Great Age". *The Annals of Probability*, 2(5), 792-804. DOI: https://doi.org/10.1214/aop/1176996548.  
   Одна из основ теоремы Pickands-Balkema-de Haan для POT/GPD.

10. Dekkers, A. L. M., Einmahl, J. H. J., de Haan, L. (1989). "A Moment Estimator for the Index of an Extreme-Value Distribution". *The Annals of Statistics*, 17(4), 1833-1855. DOI: https://doi.org/10.1214/aos/1176347397.  
    Источник moment estimator, который используется рядом с Hill.

11. Embrechts, P., Kluppelberg, C., Mikosch, T. (1997). *Modelling Extremal Events for Insurance and Finance*. Springer. DOI: https://doi.org/10.1007/978-3-642-33483-2.  
    Базовый учебник по EVT, regular variation, finance/insurance tails.

12. de Haan, L., Ferreira, A. (2006). *Extreme Value Theory: An Introduction*. Springer. DOI: https://doi.org/10.1007/0-387-34471-3.  
    Строгая EVT-база для tail index и POT.

13. McNeil, A. J., Frey, R., Embrechts, P. (2015). *Quantitative Risk Management: Concepts, Techniques and Tools*. 2nd ed., Princeton University Press. ISBN: 978-0-691-16627-8.  
    Практическая база по VaR/ES, EVT и финансовым хвостам.

14. Mainik, G., Embrechts, P. (2013). "Diversification in heavy-tailed portfolios: properties and pitfalls". *Annals of Actuarial Science*, 7(1), 26-45. DOI: https://doi.org/10.1017/S1748499512000280.  
    Полезно для осторожной формулировки о диверсификации при тяжелых хвостах.

15. Ibragimov, R., Jaffee, D., Walden, J. (2011). "Diversification disasters". *Journal of Financial Economics*, 99(2), 333-348. DOI: https://doi.org/10.1016/j.jfineco.2010.08.015.  
    Ключевая статья о том, что при очень тяжелых хвостах диверсификация может ухудшать tail risk.

16. Ibragimov, R. (2009). "Portfolio diversification and value at risk under thick-tailedness". *Quantitative Finance*, 9(5), 565-580. DOI: https://doi.org/10.1080/14697680802629384.  
    Релевантно для тезиса о порогах tail index и VaR.

17. Ibragimov, M., Ibragimov, R., Prokhorov, A. (2017). *Heavy Tails and Copulas: Topics in Dependence Modelling in Economics and Finance*. World Scientific. DOI: https://doi.org/10.1142/9644.  
    Релевантно как обобщающая книга по heavy tails, dependence, copulas и финансовой диверсификации.

## 2. Формулы DQ, которые надо использовать

### VaR и ES

Для потерь \(X\):

```latex
\operatorname{VaR}_{\alpha}(X)
= \inf\{x\in\mathbb{R}: \mathbb{P}(X\le x)\ge 1-\alpha\},
\qquad \alpha\in[0,1).
```

```latex
\operatorname{ES}_{\alpha}(X)
= \frac{1}{\alpha}\int_{0}^{\alpha}\operatorname{VaR}_{u}(X)\,du,
\qquad \alpha\in(0,1).
```

Пояснение для курсовой: \(\alpha=0.025\) соответствует уровню 97.5%. В тексте нельзя одновременно писать "\(\alpha=0.975\)" и использовать формулы DQ из Han-Lin-Wang.

### Общее определение DQ

Пусть \(\rho=(\rho_\alpha)_{\alpha\in I}\), \(I=(0,\bar\alpha)\), - семейство риск-мер, убывающее по \(\alpha\). Для портфеля потерь \(\mathbf X=(X_1,\ldots,X_n)\):

```latex
\operatorname{DQ}^{\rho}_{\alpha}(\mathbf X)
= \frac{\alpha^*}{\alpha},
\qquad
\alpha^*
= \inf\left\{\beta\in I:
\rho_{\beta}\left(\sum_{i=1}^{n}X_i\right)
\le
\sum_{i=1}^{n}\rho_{\alpha}(X_i)
\right\},
```

с соглашением \(\inf(\varnothing)=\bar\alpha\).

Интерпретация: \(\alpha^*\) - хвостовой уровень, при котором риск объединенного портфеля не превышает сумму одиночных капиталов на уровне \(\alpha\). Поэтому DQ измеряет выигрыш в горизонтальном направлении по параметру risk level. Если диверсификация сильная, \(\alpha^*<\alpha\) и DQ меньше 1. Если хвостовые события концентрируются вместе, DQ близок к 1. Для ES при стандартных условиях диапазон \([0,1]\); для VaR диапазон может быть \([0,\min\{n,1/\alpha\}]\).

### DQ на VaR

Если \(S=\sum_i X_i\), \(F_S\) - распределение \(S\), то в удобном непрерывном случае:

```latex
\operatorname{DQ}^{\operatorname{VaR}}_{\alpha}(\mathbf X)
=
\frac{1}{\alpha}
\mathbb{P}\left(
S >
\sum_{i=1}^{n}\operatorname{VaR}_{\alpha}(X_i)
\right).
```

Более общая формула через \(F_S\):

```latex
\operatorname{DQ}^{\operatorname{VaR}}_{\alpha}(\mathbf X)
=
\frac{1-F_S\left(\sum_{i=1}^{n}\operatorname{VaR}_{\alpha}(X_i)\right)}
{\alpha}.
```

Эту формулу стоит включить в курсовую, потому что она сразу показывает отличие DQ от DR: DQ смотрит, насколько редким стало превышение суммы одиночных VaR.

### DQ на ES

Точное определение остается тем же, но с \(\rho_\alpha=\operatorname{ES}_\alpha\):

```latex
\operatorname{DQ}^{\operatorname{ES}}_{\alpha}(\mathbf X)
= \frac{\alpha^*}{\alpha},
\qquad
\alpha^*
= \inf\left\{\beta\in(0,1):
\operatorname{ES}_{\beta}(S)
\le
\sum_{i=1}^{n}\operatorname{ES}_{\alpha}(X_i)
\right\}.
```

У Han-Lin-Wang также есть вычислительная формула:

```latex
\operatorname{DQ}^{\operatorname{ES}}_{\alpha}(\mathbf X)
=
\frac{1}{\alpha}
\min_{r>0}
\mathbb{E}
\left[
\left(
r\left(S-\sum_{i=1}^{n}\operatorname{ES}_{\alpha}(X_i)\right)+1
\right)_+
\right],
```

если \(\mathbb{P}(S>\sum_i\operatorname{ES}_\alpha(X_i))>0\); иначе DQ равен 0.

Для курсовой достаточно включить определение через \(\alpha^*\). Формулу с минимумом по \(r\) можно дать в методическом приложении как источник для будущего улучшения эмпирического кода.

## 3. DR: две разные конвенции

### Классический volatility Diversification Ratio

У Choueifaty-Coignard:

```latex
\operatorname{DR}_{\mathrm{vol}}(w)
=
\frac{w^\top\sigma}
{\sqrt{w^\top\Sigma w}},
```

где \(\sigma_i=\sqrt{\Sigma_{ii}}\). Здесь большее значение означает лучшую диверсификацию.

### Risk-ratio / concentration ratio в DQ-литературе

В DQ-статьях для риск-меры \(\phi\) используется отношение:

```latex
\operatorname{DR}^{\phi}(\mathbf X)
=
\frac{\phi\left(\sum_{i=1}^{n}X_i\right)}
{\sum_{i=1}^{n}\phi(X_i)}.
```

Здесь меньшее значение означает лучшую диверсификацию. Для ES и весов \(w_i\ge0\):

```latex
\operatorname{CR}_{\operatorname{ES},\alpha}(w)
=
\frac{\operatorname{ES}_{\alpha}\left(\sum_{i=1}^{n}w_iL_i\right)}
{\sum_{i=1}^{n}w_i\operatorname{ES}_{\alpha}(L_i)}.
```

Текущий код считает именно это отношение и называет его `dr_es_concentration`. В курсовой лучше не называть эту величину просто "классический DR" без уточнения. Безопасная формулировка: "ES concentration ratio / risk-measure DR in the Han-Lin-Wang convention". Если нужен Choueifaty-style DR, надо брать обратную величину для ES:

```latex
\operatorname{DR}^{\mathrm{classic}}_{\operatorname{ES},\alpha}(w)
=
\frac{\sum_i w_i\operatorname{ES}_{\alpha}(L_i)}
{\operatorname{ES}_{\alpha}\left(\sum_i w_iL_i\right)}
=
\frac{1}{\operatorname{CR}_{\operatorname{ES},\alpha}(w)}.
```

## 4. EVT и tail index

Пусть положительные потери \(L\) имеют регулярно меняющийся хвост:

```latex
\mathbb{P}(L>x)=\bar F(x)=x^{-\alpha}\ell(x),
\qquad x\to\infty,
```

где \(\ell(x)\) медленно меняется. Тогда \(\alpha>0\) - tail index. Эквивалентно extreme-value index \(\gamma=1/\alpha\).

Практические пороги:

- \(\alpha>2\): конечны среднее и дисперсия; волатильностные аргументы более осмысленны.
- \(1<\alpha\le2\): среднее конечно, дисперсия бесконечна; ES может быть конечным, но оценки нестабильны.
- \(\alpha\le1\): среднее бесконечно; теоретический ES бесконечен для Pareto-типа хвоста. Эмпирический ES на конечном окне все равно конечен, но его нельзя трактовать как стабильную оценку конечной величины.

### Hill estimator

Для порядковых статистик \(L_{1:n}\le\cdots\le L_{n:n}\):

```latex
\widehat{\gamma}_{H}(k)
=
\frac{1}{k}
\sum_{j=1}^{k}
\log L_{n-j+1:n}
-
\log L_{n-k:n},
\qquad
\widehat{\alpha}_{H}(k)=\frac{1}{\widehat{\gamma}_{H}(k)}.
```

Hill чувствителен к выбору \(k\). В курсовой надо писать, что \(k\) выбирается как threshold/robustness problem, а не как "истинный" параметр.

### Pickands estimator

Одна стандартная форма:

```latex
\widehat{\gamma}_{P}(k)
=
\frac{1}{\log 2}
\log
\frac{L_{n-k+1:n}-L_{n-2k+1:n}}
{L_{n-2k+1:n}-L_{n-4k+1:n}},
\qquad
\widehat{\alpha}_{P}(k)=\frac{1}{\widehat{\gamma}_{P}(k)}.
```

Текущий код реализует эту идею через ascending array и индексы \(n-k,n-2k,n-4k\).

### Moment estimator

```latex
M_j(k)
=
\frac{1}{k}
\sum_{i=1}^{k}
\left(\log L_{n-i+1:n}-\log L_{n-k:n}\right)^j,
\qquad j=1,2.
```

```latex
\widehat{\gamma}_{M}(k)
=
M_1(k)+1
-
\frac{1}{2}
\left(1-\frac{M_1(k)^2}{M_2(k)}\right)^{-1},
\qquad
\widehat{\alpha}_{M}(k)=\frac{1}{\widehat{\gamma}_{M}(k)}.
```

### POT/GPD

По Pickands-Balkema-de Haan для высокого порога \(u\) распределение превышений \(Y=L-u\mid L>u\) приближается GPD:

```latex
G_{\xi,\sigma}(y)
=
1-\left(1+\xi\frac{y}{\sigma}\right)^{-1/\xi},
\qquad y\ge0,\quad 1+\xi y/\sigma>0.
```

Для тяжелого Pareto-типа хвоста \(\xi>0\), и:

```latex
\alpha=\frac{1}{\xi}.
```

## 5. Сверка с репозиторием

### Что согласовано с литературой

- `pipeline/moex_dq_dr_stage2_robustness_parallel.py:74-89` и `pipeline/moex_heavy_tails_pipeline.py:134-158` используют малую хвостовую вероятность `tail_prob`: VaR считается как квантиль \(1-\alpha\), ES - как среднее худших наблюдений. Это согласовано с DQ-нотацией "small alpha".
- `pipeline/moex_dq_dr_stage2_robustness_parallel.py:149-199` и `pipeline/moex_heavy_tails_pipeline.py:217-265` реализуют ES-DQ как эмпирическую инверсию \(\alpha^*\): найти \(\beta\), при котором \(\operatorname{ES}_\beta(S)\le\sum_i w_i\operatorname{ES}_\alpha(L_i)\). Это соответствует определению DQ, но не является точной статистической процедурой из Han-Lin-Zhao (2025).
- `pipeline/moex_tail_index_stage4.py:416-528` корректно отражает семейство EVT-оценок: Hill, moment, Pickands, GPD-MLE; результат возвращается как \(\alpha=1/\gamma\) или \(\alpha=1/\xi\).
- `docs/AUDIT_2026-06-01.md:121-125` верно смягчает тезис: не заявлять "DQ wins at \(\alpha<1\)", потому что строгого режима \(\alpha<1\) в Stage4 нет.

### Потенциальные расхождения и риски

1. Ранее в комментариях к коду была неверная ссылка на источник DQ-нотации.  
   Для определения DQ нужен Han-Lin-Wang (2025). Han-Lin-Zhao (2025) - препринт по empirical estimator. Комментарии в `pipeline/moex_dq_dr_stage2_robustness_parallel.py` и `pipeline/moex_heavy_tails_pipeline.py` уже уточнены: текущая реализация названа practical grid inversion / proxy implementation.

2. `dq_es` в коде - grid inversion, не опубликованный empirical DQ estimator.  
   Код ищет \(\beta^*\) по сетке и историческому ES. В препринте Han-Lin-Zhao для ES-оценки используется формула с \(\min_{r>0}\) и sample average. Это не означает, что текущий код неверен как исследовательский proxy, но в курсовой надо назвать его "эмпирическая инверсия DQ", а не "строго воспроизведенный estimator из статьи".

3. Нижняя граница DQ в коде не может быть 0.  
   В точной теории DQ может быть 0. В коде `min_prob=max(1/n,1e-4)`, поэтому минимум примерно \((1/n)/\alpha\). Для окна 504 и \(\alpha=0.025\) это около 0.079. Это важно, если интерпретировать абсолютные значения DQ.

4. ES в коде - среднее `ceil(alpha*n)` худших потерь.  
   Теоретический ES - интеграл по VaR. Для дискретного эмпирического распределения лучше использовать стандартный AVaR/ES с корректировкой веса на квантиле. Простое `ceil`-среднее годится для exploratory pipeline, но в финальной работе надо назвать это historical top-k ES approximation.

5. `dr_es_concentration` - не Choueifaty DR.  
   В коде `dr_es_concentration = ES(portfolio) / sum_i w_i ES(asset_i)`. Это risk concentration ratio: меньше - лучше. Классический volatility DR у Choueifaty-Coignard имеет обратную интерпретацию: больше - лучше. В тексте и таблицах надо явно указать знак.

6. Теоретический ES при \(\alpha\le1\) tail index.  
   Если распределение действительно Pareto-type с \(\alpha_{\text{tail}}\le1\), ES бесконечен. Поэтому гипотеза "DQ vs DR at tail index < 1" требует осторожности: эмпирический finite-window ES существует, но не оценивает конечный теоретический ES.

7. Гипотеза в Stage4 docstring была слишком сильной.  
   `pipeline/moex_tail_index_stage4.py` и `pipeline/moex_tail_index_stage4_db_checkpoint.py` уже уточняют, что слабость DR при \(\alpha<1\) является рабочей гипотезой, а не выводом. Аудит показывает 0 строгих наблюдений \(\alpha<1\).

8. Высокая коллинеарность DQ и tail-heaviness.  
   `docs/AUDIT_2026-06-01.md:114-117` отмечает корреляции около 0.926 и -0.871. В итоговой работе interaction regressions лучше оставить как диагностику, а не как главный идентификационный аргумент.

## 6. Что включить в курсовую

Минимальный теоретический блок:

1. Определить VaR/ES в small-\(\alpha\) нотации.
2. Дать общее определение DQ через \(\alpha^*\).
3. Объяснить DQ как "улучшение хвостового уровня", а DR/concentration ratio как "отношение капиталов".
4. Для эмпирики указать, что используется ES-DQ:

```latex
\widehat{\operatorname{DQ}}^{\operatorname{ES}}_{\alpha}
\approx
\frac{\widehat{\beta}^{*}}{\alpha},
\quad
\widehat{\beta}^{*}
=
\inf\left\{\beta:
\widehat{\operatorname{ES}}_{\beta}(S)
\le
\sum_i w_i\widehat{\operatorname{ES}}_{\alpha}(L_i)
\right\}.
```

5. Дать формулу `dr_es_concentration`:

```latex
\widehat{\operatorname{CR}}_{\operatorname{ES},\alpha}
=
\frac{\widehat{\operatorname{ES}}_{\alpha}(S)}
{\sum_i w_i\widehat{\operatorname{ES}}_{\alpha}(L_i)}.
```

6. Для EVT дать regular variation, Hill estimator и GPD/POT. Pickands и moment estimator можно перенести в приложение или коротко упомянуть как robustness estimators.

## 7. Формулировка результата, которую можно защищать

Безопасная версия:

> В работе DQ рассматривается как tail-sensitive индекс диверсификации, основанный на изменении хвостового уровня риск-меры. В эмпирической части используется ES-based plug-in approximation DQ и ES concentration ratio. На данных ликвидных акций MOEX строгий режим \(\alpha_{\text{tail}}<1\) не подтверждается, поэтому основной вывод должен быть не о "победе DQ в ultra-heavy tails", а о дополнительной прогнозной информации DQ для будущих tail events и о связи DQ с оценками tail-heaviness.

## 8. Что проверить перед финальной версией

1. Пересчитать `dq_es` через опубликованную empirical ES-DQ формулу с \(\min_{r>0}\) хотя бы на нескольких окнах и сравнить с grid inversion.
2. Проверить, есть ли в результатах `dq_es>1`; если есть, отдельно объяснить, что это эффект эмпирического top-k ES/сетки/дискретности, а не свойство точного ES-DQ.
3. В рукописи использовать Han-Lin-Wang там, где речь об определении DQ; Han-Lin-Zhao оставлять только для обсуждения empirical DQ estimators.
4. Везде заменить неясное "DR" на одно из двух: `volatility DR` или `ES concentration ratio`.
5. Не утверждать \(\alpha<1\) как найденный режим. В текущем аудите: строгих \(\alpha<1\) наблюдений нет.
6. Проверить обозначения: не использовать одну и ту же букву \(\alpha\) одновременно для DQ tail probability и для tail index. Для tail index лучше писать \(\tau\), \(a\) или \(\alpha_{\text{tail}}\).
