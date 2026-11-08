bits 64
%define STEP_SIZE 8

%macro advance 2
    add %1, %2
%endmacro

section .text
global next_record
next_record:
    mov rax, rdi
    advance rax, STEP_SIZE
    ret
