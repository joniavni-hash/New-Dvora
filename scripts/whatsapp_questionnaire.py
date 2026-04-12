#!/usr/bin/env python3
"""
ממשק WhatsApp לשאלון אנשי קשר
"""

import json
import os
import sys
import os
sys.path.append(os.path.dirname(__file__))
from contact_questionnaire import ContactQuestionnaire

class WhatsAppQuestionnaire:
    def __init__(self):
        self.state_file = "/home/jonia/.openclaw/workspace/state/active_questionnaire.json"
        
    def load_state(self):
        """טוען מצב שאלון פעיל"""
        if not os.path.exists(self.state_file):
            return None
            
        with open(self.state_file, 'r') as f:
            state = json.load(f)
            
        if state is None:
            return None
            
        # שחזור המצב
        questionnaire = ContactQuestionnaire()
        questionnaire.current_contact = state.get('contact', {})
        questionnaire.current_step = state.get('step', 0)
        
        return questionnaire
    
    def save_state(self, questionnaire):
        """שומר מצב שאלון"""
        state = {
            'contact': questionnaire.current_contact,
            'step': questionnaire.current_step
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def clear_state(self):
        """מוחק שאלון פעיל"""
        with open(self.state_file, 'w') as f:
            json.dump(None, f)
    
    def start_questionnaire(self, contact_name=None):
        """מתחיל שאלון חדש"""
        questionnaire = ContactQuestionnaire()
        result = questionnaire.start_questionnaire(contact_name)
        
        if result.get('completed'):
            self.clear_state()
            return self.format_completion(result)
        
        self.save_state(questionnaire)
        return self.format_question(result, questionnaire)
    
    def process_answer(self, answer):
        """מעבד תשובה לשאלון פעיל"""
        questionnaire = self.load_state()
        
        if not questionnaire:
            return "❌ אין שאלון פעיל. התחל שאלון חדש עם 'שאלון ל[שם]'"
        
        # בדיקת פקודות מיוחדות
        answer_lower = answer.lower().strip()
        if answer_lower in ['בטל', 'עצור', 'cancel']:
            self.clear_state()
            return "❌ השאלון בוטל"
        
        if answer_lower in ['חזור', 'back'] and questionnaire.current_step > 0:
            questionnaire.current_step -= 1
            result = questionnaire.next_question()
            self.save_state(questionnaire)
            return self.format_question(result, questionnaire)
        
        # עיבוד תשובה רגילה
        result = questionnaire.process_answer(answer)
        
        if result.get('error'):
            return f"❌ {result['error']}\n\n{self.format_question(questionnaire.next_question(), questionnaire)}"
        
        if result.get('completed'):
            self.clear_state()
            return self.format_completion(result)
        
        self.save_state(questionnaire)
        return self.format_question(result, questionnaire)
    
    def format_question(self, result, questionnaire):
        """מעצב שאלה לWhatsApp"""
        if not result or result.get('completed'):
            return "השאלון הושלם"
        
        contact_name = questionnaire.current_contact.get('name', 'איש קשר')
        progress = f"[{result['step'] + 1}/{len(questionnaire.questions)}]"
        
        formatted = f"📝 {progress} {contact_name}\n\n"
        formatted += result['question']
        formatted += f"\n\n💡 אפשר לענות: מספר | טקסט | 'חזור' | 'בטל'"
        
        return formatted
    
    def format_completion(self, result):
        """מעצב סיום שאלון"""
        return f"✅ השאלון הושלם!\n\n{result['summary']}\n\n💾 נשמר בקובץ: {os.path.basename(result['file'])}"

def main():
    # בדיקה
    wq = WhatsAppQuestionnaire()
    result = wq.start_questionnaire("דוד כהן")
    print(result)

if __name__ == "__main__":
    main()