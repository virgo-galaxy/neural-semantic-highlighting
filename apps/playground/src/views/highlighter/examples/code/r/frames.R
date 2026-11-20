documents <- data.frame(
  title = c("Introduction", "Components", "Themes"),
  views = c(120L, 85L, 160L),
  published = c(TRUE, FALSE, TRUE)
)

visible <- documents[documents$published, , drop = FALSE]
visible$rank <- rank(-visible$views)
rownames(visible) <- NULL

summary <- list(
  titles = visible[["title"]],
  total = sum(visible$views),
  columns = names(visible)
)
print(summary)
