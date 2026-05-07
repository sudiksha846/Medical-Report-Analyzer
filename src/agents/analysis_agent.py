from datetime import datetime, timedelta
import streamlit as st
import re
from agents.model_manager import ModelManager


class AnalysisAgent:
    """
    Clinically-augmented Analysis Agent:
    - Multi-report support
    - Rule-based medical reasoning
    - LLM explanations
    """

    def __init__(self):
        self.model_manager = ModelManager()
        self._init_state()

   
    def _init_state(self):

        if 'analysis_count' not in st.session_state:
            
            st.session_state.analysis_count = 0

        if 'last_analysis' not in st.session_state:
            st.session_state.last_analysis = datetime.now()

        if 'analysis_limit' not in st.session_state:
            st.session_state.analysis_limit = 15

        if 'knowledge_base' not in st.session_state:
            st.session_state.knowledge_base = {}

    def check_rate_limit(self):

       
        if datetime.now() - st.session_state.last_analysis > timedelta(days=1):

            st.session_state.analysis_count = 0
            st.session_state.last_analysis = datetime.now()

        if st.session_state.analysis_count >= st.session_state.analysis_limit:
            return False, "Daily limit reached"

        return True, None

  
    def analyze_report(self, data, system_prompt, chat_history=None):

       
        can_analyze, error = self.check_rate_limit()

        if not can_analyze:
            return {
                "success": False,
                "error": error
            }

      
        processed = self._preprocess_data(data)

        clinical_findings = self._run_clinical_rules(processed)

        system_prompt += (
            f"\n\n## Clinical Rule-Based Findings:\n"
            f"{clinical_findings}"
        )

     
        result = self.model_manager.generate_analysis(
            processed,
            system_prompt
        )

        if result["success"]:

           
            st.session_state.analysis_count += 1

          
            st.session_state.last_analysis = datetime.now()

            self._update_knowledge_base(
                processed,
                result["content"]
            )

        return result

  
    def _detect_report_type(self, text):

        text = text.lower()

        mapping = {
            "blood": ["hemoglobin", "wbc", "rbc"],
            "urine": ["urine", "ph", "protein"],
            "liver": ["alt", "ast", "bilirubin"],
            "thyroid": ["tsh", "t3", "t4"],
            "kidney": ["creatinine", "urea", "egfr"],
            "radiology": ["mri", "ct", "x-ray", "impression"]
        }

        scores = {
            k: sum(w in text for w in v)
            for k, v in mapping.items()
        }

        detected = max(scores, key=scores.get)

        return detected if scores[detected] > 0 else "unknown"

    
    def _preprocess_data(self, data):

        report = data.get("report", "")

        report_type = self._detect_report_type(report)

        return {
            "patient_name": data.get("patient_name"),
            "age": data.get("age"),
            "gender": data.get("gender"),
            "report": report,
            "report_type": report_type
        }

   
    def _run_clinical_rules(self, data):

        text = data["report"].lower()

        findings = []

        tsh = self._extract_value(text, "tsh")

        if tsh:
            if tsh > 4.5:
                findings.append(
                    "High TSH → Possible Hypothyroidism"
                )

            elif tsh < 0.4:
                findings.append(
                    "Low TSH → Possible Hyperthyroidism"
                )

        alt = self._extract_value(text, "alt")
        ast = self._extract_value(text, "ast")

        if alt and alt > 50:
            findings.append(
                "Elevated ALT → Liver inflammation"
            )

        if ast and ast > 50:
            findings.append(
                "Elevated AST → Liver damage"
            )

        
        creatinine = self._extract_value(text, "creatinine")

        if creatinine and creatinine > 1.3:
            findings.append(
                "High Creatinine → Possible kidney dysfunction"
            )

       
        if "protein" in text and "+" in text:
            findings.append(
                "Proteinuria detected → Kidney issue possible"
            )

        if "pus cells" in text:
            findings.append(
                "Pus cells → Possible UTI"
            )

        if "hemoglobin" in text:

            hb = self._extract_value(text, "hemoglobin")

            if hb and hb < 12:
                findings.append(
                    "Low Hemoglobin → Possible anemia"
                )

        
        if "mass" in text or "lesion" in text:
            findings.append(
                "Mass/Lesion detected → Requires clinical correlation"
            )

        return (
            "\n".join(findings)
            if findings
            else "No strong rule-based abnormalities detected."
        )

   
    def _extract_value(self, text, keyword):
        """
        Extract numeric values like:
        'TSH: 5.6'
        'TSH 5.6'
        """

        pattern = rf"{keyword}\s*[:\-]?\s*(\d+\.?\d*)"

        match = re.search(pattern, text)

        return float(match.group(1)) if match else None

  
    def _update_knowledge_base(self, data, analysis):

        report_type = data["report_type"]

        if report_type not in st.session_state.knowledge_base:
            st.session_state.knowledge_base[report_type] = []

        st.session_state.knowledge_base[report_type].append({
            "report": data["report"][:200],
            "analysis": analysis[:200]
        })

   
    def get_remaining_analyses(self):

        return (
            st.session_state.analysis_limit
            - st.session_state.analysis_count
        )