import typing as t

from indigo.models.base import Error
from indigo.systems.purpose.models import (
    ID,
    CurrentExamInfo,
    Exam,
    Note,
    Question,
    QuestionStats,
    RankedGrade,
)
from indigo.tools.typer import Typer
from indigo.utils import date_utils


class ExaminerError(Error): ...


class Examiner:
    exam: Exam
    current_exam_info: CurrentExamInfo

    _notes: t.Sequence[Note]
    _questions: t.Sequence[Question]
    _question_stats_by_id: t.Mapping[ID, QuestionStats]

    _on_ask: t.Callable[[CurrentExamInfo], None]
    on_answer: t.Callable[[Exam, QuestionStats], None]
    on_complete: t.Callable[[Exam], None]

    @staticmethod
    def make_exam(
        file_id: ID,
        subject_id: ID,
        notes_and_questions: t.Sequence[Note],
        question_stats: t.Sequence[QuestionStats],
    ) -> Exam:
        notes: t.List[Note] = []
        primary_questions: t.List[Question] = []
        secondary_questions: t.List[Question] = []
        question_stats_by_id: t.Mapping[ID, QuestionStats] = {
            stats.question_id: stats for stats in question_stats
        }

        for note_or_question in notes_and_questions:
            if note_or_question.file_id != file_id:
                raise ExaminerError(
                    "Exams cannot contain questions or notes from another"
                    " file."
                )
            if note_or_question.is_question:
                (
                    primary_questions
                    if note_or_question.is_starred
                    else secondary_questions
                ).append(note_or_question)
            else:
                notes.append(note_or_question)

        if len(primary_questions) + len(secondary_questions) < 27:
            raise ExaminerError(
                "Exams cannot be created with less than 27 questions."
            )

        selected_questions: t.Sequence[Question] = []

        # Add key questions

        while len(selected_questions) < 18:
            sorted_by_recent_grade = [
                [
                    question.id_,
                    (
                        question_stats.last_grade
                        if (
                            question_stats := question_stats_by_id.get(
                                question.id_
                            )
                        )
                        else 100
                    ),
                ]
                for question in primary_questions
            ]
            sorted_by_recent_grade.sort(key=lambda qs: qs[1])
            if not primary_questions:
                break

        # Add secondary questions

        while len(selected_questions) < 27:
            ...

        # What If we have:
        # B) 1/3 - have had low recent grade
        # C) 1/3 - have low overall grade
        # A) 1/3 - haven't been asked recently (select ones which have not been asked)

        # cls, file_id: ID, subject_id: ID,
        # primary_question_ids: t.Sequence[ID],
        # secondary_questions_ids: t.Sequence[ID]
        return Exam.make_blank(file_id=file_id, subject_id=subject_id)

    def __init__(
        self,
        exam: Exam,
        current_exam_info: CurrentExamInfo,
        on_ask: t.Callable[[CurrentExamInfo], None],
        on_answer: t.Callable[[Exam, QuestionStats], None],
        on_complete: t.Callable[[Exam], None],
    ):
        self.exam = exam
        self.current_exam_info = current_exam_info
        self.on_ask = on_ask
        self._on_answer = on_answer
        self._on_complete = on_complete

        questions = []
        filtered_notes = []  # noqa
        for note in notes:
            if note.is_question:
                questions.append(note)
            else:
                filtered_notes.append(note)
        self._notes = filtered_notes

        # What if the exam is already in progress?
        # Then, …… o, devils! The exam already has the
        # set of questions in its model, the selection can
        # happen elsewhere perhaps?

    def ask_questions(self):
        ...
        self._on_answer()

    def _save_answer(
        self, exam: Exam, question: Question, grade: RankedGrade
    ):
        exam.answer(question.id_, grade)
        question_stats = QuestionStats(
            question_id=question.id_,
            last_asked=date_utils.now(),
            last_grade=grade,
            overall_grade=(
                grade
                if not (
                    last_stats := self._question_stats_by_id.get(
                        question.id_
                    )
                )
                else round((last_stats.overall_grade + grade) / 2, 1)
            ),
        )

        self._on_answer(exam, question_stats)

    def _complete_exam(self, exam: Exam):
        Typer.header("Exam completed.")
        self._on_complete(exam)
        # Log results, etc?
