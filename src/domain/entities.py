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
    order: int

@dataclass
class Lesson:
    teacher_id: str
    subject_id: str
    class_group_id: str
    time_slot_id: str