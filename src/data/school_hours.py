"""Grade da escola → TimeSlot."""

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
SHIFT_LABEL = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}
DAYS = list(DAY_LABEL)

DAY_ALIASES = {
    "segunda": ("segunda", "seg", "monday", "mon"),
    "terca": ("terca", "terça", "ter", "tuesday", "tue"),
    "quarta": ("quarta", "qua", "wednesday", "wed"),
    "quinta": ("quinta", "qui", "thursday", "thu", "thur", "thurs"),
    "sexta": ("sexta", "sex", "friday", "fri"),
    "sabado": ("sabado", "sábado", "sab", "saturday", "sat"),
}
SHIFT_ALIASES = {
    "manha": ("manha", "manhã", "morning", "am"),
    "tarde": ("tarde", "afternoon", "pm"),
    "noite": ("noite", "evening", "night"),
}


def _alias_map(groups: dict[str, tuple[str, ...]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canon, aliases in groups.items():
        mapping[canon] = canon
        for alias in aliases:
            mapping[slugify(alias)] = canon
    return mapping


_DAY_CANON = _alias_map(DAY_ALIASES)
_SHIFT_CANON = _alias_map(SHIFT_ALIASES)


def day_column_names(day: str) -> tuple[str, ...]:
    return DAY_ALIASES.get(day, (day,))


@dataclass
class SchoolHours:
    days: list[str] = field(default_factory=lambda: ["segunda", "terca", "quarta", "quinta", "sexta"])
    periods_per_day: int = 5
    shift: str = "manha"

    @property
    def slots_per_class(self) -> int:
        return len(self.days) * self.periods_per_day


def normalize_day(value: str) -> str:
    key = slugify(str(value))
    return _DAY_CANON.get(key, key)


def normalize_shift(value: str) -> str:
    key = slugify(str(value))
    return _SHIFT_CANON.get(key, key)


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
        raise ValueError("grade precisa de school_days, shift e lessons_per_day.")
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


def hours_from_slots(slots: list[TimeSlot]) -> SchoolHours:
    days = list(dict.fromkeys(slot.day_of_week for slot in slots))
    return SchoolHours(
        days=days,
        periods_per_day=max((slot.order for slot in slots), default=1),
        shift=slots[0].shift if slots else "manha",
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
