from dataclasses import dataclass, field

from entities import *

@dataclass
class Schedule:
    lessons: list[Lesson] = field(default_factory=list)

    def add_lesson(
            self,
            lesson: Lesson,
    ):
        """
        Adiciona uma aula ao horário.
        """
        self.lessons.append(lesson)

    def get_lessons_for_teacher(
            self,
            teacher_id: str,
    ) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a um professor específico.
        """
        return [lesson for lesson in self.lessons if lesson.teacher_id == teacher_id]

    def get_lessons_for_class_group(
            self,
            class_group_id: str,
    ) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a uma turma específica.
        """
        return [lesson for lesson in self.lessons if lesson.class_group_id == class_group_id]

    def get_lessons_for_subject(
            self,
            subject_id: str,
    ) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a uma disciplina específica.
        """
        return [lesson for lesson in self.lessons if lesson.subject_id == subject_id]

    def get_lessons_for_time_slot(
            self,
            time_slot_id: str
    ) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a um horário específico.
        """
        return [lesson for lesson in self.lessons if lesson.time_slot_id == time_slot_id]

#não há duas aulas no mesmo horário para a mesma turma ou professor, se isso retornar mais de uma aula, há um erro no horário
    def get_cell_lessons(
            self,
            time_slot_id: str,
            class_group_id: str
    ) -> list[Lesson]:
        """
        Retorna a aula associada a um horário e turma específicos.
        """
        return[
            lesson for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.class_group_id == class_group_id
        ]

    def get_teacher_cell_lesson(
            self,
            time_slot_id: str,
            teacher_id: str
    ) -> list[Lesson]:
        """
        Retorna a aula associada a um horário e professor específicos.
        """
        return[
            lesson for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.teacher_id == teacher_id
        ]

    def get_lessons_for_class_group_by_day_and_shift(
            self,
            class_group_id: str,
            day_of_week: str,
            shift: str,
            time_slots: list[TimeSlot]
    ) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a uma turma específica em um dia e turno específicos.
        """
        valid_time_slot_ids = {
            time_slot.id
            for time_slot in time_slots
            if time_slot.day_of_week == day_of_week
               and time_slot.shift == shift
        }

        return [
            lesson
            for lesson in self.lessons
            if lesson.class_group_id == class_group_id
               and lesson.time_slot_id in valid_time_slot_ids
        ]


    def matrix_view(
            self,
            time_slots: list[TimeSlot],
            class_groups: list[ClassGroup],
    ) -> dict[str, dict[str, dict[str, dict[str, list[Lesson]]]]]:
        """
        Retorna uma representação matricial do horário,

        Estrutura:
        {
            "Segunda-feira": {
                "manha": {
                    "segunda_manha_1": {
                        "6_ano_a": [Lesson],
                    }
                }
            }
        }

        """
        matrix = {}

        ordered_time_slots = sorted(
            time_slots,
            key=lambda
                time_slot: (
                time_slot.day_of_week,
                time_slot.shift,
                time_slot.order,
            )
        )

        for time_slot in ordered_time_slots:
            if time_slot.day_of_week not in matrix:
                matrix[time_slot.day_of_week] = {}

            if time_slot.shift not in matrix[time_slot.day_of_week]:
                matrix[time_slot.day_of_week][time_slot.shift] = {}

            matrix[time_slot.day_of_week][time_slot.shift][time_slot.id] = {}

            for class_group in class_groups:
                if class_group.id not in matrix[time_slot.day_of_week][time_slot.shift][time_slot.id]:
                    matrix[time_slot.day_of_week][time_slot.shift][time_slot.id][class_group.id] = (
                        self.get_cell_lessons(
                            time_slot_id=time_slot.id,
                            class_group_id=class_group.id
                        )
                    )

        return matrix
