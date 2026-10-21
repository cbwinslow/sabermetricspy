# Regenerates tests/golden/baseballr/baseballr_tieout.json from real baseballr output.
# Run: Rscript tools/baseballr_golden.R   (needs R, baseballr, jsonlite and internet for fg_guts())
# The JSON records the baseballr version, the exact calls and the run date; tests only compare to what is stored there.
suppressMessages({ library(baseballr); library(jsonlite) })

batters <- data.frame(
  id = paste0("bat", 1:8),
  season = c(2006L, 2012L, 2016L, 2019L, 2021L, 2023L, 2024L, 2025L),
  AB = c(540L, 602L, 480L, 560L, 455L, 620L, 589L, 512L),
  X1B = c(98L, 101L, 77L, 90L, 70L, 104L, 99L, 80L),
  X2B = c(30L, 35L, 22L, 31L, 19L, 38L, 33L, 25L),
  X3B = c(3L, 4L, 2L, 5L, 1L, 6L, 2L, 3L),
  HR = c(24L, 31L, 18L, 40L, 12L, 28L, 35L, 22L),
  uBB = c(55L, 80L, 41L, 70L, 38L, 62L, 66L, 48L),
  IBB = c(4L, 12L, 2L, 6L, 3L, 9L, 5L, 1L),
  HBP = c(5L, 8L, 3L, 6L, 4L, 7L, 9L, 2L),
  SF = c(4L, 6L, 3L, 5L, 2L, 4L, 7L, 3L),
  SO = c(110L, 130L, 95L, 160L, 90L, 140L, 125L, 100L)
)
pitchers <- data.frame(
  id = paste0("pit", 1:8),
  season = c(2005L, 2011L, 2015L, 2018L, 2021L, 2022L, 2024L, 2025L),
  outs = c(600L, 640L, 575L, 543L, 580L, 610L, 585L, 520L),
  HR = c(20L, 18L, 22L, 15L, 25L, 17L, 19L, 21L),
  uBB = c(50L, 45L, 60L, 38L, 55L, 41L, 36L, 52L),
  IBB = c(3L, 2L, 5L, 1L, 4L, 2L, 0L, 3L),
  HBP = c(6L, 5L, 8L, 3L, 9L, 4L, 5L, 7L),
  SO = c(180L, 200L, 170L, 210L, 190L, 220L, 205L, 160L)
)
pitchers$IP <- pitchers$outs / 3
# FanGraphs FIP counts intentional walks in BB (see METHODOLOGY); baseballr's fip_plus names its walk column uBB, so total
# walks are passed in that column to compare the same quantity.
pitchers$BB <- pitchers$uBB + pitchers$IBB

bw <- woba_plus(cbind(batters[, c("season","X1B","X2B","X3B","HR","uBB","HBP","AB","SF","SO")], id = batters$id))
pf <- fip_plus(cbind(transform(pitchers, uBB = BB)[, c("season","HR","uBB","HBP","SO","IP")], X1B = 0, X2B = 0, X3B = 0, AB = 1, BF = 1, id = pitchers$id))
guts <- as.data.frame(fg_guts())

out <- list(
  provenance = list(
    package = "baseballr", version = as.character(packageVersion("baseballr")),
    r_version = as.character(getRversion()), run_date = format(Sys.Date()),
    calls = c("fg_guts()", "woba_plus(df)", "fip_plus(df)"),
    note = "Inputs are chosen counting lines (not real players); outputs are baseballr's own, rounded as baseballr rounds them (wOBA 3 dp, FIP 2 dp). For FIP, total walks (incl. intentional) are passed to fip_plus because FanGraphs FIP counts them; fip_plus itself names that column uBB."
  ),
  guts = guts,
  batters = merge(batters, bw[, c("id","wOBA")], by = "id"),
  pitchers = merge(pitchers, pf[, c("id","FIP")], by = "id")
)
write_json(out, "tests/golden/baseballr/baseballr_tieout.json", digits = NA, auto_unbox = TRUE, pretty = TRUE)
cat("wrote", nrow(guts), "guts rows,", nrow(bw), "batters,", nrow(pf), "pitchers\n")
