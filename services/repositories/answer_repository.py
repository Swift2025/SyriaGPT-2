from typing import List, Optional
from sqlalchemy.orm import Session
from models.domain.answer import Answer
import uuid

class AnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_answer(self, answer: str, question_id: uuid.UUID, user_id: uuid.UUID, author: str) -> Answer:
        """إنشاء إجابة جديدة"""
        db_answer = Answer(
            answer=answer,
            question_id=question_id,
            user_id=user_id,
            author=author
        )
        self.db.add(db_answer)
        self.db.commit()
        self.db.refresh(db_answer)
        return db_answer

    def get_answer_by_id(self, answer_id: uuid.UUID) -> Optional[Answer]:
        """الحصول على إجابة بواسطة المعرف"""
        return self.db.query(Answer).filter(Answer.id == answer_id).first()

    def get_answers_by_question_id(self, question_id: uuid.UUID) -> List[Answer]:
        """الحصول على جميع إجابات سؤال معين"""
        return self.db.query(Answer).filter(Answer.question_id == question_id).all()

    def get_answers_by_user_id(self, user_id: uuid.UUID) -> List[Answer]:
        """الحصول على جميع إجابات المستخدم"""
        return self.db.query(Answer).filter(Answer.user_id == user_id).all()

    def get_all_answers(self) -> List[Answer]:
        """الحصول على جميع الإجابات"""
        return self.db.query(Answer).all()

    def update_answer(self, answer_id: uuid.UUID, answer: str) -> Optional[Answer]:
        """تحديث إجابة"""
        db_answer = self.get_answer_by_id(answer_id)
        if db_answer:
            db_answer.answer = answer
            self.db.commit()
            self.db.refresh(db_answer)
        return db_answer

    def delete_answer(self, answer_id: uuid.UUID) -> bool:
        """حذف إجابة"""
        db_answer = self.get_answer_by_id(answer_id)
        if db_answer:
            self.db.delete(db_answer)
            self.db.commit()
            return True
        return False
