import streamlit as st
from groq import Groq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class ChatAgent:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model_name = "llama-3.3-70b-versatile"

    def initialize_vector_store(self, text_content):
        if not text_content or text_content.strip() == "":
            text_content = "No report context available."

        texts = self.text_splitter.split_text(text_content)
        if not texts:
            texts = [text_content]

        vectorstore = FAISS.from_texts(texts, self.embeddings)
        return vectorstore

    
    def _format_chat_history(self, chat_history):
        return [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    
    def _contextualize_query(self, query, chat_history):
        if not chat_history:
            return query

        recent_history = chat_history[-4:]
        history_text = "\n".join(
            [
                f"{'User' if msg['role']=='user' else 'Assistant'}: {msg['content']}"
                for msg in recent_history
            ]
        )

        prompt = f"""
Given a chat history and the latest user question, formulate a standalone question.

Chat History:
{history_text}

Question:
{query}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You reformulate questions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except:
            return query

    def _grade_documents(self, query, docs):
        if not docs:
            return False

        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
Check if the context is relevant to the question.

Question:
{query}

Context:
{context}

Answer ONLY YES or NO.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10,
            )
            result = response.choices[0].message.content.strip().lower()
            return "yes" in result
        except:
            return True  # fallback

   
    def _simplify_query(self, query):
        prompt = f"Rewrite this question in a simpler way:\n{query}"
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=50,
            )
            return response.choices[0].message.content.strip()
        except:
            return query

   
    def _evaluate_response(self, response):
        prompt = f"""
You are a medical expert.

Check if the following answer is medically correct.

Answer:
{response}

Reply ONLY:
YES or NO
"""
        try:
            result = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10,
            )
            verdict = result.choices[0].message.content.strip().upper()
            return verdict
        except:
            return "UNKNOWN"

    
    def get_response(self, query, vectorstore, chat_history=None):
        if chat_history is None:
            chat_history = []

        
        contextualized_query = self._contextualize_query(query, chat_history)

        
        try:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            docs = retriever.get_relevant_documents(contextualized_query)

            
            if not self._grade_documents(contextualized_query, docs):
                
                docs = retriever.get_relevant_documents(query)

                if not self._grade_documents(query, docs):
                    simple_query = self._simplify_query(query)
                    docs = retriever.get_relevant_documents(simple_query)

                    if not self._grade_documents(simple_query, docs):
                        docs = []

            context = "\n\n".join([doc.page_content for doc in docs]) if docs else ""

        except:
            context = ""

        system_prompt = (
            "You are a medical assistant. Use context if available. "
            "If unsure, say you don't know. Keep answer concise."
        )

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            messages.extend(self._format_chat_history(chat_history[-6:]))

        if context:
            user_message = f"Context:\n{context}\n\nQuestion: {query}"
        else:
            user_message = f"Question: {query}"

        messages.append({"role": "user", "content": user_message})

        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            final_answer = response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"

        
        verdict = self._evaluate_response(final_answer)

        if verdict == "NO":
            correction_prompt = f"""
The following answer may be incorrect.

Answer:
{final_answer}

Please correct it.
"""
            try:
                correction = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You correct answers."},
                        {"role": "user", "content": correction_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )
                return correction.choices[0].message.content
            except:
                return final_answer

        return final_answer




        
