#' Construct a source-local document record.
#' @param title Display title.
new_document <- function(title, views = 0L) {
  structure(list(title = title, views = views), class = "document")
}

print.document <- function(x, ...) {
  cat(sprintf("<document %s: %d views>\n", x$title, x$views))
  invisible(x)
}

setClass("DocumentStore", slots = c(records = "list"))
store <- new("DocumentStore", records = list(new_document("Overview")))
print(store@records[[1]])
