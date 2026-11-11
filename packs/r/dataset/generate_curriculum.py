"""Original independent R task families; never Golden or display copies."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'function':'@FN@ <- function(value, scale = @N@) { result <- value * scale; result }',
'lambda':'@FN@ <- \\(value) value + @N@\nresult <- @FN@(3)',
'defaults':'@FN@ <- function(value, extra = value + @N@) { extra * value }',
'closure':'@FN@ <- function(step) { count <- @N@; function(value) { count + value + step } }',
'variadic':'@FN@ <- function(..., prefix = "@WORD@") { paste(prefix, ..., sep = ":") }',
'right-assign':'@N@ -> count\nfunction(value) value + count -> @FN@\n@FN@(2)',
'super-assign':'@FN@ <- function() { count <<- @N@; invisible(count) }',
'loop':'@FN@ <- function(values) { total <- @N@; for (item in values) { total <- total + item }; total }',
'while':'@FN@ <- function(limit) { n <- @N@; while (n < limit) { n <- n + 1 }; n }',
'repeat':'@FN@ <- function() { n <- 0; repeat { n <- n + 1; if(n > @N@) break }; n }',
'next':'@FN@ <- function(values) { out <- list(); for (item in values) { if (is.na(item)) next; out[[length(out)+1]] <- item }; out }',
'condition':'@FN@ <- function(value) { if (value > @N@) "@WORD@" else "other" }',
'boolean':'@FN@ <- function(value) isTRUE(value) && !is.na(value) || FALSE',
'vectors':'@FN@ <- function() c(@N@L, 2.5, 3+4i, NA_real_, Inf, NaN)',
'list':'@FN@ <- list(title = "@WORD@", count = @N@, active = TRUE)\n@FN@$title',
'dataframe':'@FN@ <- data.frame(name = c("@WORD@", "source"), score = c(@N@, 4))\n@FN@$score',
'matrix':'@FN@ <- matrix(seq_len(@N@), nrow = 2)\n@FN@[1, , drop = FALSE]',
'subset':'@FN@ <- function(values) values[!is.na(values) & values > @N@]',
'subset2':'@FN@ <- function(values) { first <- values[[1]]; list(value = first, offset = @N@) }',
'names':'@FN@ <- function(values) { names(values) <- c("@WORD@", "second"); values }',
'slot':'@FN@ <- function(object) { slot <- object@data; slot[[@N@]] }',
'namespace':'@FN@ <- function(values) stats::median(values, na.rm = TRUE) + @N@',
'namespace-internal':'@FN@ <- function(object) utils:::format.object_size(object, units = "@WORD@")',
'pipe':'@FN@ <- function(values) values |> abs() |> sort(decreasing = TRUE) |> head(@N@)',
'pipe-placeholder':'@FN@ <- function(values) values |> stats::lm(formula = y ~ x, data = _)',
'magrittr':'@FN@ <- function(data) data %>% dplyr::filter(score > @N@) %>% dplyr::select(name, score)',
'pipe-mutate':'@FN@ <- function(data) data |> dplyr::mutate(label = paste0("@WORD@", score)) |> dplyr::arrange(score)',
'group-summarise':'@FN@ <- function(data) data |> dplyr::group_by(kind) |> dplyr::summarise(total = sum(value), .groups = "drop")',
'formula':'@FN@ <- function(data) stats::lm(score ~ scale(value) + group, data = data)',
'formula-lambda':'@FN@ <- function(values) purrr::map_dbl(values, ~ .x + @N@)',
'join':'@FN@ <- function(left, right) dplyr::left_join(left, right, by = "@WORD@")',
'plot':'@FN@ <- function(data) ggplot2::ggplot(data, ggplot2::aes(x = value, y = score)) + ggplot2::geom_point(size = @N@)',
'errors':'@FN@ <- function(path) tryCatch(readLines(path), error = function(problem) { warning(conditionMessage(problem)); "@WORD@" })',
'on-exit':'@FN@ <- function(path) { con <- file(path); on.exit(close(con), add = TRUE); readLines(con, n = @N@) }',
's3':'print.@WORD@ <- function(x, ...) { cat("@WORD@", x$value, "\\n"); invisible(x) }',
's4':'setClass("@WORD@", slots = c(value = "numeric"))\n@FN@ <- function(x) x@value + @N@',
'backticks':'`@WORD@ value` <- @N@\n@FN@ <- function(`input value`) `input value` + `@WORD@ value`',
'custom-operator':'`%join@WORD@%` <- function(left, right) paste(left, right)\n@FN@ <- "one" %join@WORD@% "two"',
'raw-string':'@FN@ <- r"(C:\\@WORD@\\files\n# raw comment text and "quotes"\n)"',
'raw-delimited':'@FN@ <- R"---[@WORD@ (text) "quoted" \\path\n# stays text]---"',
'escaped':'@FN@ <- "@WORD@ \\"quoted\\"\\n\\t path \\\\ end"',
'comments':'# @WORD@ 🌌 report\n@FN@ <- function(value) { # body\n value + @N@ # result\n}',
'roxygen':"#' @WORD@ transformation\n#' @param value Numeric input.\n#' @return Numeric output.\n@FN@ <- function(value) value + @N@",
'numbers':'@FN@ <- c(@N@L, 0xff, 1.25e-3, 2i, NA_integer_, NA_complex_, -Inf)',
'assign-equals':'@FN@ = function(value) { result = value + @N@; result }',
'nested-scope':'@FN@ <- function(value) { helper <- function(value) value + @N@; helper(value) }',
'braced-scope':'@FN@ <- function(value) { { local <- value + @N@ }; local + value }',
'dynamic-call':'@FN@ <- function(callback, value) callback(value, extra = @N@)',
'environment':'@FN@ <- new.env(parent = emptyenv())\n@FN@$count <- @N@\nget("count", envir = @FN@)',
'long-mixed':'@FN@ <- function(value) { header <- "@WORD@"; text <- r"(Original @WORD@ payload\nC:\\records\\raw\n# still text, with (nesting) and quotes\n)"; paste(header, text, value, sep = "\\n") }',
}
WORDS='amber birch cobalt dawn elm fjord grove hazel iris jade kelp lotus maple north opal pine quartz reed sage tide'.split()
def main():
 root=PackSpec.open('r').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(1163+index*101+variant);word=WORDS[(index+variant)%len(WORDS)]
   source=template.replace('@FN@',word+'_process').replace('@WORD@',word).replace('@N@',str(rng.randrange(2,30)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();path=root/family/f'{variant:02}.R';path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous R task')
   if not path.exists():path.write_bytes(raw)
   files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original R tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n'
 p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original R license')
 p.write_bytes(license)
 lock=dict(format='nsh-r-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous R curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
