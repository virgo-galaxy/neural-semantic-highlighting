plot_traffic <- function(observations, title = "Document traffic") {
  ggplot2::ggplot(
    observations,
    ggplot2::aes(x = day, y = views, colour = category)
  ) +
    ggplot2::geom_line(linewidth = 0.8) +
    ggplot2::geom_point(size = 2) +
    ggplot2::labs(title = title, x = "Day", y = "Views") +
    ggplot2::theme_minimal()
}
