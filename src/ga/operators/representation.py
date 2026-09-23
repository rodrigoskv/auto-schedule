"""Representação da solução no algoritmo genético.

Indivíduo  = Schedule
Cromossomo = lista de Lesson
Gene       = uma Lesson (professor, disciplina, turma, horário)
"""

from typing import Callable

from domain.entities import TimeSlot

DAY_ORDER = {
    "segunda": 0,
    "terca": 1,
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sabado": 5,
    "domingo": 6,
}
SHIFT_ORDER = {"manha": 0, "tarde": 1, "noite": 2}


def order_by_day_shift_order(slot: TimeSlot) -> tuple:
    return (
        DAY_ORDER.get(slot.day_of_week, 99),
        SHIFT_ORDER.get(slot.shift, 99),
        slot.order,
    )


def order_by_global_order(slot: TimeSlot) -> int:
    return slot.global_order


def order_by_shift_then_day(slot: TimeSlot) -> tuple:
    return (
        SHIFT_ORDER.get(slot.shift, 99),
        DAY_ORDER.get(slot.day_of_week, 99),
        slot.order,
    )


SlotOrderingKey = Callable[[TimeSlot], object]

SLOT_ORDERING_STRATEGIES: dict[str, SlotOrderingKey] = {
    "day_shift_order": order_by_day_shift_order,
    "global_order": order_by_global_order,
    "shift_then_day": order_by_shift_then_day,
}
