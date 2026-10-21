# Pulls the FanGraphs pitcher leaderboards (2002 on) that tools/siera_constants.py fits the SIERA constants to.
# Run: Rscript tools/siera_constants.R <output folder>   (needs R, baseballr and internet)
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) >= 1) args[[1]] else "siera_pull"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
suppressMessages(library(baseballr))
for (y in 2002:as.integer(format(Sys.Date(), "%Y"))) {
  f <- file.path(out, paste0("p", y, ".csv"))
  if (file.exists(f)) next
  x <- tryCatch(fg_pitcher_leaders(startseason = y, endseason = y, qual = 50), error = function(e) conditionMessage(e))
  if (is.character(x)) { cat(y, "ERR", substr(x, 1, 120), "\n") } else { write.csv(x, f, row.names = FALSE); cat(y, nrow(x), "\n") }
  Sys.sleep(5)
}
