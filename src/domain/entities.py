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
    id: int
    day_of_week: int
    period: int

@dataclass
class Lesson:
    time_slot_id: int
    subject_id: str
    class_group_id: str
    teacher_id: int

@dataclass
class Schedule:
    lessons: list[Lesson]










