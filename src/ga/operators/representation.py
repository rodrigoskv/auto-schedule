"""Representação da solução no algoritmo genético.

Indivíduo  = Schedule
Cromossomo = lista de Lesson
Gene       = uma Lesson (professor, disciplina, turma, horário)
"""

from typing import Callable

from domain.entities import Schedule, TimeSlot


def order_by_day_shift_order(slot: TimeSlot) -> tuple:
    """Ordena por (dia, turno, ordem)."""
    day_order = {
        "segunda": 0,
        "terca": 1,
        "quarta": 2,
        "quinta": 3,
        "sexta": 4,
        "sabado": 5,
        "domingo": 6,
    }
    shift_order = {"manha": 0, "tarde": 1, "noite": 2}
    return (
        day_order.get(slot.day_of_week, 99),
        shift_order.get(slot.shift, 99),
        slot.order,
    )


def order_by_global_order(slot: TimeSlot) -> int:
    return slot.global_order


def order_by_shift_then_day(slot: TimeSlot) -> tuple:
    """Agrupa primeiro por turno, depois por dia e ordem."""
    shift_order = {"manha": 0, "tarde": 1, "noite": 2}
    day_order = {
        "segunda": 0,
        "terca": 1,
        "quarta": 2,
        "quinta": 3,
        "sexta": 4,
        "sabado": 5,
        "domingo": 6,
    }
    return (
        shift_order.get(slot.shift, 99),
        day_order.get(slot.day_of_week, 99),
        slot.order,
    )


SlotOrderingKey = Callable[[TimeSlot], object]

SLOT_ORDERING_STRATEGIES: dict[str, SlotOrderingKey] = {
    "day_shift_order": order_by_day_shift_order,
    "global_order": order_by_global_order,
    "shift_then_day": order_by_shift_then_day,
}


def lessons_for_class(schedule: Schedule, class_group_id: str) -> list:
    """Segmento do cromossomo correspondente a uma turma."""
    return schedule.get_lessons_for_class_group(class_group_id)