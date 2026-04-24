from dataclasses import dataclass, field

from entities import Lesson, TimeSlot, ClassGroup

@dataclass
class Schedule:
    lessons: list[Lesson] = field(default_factory=list)

    def add_lesson(self, lesson: Lesson):
        """
        Adiciona uma aula ao horário.
        """
        self.lessons.append(lesson)

    def get_lessons_for_teacher(self, teacher_id: str) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a um professor específico.
        """
        return [lesson for lesson in self.lessons if lesson.teacher_id == teacher_id]

    def get_lessons_for_class_group(self, class_group_id: str) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a uma turma específica.
        """
        return [lesson for lesson in self.lessons if lesson.class_group_id == class_group_id]

    def get_lessons_for_subject(self, subject_id: str) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a uma disciplina específica.
        """
        return [lesson for lesson in self.lessons if lesson.subject_id == subject_id]

    def get_lessons_for_time_slot(self, time_slot_id: str) -> list[Lesson]:
        """
        Retorna todas as aulas associadas a um horário específico.
        """
        return [lesson for lesson in self.lessons if lesson.time_slot_id == time_slot_id]

#não há duas aulas no mesmo horário para a mesma turma ou professor, se isso retornar mais de uma aula, há um erro no horário
    def get_cell_lessons(self, time_slot_id: str, class_group_id: str) -> list[Lesson]:
        """
        Retorna a aula associada a um horário e turma específicos.
        """
        return[
            lesson for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.class_group_id == class_group_id
        ]

    def get_teacher_cell_lesson(self, time_slot_id: str, teacher_id: str) -> list[Lesson]:
        """
        Retorna a aula associada a um horário e professor específicos.
        """
        return[
            lesson for lesson in self.lessons
            if lesson.time_slot_id == time_slot_id and lesson.teacher_id == teacher_id
        ]

    def matrix_view(self, time_slots: list[TimeSlot], class_groups: list[ClassGroup]) -> dict[str, dict[str, list[Lesson]]]:
        """
        Retorna uma representação matricial do horário,
        Linha: Horário
        Coluna: Turma
        Célula: Aula (ou None se não houver aula)
        """
        matrix = {}
        for time_slot in time_slots:
            matrix[time_slot.id] = {}
            for class_group in class_groups:
                matrix[time_slot.id][class_group.id] = self.get_cell_lessons(
                    time_slot.id, class_group.id
                )
        return matrix
