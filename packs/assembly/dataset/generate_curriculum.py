"""Original small assembly programs, grouped by task across syntax profiles."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, file_hash

PROFILES = ['nasm', 'gas', 'masm', 'aarch64']
NAMES = ['mix', 'step', 'read_value', 'accumulate', 'sample_count', 'measure', 'adjust', 'transform']


def function(profile, name, body):
    if profile == 'nasm':
        return f'bits 64\nsection .text\nglobal {name}\n{name}:\n{body}\n'
    if profile == 'masm':
        return f'.code\n{name} PROC\n{body}\n{name} ENDP\n'
    return f'.text\n.globl {name}\n{name}:\n{body}\n'


def task(profile, family, name, n):
    arm, att = profile == 'aarch64', profile == 'gas'
    reg = 'x0' if arm else '%rax' if att else 'rax'
    arg = 'x1' if arm else '%rdi' if att else 'rcx' if profile == 'masm' else 'rdi'
    immediate = f'#{n}' if arm else f'${n}' if att else str(n)
    def op(arm_code, gas_code, intel_code):
        return arm_code if arm else gas_code if att else intel_code
    bodies = {
        'arithmetic-add': op(f'    add x0, x1, #{n}\n    ret', f'    movq %rdi, %rax\n    addq ${n}, %rax\n    ret', f'    mov rax, {arg}\n    add rax, {n}\n    ret'),
        'arithmetic-multiply': op(f'    mov x2, #{n}\n    mul x0, x1, x2\n    ret', f'    imulq ${n}, %rdi, %rax\n    ret', f'    imul rax, {arg}, {n}\n    ret'),
        'arithmetic-subtract': op(f'    sub x0, x1, #{n}\n    ret', f'    movq %rdi, %rax\n    subq ${n}, %rax\n    ret', f'    mov rax, {arg}\n    sub rax, {n}\n    ret'),
        'bits-mask': op(f'    and x0, x1, #255\n    eor x0, x0, x2\n    ret', f'    movq %rdi, %rax\n    andq $255, %rax\n    xorq %rsi, %rax\n    ret', f'    mov rax, {arg}\n    and rax, 255\n    xor rax, rdx\n    ret'),
        'bits-shift': op(f'    lsl x0, x1, #3\n    lsr x2, x0, #1\n    ret', f'    movq %rdi, %rax\n    shlq $3, %rax\n    shrq $1, %rax\n    ret', f'    mov rax, {arg}\n    shl rax, 3\n    shr rax, 1\n    ret'),
        'memory-load': op(f'    ldr x0, [x1, #{n * 8}]\n    ret', f'    movq {n * 8}(%rdi), %rax\n    ret', f'    mov rax, [{arg} + {n * 8}]\n    ret'),
        'memory-store': op(f'    str x0, [x1, #{n * 8}]\n    ret', f'    movq %rsi, {n * 8}(%rdi)\n    ret', f'    mov [{arg} + {n * 8}], rdx\n    ret'),
        'memory-indexed': op('    ldr x0, [x1, x2, lsl #3]\n    ret', '    movq (%rdi,%rsi,8), %rax\n    ret', f'    mov rax, [{arg} + rdx * 8]\n    ret'),
        'branch-positive': op(f'    cmp x1, #{n}\n    b.le {name}_done\n    mov x0, x1\n{name}_done:\n    ret', f'    cmpq ${n}, %rdi\n    jle {name}_done\n    movq %rdi, %rax\n{name}_done:\n    ret', f'    cmp {arg}, {n}\n    jle {name}_done\n    mov rax, {arg}\n{name}_done:\n    ret'),
        'branch-zero': op(f'    cbz x1, {name}_done\n    add x0, x1, #{n}\n{name}_done:\n    ret', f'    testq %rdi, %rdi\n    jz {name}_done\n    addq ${n}, %rax\n{name}_done:\n    ret', f'    test {arg}, {arg}\n    jz {name}_done\n    add rax, {n}\n{name}_done:\n    ret'),
        'loop-sum': op(f'    mov x0, #0\n    mov x2, #{n}\n{name}_loop:\n    add x0, x0, x2\n    subs x2, x2, #1\n    b.ne {name}_loop\n    ret', f'    xorq %rax, %rax\n    movq ${n}, %rcx\n{name}_loop:\n    addq %rcx, %rax\n    decq %rcx\n    jne {name}_loop\n    ret', f'    xor rax, rax\n    mov rdx, {n}\n{name}_loop:\n    add rax, rdx\n    dec rdx\n    jne {name}_loop\n    ret'),
        'loop-buffer': op(f'    mov x2, #{n}\n{name}_loop:\n    strb wzr, [x1], #1\n    subs x2, x2, #1\n    b.ne {name}_loop\n    ret', f'    movq ${n}, %rcx\n{name}_loop:\n    movb $0, (%rdi)\n    incq %rdi\n    decq %rcx\n    jne {name}_loop\n    ret', f'    mov rdx, {n}\n{name}_loop:\n    mov byte [{arg}], 0\n    inc {arg}\n    dec rdx\n    jne {name}_loop\n    ret'),
        'stack-frame': op('    stp x29, x30, [sp, #-16]!\n    mov x29, sp\n    add x0, x0, #1\n    ldp x29, x30, [sp], #16\n    ret', '    pushq %rbp\n    movq %rsp, %rbp\n    addq $1, %rax\n    popq %rbp\n    ret', '    push rbp\n    mov rbp, rsp\n    add rax, 1\n    pop rbp\n    ret'),
        'call-helper': op(f'    stp x29, x30, [sp, #-16]!\n    bl external_helper\n    add x0, x0, #{n}\n    ldp x29, x30, [sp], #16\n    ret', f'    call external_helper\n    addq ${n}, %rax\n    ret', f'    call external_helper\n    add rax, {n}\n    ret'),
        'vector-load': op('    ldr q0, [x1]\n    ldr q1, [x2]\n    add v0.4s, v0.4s, v1.4s\n    str q0, [x3]\n    ret', '    movdqu (%rdi), %xmm0\n    paddd %xmm1, %xmm0\n    movdqu %xmm0, (%rsi)\n    ret', f'    movdqu xmm0, [{arg}]\n    paddd xmm0, xmm1\n    movdqu [rdx], xmm0\n    ret'),
        'conditional-result': op(f'    cmp x1, #{n}\n    cset w0, gt\n    ret', f'    cmpq ${n}, %rdi\n    setg %al\n    movzbl %al, %eax\n    ret', f'    cmp {arg}, {n}\n    setg al\n    movzx eax, al\n    ret'),
        'numeric-label': op('    mov x0, #0\n1:\n    add x0, x0, #1\n    cmp x0, #8\n    b.lt 1b\n    ret', '    xorq %rax, %rax\n1:\n    incq %rax\n    cmpq $8, %rax\n    jl 1b\n    ret', f'    xor rax, rax\n{name}_again:\n    inc rax\n    cmp rax, 8\n    jl {name}_again\n    ret'),
        'alignment': op(f'    .p2align 2\n    mov x0, #{n}\n    ret', f'    .p2align 4\n    movq ${n}, %rax\n    ret', f'    align 16\n    mov rax, {n}\n    ret'),
        'constant-values': op(f'    mov x0, #0x{n:X}\n    mov x1, #0b1010\n    ret', f'    movq $0x{n:X}, %rax\n    movq $0b1010, %rdx\n    ret', f'    mov eax, 0{n:X}h\n    mov edx, 1010b\n    ret'),
    }
    if family in bodies:
        return function(profile, name, bodies[family])
    text = f'Original message {n}'
    data_word = '.asciz' if profile in {'gas', 'aarch64'} else 'db' if profile == 'nasm' else 'BYTE'
    line = f'{name}_text: {data_word} "{text}"' if profile != 'masm' else f'{name}_text {data_word} "{text}", 0'
    if profile == 'nasm':
        line += ', 0'
    data_header = 'section .rodata' if profile == 'nasm' else '.const' if profile == 'masm' else '.section .rodata'
    if family == 'string-directive':
        return data_header + '\n' + line + '\n'
    if family == 'string-table':
        return data_header + '\n' + line + '\n' + line.replace('_text', '_other').replace('Original message', 'Another record') + '\n'
    if family == 'string-size':
        size = f'{name}_size equ $ - {name}_text' if profile in {'nasm', 'masm'} else f'.equ {name}_size, . - {name}_text'
        return data_header + '\n' + line + '\n' + size + '\n'
    if family == 'string-address':
        body = op(f'    adrp x0, {name}_text\n    add x0, x0, :lo12:{name}_text\n    ret', f'    leaq {name}_text(%rip), %rax\n    ret', f'    lea rax, [{name}_text]\n    ret')
        return function(profile, name, body) + '\n' + data_header + '\n' + line + '\n'
    if family == 'string-unicode':
        return data_header + '\n' + line.replace(text, '星空 🌌 record ' + str(n)) + '\n'
    if family == 'macro-definition':
        if profile == 'nasm':
            return f'%macro {name} 1\n    add rax, %1\n%endmacro\nsection .text\n{name} {n}\n'
        if profile == 'masm':
            return f'{name} MACRO value\n    add rax, value\nENDM\n.code\n{name} {n}\nEND\n'
        return f'.macro {name} value\n    add x0, x0, #\\value\n.endm\n{name} {n}\n' if arm else f'.macro {name} value\n    addq $\\value, %rax\n.endm\n{name} {n}\n'
    if family == 'constant-definition':
        prefix = f'%define LIMIT {n}\n' if profile == 'nasm' else f'LIMIT EQU {n}\n' if profile == 'masm' else f'.equ LIMIT, {n}\n'
        body = op('    mov x0, #LIMIT\n    ret', '    movq $LIMIT, %rax\n    ret', '    mov rax, LIMIT\n    ret')
        return prefix + function(profile, name, body)
    if family == 'preprocessor':
        opening, closing = ('%ifdef ENABLE_FAST\n', '%endif\n') if profile == 'nasm' else ('IFDEF ENABLE_FAST\n', 'ENDIF\n') if profile == 'masm' else ('#if defined(ENABLE_FAST)\n', '#endif\n')
        return opening + function(profile, name, op('    mov x0, #1\n    ret', '    movq $1, %rax\n    ret', '    mov rax, 1\n    ret')) + closing
    raise ValueError(family)


def main():
    root = PackSpec.open('assembly').dataset_root / 'sources/curriculum-v2'
    families = ['arithmetic-add', 'arithmetic-multiply', 'arithmetic-subtract', 'bits-mask', 'bits-shift',
                'memory-load', 'memory-store', 'memory-indexed', 'branch-positive', 'branch-zero',
                'loop-sum', 'loop-buffer', 'stack-frame', 'call-helper', 'vector-load', 'conditional-result',
                'numeric-label', 'alignment', 'constant-values', 'string-directive', 'string-table',
                'string-size', 'string-address', 'string-unicode', 'macro-definition', 'constant-definition', 'preprocessor']
    files = {}
    for profile in PROFILES:
        for family in families:
            for i in range(24):
                source = task(profile, family, NAMES[i % len(NAMES)], i + 5)
                if profile == 'masm' and not source.rstrip().endswith('END'):
                    source += 'END\n'
                comment = '; Original source task\n' if profile in {'nasm', 'masm'} else '# Original source task\n' if profile == 'gas' else '// Original source task\n'
                position = (i // 6) % 4
                if position == 1:
                    source = comment + source
                elif position == 2:
                    source = '\n' + source
                elif position == 3:
                    source = ('; Original note\n; Source fragment\n' if profile in {'nasm', 'masm'} else '/* Original block note */\n') + source
                if profile in {'nasm', 'masm'} and i % 7 == 3:
                    source = source.upper()
                if i % 5 == 2:
                    source = source.replace('\n', '\r\n')
                extension = '.asm' if profile in {'nasm', 'masm'} else '.S' if family == 'preprocessor' else '.s'
                files[f'{profile}/{family}/{i:02}{extension}'] = source.encode()
    files['LICENSE'] = b'Original private neural-semantic-highlighting Assembly tasks. No additional license grant.\n'
    for name, raw in files.items():
        path = root / name
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('Preserve prior original assembly source')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    lock = {'format': 'nsh-assembly-original-curriculum-v2', 'generatorHash': file_hash(Path(__file__)),
            'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}}
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock:
        raise ValueError('Preserve previous assembly source lock')
    path.write_text(json.dumps(lock, indent=2) + '\n')
    print(root, len(files) - 1, 'profile-addressed original assembly tasks')


if __name__ == '__main__':
    main()
