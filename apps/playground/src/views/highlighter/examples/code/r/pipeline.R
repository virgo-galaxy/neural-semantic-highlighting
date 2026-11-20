library(dplyr)

summarize_documents <- function(documents, minimum_views = 20) {
  documents |>
    filter(.data$published, .data$views >= minimum_views) |>
    group_by(.data$category) |>
    summarise(
      count = n(),
      views = sum(.data$views, na.rm = TRUE),
      .groups = "drop"
    ) |>
    arrange(desc(.data$views))
}

labels <- c(" Button ", "Surface", NA_character_) %>%
  purrr::discard(is.na) %>%
  purrr::map_chr(~ trimws(.x))
