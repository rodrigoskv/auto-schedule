"""
Representação genética de um indivíduo (horário completo).

Um indivíduo é um Schedule — uma lista de Lessons que mapeia cada
(class_group, time_slot) -> subject (e consequentemente teacher).

"""

from __future__ import annotations
from typing import Callable
from domain.entities import Teacher, ClassGroup, Subject, TimeSlot


def order_by_day_shift_order(slot: TimeSlot) -> tuple:
    """Ordena por (dia_da_semana, turno, ordem). Padrão pt-BR."""
    DAY_ORDER = {
        "segunda": 0, "terca": 1, "quarta": 2,
        "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6,
    }
    SHIFT_ORDER = {"manha": 0, "tarde": 1, "noite": 2}
    return (
        DAY_ORDER.get(slot.day_of_week, 99),
        SHIFT_ORDER.get(slot.shift, 99),
        slot.order,
    )


def order_by_global_order(slot: TimeSlot) -> int:
    """Ordena pelo campo global_order diretamente."""
    return slot.global_order


def order_by_shift_then_day(slot: TimeSlot) -> tuple:
    """Agrupa primeiro por turno, depois por dia e ordem."""
    SHIFT_ORDER = {"manha": 0, "tarde": 1, "noite": 2}
    DAY_ORDER = {
        "segunda": 0, "terca": 1, "quarta": 2,
        "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6,
    }
    return (
        SHIFT_ORDER.get(slot.shift, 99),
        DAY_ORDER.get(slot.day_of_week, 99),
        slot.order,
    )


# Tipo da função de ordenação
SlotOrderingKey = Callable[[TimeSlot], object]

# estratégias disponíveis (editavel via string no main.py)
SLOT_ORDERING_STRATEGIES: dict[str, SlotOrderingKey] = {
    "day_shift_order": order_by_day_shift_order,
    "global_order": order_by_global_order,
    "shift_then_day": order_by_shift_then_day,
}


# Contexto de dados do AG

from dataclasses import dataclass, field


@dataclass
class GAContext:
    """
    Agrupa todos os dados de domínio necessários para o AG.
    Passado para todos os operadores para evitar variáveis globais.
    """
    teachers: list[Teacher]
    class_groups: list[ClassGroup]
    subjects: list[Subject]
    time_slots: list[TimeSlot]
    slot_ordering_key: SlotOrderingKey = field(default=order_by_day_shift_order)

    def __post_init__(self):
        self.teachers_by_id: dict[str, Teacher] = {t.id: t for t in self.teachers}
        self.subjects_by_id: dict[str, Subject] = {s.id: s for s in self.subjects}
        self.class_groups_by_id: dict[str, ClassGroup] = {cg.id: cg for cg in self.class_groups}
        self.time_slots_by_id: dict[str, TimeSlot] = {ts.id: ts for ts in self.time_slots}

        self.subjects_by_class_group: dict[str, list[Subject]] = {}
        for subject in self.subjects:
            for cg in self.class_groups:
                if subject.id.startswith(cg.id + "_"):
                    self.subjects_by_class_group.setdefault(cg.id, []).append(subject)
                    break

        self.ordered_slots: list[TimeSlot] = sorted(self.time_slots, key=self.slot_ordering_key)

