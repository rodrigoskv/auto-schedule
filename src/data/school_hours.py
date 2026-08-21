from dataclasses import dataclass, field

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