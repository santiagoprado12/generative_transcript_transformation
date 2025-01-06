import asyncio
import os
from typing import Any, Dict, List, Literal, TypedDict

import markdown
from dotenv import load_dotenv
from langchain_core.output_parsers import (
    JsonOutputParser,
    StrOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from weasyprint import HTML

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
words_required = 3900

# Initialize the language model
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)


# Define the state structure
class State(TypedDict):
    pdf_path: str
    text: str
    content_table: List[str]
    word_counts: Dict[str, int]
    chapters: Dict[str, str]
    final_document: str


# Node 1: Extract Text from PDF
def extract_text_from_pdf(state: State, config: RunnableConfig) -> Dict[str, Any]:
    import fitz  # PyMuPDF

    doc = fitz.open(state["pdf_path"])
    text = "".join(page.get_text() for page in doc)
    return {"text": text.strip()}


# Node 2: Generate a Content Table
def generate_content_table(state: State, config: RunnableConfig) -> Dict[str, Any]:
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate(
        [
            (
                "system",
                "You are an expert in creating structured content tables for educational materials, in json format.",
            ),
            (
                "user",
                "Based on the following text, with the objective of create a instruction teacher-friendly transcript,"
                "select between 5 and 7 chapters that should have the text, and the topics it should include, try to avoid duplication of information between chapters:\n\n{context}"
                "\n\n example of outcome, only wite the output dict, a dict with: 'Chapter 1: ...': [topics that should have], 'Chapter 2: ...':[...], 'Chapter 3: ...':[...], 'Chapter 4: ...':[...], 'Chapter 5: ...':[...], ...",
            ),
        ]
    )
    content_table_chain = prompt | llm | parser
    content_table = content_table_chain.invoke({"context": state["text"]}, config)

    print("Content table generated:\n", content_table)

    return {"content_table": content_table}


# Node 3: Assign Word Counts
def assign_word_counts(state: State, config: RunnableConfig) -> Dict[str, Any]:
    parser = JsonOutputParser()

    template = "{" + ": (words_perc),".join(state["content_table"].keys()) + "}"

    prompt = ChatPromptTemplate(
        [
            (
                "system",
                "You are an expert in creating structured content tables for educational materials.",
            ),
            (
                "user",
                "Fill the json with the percentage of words that should have each chapter based in its importance, use a number between 0 and 1, the sum should be 1:\n\n{template}",
            ),
        ]
    )
    content_table_chain = prompt | llm | parser
    word_counts = content_table_chain.invoke({"template": template}, config)

    word_counts = {
        chapter: int(words_required * perc) for chapter, perc in word_counts.items()
    }

    print("Word counts assigned:\n", word_counts)
    return {"word_counts": word_counts}


# Node 4: Fill Each Chapter
async def fill_each_chapter(state: State, config: RunnableConfig) -> Dict[str, Any]:
    chapters = {}
    topics = state["content_table"]
    for chapter, words in state["word_counts"].items():
        prompt = ChatPromptTemplate(
            [
                (
                    "system",
                    f"You are writing detailed content for the chapter '{chapter}' in an educational transcript.",
                ),
                (
                    "user",
                    f"Based on the following text, write content for the chapter '{chapter}' with approximately {words} words and using the topics {topics[chapter]}, you can add important information that might not be in the text:\n\n{{context}}",
                ),
            ]
        )
        fill_chapter_chain = prompt | llm | StrOutputParser()
        chapters[chapter] = fill_chapter_chain.ainvoke(
            {"context": state["text"]}, config
        )
        print(f"Chapter '{chapter}' is loading.")

    results = asyncio.gather(*chapters.values())
    chapters = {
        chapter: result for chapter, result in zip(chapters.keys(), await results)
    }

    return {"chapters": chapters}


def should_refine_chapter(
    state: State,
) -> Literal["refine_chapter", "assemble_final_document"]:

    chapters_to_refine = []
    for chapter, content in state["chapters"].items():
        if len(content.split()) < state["word_counts"][chapter] * 0.9:
            chapters_to_refine.append(chapter)

    if len(chapters_to_refine) == 0:
        print("All chapters are correctly filled.")
        print(
            {
                chapter: len(content.split())
                for chapter, content in state["chapters"].items()
            }
        )
        return "assemble_final_document"

    print("Chapters to refine: ", chapters_to_refine)

    return "refine_chapter"


# Node 5: Refine Each Chapter


async def refine_chapter(state: State, config: RunnableConfig) -> Dict[str, Any]:
    chapters_to_refine = []
    for chapter, content in state["chapters"].items():
        if len(content.split()) < state["word_counts"][chapter]:
            chapters_to_refine.append(chapter)

    temp_chapter = {}
    for chapter in chapters_to_refine:
        current_words = len(state["chapters"][chapter].split())
        prompt = ChatPromptTemplate(
            [
                (
                    "system",
                    f"You are refining the chapter '{chapter}' in an educational transcript.",
                ),
                (
                    "user",
                    f"The current words count is {current_words} and should be {state['word_counts'][chapter]},"
                    f" create a text { state['word_counts'][chapter]/current_words } times larger, extend the information"
                    f" you consider relevant, be detailed, the information you add might or not be in the text in order to achieve the required lenght:\n\n {state['chapters'][chapter]}",
                ),
            ]
        )
        print(f"Refining the chapter '{chapter}'....")
        print(
            "current words count: ",
            current_words,
            "should be: ",
            state["word_counts"][chapter],
        )
        refine_chain = prompt | llm | StrOutputParser()
        temp_chapter[chapter] = refine_chain.ainvoke(
            {"context": state["chapters"][chapter]}, config
        )

    results = await asyncio.gather(*temp_chapter.values())

    for chapter, result in zip(temp_chapter.keys(), results):
        state["chapters"][chapter] = result


# Node 5: Assemble the Final Document
def assemble_final_document(state: State, config: RunnableConfig) -> Dict[str, Any]:
    final_document = "\n\n".join(
        f"{content}" for _, content in state["chapters"].items()
    )
    return {"final_document": final_document}


def refine_summary(state: State, config: RunnableConfig) -> Dict[str, Any]:

    current_words = len(state["final_document"].split())
    prompt = ChatPromptTemplate(
        [
            (
                "system",
                "You are refining the final document for an educational transcript.",
            ),
            (
                "user",
                f"Based on the following text, refine the content to make it more coherent and teacher-friendly, "
                f"fix titles and remove duplication of information, but try to maintain as much as possible the original:\n\n {state['final_document']}",
            ),
        ]
    )
    print("Refining the final document....")
    print("current words count: ", current_words)
    refine_chain = prompt | llm | StrOutputParser()
    final_document = refine_chain.invoke({"context": state["text"]}, config)
    print("Final document refined.", len(final_document.split()))
    return {"final_document": final_document}


def save_as_pdf(state: State, config: RunnableConfig):

    print("final document length: ", len(state["final_document"].split()))
    # Convert Markdown to HTML
    html_content = markdown.markdown(state["final_document"])

    # Convert HTML to PDF
    HTML(string=html_content).write_pdf("output_file.pdf")

    print("PDF has been saved as: output_file.pdf")


# Define the graph
graph = StateGraph(State)
graph.add_node("extract_text_from_pdf", extract_text_from_pdf)
graph.add_node("generate_content_table", generate_content_table)
graph.add_node("assign_word_counts", assign_word_counts)
graph.add_node("fill_each_chapter", fill_each_chapter)
graph.add_node("assemble_final_document", assemble_final_document)
graph.add_node("refine_summary", refine_summary)
graph.add_node("refine_chapter", refine_chapter)
graph.add_node("save_as_pdf", save_as_pdf)

# Define the workflow
graph.add_edge(START, "extract_text_from_pdf")
graph.add_edge("extract_text_from_pdf", "generate_content_table")
graph.add_edge("generate_content_table", "assign_word_counts")
graph.add_edge("assign_word_counts", "fill_each_chapter")
graph.add_edge("assemble_final_document", "save_as_pdf")
#graph.add_edge("refine_summary", "save_as_pdf")
graph.add_edge("save_as_pdf", END)

graph.add_conditional_edges("fill_each_chapter", should_refine_chapter)
graph.add_conditional_edges("refine_chapter", should_refine_chapter)

# Compile the graph into an application
app = graph.compile()

# Execute the graph


async def main():

    initial_state = {"pdf_path": "example_data/Practical Test v2.pdf"}
    await app.ainvoke(initial_state)


if __name__ == "__main__":
    asyncio.run(main())
