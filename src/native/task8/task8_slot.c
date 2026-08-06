typedef unsigned char uint8_t;
typedef unsigned int uint32_t;

#define TASK8_SLOT_SIZE 64u
#define TASK8_STATE_VALIDATION_SEED 0x43555354u
#define TASK8_CRC32_POLYNOMIAL 0xEDB88320u
#define TASK8_SCHEMA_VERSION 1u
#define TASK8_BLANK_CORE_DORMANT 0u
#define TASK8_BLANK_CORE_ID 0xF0u

/* Slot sentinels are ASCII "SU8C" and "OK8!". */
static const uint8_t Task8_DefaultSlot[TASK8_SLOT_SIZE] = {
    0x53, 0x55, 0x38, 0x43, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x01, 0x42, 0x6c, 0x61, 0x64, 0x65, 0x72,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x42, 0x6c,
    0x61, 0x6e, 0x6b, 0x20, 0x42, 0x65, 0x79, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xf0, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x4c, 0x31, 0x04, 0x45, 0x00, 0x00,
    0xf6, 0x4a, 0x43, 0x81, 0x4f, 0x4b, 0x38, 0x21,
};

static uint32_t Task8_ReadU32(const uint8_t *value) {
    return (uint32_t)value[0] |
           ((uint32_t)value[1] << 8) |
           ((uint32_t)value[2] << 16) |
           ((uint32_t)value[3] << 24);
}

static void Task8_WriteU32(uint8_t *output, uint32_t value) {
    output[0] = (uint8_t)value;
    output[1] = (uint8_t)(value >> 8);
    output[2] = (uint8_t)(value >> 16);
    output[3] = (uint8_t)(value >> 24);
}

static int Task8_AllowedNameByte(uint8_t value) {
    if (value == 0x20 || value == 0x27 || value == 0x2d) {
        return 1;
    }
    if (value >= '0' && value <= '9') {
        return 1;
    }
    if (value >= 'A' && value <= 'Z') {
        return 1;
    }
    if (value >= 'a' && value <= 'z') {
        return 1;
    }
    return 0;
}

static int Task8_ValidName(const uint8_t *name) {
    unsigned int length = 0;
    while (length < 12u && name[length] != 0) {
        if (!Task8_AllowedNameByte(name[length])) {
            return 0;
        }
        ++length;
    }
    if (length == 0u || name[0] == 0x20 || name[length - 1u] == 0x20) {
        return 0;
    }
    return 1;
}

static uint32_t Task8_HashStep(uint32_t value, uint8_t byte) {
    return (value << 5) - value + (uint32_t)byte;
}

static uint32_t Task8_HashName(uint32_t value, const uint8_t *name) {
    unsigned int index = 0;
    while (index < 12u && name[index] != 0) {
        value = Task8_HashStep(value, name[index]);
        ++index;
    }
    return value;
}

static uint32_t Task8_StateValidation(const uint8_t *slot) {
    static const uint8_t order[16] = {
        34, 35, 36, 37, 38, 39, 40, 41,
        42, 43, 44, 46, 47, 48, 49, 45,
    };
    uint32_t value = TASK8_STATE_VALIDATION_SEED;
    unsigned int index;

    value = Task8_HashStep(value, slot[8]);
    value = Task8_HashStep(value, slot[9]);
    value = Task8_HashName(value, slot + 10);
    value = Task8_HashName(value, slot + 22);
    for (index = 0; index < 16u; ++index) {
        value = Task8_HashStep(value, slot[order[index]]);
    }
    return value;
}

static uint32_t Task8_Crc32(const uint8_t *data, unsigned int length) {
    uint32_t crc = 0xffffffffu;
    unsigned int index;

    for (index = 0; index < length; ++index) {
        unsigned int bit;
        crc ^= (uint32_t)data[index];
        for (bit = 0; bit < 8u; ++bit) {
            uint32_t mask = (uint32_t)-(int)(crc & 1u);
            crc = (crc >> 1) ^ (TASK8_CRC32_POLYNOMIAL & mask);
        }
    }
    return ~crc;
}

static int Task8_FieldInvariantsValid(const uint8_t *slot) {
    static const uint8_t id_offsets[7] = {34, 35, 36, 38, 39, 40, 41};
    unsigned int index;

    if (slot[8] != TASK8_SCHEMA_VERSION) {
        return 0;
    }
    if (!Task8_ValidName(slot + 10) || !Task8_ValidName(slot + 22)) {
        return 0;
    }
    for (index = 0; index < 7u; ++index) {
        if (slot[id_offsets[index]] > 3u) {
            return 0;
        }
    }
    if (slot[37] != slot[34] || slot[37] > 3u) {
        return 0;
    }
    if (slot[42] != TASK8_BLANK_CORE_DORMANT || slot[43] != TASK8_BLANK_CORE_ID) {
        return 0;
    }
    if (slot[54] != 0u || slot[55] != 0u) {
        return 0;
    }
    return 1;
}

int Task8_ValidateSlot(const uint8_t *slot) {
    if (slot[0] != 'S' || slot[1] != 'U' || slot[2] != '8' || slot[3] != 'C') {
        return 0;
    }
    if (slot[60] != 'O' || slot[61] != 'K' || slot[62] != '8' || slot[63] != '!') {
        return 0;
    }
    if (!Task8_FieldInvariantsValid(slot)) {
        return 0;
    }
    if (Task8_ReadU32(slot + 50) != Task8_StateValidation(slot)) {
        return 0;
    }
    if (Task8_ReadU32(slot + 56) != Task8_Crc32(slot, 56u)) {
        return 0;
    }
    return 1;
}

int Task8_SealSlot(uint8_t *slot) {
    slot[0] = 'S';
    slot[1] = 'U';
    slot[2] = '8';
    slot[3] = 'C';
    slot[8] = TASK8_SCHEMA_VERSION;
    slot[37] = slot[34];
    slot[42] = TASK8_BLANK_CORE_DORMANT;
    slot[43] = TASK8_BLANK_CORE_ID;
    slot[54] = 0;
    slot[55] = 0;
    slot[60] = 'O';
    slot[61] = 'K';
    slot[62] = '8';
    slot[63] = '!';

    if (!Task8_FieldInvariantsValid(slot)) {
        return 0;
    }
    Task8_WriteU32(slot + 50, Task8_StateValidation(slot));
    Task8_WriteU32(slot + 56, Task8_Crc32(slot, 56u));
    return 1;
}

void Task8_InitializeDefaultSlot(uint8_t *slot) {
    unsigned int index;
    for (index = 0; index < TASK8_SLOT_SIZE; ++index) {
        slot[index] = Task8_DefaultSlot[index];
    }
}

void Task8_PrepareSlotForSave(uint8_t *slot) {
    if (!Task8_SealSlot(slot)) {
        Task8_InitializeDefaultSlot(slot);
    }
}

void Task8_ValidateOrDefaultSlot(uint8_t *slot) {
    if (!Task8_ValidateSlot(slot)) {
        Task8_InitializeDefaultSlot(slot);
    }
}

void Task8_CommitPlayerName(uint8_t *slot, const uint8_t *retail_name) {
    unsigned int index;
    for (index = 0; index < 12u; ++index) {
        slot[10u + index] = retail_name[index];
    }
    if (!Task8_SealSlot(slot)) {
        Task8_InitializeDefaultSlot(slot);
    }
}
