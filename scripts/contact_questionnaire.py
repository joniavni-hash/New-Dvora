#!/usr/bin/env python3
"""
שאלון אינטראקטיבי לאנשי קשר
מנהל תהליך איסוף מידע על אנשי קשר בצורה חכמה ומותאמת
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ContactQuestionnaire:
    def __init__(self):
        self.contacts_dir = "/home/jonia/.openclaw/workspace/contacts"
        self.current_contact = {}
        self.current_step = 0
        
        # יצירת תיקיית אנשי קשר
        os.makedirs(self.contacts_dir, exist_ok=True)
        
        self.questions = [
            {"key": "name", "question": "איך קוראים לו/לה? (שם מלא)", "type": "text"},
            {"key": "title", "question": "מה התפקיד/העסק שלו/שלה?", "type": "text"},
            {"key": "company", "question": "באיזה חברה/ארגון?", "type": "text"},
            {"key": "how_met", "question": "איך הכרתם? (עבודה, חברים משותפים, אירוע, רשתות...)", "type": "text"},
            {"key": "when_met", "question": "מתי בערך הכרתם? (חודש/שנה)", "type": "text"},
            
            {"key": "phone", "question": "טלפון עיקרי:", "type": "text"},
            {"key": "email", "question": "מייל עיקרי:", "type": "text"},
            {"key": "preferred_channel", "question": "איך הכי נוח לו/לה לקבל הודעות?", 
             "type": "choice", "options": ["WhatsApp", "טלפון", "מייל", "פגישה פנים אל פנים"]},
            
            {"key": "relationship_type", "question": "איזה סוג קשר זה?", 
             "type": "choice", "options": ["לקוח", "ספק", "שותף עסקי", "מועמד לעבודה", "מנטור/יועץ", "חבר אישי", "רשות/ממשל", "משקיע", "אחר"]},
             
            {"key": "shared_interest", "question": "מה תחום העניין המשותף?", "type": "text"},
            {"key": "mutual_value", "question": "מה הערך ההדדי? (מה אתה יכול לתת, מה הם יכולים לתת)", "type": "text"},
            
            {"key": "communication_style", "question": "איזה סגנון תקשורת מתאים להם?", 
             "type": "choice", "options": ["ישיר ועניני", "נימוסי ומפורט", "רשמי", "חברי ונינוח"]},
             
            {"key": "contact_frequency", "question": "כמה פעמים כדאי להיות בקשר?", 
             "type": "choice", "options": ["שבועי", "חודשי", "רבעוני", "שנתי", "לפי צורך בלבד"]},
             
            {"key": "contact_purpose", "question": "בשביל מה הקשר?", 
             "type": "choice", "options": ["שמירה על קשר", "הזדמנויות עסקיות", "ייעוץ ותמיכה", "שיתוף פעולה", "רשת חברתי"]},
             
            {"key": "special_notes", "question": "משהו מיוחד שכדאי לזכור? (תחביבים, אלרגיות, מגבלות, ילדים...)", "type": "text", "optional": True},
            {"key": "memory_hook", "question": "איך הכי קל לזכור אותם? (סיפור, מאפיין יחודי, משהו בולט)", "type": "text", "optional": True}
        ]
    
    def start_questionnaire(self, contact_name_hint=None):
        """מתחיל שאלון חדש"""
        self.current_contact = {"created": datetime.now().isoformat()}
        self.current_step = 0
        
        if contact_name_hint:
            self.current_contact["name"] = contact_name_hint
            self.current_step = 1
            
        return self.next_question()
    
    def next_question(self):
        """מחזיר את השאלה הבאה"""
        if self.current_step >= len(self.questions):
            return self.finish_questionnaire()
            
        question = self.questions[self.current_step]
        
        # בניית טקסט השאלה
        question_text = f"📝 שאלה {self.current_step + 1}/{len(self.questions)}\n"
        question_text += f"{question['question']}\n"
        
        if question['type'] == 'choice':
            question_text += "\nבחר מספר:\n"
            for i, option in enumerate(question['options'], 1):
                question_text += f"{i}. {option}\n"
        
        if question.get('optional'):
            question_text += "\n(אופציונלי - אפשר לדלג)"
            
        return {"question": question_text, "step": self.current_step}
    
    def process_answer(self, answer):
        """מעבד תשובה ועובר לשאלה הבאה"""
        if self.current_step >= len(self.questions):
            return {"error": "השאלון כבר הסתיים"}
            
        question = self.questions[self.current_step]
        
        # עיבוד התשובה
        if question['type'] == 'choice':
            try:
                choice_num = int(answer.strip())
                if 1 <= choice_num <= len(question['options']):
                    processed_answer = question['options'][choice_num - 1]
                else:
                    return {"error": f"בחר מספר בין 1 ל-{len(question['options'])}"}
            except ValueError:
                return {"error": "בחר מספר מהרשימה"}
        else:
            processed_answer = answer.strip()
        
        # שמירת התשובה
        if processed_answer:
            self.current_contact[question['key']] = processed_answer
        
        # מעבר לשאלה הבאה
        self.current_step += 1
        return self.next_question()
    
    def finish_questionnaire(self):
        """מסיים את השאלון ושומר את המידע"""
        # יצירת קובץ לאיש הקשר
        name_safe = self.current_contact.get('name', 'unknown').replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{name_safe}_{timestamp}.json"
        
        contact_file = os.path.join(self.contacts_dir, filename)
        
        with open(contact_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_contact, f, ensure_ascii=False, indent=2)
        
        # יצירת סיכום
        summary = self.create_summary()
        
        return {
            "completed": True,
            "file": contact_file,
            "summary": summary,
            "contact": self.current_contact
        }
    
    def create_summary(self):
        """יוצר סיכום של איש הקשר"""
        c = self.current_contact
        
        summary = f"""📇 איש קשר חדש נוסף: {c.get('name', 'לא צוין')}

🏢 פרטים מקצועיים:
• תפקיד: {c.get('title', 'לא צוין')}
• חברה: {c.get('company', 'לא צוין')}
• סוג קשר: {c.get('relationship_type', 'לא צוין')}

📞 קשר:
• טלפון: {c.get('phone', 'לא צוין')}
• מייל: {c.get('email', 'לא צוין')}
• ערוץ מועדף: {c.get('preferred_channel', 'לא צוין')}

💡 איך לנהל:
• תדירות קשר: {c.get('contact_frequency', 'לא צוין')}
• מטרת קשר: {c.get('contact_purpose', 'לא צוין')}
• סגנון תקשורת: {c.get('communication_style', 'לא צוין')}

{f"📝 הערות: {c.get('special_notes')}" if c.get('special_notes') else ""}
{f"💭 איך לזכור: {c.get('memory_hook')}" if c.get('memory_hook') else ""}"""

        return summary

def main():
    # דוגמה לשימוש
    questionnaire = ContactQuestionnaire()
    result = questionnaire.start_questionnaire()
    print(result['question'])

if __name__ == "__main__":
    main()