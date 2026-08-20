import copy
import random

from domain.entities import Schedule
from ga.context import GAContext


def mutate(
    schedule: Schedule,
    context: GAContext,
    mutation_rate: float = 0.08,
) -> Schedule:
    mutated = copy.deepcopy(schedule)

    for group in context.class_groups:
        indices = [
            index
            for index, lesson in enumerate(mutated.lessons)
            if lesson.class_group_id == group.id
        ]
        if len(indices) < 2:
            continue

        occupied = mutated.occupied_slot_ids_for_class(group.id)
        free_slots = [slot.id for slot in context.slots_for_class(group.id) if slot.id not in occupied]

        for index in indices:
            if random.random() >= mutation_rate:
                continue

            lesson = mutated.lessons[index]
            if free_slots and (not lesson.time_slot_id or random.random() < 0.35):
                target = random.choice(free_slots)
                if lesson.time_slot_id:
                    free_slots.append(lesson.time_slot_id)
                lesson.time_slot_id = target
                free_slots.remove(target)
                continue

            other_index = random.choice([item for item in indices if item != index])
            mutated.lessons[index].time_slot_id, mutated.lessons[other_index].time_slot_id = (
                mutated.lessons[other_index].time_slot_id,
                mutated.lessons[index].time_slot_id,
            )

    return mutated