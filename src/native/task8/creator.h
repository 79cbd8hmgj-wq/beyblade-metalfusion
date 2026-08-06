#ifndef TASK8_CREATOR_H
#define TASK8_CREATOR_H

typedef unsigned char Task8CreatorByte;

#define TASK8_CREATOR_STAGE_PLAYER_NAME 0u
#define TASK8_CREATOR_STAGE_BEY_NAME 1u
#define TASK8_CREATOR_STAGE_AVATAR 2u
#define TASK8_CREATOR_STAGE_SKIN 3u
#define TASK8_CREATOR_STAGE_HAIR 4u
#define TASK8_CREATOR_STAGE_OUTFIT 5u
#define TASK8_CREATOR_STAGE_PORTRAIT 6u
#define TASK8_CREATOR_STAGE_ORIGIN 7u
#define TASK8_CREATOR_STAGE_TENDENCY 8u
#define TASK8_CREATOR_STAGE_CONFIRM 9u
#define TASK8_CREATOR_COMPLETE 0x80u

void Task8_CreatorInit(Task8CreatorByte *slot);
void Task8_CreatorRefresh(
    void *scene,
    Task8CreatorByte *slot,
    Task8CreatorByte *retail_name
);
void Task8_CreatorCommit(
    void *scene,
    Task8CreatorByte *slot,
    const Task8CreatorByte *input,
    Task8CreatorByte *retail_name
);
void Task8_CreatorBack(
    void *scene,
    Task8CreatorByte *slot,
    Task8CreatorByte *retail_name
);

#endif
