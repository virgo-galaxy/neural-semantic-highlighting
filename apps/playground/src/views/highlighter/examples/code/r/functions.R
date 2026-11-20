make_counter <- function(start = 0L) {
  count <- start
  function(step = 1L) {
    count <<- count + step
    count
  }
}

summarize_values <- function(values, transform = identity, ...) {
  cleaned <- values[!is.na(values)]
  transformed <- transform(cleaned)
  list(total = sum(transformed, ...), count = length(transformed))
}

counter <- make_counter(10L)
result <- summarize_values(c(1, NA, 3), transform = \(x) x * 2)
print(counter())
