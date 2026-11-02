# Robustness, not used for claims. Rscript analysis/robust.R data_long.csv results/robust.txt
# Linear mixed model on the probability scale: reason slopes vary by rule, intercepts by run and task.
suppressMessages(library(lme4))
a <- commandArgs(TRUE)
d <- read.csv(a[1])
d$reason <- relevel(factor(d$reason), "filler")
d$position <- relevel(factor(d$position), "middle")
d$real <- as.numeric(d$reason == "real")
d$placebo <- as.numeric(d$reason == "placebo")
m <- lmer(y ~ reason + modal + prefix + case + example + position + length + pressure +
            (1 + real + placebo || rule) + (1 | run) + (1 | task), data = d,
          control = lmerControl(optimizer = "bobyqa"))
sink(a[2])
print(summary(m)$coefficients)
vc <- as.data.frame(VarCorr(m))
print(vc[, c("grp", "var1", "sdcor")])
fx <- fixef(m)
for (k in c("real", "placebo")) {
  sd_slope <- vc$sdcor[vc$grp %in% c("rule", "rule.1", "rule.2") & vc$var1 == k]
  est <- fx[paste0("reason", k)]
  se <- sqrt(vcov(m)[paste0("reason", k), paste0("reason", k)])
  half <- 1.96 * sqrt(se^2 + sd_slope^2)
  cat(k, "against filler: prediction interval for a new rule", round(est - half, 3), round(est + half, 3), "\n")
}
sink()
