---
title: "RAG Q&A Application"
date: 2026-03-22
summary: "A retrieval-augmented generation system for intelligent question answering over custom knowledge bases."
description: "A retrieval-augmented generation system for intelligent question answering over custom knowledge bases."
tags: ["Python", "LangChain", "React"]
github: "https://github.com/Bernard203/rag_app_backend"
---

This project implements a Retrieval-Augmented Generation (RAG) pipeline that allows users to ask natural-language questions against a custom corpus of documents. The backend is built with Python and LangChain, handling document ingestion, vector embedding, and LLM-based answer synthesis. A React frontend provides a clean chat interface where users can upload documents, ask questions, and view source citations inline.

The ingestion pipeline splits uploaded PDFs and Markdown files into semantically meaningful chunks, embeds them with OpenAI's embedding model, and stores the vectors in a local FAISS index. At query time the system retrieves the most relevant chunks, feeds them as context to the language model, and returns a grounded answer with references back to the original documents.

Key challenges included managing chunk boundaries to avoid cutting sentences mid-thought, tuning the retrieval threshold to balance precision and recall, and streaming long answers token-by-token to keep the UI responsive. The project is deployed as a Docker Compose stack with separate containers for the API server, the vector store, and a Nginx reverse proxy.
