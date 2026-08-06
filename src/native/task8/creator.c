#include "creator.h"

typedef unsigned int uint32_t;
typedef unsigned char uint8_t;

#define TASK8_SLOT_INITIALIZED_OFFSET 9u
#define TASK8_SLOT_PLAYER_NAME_OFFSET 10u
#define TASK8_SLOT_BEY_NAME_OFFSET 22u
#define TASK8_SLOT_AVATAR_OFFSET 34u
#define TASK8_SLOT_PORTRAIT_OFFSET 35u
#define TASK8_SLOT_SKIN_OFFSET 36u
#define TASK8_SLOT_HAIR_STYLE_OFFSET 37u
#define TASK8_SLOT_HAIR_PALETTE_OFFSET 38u
#define TASK8_SLOT_OUTFIT_OFFSET 39u
#define TASK8_SLOT_ORIGIN_OFFSET 40u
#define TASK8_SLOT_TENDENCY_OFFSET 41u
#define TASK8_SLOT_FUTURE_FLAGS_OFFSET 45u
#define TASK8_SCENE_TEXT_HANDLE_OFFSET 0x234u
#define TASK8_SCENE_ACTIVE_FLAG_OFFSET 0x2D5u
#define TASK8_SCENE_PHASE_OFFSET 0x2FCu
#define TASK8_SCENE_CURSOR_COLUMN_OFFSET 0x304u
#define TASK8_SCENE_CURSOR_ROW_OFFSET 0x308u
#define TASK8_TEXT_OBJECT_STRIDE 0x30u
#define TASK8_TEXT_STYLE 15u
#define TASK8_NAME_BYTES 12u
#define TASK8_RETAIL_NAME_BYTES 16u
#define TASK8_KEYBOARD_BUFFER_POINTER 0x030009ACu

extern void Task8_InitializeDefaultSlot(uint8_t *slot);
extern int Task8_SealSlot(uint8_t *slot);
extern void Task8_CallRetailSetText(
    void *object,
    const uint8_t *text,
    unsigned int style
);
extern void Task8_CallRetailUpdateNameCursor(void *scene);

static const uint8_t Task8_PromptPlayerName[] = "Blader name";
static const uint8_t Task8_PromptBeyName[] = "Bey name";
static const uint8_t Task8_PromptAvatar[] = "Avatar 1-4";
static const uint8_t Task8_PromptSkin[] = "Skin 1-4";
static const uint8_t Task8_PromptHair[] = "Hair 1-4";
static const uint8_t Task8_PromptOutfit[] = "Outfit 1-4";
static const uint8_t Task8_PromptPortrait[] = "Portrait 1-4";
static const uint8_t Task8_PromptOrigin[] = "Origin 1-4";
static const uint8_t Task8_PromptTendency[] = "Style 1-4";
static const uint8_t Task8_PromptConfirm[] = "Confirm Y/N";

const uint8_t *const Task8_PromptBladerNameRow[5] = {
    Task8_PromptPlayerName,
    Task8_PromptPlayerName,
    Task8_PromptPlayerName,
    Task8_PromptPlayerName,
    Task8_PromptPlayerName,
};

static uint8_t *Task8_KeyboardBuffer(void) {
    return *(uint8_t **)(unsigned long)TASK8_KEYBOARD_BUFFER_POINTER;
}

static void Task8_Clear(uint8_t *output, unsigned int length) {
    unsigned int index;
    for (index = 0; index < length; ++index) {
        output[index] = 0;
    }
}

static void Task8_CopyName(uint8_t *output, const uint8_t *input) {
    unsigned int index;
    for (index = 0; index < TASK8_NAME_BYTES; ++index) {
        output[index] = input[index];
    }
}

static void Task8_RestoreRetailPlayerName(
    uint8_t *retail_name,
    const uint8_t *slot
) {
    Task8_Clear(retail_name, TASK8_RETAIL_NAME_BYTES);
    Task8_CopyName(
        retail_name,
        slot + TASK8_SLOT_PLAYER_NAME_OFFSET
    );
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
    while (length < TASK8_NAME_BYTES && name[length] != 0) {
        if (!Task8_AllowedNameByte(name[length])) {
            return 0;
        }
        ++length;
    }
    if (
        length == 0u ||
        name[0] == 0x20 ||
        name[length - 1u] == 0x20
    ) {
        return 0;
    }
    return 1;
}

static unsigned int Task8_Stage(const uint8_t *slot) {
    return (unsigned int)(
        slot[TASK8_SLOT_FUTURE_FLAGS_OFFSET] & 0x0fu
    );
}

static void Task8_SetStage(uint8_t *slot, unsigned int stage) {
    slot[TASK8_SLOT_FUTURE_FLAGS_OFFSET] = (uint8_t)(stage & 0x0fu);
}

static unsigned int Task8_Option(const uint8_t *input) {
    unsigned int index = 0;
    while (index < TASK8_RETAIL_NAME_BYTES && input[index] != 0) {
        if (input[index] >= '1' && input[index] <= '4') {
            return (unsigned int)(input[index] - '1');
        }
        ++index;
    }
    return 0u;
}

static uint8_t Task8_LastCharacter(const uint8_t *input) {
    unsigned int index = 0;
    uint8_t value = 0;
    while (index < TASK8_RETAIL_NAME_BYTES && input[index] != 0) {
        value = input[index];
        ++index;
    }
    return value;
}

static const uint8_t *Task8_Prompt(unsigned int stage) {
    static const uint8_t *const prompts[10] = {
        Task8_PromptPlayerName,
        Task8_PromptBeyName,
        Task8_PromptAvatar,
        Task8_PromptSkin,
        Task8_PromptHair,
        Task8_PromptOutfit,
        Task8_PromptPortrait,
        Task8_PromptOrigin,
        Task8_PromptTendency,
        Task8_PromptConfirm,
    };
    if (stage > TASK8_CREATOR_STAGE_CONFIRM) {
        stage = TASK8_CREATOR_STAGE_PLAYER_NAME;
    }
    return prompts[stage];
}

static uint8_t *Task8_TextObjects(void *scene) {
    uint8_t *holder = *(uint8_t **)(
        (uint8_t *)scene + TASK8_SCENE_TEXT_HANDLE_OFFSET
    );
    if (holder == 0) {
        return 0;
    }
    return *(uint8_t **)holder;
}

static void Task8_AppendOption(
    uint8_t *output,
    unsigned int *position,
    uint8_t label,
    uint8_t value
) {
    output[(*position)++] = label;
    output[(*position)++] = (uint8_t)('1' + (value & 3u));
}

static void Task8_BuildSummary(
    uint8_t *prompt,
    uint8_t *input,
    const uint8_t *slot
) {
    unsigned int prompt_position = 0;
    unsigned int input_position = 0;
    Task8_Clear(prompt, TASK8_RETAIL_NAME_BYTES);
    Task8_Clear(input, TASK8_RETAIL_NAME_BYTES);

    Task8_AppendOption(
        prompt,
        &prompt_position,
        'A',
        slot[TASK8_SLOT_AVATAR_OFFSET]
    );
    prompt[prompt_position++] = ' ';
    Task8_AppendOption(
        prompt,
        &prompt_position,
        'S',
        slot[TASK8_SLOT_SKIN_OFFSET]
    );
    prompt[prompt_position++] = ' ';
    Task8_AppendOption(
        prompt,
        &prompt_position,
        'H',
        slot[TASK8_SLOT_HAIR_PALETTE_OFFSET]
    );
    prompt[prompt_position++] = ' ';
    Task8_AppendOption(
        prompt,
        &prompt_position,
        'O',
        slot[TASK8_SLOT_OUTFIT_OFFSET]
    );

    Task8_AppendOption(
        input,
        &input_position,
        'P',
        slot[TASK8_SLOT_PORTRAIT_OFFSET]
    );
    input[input_position++] = ' ';
    Task8_AppendOption(
        input,
        &input_position,
        'R',
        slot[TASK8_SLOT_ORIGIN_OFFSET]
    );
    input[input_position++] = ' ';
    Task8_AppendOption(
        input,
        &input_position,
        'T',
        slot[TASK8_SLOT_TENDENCY_OFFSET]
    );
    input[input_position++] = ' ';
    input[input_position++] = 'Y';
}

void Task8_CreatorInit(uint8_t *slot) {
    Task8_InitializeDefaultSlot(slot);
    slot[TASK8_SLOT_INITIALIZED_OFFSET] = 0u;
    Task8_SetStage(slot, TASK8_CREATOR_STAGE_PLAYER_NAME);
    Task8_SealSlot(slot);
}

void Task8_CreatorRefresh(
    void *scene,
    uint8_t *slot,
    uint8_t *retail_name
) {
    unsigned int stage = Task8_Stage(slot);
    uint8_t *buffer = Task8_KeyboardBuffer();
    uint8_t *text = Task8_TextObjects(scene);
    const uint8_t *prompt = Task8_Prompt(stage);

    if (buffer == 0) {
        return;
    }
    Task8_Clear(buffer, TASK8_RETAIL_NAME_BYTES);
    if (stage == TASK8_CREATOR_STAGE_CONFIRM) {
        Task8_BuildSummary(retail_name, buffer, slot);
        prompt = retail_name;
    } else {
        Task8_RestoreRetailPlayerName(retail_name, slot);
    }

    *(uint32_t *)(
        (uint8_t *)scene + TASK8_SCENE_PHASE_OFFSET
    ) = 1u;
    *((uint8_t *)scene + TASK8_SCENE_ACTIVE_FLAG_OFFSET) = 0u;
    *(uint32_t *)(
        (uint8_t *)scene + TASK8_SCENE_CURSOR_COLUMN_OFFSET
    ) = 0u;
    *(uint32_t *)(
        (uint8_t *)scene + TASK8_SCENE_CURSOR_ROW_OFFSET
    ) = 0u;

    if (text != 0) {
        Task8_CallRetailSetText(text, prompt, TASK8_TEXT_STYLE);
        Task8_CallRetailSetText(
            text + TASK8_TEXT_OBJECT_STRIDE,
            buffer,
            TASK8_TEXT_STYLE
        );
    }
    Task8_CallRetailUpdateNameCursor(scene);
}

void Task8_CreatorCommit(
    void *scene,
    uint8_t *slot,
    const uint8_t *input,
    uint8_t *retail_name
) {
    unsigned int stage = Task8_Stage(slot);
    unsigned int option;
    uint8_t final_character;

    if (
        stage == TASK8_CREATOR_STAGE_PLAYER_NAME ||
        stage == TASK8_CREATOR_STAGE_BEY_NAME
    ) {
        if (!Task8_ValidName(input)) {
            Task8_RestoreRetailPlayerName(retail_name, slot);
            Task8_CreatorRefresh(scene, slot, retail_name);
            return;
        }
        if (stage == TASK8_CREATOR_STAGE_PLAYER_NAME) {
            Task8_CopyName(
                slot + TASK8_SLOT_PLAYER_NAME_OFFSET,
                input
            );
        } else {
            Task8_CopyName(
                slot + TASK8_SLOT_BEY_NAME_OFFSET,
                input
            );
        }
        Task8_SetStage(slot, stage + 1u);
        Task8_SealSlot(slot);
        Task8_RestoreRetailPlayerName(retail_name, slot);
        Task8_CreatorRefresh(scene, slot, retail_name);
        return;
    }

    if (
        stage >= TASK8_CREATOR_STAGE_AVATAR &&
        stage <= TASK8_CREATOR_STAGE_TENDENCY
    ) {
        option = Task8_Option(input);
        if (stage == TASK8_CREATOR_STAGE_AVATAR) {
            slot[TASK8_SLOT_AVATAR_OFFSET] = (uint8_t)option;
            slot[TASK8_SLOT_HAIR_STYLE_OFFSET] = (uint8_t)option;
        } else if (stage == TASK8_CREATOR_STAGE_SKIN) {
            slot[TASK8_SLOT_SKIN_OFFSET] = (uint8_t)option;
        } else if (stage == TASK8_CREATOR_STAGE_HAIR) {
            slot[TASK8_SLOT_HAIR_PALETTE_OFFSET] = (uint8_t)option;
        } else if (stage == TASK8_CREATOR_STAGE_OUTFIT) {
            slot[TASK8_SLOT_OUTFIT_OFFSET] = (uint8_t)option;
        } else if (stage == TASK8_CREATOR_STAGE_PORTRAIT) {
            slot[TASK8_SLOT_PORTRAIT_OFFSET] = (uint8_t)option;
        } else if (stage == TASK8_CREATOR_STAGE_ORIGIN) {
            slot[TASK8_SLOT_ORIGIN_OFFSET] = (uint8_t)option;
        } else {
            slot[TASK8_SLOT_TENDENCY_OFFSET] = (uint8_t)option;
        }
        Task8_SetStage(slot, stage + 1u);
        Task8_SealSlot(slot);
        Task8_RestoreRetailPlayerName(retail_name, slot);
        Task8_CreatorRefresh(scene, slot, retail_name);
        return;
    }

    final_character = Task8_LastCharacter(input);
    if (final_character == 'Y' || final_character == 'y') {
        slot[TASK8_SLOT_INITIALIZED_OFFSET] = 1u;
        slot[TASK8_SLOT_FUTURE_FLAGS_OFFSET] = TASK8_CREATOR_COMPLETE;
        Task8_SealSlot(slot);
        Task8_RestoreRetailPlayerName(retail_name, slot);
        return;
    }
    if (final_character == 'N' || final_character == 'n') {
        Task8_CreatorInit(slot);
    }
    Task8_CreatorRefresh(scene, slot, retail_name);
}

void Task8_CreatorBack(
    void *scene,
    uint8_t *slot,
    uint8_t *retail_name
) {
    unsigned int stage = Task8_Stage(slot);
    if (stage == TASK8_CREATOR_STAGE_PLAYER_NAME) {
        *(uint32_t *)(
            (uint8_t *)scene + TASK8_SCENE_PHASE_OFFSET
        ) = 2u;
        return;
    }
    Task8_SetStage(slot, stage - 1u);
    Task8_SealSlot(slot);
    Task8_RestoreRetailPlayerName(retail_name, slot);
    Task8_CreatorRefresh(scene, slot, retail_name);
}
