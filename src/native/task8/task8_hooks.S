.syntax unified
.cpu arm7tdmi
.thumb

/*
 * Task 8 native research hooks.
 *
 * The module integrates one validated 64-byte SU8C custom-state slot with the
 * retail payload and reuses the retail name-entry scene as the Tier-A creator.
 * Native EEPROM-tail writes remain disabled.
 */

.equ Retail_SelectNewGameDescriptor, 0x08066391
.equ Retail_SerializeSavePayload, 0x08045199
.equ Retail_DeserializeSavePayload, 0x08045591
.equ Retail_CopyBytes, 0x08073219
.equ Retail_SetText, 0x08070AD5
.equ Retail_UpdateNameCursor, 0x08066AD5
.equ Task8_RuntimeRootPointer, 0x03000198
.equ Task8_CustomSlotOffset, 0x000018C8
.equ Task8_RetailNameOffset, 0x00000858
.equ Task8_PayloadSlotFirstOffset, 0x000002F2

.section .text.task8_entry,"ax",%progbits
.global Task8_NewGameHook
.global Task8_SavePayloadHook
.global Task8_LoadPayloadHook
.global Task8_NameCommitHook
.global Task8_CreatorBackHook
.global Task8_CallRetailSetText
.global Task8_CallRetailUpdateNameCursor
.type Task8_NewGameHook,%function
.type Task8_SavePayloadHook,%function
.type Task8_LoadPayloadHook,%function
.type Task8_NameCommitHook,%function
.type Task8_CreatorBackHook,%function

.thumb_func
Task8_NewGameHook:
    push {r4, lr}
    adds r4, r0, #0
    ldr r0, =Task8_RuntimeRootPointer
    ldr r0, [r0]
    ldr r1, =Task8_CustomSlotOffset
    adds r0, r0, r1
    bl Task8_CreatorInit
    adds r0, r4, #0
    bl Task8_CallSelectNewGameDescriptor
    pop {r4, pc}
.size Task8_NewGameHook, .-Task8_NewGameHook

.align 2
.thumb_func
Task8_SavePayloadHook:
    push {r4-r7, lr}
    adds r4, r0, #0
    bl Task8_CallSerializeSavePayload

    ldr r5, =Task8_RuntimeRootPointer
    ldr r5, [r5]
    ldr r0, =Task8_CustomSlotOffset
    adds r5, r5, r0
    adds r0, r5, #0
    bl Task8_PrepareSlotForSave
    ldr r0, =Task8_PayloadSlotFirstOffset
    adds r4, r4, r0
    movs r6, #32
1:
    ldrb r0, [r5, #0]
    strb r0, [r4, #0]
    ldrb r0, [r5, #1]
    strb r0, [r4, #1]
    adds r5, #2
    adds r4, #12
    subs r6, #1
    bne 1b
    pop {r4-r7, pc}
.size Task8_SavePayloadHook, .-Task8_SavePayloadHook

.align 2
.thumb_func
Task8_LoadPayloadHook:
    push {r4-r7, lr}
    adds r4, r0, #0
    bl Task8_CallDeserializeSavePayload

    ldr r5, =Task8_RuntimeRootPointer
    ldr r5, [r5]
    ldr r0, =Task8_CustomSlotOffset
    adds r5, r5, r0
    adds r7, r5, #0
    ldr r0, =Task8_PayloadSlotFirstOffset
    adds r4, r4, r0
    movs r6, #32
2:
    ldrb r0, [r4, #0]
    strb r0, [r5, #0]
    ldrb r0, [r4, #1]
    strb r0, [r5, #1]
    adds r4, #12
    adds r5, #2
    subs r6, #1
    bne 2b
    adds r0, r7, #0
    bl Task8_ValidateOrDefaultSlot
    pop {r4-r7, pc}
.size Task8_LoadPayloadHook, .-Task8_LoadPayloadHook

.align 2
.thumb_func
Task8_NameCommitHook:
    push {r4-r7, lr}
    adds r5, r0, #0
    adds r6, r1, #0
    bl Task8_CallRetailCopyBytes

    ldr r1, =Task8_RuntimeRootPointer
    ldr r1, [r1]
    ldr r0, =Task8_CustomSlotOffset
    adds r1, r1, r0
    adds r0, r4, #0
    adds r2, r5, #0
    adds r3, r6, #0
    bl Task8_CreatorCommit
    pop {r4-r7, pc}
.size Task8_NameCommitHook, .-Task8_NameCommitHook

.align 2
.thumb_func
Task8_CreatorBackHook:
    push {r4-r7, lr}
    ldr r1, =Task8_RuntimeRootPointer
    ldr r1, [r1]
    ldr r0, =Task8_CustomSlotOffset
    adds r1, r1, r0
    ldr r2, =Task8_RetailNameOffset
    adds r2, r2, r1
    ldr r0, =Task8_CustomSlotOffset
    subs r2, r2, r0
    adds r0, r7, #0
    bl Task8_CreatorBack
    pop {r4-r7, pc}
.size Task8_CreatorBackHook, .-Task8_CreatorBackHook

/* Local Thumb veneers keep retail calls in Thumb state. */
.align 2
.thumb_func
Task8_CallSelectNewGameDescriptor:
    ldr r3, =Retail_SelectNewGameDescriptor
    bx r3

.align 2
.thumb_func
Task8_CallSerializeSavePayload:
    ldr r3, =Retail_SerializeSavePayload
    bx r3

.align 2
.thumb_func
Task8_CallDeserializeSavePayload:
    ldr r3, =Retail_DeserializeSavePayload
    bx r3

.align 2
.thumb_func
Task8_CallRetailCopyBytes:
    ldr r3, =Retail_CopyBytes
    bx r3

.align 2
.thumb_func
Task8_CallRetailSetText:
    ldr r3, =Retail_SetText
    bx r3

.align 2
.thumb_func
Task8_CallRetailUpdateNameCursor:
    ldr r3, =Retail_UpdateNameCursor
    bx r3

.ltorg
