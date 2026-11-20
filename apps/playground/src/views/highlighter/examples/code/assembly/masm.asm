option casemap:none
.data
counter QWORD 0

.code
IncrementCounter PROC
    lea rdx, counter
    mov rax, QWORD PTR [rdx]
    add rax, rcx
    mov QWORD PTR [rdx], rax
    ret
IncrementCounter ENDP
END
