"""Grade da escola (dias, turno, aulas por dia) → lista de TimeSlot."""

from dataclasses import dataclass, field

from data.ids import slugify
from domain.entities import TimeSlot

DAY_LABEL = {
    "segunda": "Segunda",
    "terca": "Terça",
    "quarta": "Quarta",
    "quinta": "Quinta",
    "sexta": "Sexta",
    "sabado": "Sábado",
}


@dataclass
class SchoolHours:
    days: list[str] = field(default_factory=lambda: ["segunda", "terca", "quarta", "quinta", "sexta"])
    periods_per_day: int = 5
    shift: str = "manha"

    @property
    def slots_per_class(self) -> int:
        return len(self.days) * self.periods_per_day


def normalize_day(value: str) -> str:
    return slugify(str(value))


def normalize_shift(value: str) -> str:
    return slugify(str(value))


def parse_days(value) -> list[str]:
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = [part.strip() for part in str(value).replace(";", ",").split(",") if part.strip()]
    days = [normalize_day(item) for item in items if str(item).strip()]
    if not days:
        raise ValueError("school_days não pode ser vazio.")
    return days


def hours_from_grade(data: dict) -> SchoolHours:
    if not isinstance(data, dict):
        raise ValueError("grade precisa ser um objeto com school_days, shift e lessons_per_day.")
    days = data.get("school_days")
    shift = data.get("shift")
    lessons = data.get("lessons_per_day")
    if not days or shift in (None, "") or lessons is None:
        raise ValueError("grade precisa de school_days, shift e lessons_per_day.")
    periods = int(lessons)
    if periods < 1:
        raise ValueError("lessons_per_day deve ser >= 1.")
    return SchoolHours(
        days=parse_days(days),
        periods_per_day=periods,
        shift=normalize_shift(str(shift)),
    )


def build_time_slots(hours: SchoolHours) -> list[TimeSlot]:
    slots: list[TimeSlot] = []
    global_order = 1
    for day in hours.days:
        for order in range(1, hours.periods_per_day + 1):
            slots.append(
                TimeSlot(
                    id=f"{day}_{hours.shift}_{order}",
                    day_of_week=day,
                    shift=hours.shift,
                    order=order,
                    global_order=global_order,
                    label=f"{DAY_LABEL.get(day, day)} {order}º aula",
                )
            )
            global_order += 1
    return slots