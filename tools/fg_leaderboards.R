# Pulls FanGraphs qualified-batter and all-pitcher leaderboards (baseballr::fg_batter_leaders / fg_pitcher_leaders) for six seasons.
# Usage: Rscript tools/fg_leaderboards.R <output dir>; then python tools/fg_leaderboards.py <output dir> to build tests/golden/fg_{batting,pitching}_rates.csv.
.libPaths("C:/Users/blain/Documents/R/win-library/4.6")
suppressMessages(library(baseballr))
args <- commandArgs(trailingOnly = TRUE)
out <- paste0(args[1], "/")  # directory for the per-season CSVs
for (s in c(2005, 2012, 2016, 2019, 2022, 2024)) {
  b <- fg_batter_leaders(startseason=as.character(s), endseason=as.character(s), qual="y")
  want <- c("Season","PlayerName","G","AB","PA","H","1B","2B","3B","HR","R","RBI","BB","IBB","SO","HBP","SF","SH","GDP","SB","CS","AVG","OBP","SLG","OPS","ISO","BABIP","BB_pct","K_pct","BB_K","wOBA","wRAA","wRC","Off","BaseRunning","wBsR","UBR","GDPRuns","Spd"); b <- b[, intersect(want, names(b))]
  write.csv(b, paste0(out,"bat_",s,".csv"), row.names=FALSE); Sys.sleep(5)
  p <- fg_pitcher_leaders(startseason=as.character(s), endseason=as.character(s), qual="n")
  want <- c("Season","PlayerName","W","L","ERA","G","GS","QS","CG","ShO","SV","BS","HLD","IP","TBF","H","R","ER","HR","BB","IBB","HBP","SO","GB","FB","LD","K_9","BB_9","K_BB","H_9","HR_9","AVG","WHIP","BABIP","LOB_pct","FIP","xFIP","K_pct","BB_pct","K-BB_pct","RS_9","tERA","kwERA","xERA"); p <- p[, intersect(want, names(p))]
  write.csv(p, paste0(out,"pit_",s,".csv"), row.names=FALSE); Sys.sleep(5)
}
