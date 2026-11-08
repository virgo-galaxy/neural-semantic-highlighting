.intel_syntax noprefix
.text
.globl read_offset

read_offset:
    mov rax, QWORD PTR [rdi + 16]
    add rax, 5
    ret

.section .rodata
message:
    .asciz "Ready for Virgo"
