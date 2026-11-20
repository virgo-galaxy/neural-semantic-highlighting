fit_trend <- function(observations) {
  model <- stats::lm(views ~ day + category, data = observations)
  predictions <- stats::predict(model, newdata = observations)
  list(
    coefficients = stats::coef(model),
    residuals = observations$views - predictions,
    summary = summary(model)
  )
}

safe_average <- function(values) {
  tryCatch(
    mean(values, na.rm = TRUE),
    warning = function(problem) {
      message(conditionMessage(problem))
      NA_real_
    }
  )
}
