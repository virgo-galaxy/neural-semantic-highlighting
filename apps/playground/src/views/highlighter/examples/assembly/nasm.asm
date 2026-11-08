bits 64
default rel
section .text
global sum_positive

sum_positive:
    xor rax, rax
    test rsi, rsi
    jz .done
.loop:
    mov rdx, [rdi]
    test rdx, rdx
    jle .next
    add rax, rdx
.next:
    add rdi, 8
    dec rsi
    jnz .loop
.done:
    ret
