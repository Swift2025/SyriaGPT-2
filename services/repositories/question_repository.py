from typing import List, Optional
from sqlalchemy.orm import Session
from models.domain.question import Question
import uuid

class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_question(self, user_id: uuid.UUID, question: str) -> Question:
        """إنشاء سؤال جديد"""
        db_question = Question(
            user_id=user_id,
            question=question
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question

    def get_question_by_id(self, question_id: uuid.UUID) -> Optional[Question]:
        """الحصول على سؤال بواسطة المعرف"""
        return self.db.query(Question).filter(Question.id == question_id).first()

    def get_questions_by_user_id(self, user_id: uuid.UUID) -> List[Question]:
        """الحصول على جميع أسئلة المستخدم"""
        return self.db.query(Question).filter(Question.user_id == user_id).all()

    def get_all_questions(self) -> List[Question]:
        """الحصول على جميع الأسئلة"""
        return self.db.query(Question).all()

    def update_question(self, question_id: uuid.UUID, question: str) -> Optional[Question]:
        """تحديث سؤال"""
        db_question = self.get_question_by_id(question_id)
        if db_question:
            db_question.question = question
            self.db.commit()
            self.db.refresh(db_question)
        return db_question

    def delete_question(self, question_id: uuid.UUID) -> bool:
        """حذف سؤال"""
        db_question = self.get_question_by_id(question_id)
        if db_question:
            self.db.delete(db_question)
            self.db.commit()
            return True
        return False
