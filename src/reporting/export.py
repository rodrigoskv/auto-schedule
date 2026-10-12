"""Exporta o horário gerado para Excel (uma aba por turma)."""

from io import BytesIO

import pandas as pd

from data.school_hours import DAY_LABEL
from domain.entities import Schedule
from ga.context import GAContext


def timetable_excel(schedule: Schedule, context: GAContext) -> bytes:
    days = list(dict.fromkeys(slot.day_of_week for slot in context.time_slots))
    periods = sorted({slot.order for slot in context.time_slots})
    slots = {(slot.day_of_week, slot.order, slot.shift): slot for slot in context.time_slots}

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for group in context.class_groups:
            by_slot = {
                lesson.time_slot_id: lesson
                for lesson in schedule.get_lessons_for_class_group(group.id)
                if lesson.time_slot_id
            }
            rows = []
            for order in periods:
                row = {"Aula": f"{order}º"}
                for day in days:
                    slot = slots.get((day, order, group.shift))
                    lesson = by_slot.get(slot.id) if slot else None
                    if lesson:
                        subject = context.subjects_by_id.get(lesson.subject_id)
                        teacher = context.teachers_by_id.get(lesson.teacher_id)
                        subject_name = subject.name if subject else lesson.subject_id
                        teacher_name = teacher.name if teacher else lesson.teacher_id
                        row[DAY_LABEL.get(day, day)] = f"{subject_name} — {teacher_name}"
                    else:
                        row[DAY_LABEL.get(day, day)] = ""
                rows.append(row)
            sheet = group.name[:31] or group.id[:31]
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet, index=False)

        leftover = [
            {
                "Turma": context.class_groups_by_id.get(lesson.class_group_id).name
                if lesson.class_group_id in context.class_groups_by_id
                else lesson.class_group_id,
                "Disciplina": context.subjects_by_id.get(lesson.subject_id).name
                if lesson.subject_id in context.subjects_by_id
                else lesson.subject_id,
                "Professor": context.teachers_by_id.get(lesson.teacher_id).name
                if lesson.teacher_id in context.teachers_by_id
                else lesson.teacher_id,
            }
            for lesson in schedule.get_unassigned_lessons()
        ]
        if leftover:
            pd.DataFrame(leftover).to_excel(writer, sheet_name="Sem horário", index=False)

    return buffer.getvalue()
