from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from services.database import get_db
from services.repositories import get_question_repository
from services.repositories import get_answer_repository
from models.schemas.request_models import QuestionCreateRequest
from models.schemas.response_models import QuestionResponse, QuestionWithAnswersResponse, GeneralResponse
from services.dependencies import get_current_user
from models.domain.user import User

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/", response_model=QuestionResponse)
def create_question(
    question_data: QuestionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """إنشاء سؤال جديد"""
    try:
        question_repo = get_question_repository()
        question = question_repo.create_question(
            user_id=uuid.UUID(current_user.id),
            question=question_data.question
        )
        return QuestionResponse(
            id=str(question.id),
            user_id=str(question.user_id),
            question=question.question,
            created_at=question.created_at,
            updated_at=question.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating question: {str(e)}"
        )


@router.get("/", response_model=List[QuestionResponse])
def get_all_questions(db: Session = Depends(get_db)):
    """الحصول على جميع الأسئلة"""
    try:
        question_repo = get_question_repository()
        questions = question_repo.get_all_questions()
        return [
            QuestionResponse(
                id=str(q.id),
                user_id=str(q.user_id),
                question=q.question,
                created_at=q.created_at,
                updated_at=q.updated_at
            )
            for q in questions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questions: {str(e)}"
        )


@router.get("/{question_id}", response_model=QuestionWithAnswersResponse)
def get_question_with_answers(question_id: str, db: Session = Depends(get_db)):
    """الحصول على سؤال مع إجاباته"""
    try:
        question_repo = get_question_repository()
        answer_repo = get_answer_repository()
        
        question = question_repo.get_question_by_id(uuid.UUID(question_id))
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        answers = answer_repo.get_answers_by_question_id(uuid.UUID(question_id))
        
        return QuestionWithAnswersResponse(
            question=QuestionResponse(
                id=str(question.id),
                user_id=str(question.user_id),
                question=question.question,
                created_at=question.created_at,
                updated_at=question.updated_at
            ),
            answers=[
                {
                    "id": str(a.id),
                    "answer": a.answer,
                    "question_id": str(a.question_id),
                    "user_id": str(a.user_id),
                    "created_at": a.created_at,
                    "author": a.author
                }
                for a in answers
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching question: {str(e)}"
        )


@router.delete("/{question_id}", response_model=GeneralResponse)
def delete_question(question_id: str, db: Session = Depends(get_db)):
    """حذف سؤال"""
    try:
        question_repo = get_question_repository()
        success = question_repo.delete_question(uuid.UUID(question_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return GeneralResponse(
            status="success",
            message="Question deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting question: {str(e)}"
        )
