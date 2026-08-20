from dataclasses import dataclass, field


@dataclass
class Teacher:
    id: str
    name: str
    available_periods: list[str]

    def is_available_for(self, slot: "TimeSlot") -> bool:
        """available_periods usa a chave dia_turno, ex.: segunda_manha."""
        if not self.available_periods:
            return True
        return slot.period_key in self.available_periods


@dataclass
class ClassGroup:
    id: str
    name: str
    shift: str | None = None


@dataclass
class Subject:
    id: str
    name: str
    weekly_workload: int
    teacher_id: str


@dataclass
class TimeSlot:
    id: str
    day_of_week: str
    shift: str
    order: int
    global_order: int
    label: str | None = None

    @property
    def period_key(self) -> str:
        return f"{self.day_of_week}_{self.shift}"


@dataclass
class Lesson:
    teacher_id: str
    subject_id: str
    class_group_id: str
    time_slot_id: str


@dataclass
class Schedule:
    lessons: list[Lesson] = field(default_factory=list)

    def add_lesson(self, lesson: Lesson) -> None:
        self.lessons.append(lesson)

    def get_lessons_for_teacher(self, teacher_id: str) -> list[Lesson]:
        return [lesson for lesson in self.lessons if lesson.teacher_id == teacher_id]

    def get_lessons_for_class_group(self, class_group_id: str) -> list[Lesson]:
        return [lesson for lesson in self.lessons if lesson.class_group_id == class_group_id]

    def get_lessons_for_subject(self, subject_id: str) -> list[Lesson]:
        return [lesson for lesson in self.lessons if lesson.subject_id == subject_id]

    def get_lessons_for_time_slot(self, time_slot_id: str) -> list[Lesson]:
        if not time_slot_id:
            return []
        return [lesson for lesson in self.lessons if lesson.time_slot_id == time_slot_id]

    def get_cell_lessons(self, time_slot_id: str, class_group_id: str) -> list[Lesson]:
        if not time_slot_id:
            return []
        return [
            lesson
            for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.class_group_id == class_group_id
        ]

    def get_teacher_cell_lesson(self, time_slot_id: str, teacher_id: str) -> list[Lesson]:
        if not time_slot_id:
            return []
        return [
            lesson
            for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.teacher_id == teacher_id
        ]

    def get_unassigned_lessons(self) -> list[Lesson]:
        return [lesson for lesson in self.lessons if not lesson.time_slot_id]

    def occupied_slot_ids_for_class(self, class_group_id: str) -> set[str]:
        return {
            lesson.time_slot_id
            for lesson in self.lessons
            if lesson.class_group_id == class_group_id and lesson.time_slot_id
        }

    def get_lessons_for_class_group_by_day_and_shift(
        self,
        class_group_id: str,
        day_of_week: str,
        shift: str,
        time_slots: list[TimeSlot],
    ) -> list[Lesson]:
        valid_time_slot_ids = {
            time_slot.id
            for time_slot in time_slots
            if time_slot.day_of_week == day_of_week and time_slot.shift == shift
        }
        return [
            lesson
            for lesson in self.lessons
            if lesson.class_group_id == class_group_id and lesson.time_slot_id in valid_time_slot_ids
        ]

    def matrix_view(
        self,
        time_slots: list[TimeSlot],
        class_groups: list[ClassGroup],
    ) -> dict[str, dict[str, dict[str, dict[str, list[Lesson]]]]]:
        matrix: dict[str, dict[str, dict[str, dict[str, list[Lesson]]]]] = {}

        ordered_time_slots = sorted(
            time_slots,
            key=lambda time_slot: (time_slot.day_of_week, time_slot.shift, time_slot.order),
        )

        for time_slot in ordered_time_slots:
            matrix.setdefault(time_slot.day_of_week, {})
            matrix[time_slot.day_of_week].setdefault(time_slot.shift, {})
            matrix[time_slot.day_of_week][time_slot.shift][time_slot.id] = {}

            for class_group in class_groups:
                matrix[time_slot.day_of_week][time_slot.shift][time_slot.id][class_group.id] = (
                    self.get_cell_lessons(
                        time_slot_id=time_slot.id,
                        class_group_id=class_group.id,
                    )
                )

        return matrix