greeting <- function(name, excited = FALSE) {
  title <- trimws(name)
  suffix <- if (excited) "!" else "."
  paste0("Hello, ", title, suffix)
}

names <- c("Virgo", "星空 🌌", "R")
for (name in names) {
  message(greeting(name, excited = TRUE))
}
