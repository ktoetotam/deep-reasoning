import asyncio
import aiohttp
import json
import os
import re
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import dotenv
# ---------------------------
# Configuration Constants
# ---------------------------
dotenv.load_dotenv()
DEFAULT_MODEL = os.environ['DEFAULT_MODEL']


# ============================
# ResearchAssistant Class
# ============================
class ResearchAssistant:
    def __init__(self, iteration_limit=10, model=DEFAULT_MODEL):
        self.iteration_limit = iteration_limit
        self.aggregated_contexts = []    # All useful contexts from every iteration
        self.all_search_queries = []     # Every search query used across iterations
        self.model = model
        self.client = self.initialize_openai_client()  # the client initialization here.
        

    @staticmethod
    def clean_and_split_string(input_string: str):
        """
        Remove unnecessary quotes and whitespace, then split by commas.
        """
        cleaned_string = re.sub(r"[\"']", "", input_string).strip()
        split_list = cleaned_string.split(',')
        cleaned_list = [item.strip() for item in split_list if item.strip()]


        return cleaned_list
    

    def initialize_openai_client(self):
        try:
            client = OpenAI(api_key=os.getenv("LLM_API_KEY"))
            client.base_url = os.getenv("LLM_API_BASE")
            client.api_key = os.getenv("LLM_API_KEY")
            return client
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
    

    async def ask_openai(self,prompt, chat_history=[]):
        """
        Sends a prompt (with optional chat history) to the OpenAI API and returns the response.
        """
        
        if self.model is None:
            self.model = DEFAULT_MODEL
        

        token_limit = 4096
        if chat_history and isinstance(chat_history, list):
            chat_history.append({'role': 'user', 'content': prompt})
        else:
            chat_history.append({'role': 'user', 'content': prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                max_tokens=token_limit
            )
            answer = response.choices[0].message.content

            try:
                if len(answer) == 2:
                    answer = "Thoughts:" + "\n" + answer[0] + "\n\n\n" + "Answer:" + "\n" + answer[1]
                    return answer
            except Exception as e:
                print(f"Error extracting think content: {e}")

            return answer
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None

    async def generate_search_queries_async(self, session, user_query):
        """
        Ask the LLM to produce up to four precise search queries (in Python list format)
        based on the user’s query.
        """
        prompt = (
            "You are an expert research assistant. Given the user's query, generate up to four distinct, "
            "precise search queries that would help gather comprehensive information on the topic. "
            "Return only a Python list of strings, for example: ['query1', 'query2', 'query3']."
        )
        messages = [
            {"role": "system", "content": "You are a helpful and precise research assistant."},
            {"role": "user", "content": f"User Query: {user_query}\n\n{prompt}"}
        ]
        response = await self.ask_openai(prompt, messages)
        if response:
            try:
                search_queries = ResearchAssistant.clean_and_split_string(response)
                if isinstance(search_queries, list):
                    return search_queries
                else:
                    print("LLM did not return a list. Response:", response)
                    return []
            except Exception as e:
                print("Error parsing search queries:", e, "\nResponse:", response)
                return []
        return []
    
    
    async def perform_beautiful_soup_search_async(self, session, query):
        """
        Asynchronously perform a Google search by scraping the results page with Beautiful Soup.
        Returns a list of result URLs.
        """
        print("starting google query")
        # Build the Google search URL with query parameters
        url = "https://www.google.com/search"
        params = {
            "q": query,
            # Additional parameters (e.g., "hl": "en") can be added if needed
        }
        # Use a realistic User-Agent header to mimic a browser
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/90.0.4430.93 Safari/537.36")
        }
        try:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    links = []
                    print("Beautiful Soup search")
                    # Google search result URLs are usually embedded in <a> tags with hrefs that begin with "/url?q="
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("/url?q="):
                            # Extract the actual URL from the href value
                            actual_url = href.split("/url?q=")[1].split("&")[0]
                            links.append(actual_url)
                    return links
                else:
                    text = await resp.text()
                    print(f"Google search error: {resp.status} - {text}")
                    return []
        except Exception as e:
            print("Error performing Google search:", e)
            return []
        

    async def perform_custom_search_async(self, session, query):
        """
        Asynchronously perform a Google Custom Search query using the JSON API.
        Returns a list of result URLs.
        """
        print("starting Google Custom Search query")
        # Google Custom Search API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Retrieve the API key and custom search engine ID from environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        cse_id = os.getenv("GOOGLE_API_CX")
        
        # Build query parameters
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query
        }
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    links = []
                    print("Google Custom Search query successful")
                    # Extract the 'link' field from each item in the response
                    for item in data.get("items", []):
                        link = item.get("link")
                        if link:
                            links.append(link)
                    return links
                else:
                    text = await resp.text()
                    print(f"Google Custom Search error: {resp.status} - {text}")
                    return []
        except Exception as e:
            print("Error performing Google Custom Search:", e)
            return []


    async def perform_search_async(self, session, query):
        """
        Asynchronously perform a Google search using SERPAPI for the given query.
        Returns a list of result URLs.
        """
        params = {
            "q": query,
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "google"
        }
        try:
            async with session.get(os.getenv("SERPAPI_URL"), params=params) as resp:
                if resp.status == 200:
                    results = await resp.json()
                    if "organic_results" in results:
                        links = [item.get("link") for item in results["organic_results"] if "link" in item]
                        return links
                    else:
                        print("No organic results in SERPAPI response.")
                        return []
                else:
                    text = await resp.text()
                    print(f"SERPAPI error: {resp.status} - {text}")
                    return []
        except Exception as e:
            print("Error performing SERPAPI search:", e)
            return []
        


    async def fetch_webpage_text_with_bs(self,session, url):
        """
        Asynchronously fetch the text content of a webpage using aiohttp and Beautiful Soup.
        Returns the extracted text.
        """
        try:
            async with session.get(url, timeout=1000) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Extract text from the whole document; adjust separator if needed
                    text = soup.get_text(separator="\n", strip=True)
                    return text
                else:
                    error_text = await resp.text()
                    print(f"Error fetching {url}: {resp.status} - {error_text}")
                    return ""
        except asyncio.TimeoutError:
            print(f"Timeout error fetching {url}")
            return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    async def fetch_webpage_text_async(self, session, url):
        """
        Asynchronously retrieve the text content of a webpage using Jina.
        The URL is appended to the Jina endpoint.
        """
        full_url = f"{os.getenv('JINA_BASE_URL')}{url}"
        headers = {
            "Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"
        }
        try:
            async with session.get(full_url, headers=headers, timeout=1000) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    text = await resp.text()
                    print(f"Jina fetch error for {url}: {resp.status} - {text}")
                    return ""
        except asyncio.TimeoutError:
            print(f"Timeout error fetching webpage text for {url}")
            return ""
        except Exception as e:
            print("Error fetching webpage text with Jina:", e)
            return ""

    async def is_page_useful_async(self, session, user_query, page_text):
        """
        Ask the LLM if the provided webpage content is useful for answering the user's query.
        The LLM must reply with exactly "Yes" or "No".
        """
        prompt = (
            "You are a critical research evaluator. Given the user's query and the content of a webpage, "
            "determine if the webpage contains information relevant and useful for addressing the query. "
            "Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not. Do not include any extra text."
        )
        messages = [
            {"role": "system", "content": "You are a strict and concise evaluator of research relevance."},
            {"role": "user", "content": f"User Query: {user_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
        ]
        response = await self.ask_openai(prompt, messages)
        if response:
            answer = response.strip()
            if answer in ["Yes", "No"]:
                return answer
            else:
                # Fallback: try to extract Yes/No from the response.
                if "Yes" in answer:
                    return "Yes"
                elif "No" in answer:
                    return "No"
        return "No"

    async def extract_relevant_context_async(self, session, user_query, search_query, page_text):
        """
        Given the original query, the search query used, and the page content,
        have the LLM extract all information relevant for answering the query.
        """
        prompt = (
            "You are an expert information extractor. Given the user's query, the search query that led to this page, "
            "and the webpage content, extract all pieces of information that are relevant to answering the user's query. "
            "Return only the relevant context as plain text without commentary."
        )
        messages = [
            {"role": "system", "content": "You are an expert in extracting and summarizing relevant information."},
            {"role": "user", "content": f"User Query: {user_query}\nSearch Query: {search_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
        ]
        response = await self.ask_openai(prompt, messages)
        if response:
            return response.strip()
        return ""

    async def get_new_search_queries_async(self, session, user_query):
        """
        Based on the original query, the previously used search queries, and all the extracted contexts,
        ask the LLM whether additional search queries are needed. If yes, return a Python list of up to four queries;
        if the LLM thinks research is complete, it should return "<done>".
        """
        context_combined = "\n".join(self.aggregated_contexts)
        prompt = (
            "You are an analytical research assistant. Based on the original query, the search queries performed so far, "
            "and the extracted contexts from webpages, determine if further research is needed. "
            "If further research is needed, provide up to four new search queries as a Python list (for example, "
            "['new query1', 'new query2']). If you believe no further research is needed, respond with exactly <done>."
            "\nOutput only a Python list or the token <done> without any additional text."
        )
        messages = [
            {"role": "system", "content": "You are a systematic research planner."},
            {"role": "user", "content": f"User Query: {user_query}\nPrevious Search Queries: {self.all_search_queries}\n\nExtracted Relevant Contexts:\n{context_combined}\n\n{prompt}"}
        ]
        response = await self.ask_openai(prompt, messages)
        if response:
            cleaned = response.strip()
            if cleaned == "<done>":
                return "<done>"
            try:
                # Use eval with caution; consider using ast.literal_eval in production.
                new_queries = eval(cleaned)
                if isinstance(new_queries, list):
                    return new_queries
                else:
                    print("LLM did not return a list for new search queries. Response:", response)
                    return []
            except Exception as e:
                print("Error parsing new search queries:", e, "\nResponse:", response)
                return []
        return []

    async def generate_final_report_async(self, session, user_query):
        """
        Generate the final comprehensive report using all gathered contexts.
        """
        context_combined = "\n".join(self.aggregated_contexts)
        prompt = (
            "You are an expert researcher and report writer. Based on the gathered contexts below and the original query, "
            "write a comprehensive, well-structured, and detailed report that addresses the query thoroughly. "
            "Include all relevant insights and conclusions without extraneous commentary."
        )
        messages = [
            {"role": "system", "content": "You are a skilled report writer."},
            {"role": "user", "content": f"User Query: {user_query}\n\nGathered Relevant Contexts:\n{context_combined}\n\n{prompt}"}
        ]
        report = await self.ask_openai(prompt, messages)
        return report
    

    def format_report_as_html(self,final_report):
        """
        Takes the final report as a string, formats it, and returns it as nicely formatted HTML.
        """
        # Initialize the HTML content
        html_content = ""

        # Split the report into sections based on headers (assuming headers are marked with "===")
        sections = re.split(r'===+', final_report)
        
        for section in sections:
            if section.strip():
                # Add section header
                header_match = re.match(r'\s*(.*?)\s*\n', section)
                if header_match:
                    header = header_match.group(1)
                    html_content += f"<h2>{header}</h2>"
                    section = section[len(header_match.group(0)):]  # Remove the header from the section content

                # Add section content
                paragraphs = section.strip().split('\n\n')
                for paragraph in paragraphs:
                    html_content += f"<p>{paragraph.strip()}</p>"

        return html_content


    async def process_link(self, session, link, user_query, search_query):
        """
        Process a single link: fetch its content, judge its usefulness, and if useful, extract the relevant context.
        """
        links = []
        print(f"Fetching content from: {link}")
        page_text = await self.fetch_webpage_text_async(session, link)
        if not page_text:
            page_text = await self.fetch_webpage_text_with_bs(session, link)    
        if not page_text:
            return None
        usefulness = await self.is_page_useful_async(session, user_query, page_text)
        print(f"Page usefulness for {link}: {usefulness}")
        if usefulness == "Yes":
            context = await self.extract_relevant_context_async(session, user_query, search_query, page_text)
            links.append(link)
            if context:
                print(f"Extracted context from {link} (first 200 chars): {context[:200]}")
                return context, links
        return None


    def format_links_as_html(self,links):
        """
        Takes a list of HTML links and returns them in a nicely formatted HTML list.
        """
        if not links:
            return "<p>No links available.</p>"

        html_content = "<ul>"
        for link in links:
            html_content += f'<li><a href="{link}" target="_blank">{link}</a></li>'
        html_content += "</ul>"

        return html_content


    async def run_research(self, user_query: str):
        """
        The main asynchronous routine that performs iterative research and returns a final report.
        """
        iteration = 0
        self.aggregated_contexts = []
        self.all_search_queries = []
        useful_links = []
        async with aiohttp.ClientSession() as session:
            # ----- INITIAL SEARCH QUERIES -----
            new_search_queries = await self.generate_search_queries_async(session, user_query)
            if not new_search_queries:
                print("No search queries were generated by the LLM. Exiting.")
                return "No research could be performed."
            self.all_search_queries.extend(new_search_queries)

            # ----- ITERATIVE RESEARCH LOOP -----
            while iteration < self.iteration_limit:
                print(f"\n=== Iteration {iteration + 1} ===")
                iteration_contexts = []

                # For each search query, perform SERPAPI searches concurrently.
                search_tasks = [self.perform_search_async(session, query) for query in new_search_queries]
                print(search_tasks)
                search_results = await asyncio.gather(*search_tasks)
                if all(not sub_array for sub_array in search_results):
                    search_tasks = [self.perform_custom_search_async(session, query) for query in new_search_queries]
                    search_results = await asyncio.gather(*search_tasks)
                if all(not sub_array for sub_array in search_results):
                    search_tasks = [self.perform_beautiful_soup_search_async(session, query) for query in new_search_queries]
                    search_results = await asyncio.gather(*search_tasks)





                # Map each unique link to the search query that produced it.
                unique_links = {}
                for idx, links in enumerate(search_results):
                    query = new_search_queries[idx]
                    for link in links:
                        if link not in unique_links:
                            unique_links[link] = query

                print(f"Aggregated {len(unique_links)} unique links from this iteration.")

                # Process each link concurrently: fetch, judge, and extract context.
                link_tasks = [
                    self.process_link(session, link, user_query, unique_links[link])
                    for link in unique_links
                ]
                
                link_results = await asyncio.gather(*link_tasks)
                filtered_results = [result for result in link_results if result is not None]

                context_links = [result[0] for result in filtered_results]
                useful_links += [result[1] for result in filtered_results]

                # Collect non-None contexts.
                for res in context_links:
                    if res:
                        iteration_contexts.append(res)

                if iteration_contexts:
                    self.aggregated_contexts.extend(iteration_contexts)
                else:
                    print("No useful contexts were found in this iteration.")

                # ----- ASK THE LLM IF MORE SEARCHES ARE NEEDED -----
                new_search_queries = await self.get_new_search_queries_async(session, user_query)
                if new_search_queries == "<done>":
                    print("LLM indicated that no further research is needed.")
                    break
                elif new_search_queries:
                    print("LLM provided new search queries:", new_search_queries)
                    self.all_search_queries.extend(new_search_queries)
                else:
                    print("LLM did not provide any new search queries. Ending the loop.")
                    break

                iteration += 1

            # ----- FINAL REPORT -----
            print("\nGenerating final report...")
            final_report = await self.generate_final_report_async(session, user_query)
            format_report = self.format_report_as_html(final_report)
            format_links = self.format_links_as_html(useful_links)
            print(format_report,format_links)
            return format_report,format_links


# ============================
# Main Routine (Command-Line)
# ============================
def main():
    user_query = input("Enter your research query: ").strip()
    if not user_query:
        print("No query provided. Exiting.")
        return

    research_assistant = ResearchAssistant(iteration_limit=10)
    final_report = asyncio.run(research_assistant.run_research(user_query))
    print("\n==== FINAL REPORT ====\n")
    print(final_report)


if __name__ == '__main__':
    main()
