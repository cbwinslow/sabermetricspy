# Pulls the FanGraphs park factors page (with its FIP column) for each season; tools/park_fip.py turns the CSVs into park_fip.yaml.
# Run: Rscript tools/park_fip.R <output folder>   (needs R, baseballr and internet)
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) >= 1) args[[1]] else "park_pull"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
suppressMessages(library(baseballr))
for (y in 1990:as.integer(format(Sys.Date(), "%Y"))) {
  f <- file.path(out, paste0("park", y, ".csv"))
  if (file.exists(f)) next
  x <- tryCatch(fg_park(y), error = function(e) conditionMessage(e))
  if (is.character(x)) { cat(y, "ERR", substr(x, 1, 100), "\n") } else { write.csv(x, f, row.names = FALSE); cat(y, nrow(x), "\n") }
  Sys.sleep(5)
}
