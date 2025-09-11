import re
import logging
from typing import Dict, Optional
from config.config_loader import config_loader
from config.logging_config import get_logger

logger = get_logger(__name__)

class IdentityService:
    """Service for handling identity-related questions"""
    
    def __init__(self):
        # أنماط أسئلة الهوية
        self.identity_patterns = {
            "who_are_you": [
                r"من\s*أنت",
                r"من\s*هو\s*أنت", 
                r"من\s*أنت\s*بالضبط",
                r"من\s*أنت\s*فعلاً",
                r"من\s*أنت\s*حقيقة",
                r"من\s*أنت\s*أساساً",
                r"من\s*أنت\s*بالتحديد",
                r"من\s*أنت\s*بالدقة",
                r"من\s*أنت\s*بالضبط",
                r"من\s*أنت\s*فعلاً",
                r"من\s*أنت\s*حقيقة",
                r"من\s*أنت\s*أساساً",
                r"من\s*أنت\s*بالتحديد",
                r"من\s*أنت\s*بالدقة"
            ],
            "who_trained_you": [
                r"من\s*دربك",
                r"من\s*تدربك", 
                r"من\s*علمك",
                r"من\s*صانعك",
                r"من\s*مطورك",
                r"من\s*أنشأك",
                r"من\s*برمجك",
                r"من\s*صممك",
                r"من\s*قام\s*بتدريبك",
                r"من\s*قام\s*بتطويرك",
                r"من\s*قام\s*بإنشائك",
                r"من\s*قام\s*ببرمجتك",
                r"من\s*قام\s*بتصميمك",
                r"من\s*قام\s*بتعليمك",
                r"من\s*قام\s*بصنعك"
            ],
            "what_are_you": [
                r"ما\s*أنت",
                r"ماذا\s*أنت",
                r"ما\s*هو\s*أنت",
                r"ما\s*نوعك",
                r"ما\s*طبيعتك",
                r"ما\s*هو\s*نوعك",
                r"ما\s*هو\s*طبيعتك",
                r"ما\s*هو\s*شخصيتك",
                r"ما\s*هو\s*كيانك"
            ],
            "who_created_you": [
                r"من\s*أنشأك",
                r"من\s*خلقك",
                r"من\s*صنعك",
                r"من\s*بناك",
                r"من\s*قام\s*بإنشائك",
                r"من\s*قام\s*بخلقك",
                r"من\s*قام\s*بصنعك",
                r"من\s*قام\s*ببنائك"
            ],
            "what_can_you_do": [
                r"ماذا\s*يمكنك\s*أن\s*تفعل",
                r"ما\s*يمكنك\s*أن\s*تفعل",
                r"ماذا\s*تستطيع\s*أن\s*تفعل",
                r"ما\s*تستطيع\s*أن\s*تفعل",
                r"ماذا\s*تستطيع\s*فعله",
                r"ما\s*تستطيع\s*فعله",
                r"ماذا\s*يمكنك\s*فعله",
                r"ما\s*يمكنك\s*فعله"
            ],
            "your_purpose": [
                r"ما\s*هو\s*هدفك",
                r"ما\s*هو\s*غرضك",
                r"ما\s*هو\s*مهمتك",
                r"ما\s*هو\s*دورك",
                r"ما\s*هو\s*وظيفتك",
                r"ما\s*هو\s*عملك",
                r"ما\s*هو\s*شغلك",
                r"ما\s*هو\s*مهمتك"
            ]
        }
    
    def detect_identity_question(self, question: str) -> Optional[str]:
        """Detect if question is about identity and return the type"""
        question_lower = question.lower().strip()
        
        # تحسين اكتشاف أسئلة الهوية
        for response_type, patterns in self.identity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    logger.info(f"Detected identity question type: {response_type} for question: {question[:50]}...")
                    return response_type
        
        # إضافة أنماط إضافية لاكتشاف أسئلة الهوية
        identity_keywords = [
            "من أنت", "من هو أنت", "من انت", "من هو انت", 
            "تعريف", "هويتك", "اسمك", "من أنت؟", "من انت؟",
            "من أنت بالضبط", "من انت بالضبط", "من أنت فعلاً", "من انت فعلاً",
            "من أنت حقيقة", "من انت حقيقة", "من أنت أساساً", "من انت اساساً",
            "من أنت بالتحديد", "من انت بالتحديد", "من أنت بالدقة", "من انت بالدقة",
            "من أنت بالضبط", "من انت بالضبط", "من أنت فعلاً", "من انت فعلاً",
            "من أنت حقيقة", "من انت حقيقة", "من أنت أساساً", "من انت اساساً",
            "من أنت بالتحديد", "من انت بالتحديد", "من أنت بالدقة", "من انت بالدقة",
            "من أنت بالضبط", "من انت بالضبط", "من أنت فعلاً", "من انت فعلاً",
            "من أنت حقيقة", "من انت حقيقة", "من أنت أساساً", "من انت اساساً",
            "من أنت بالتحديد", "من انت بالتحديد", "من أنت بالدقة", "من انت بالدقة"
        ]
        for keyword in identity_keywords:
            if keyword in question_lower:
                logger.info(f"Detected identity question by keyword: {keyword} for question: {question[:50]}...")
                return "who_are_you"
        
        return None
    
    def get_identity_response(self, question: str) -> Optional[Dict[str, any]]:
        """Get appropriate identity response for the question"""
        logger.info(f"🔍 [IDENTITY_SERVICE] فحص السؤال: {question[:50]}...")
        response_type = self.detect_identity_question(question)
        
        if response_type:
            logger.info(f"✅ [IDENTITY_SERVICE] تم اكتشاف نوع السؤال: {response_type}")
            response_text = config_loader.get_identity_response(response_type)
            
            return {
                "status": "success",
                "answer": response_text,
                "source": "identity_service",
                "model_used": "identity_responses",
                "confidence": 1.0,
                "response_type": response_type,
                "is_identity_question": True,
                "debug_info": {
                    "detected_type": response_type,
                    "language": "arabic",
                    "question_length": len(question)
                }
            }
        else:
            logger.info(f"❌ [IDENTITY_SERVICE] لم يتم اكتشاف سؤال هوية")
        
        return None

# Create singleton instance
identity_service = IdentityService()
