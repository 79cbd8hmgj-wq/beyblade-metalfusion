.syntax unified
.cpu arm7tdmi
.thumb

/*
 * Task 8 research hook.
 *
 * The retail BL at 0x080652FA enters this wrapper with r0 == 10. The wrapper
 * preserves LR, calls the original retail scene-descriptor selector at
 * 0x08066390, and returns to 0x080652FE. It deliberately adds no creator logic
 * yet; this is the behavior-preserving proof that the deterministic expansion
 * module and guarded branch hook execute safely.
 */
.section .text.Task8_NewGameHook,"ax",%progbits
.global Task8_NewGameHook
.type Task8_NewGameHook,%function
.thumb_func
Task8_NewGameHook:
    push {lr}
    bl Retail_SelectNewGameDescriptor
    pop {pc}
.size Task8_NewGameHook, .-Task8_NewGameHook
