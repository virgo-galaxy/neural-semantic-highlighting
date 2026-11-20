.text
.globl sum_positive
.p2align 2

sum_positive:
    mov x2, #0
    cbz x1, .Ldone
.Lloop:
    ldr x3, [x0], #8
    cmp x3, #0
    b.le .Lnext
    add x2, x2, x3
.Lnext:
    subs x1, x1, #1
    b.ne .Lloop
.Ldone:
    mov x0, x2
    ret
