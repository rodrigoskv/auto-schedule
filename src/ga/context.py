"""Dados da escola indexados para o AG.

Subject entra na turma pelo class_group_id (campo explícito, não pelo prefixo do id).
"""

from dataclasses import dataclass, field

from domain.entities import ClassGroup, SchoolInstance, Subject, Teacher, TimeSlot
from ga.operators.representation import SlotOrderingKey, order_by_shift_then_day


@dataclass
class GAContext:
    teachers: list[Teacher]
    class_groups: list[ClassGroup]
    subjects: list[Subject]
    time_slots: list[TimeSlot]
    slot_ordering_key: SlotOrderingKey = field(default=order_by_shift_then_day)

    def __post_init__(self) -> None:
        self.teachers_by_id = {teacher.id: teacher for teacher in self.teachers}
        self.subjects_by_id = {subject.id: subject for subject in self.subjects}
        self.class_groups_by_id = {group.id: group for group in self.class_groups}
        self.time_slots_by_id = {slot.id: slot for slot in self.time_slots}

        self.subjects_by_class_group: dict[str, list[Subject]] = {}
        for subject in self.subjects:
            self.subjects_by_class_group.setdefault(subject.class_group_id, []).append(subject)

        self.ordered_slots = sorted(self.time_slots, key=self.slot_ordering_key)

    @classmethod
    def from_school(cls, school: SchoolInstance) -> "GAContext":
        return cls(
            teachers=school.teachers,
            class_groups=school.class_groups,
            subjects=school.subjects,
            time_slots=school.time_slots,
        )

    def slots_for_class(self, class_group_id: str) -> list[TimeSlot]:
        group = self.class_groups_by_id.get(class_group_id)
        if group is None or group.shift is None:
            return list(self.ordered_slots)
        return [slot for slot in self.ordered_slots if slot.shift == group.shift]

    def is_teacher_available(self, teacher_id: str, time_slot_id: str) -> bool:
        teacher = self.teachers_by_id.get(teacher_id)
        slot = self.time_slots_by_id.get(time_slot_id)
        if teacher is None or slot is None:
            return False
        return teacher.is_available_for(slot)

    def required_lessons_for_class(self, class_group_id: str) -> list[tuple[str, str]]:
        """Uma entrada (subject_id, teacher_id) para cada aula semanal da turma."""
        pool: list[tuple[str, str]] = []
        for subject in self.subjects_by_class_group.get(class_group_id, []):
            pool.extend([(subject.id, subject.teacher_id)] * subject.weekly_workload)
        return pool
