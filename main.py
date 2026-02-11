import os
from dotenv import load_dotenv
import requests
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from bs4 import BeautifulSoup
import gradio as gr
import google.generativeai as genai
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_LINK = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(
    url=QDRANT_LINK,
    api_key=QDRANT_KEY,
)
collection_name = "my_coll"

embedding_model = SentenceTransformer('intfloat/multilingual-e5-small')

genai.configure(api_key=GEMINI_KEY)
llm_model = genai.GenerativeModel('gemini-3-flash-preview')


def scrape_docs(urls):
    docs_with_urls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        page.route("**/*.{png,jpg,jpeg,svg,webp,css,woff,woff2}", lambda route: route.abort())

        for url in urls:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                page.wait_for_timeout(2000)

                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')

                for script in soup(["script", "style", "nav", "footer", "iframe", "aside", "header"]):
                    script.decompose()

                text = soup.get_text(separator=' ', strip=True)

                if text:
                    docs_with_urls.append((url, text))

            except Exception as e:
                print(f"Error  {url}: {e}")
                continue

        browser.close()
    return docs_with_urls

def get_embeddings(text, task = "passage"):
    prefixed_text = f"{task}: {text}"
    embedding = embedding_model.encode(
        prefixed_text,
        normalize_embeddings=True,
        convert_to_numpy=False,
        show_progress_bar=False
    ).tolist()
    return embedding

def make_chanks(long_text):
    splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n","\n", ". ", "! ", "? ", ]
    )
    chunks = splitter.split_text(long_text)
    return chunks

def add_point(client, collection_name, text, payload):
    client.upsert(
    collection_name=collection_name,
    points=[
        PointStruct(
            id=str(uuid4().hex),
            vector=get_embeddings(text),
            payload=payload
        )
    ])

def create_collection(client, collection_name, size):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=size, distance=Distance.COSINE)
    )

def read_and_add_point(client, collection_name, urls_with_text):
    exists = client.collection_exists(collection_name=collection_name)
    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            ),
        )

    for url, doc_text in urls_with_text:
        text_chanks = make_chanks(doc_text)

        for chank in text_chanks:
            payload = {
                "content": chank,
                "url": url
            }
            add_point(client, collection_name, chank, payload)

def clear_collection(client, collection_name):
    client.delete_collection(
        collection_name=collection_name
    )

def find_text(client, collection_name, user_request):
    results = client.query_points(
        collection_name=collection_name,
        query=get_embeddings(user_request.lower(), task="query"),
        limit=3,
        with_payload=True
    )

    content = []
    sources = set()
    for point in results.points:
        text_data = point.payload.get('text') or point.payload.get('content') or "Текст відсутній"
        url_data = point.payload.get('url')
        content.append(text_data)
        if url_data:
            sources.add(url_data)

    answer =  generate_answer(user_request, content)

    if sources:
        sources_list = "\n".join([f"- [{url}]({url})" for url in sources])
        answer += f"\n\n**Джерела:**\n{sources_list}"

    return answer

def generate_answer(query, search_results):
    context = "\n---\n".join(search_results)

    prompt = f"""
    Ти — помічник-експерт. Використовуй ТІЛЬКИ наданий контекст, щоб відповісти на питання.
    Якщо в контексті немає відповіді, скажи, що ти не знаєш.

    КОНТЕКСТ:
    {context}

    ПИТАННЯ:
    {query}

    ВІДПОВІДЬ:
    """

    response = llm_model.generate_content(prompt)
    return response.text

def predict(message, history):
    try:
        print(f"Запит від користувача: {message}")
        response = find_text(client, collection_name, message)
        return response
    except Exception as e:
        return f"Error : {str(e)}"

def process_new_urls(url_string, crawl_mode):
    if not url_string.strip():
        yield "Enter URL here...", ""
        return

    input_urls = [u.strip() for u in url_string.replace(',', ' ').split() if u.strip()]
    final_urls = []

    if crawl_mode == "Crawler":
        yield "Finding pages...", ""
        for u in input_urls:
            found = crawl_site(u, max_pages=15)
            final_urls.extend(found)
    else :
        yield "Mode: Only indicated URL. Starting to read...", ""
        final_urls = input_urls

    final_urls = list(set(final_urls))

    full_html_with_titles = "<ul style='max-height: 150px; overflow-y: auto; text-align: left;'>"
    for url in final_urls:
        title = get_page_title(url)
        full_html_with_titles += f"<li><b>{title}</b><br><small>{url}</small></li>"
    full_html_with_titles += "</ul>"

    yield f"Loading {len(final_urls)} pages into Qdrant...", full_html_with_titles

    try:
        docs_with_urls = scrape_docs(final_urls)

        read_and_add_point(client, collection_name, docs_with_urls)
        yield f"Ready! Learned {len(final_urls)} pages.", full_html_with_titles
    except Exception as e:
        yield f"Error: {str(e)}", full_html_with_titles

def get_page_title(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else url.split('/')[-1]
        return title.strip()
    except:
        return url.split('/')[-1]

def crawl_site(start_url, max_pages=10):

    visited = set()
    to_visit = [start_url]
    domain = urlparse(start_url).netloc

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        try:
            response = requests.get(current_url, timeout=5)
            visited.add(current_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href'])

                if urlparse(full_url).netloc == domain and full_url not in visited:
                    if "#" not in full_url:
                        to_visit.append(full_url)
        except Exception as e:
            print(f"Error reading {current_url}: {e}")

    return list(visited)

# --- Interface ---

with gr.Blocks(theme="ocean") as demo:
    gr.Markdown("# Auto-Doc Master")

    with gr.Row():
        with gr.Column(scale=2):
            url_input = gr.Textbox(label="URL", placeholder="https://example.com/docs")
            crawl_mode = gr.Radio(
                choices=["Only indicated URL", "Crawler"],
                value="Only indicated URL",
                label="Mode"
            )
            learn_btn = gr.Button("Learn")

        with gr.Column(scale=3):
            status_output = gr.Markdown("Status")
            pages_display = gr.HTML(label="Pages found")

    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(label="Your question", placeholder="For example: How the interface works?")
    clear = gr.Button("Clear chat")

    learn_btn.click(
        process_new_urls,
        inputs=[url_input, crawl_mode],
        outputs=[status_output, pages_display]
    )

    def respond(message, chat_history):
        bot_message = predict(message, chat_history)
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": bot_message})
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(share=False)
    clear_collection(client, collection_name)
    client.close()