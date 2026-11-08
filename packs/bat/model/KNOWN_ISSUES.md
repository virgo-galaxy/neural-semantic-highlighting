# BAT / CMD measured limits

- **Calls and conditional tails have role errors.** Short-label augmentation
  fixes the standalone CALL/GOTO Golden and stops actual call targets becoming
  comments, but bare call arguments can still become comment/function. In the
  records display probe, an IF ERRORLEVEL tail's `echo Report failed` is incorrectly
  comment-like. The arguments probe's GOTO/EXIST words and label boundaries also
  have individual errors. There is no interpreter/lexer fallback at runtime.
- **Variable/quote ranges can merge.** A quoted `%root%src` path can merge text
  into the variable span; `!count!:` and `%~1!` can absorb suffix punctuation.
  Quoted paths and percent/delayed expansions therefore remain approximate even
  when the overall script is readable. Ordinary standalone loop and argument
  modifiers have stronger Golden evidence.
- **Comments and commands are approximate.** REM comments can split into touching
  comment spans with whitespace gaps; command words such as external `node` can
  receive keyword instead of function roles. FOR /L comma and arithmetic modifier
  boundaries also retain errors. Offline Gold provides bounded lexical roles,
  not macro expansion, delayed execution order or full external-command semantics.
- **Context and compatibility are bounded.** The model has 512-byte context.
  Complex caret escapes, nested FOR /F command quoting, distant labels, code-page
  behavior and legacy COMMAND.COM are not fully certified. No batch script,
  FOR /F command, include or subroutine is executed by Gold or inference.
- **Evidence is small.** Natural validation consists of four related launcher
  files in one held-out family. The first natural test has three scripts from
  three other families, all in one official VS Code capture. They do not establish
  universal Windows batch accuracy. Natural/focus/Golden/display metrics remain
  separate; preserve the known first test and every historical source/checkpoint.
