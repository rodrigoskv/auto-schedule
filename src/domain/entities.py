from dataclasses import dataclass

@dataclass
class Teacher:
    id: str
    name: str
    avaliable_periods: list[str]

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

@dataclass
class Lesson:
    teacher_id: str
    subject_id: str
    class_group_id: str
    time_slot_id: str