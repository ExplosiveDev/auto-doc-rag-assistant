# Auto-Doc : RAG-based Documentation Assistant

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)
![Qdrant](https://img.shields.io/badge/DB-Qdrant-red.svg)

**Auto-Doc Master** — це інтелектуальна система, яка перетворює будь-яку веб-документацію на базу знань. Бот не просто шукає текст, а розуміє зміст і дає точні відповіді з посиланнями на джерела.

### Ключові можливості:
* **Deep Crawling:** Автоматичний пошук усіх підсторінок документації.
* **JS-Rendering:** Використання **Playwright** для обходу захисту (Cloudflare/Fandom) та зчитування динамічного контенту.
* **Semantic Search:** Векторний пошук через **Qdrant** для знаходження максимально релевантного контексту.
* **Source Citations:** Бот завжди вказує пряме посилання на сторінку, де знайшов відповідь.

### Tech Stack:
- **LLM:** Gemini 3 Flash
- **Vector DB:** Qdrant Cloud
- **Scraping:** Playwright, BeautifulSoup4
- **Embeddings:** Multilingual-E5-small
- **Framework:** Gradio


