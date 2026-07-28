
import streamlit as st
import google.generativeai as genai

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters  import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import tempfile

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Gemini API Key
genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel("gemini-2.5-flash")

chat_history = []

st.title(" RAG Based PDF Chatbot")

uploaded_files = st.file_uploader(
    "Upload PDF Files",
    type="pdf",
    accept_multiple_files=True
)
if uploaded_files:

    all_documents = []

    for uploaded_file in uploaded_files:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        all_documents.extend(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(all_documents)

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_documents(
        chunks,
        embedding_model
    )

    st.success(
        f"{len(uploaded_files)} PDF(s) loaded successfully!"
    )

    question = st.text_input("Ask a Question")

    if question:

        docs = vector_store.similarity_search(
            question,
            k=3
        )

        context = "\n".join(
            [doc.page_content for doc in docs]
        )

        history = "\n".join(
            st.session_state.chat_history
        )

        prompt = f"""
        Previous Conversation:
        {history}

        Context:
        {context}

        Question:
        {question}

        Answer only from the provided context.
        If the answer is not available, say:
        'The information is not available in the uploaded documents.'
        """

        response = model.generate_content(prompt)

        st.session_state.chat_history.append(
            f"User: {question}"
        )

        st.session_state.chat_history.append(
            f"Bot: {response.text}"
        )

        st.write(response.text)
