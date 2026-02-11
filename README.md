# Auto-Doc : RAG-based Documentation Assistant

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)
![Qdrant](https://img.shields.io/badge/DB-Qdrant-red.svg)

**Auto-Doc Master** is a high-performance Retrieval-Augmented Generation (RAG) system designed to transform static web documentation into an interactive knowledge base. Unlike basic search tools, it understands the context of technical manuals and provides precise answers with direct source citations.

### Key Features

* **Intelligent Crawling:** Automatically discovers sub-pages and internal documentation links using a recursive crawler.
* **JavaScript Rendering:** Utilizes **Playwright** (headless browser) to bypass anti-bot protections (Cloudflare, Fandom) and scrape dynamically rendered content.
* **Hybrid Scraping Logic:** Cleans HTML using `BeautifulSoup4` by removing redundant elements like scripts, styles, and ads for high-quality data ingestion.
* **Semantic Search:** Stores and retrieves high-dimensional vector embeddings in **Qdrant Cloud**, ensuring the LLM receives the most relevant context.
* **Source Citations:** Every AI response includes clickable direct links to the source documentation pages.

### Tech Stack:
* **LLM:** Gemini 3 Flash (via Google Generative AI)
* **Vector Database:** Qdrant (Cloud Tier)
* **Embeddings:** Multilingual-E5-small
* **Web Automation:** Playwright & BeautifulSoup4
* **Text Processing:** LangChain RecursiveCharacterTextSplitter
* **UI Framework:** Gradio

### System Architecture
1.  **Ingestion:** The user provides a URL. The system crawls or deep-scrapes the content.
2.  **Chunking:** Text is split into optimized chunks with overlap to maintain context.
3.  **Indexing:** Chunks are vectorized and stored in Qdrant with associated metadata (URLs).
4.  **Retrieval:** When a user asks a question, the system finds the top-K relevant chunks.
5.  **Generation:** Gemini 3 generates a technical answer strictly based on the retrieved context.

### Demo :
Step 1: Enter documentation URL and choose "Crawler" mode.
<img width="1902" height="880" alt="1" src="https://github.com/user-attachments/assets/f168f209-35d1-4695-b544-d4c0c57087bd" />

Step 2: Monitor real-time status as the system processes pages and updates the Qdrant database.
<img width="1140" height="109" alt="2" src="https://github.com/user-attachments/assets/5cb13bd0-e5c2-43cc-b385-22d85e636a4f" />
<img width="1502" height="885" alt="3" src="https://github.com/user-attachments/assets/08723906-6ead-4aa7-82ad-4b3c6b4c2a5e" />

Step 3: Interact with the chatbot to get technical support based on the learned material.
<img width="1830" height="404" alt="4" src="https://github.com/user-attachments/assets/bc634bf4-fa5c-43b8-876d-8f1ed4254292" />
<img width="1828" height="361" alt="5" src="https://github.com/user-attachments/assets/eb3ade12-37cf-442a-afca-3addc7bc31b9" />




