.syntax unified
.cpu arm7tdmi
.thumb

/*
 * Task 8 native research hooks.
 *
 * The module preserves the confirmed New Game descriptor-selection behavior
 * and integrates one validated 64-byte SU8C custom-state slot with the retail
 * payload. Native EEPROM-tail writes remain disabled.
 *
 * The retail payload contains 83 translated records at +0x02E8. Each record
 * advances by 0x0C bytes while the original serializer and deserializer use
 * only the first ten bytes. The first 32 two-byte padding pairs provide the
 * 64-byte custom slot. These bytes remain inside the retail checksum and save
 * transaction.
 */

.equ Retail_SelectNewGameDescriptor, 0x08066391
.equ Retail_SerializeSavePayload, 0x08045199
.equ Retail_DeserializeSavePayload, 0x08045591
.equ Task8_RuntimeRootPointer, 0x03000198
.equ Task8_CustomSlotOffset, 0x000018C8
.equ Task8_PayloadSlotFirstOffset, 0x000002F2

.section .text,"ax",%progbits
.global Task8_NewGameHook
.global Task8_SavePayloadHook
.global Task8_LoadPayloadHook
.type Task8_NewGameHook,%function
.type Task8_SavePayloadHook,%function
.type Task8_LoadPayloadHook,%function

.thumb_func
Task8_NewGameHook:
    push {r4, lr}
    adds r4, r0, #0
    ldr r0, =Task8_RuntimeRootPointer
    ldr r0, [r0]
    ldr r1, =Task8_CustomSlotOffset
    adds r0, r0, r1
    bl Task8_InitializeDefaultSlot
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

/*
 * Use local Thumb veneers instead of allowing the linker to create ARM thunks.
 * Each literal stores the odd callable address of the retail Thumb routine.
 */
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

.ltorg
