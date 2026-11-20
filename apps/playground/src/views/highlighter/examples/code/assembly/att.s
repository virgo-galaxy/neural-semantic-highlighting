.text
.globl scale_value
.type scale_value, @function

scale_value:
    pushq %rbp
    movq %rsp, %rbp
    movq %rdi, %rax
    imulq $3, %rax
    addq $7, %rax # fixed offset
    popq %rbp
    ret
.size scale_value, .-scale_value
