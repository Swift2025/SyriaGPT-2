from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from services.database import get_db
from services.repositories import get_answer_repository
from services.repositories import get_question_repository
from models.schemas.request_models import AnswerCreateRequest
from models.schemas.response_models import AnswerResponse, GeneralResponse
from services.dependencies import get_current_user
from models.domain.user import User

router = APIRouter(prefix="/answers", tags=["Answers"])


@router.post("/", response_model=AnswerResponse)
def create_answer(
    answer_data: AnswerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """إنشاء إجابة جديدة"""
    try:
        # التحقق من وجود السؤال
        question_repo = get_question_repository()
        question = question_repo.get_question_by_id(uuid.UUID(answer_data.question_id))
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        answer_repo = get_answer_repository()
        answer = answer_repo.create_answer(
            answer=answer_data.answer,
            question_id=uuid.UUID(answer_data.question_id),
            user_id=uuid.UUID(current_user.id),
            author=current_user.full_name or current_user.email
        )
        
        return AnswerResponse(
            id=str(answer.id),
            answer=answer.answer,
            question_id=str(answer.question_id),
            user_id=str(answer.user_id),
            created_at=answer.created_at,
            author=answer.author
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating answer: {str(e)}"
        )


@router.get("/question/{question_id}", response_model=List[AnswerResponse])
def get_answers_by_question(question_id: str, db: Session = Depends(get_db)):
    """الحصول على جميع إجابات سؤال معين"""
    try:
        answer_repo = get_answer_repository()
        answers = answer_repo.get_answers_by_question_id(uuid.UUID(question_id))
        
        return [
            AnswerResponse(
                id=str(a.id),
                answer=a.answer,
                question_id=str(a.question_id),
                user_id=str(a.user_id),
                created_at=a.created_at,
                author=a.author
            )
            for a in answers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching answers: {str(e)}"
        )


@router.get("/{answer_id}", response_model=AnswerResponse)
def get_answer_by_id(answer_id: str, db: Session = Depends(get_db)):
    """الحصول على إجابة بواسطة المعرف"""
    try:
        answer_repo = get_answer_repository()
        answer = answer_repo.get_answer_by_id(uuid.UUID(answer_id))
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        return AnswerResponse(
            id=str(answer.id),
            answer=answer.answer,
            question_id=str(answer.question_id),
            user_id=str(answer.user_id),
            created_at=answer.created_at,
            author=answer.author
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching answer: {str(e)}"
        )


@router.delete("/{answer_id}", response_model=GeneralResponse)
def delete_answer(answer_id: str, db: Session = Depends(get_db)):
    """حذف إجابة"""
    try:
        answer_repo = get_answer_repository()
        success = answer_repo.delete_answer(uuid.UUID(answer_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        return GeneralResponse(
            status="success",
            message="Answer deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting answer: {str(e)}"
        )
