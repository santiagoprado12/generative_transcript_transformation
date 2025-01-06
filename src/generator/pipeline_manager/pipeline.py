import asyncio
import os
from typing import Any, Dict, List, TypedDict

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from src.prompts.prompts import prompts
from src.utils.utils import (
    calculate_word_counts,
    convert_markdown_to_pdf,
    extract_text_from_pdf,
    should_refine_chapters,
)

load_dotenv()


class State(TypedDict):
    pdf_path: str
    text: str
    content_table: List[str]
    word_counts: Dict[str, int]
    chapters: Dict[str, str]
    final_document: str
    required_words: int
    instruction: str


class TranscriptPipeline:
    """A pipeline for generating educational transcripts from PDF files.

    This pipeline extracts text from a PDF file, generates a content table,
    assigns word counts to each section, fills each chapter with content,
    assembles the final document, and saves it as a PDF file.

    Attributes:
        start_state (Dict[str, Any]): The initial state of the pipeline.
        api_key (str): The API key for the OpenAI API.
        llm (ChatOpenAI): The OpenAI language model for generating content.
        graph (StateGraph): The state graph for the pipeline.
    """

    def __init__(self, start_state: Dict[str, Any]):
        """Initialize the TranscriptPipeline with the given start state.

        Args:
            start_state (Dict[str, Any]): The initial state of the pipeline, including API key and other configurations.
        """
        self.start_state = start_state
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=self.api_key)
        self.graph = StateGraph(State)
        self._build_pipeline()

    def _build_pipeline(self):
        """Build the state graph pipeline by adding nodes and edges."""
        self.graph.add_node("extract_text_from_pdf", self.extract_text_from_pdf)
        self.graph.add_node("generate_content_table", self.generate_content_table)
        self.graph.add_node("assign_word_counts", self.assign_word_counts)
        self.graph.add_node("fill_each_chapter", self.fill_each_chapter)
        self.graph.add_node("assemble_final_document", self.assemble_final_document)
        self.graph.add_node("refine_summary", self.refine_summary)
        self.graph.add_node("refine_chapter", self.refine_chapter)
        self.graph.add_node("save_as_pdf", self.save_as_pdf)

        self.graph.add_edge(START, "extract_text_from_pdf")
        self.graph.add_edge("extract_text_from_pdf", "generate_content_table")
        self.graph.add_edge("generate_content_table", "assign_word_counts")
        self.graph.add_edge("assign_word_counts", "fill_each_chapter")
        self.graph.add_edge("assemble_final_document", "save_as_pdf")
        self.graph.add_edge("save_as_pdf", END)

        self.graph.add_conditional_edges(
            "fill_each_chapter", self.should_refine_chapter
        )
        self.graph.add_conditional_edges("refine_chapter", self.should_refine_chapter)

    def extract_text_from_pdf(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Extract text from a PDF file.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with extracted text.
        """
        text = extract_text_from_pdf(state["pdf_path"])
        return {"text": text}

    def generate_content_table(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Generate a content table from the extracted text.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with the generated content table.
        """
        parser = JsonOutputParser()
        prompt = ChatPromptTemplate(prompts["generate_content_table"])
        content_table_chain = prompt | self.llm | parser
        content_table = content_table_chain.invoke(
            {"context": state["text"], "instruction": state["instruction"]}, config
        )
        return {"content_table": content_table}

    def assign_word_counts(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Assign word counts to each section in the content table.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with assigned word counts.
        """
        parser = JsonOutputParser()
        template = "{" + ": (words_perc),".join(state["content_table"].keys()) + "}"
        prompt = ChatPromptTemplate(prompts["assign_word_counts"])
        content_table_chain = prompt | self.llm | parser
        word_counts = content_table_chain.invoke(
            {"template": template, "instruction": state["instruction"]}, config
        )
        word_counts = calculate_word_counts(word_counts, state["required_words"])
        return {"word_counts": word_counts}

    async def fill_each_chapter(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Fill each chapter with content based on the assigned word counts.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with filled chapters.
        """
        chapters = {}
        topics = state["content_table"]
        for chapter, words in state["word_counts"].items():
            prompt = ChatPromptTemplate(prompts["fill_each_chapter"])
            fill_chapter_chain = prompt | self.llm | StrOutputParser()
            chapters[chapter] = fill_chapter_chain.ainvoke(
                {
                    "context": state["text"],
                    "chapter": chapter,
                    "words": words,
                    "topics": topics[chapter],
                    "instruction": state["instruction"],
                },
                config,
            )
        results = asyncio.gather(*chapters.values())
        chapters = {
            chapter: result for chapter, result in zip(chapters.keys(), await results)
        }
        return {"chapters": chapters}

    def should_refine_chapter(self, state: Dict[str, Any]) -> str:
        """Determine if any chapters need refinement.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.

        Returns:
            str: The next state in the pipeline, either "assemble_final_document" or "refine_chapter".
        """
        chapters_to_refine = should_refine_chapters(
            state["chapters"], state["word_counts"]
        )
        if not chapters_to_refine:
            return "assemble_final_document"
        return "refine_chapter"

    async def refine_chapter(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Refine chapters that need additional content.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with refined chapters.
        """
        chapters_to_refine = should_refine_chapters(
            state["chapters"], state["word_counts"]
        )
        temp_chapter = {}
        for chapter in chapters_to_refine:
            current_words = len(state["chapters"][chapter].split())
            prompt = ChatPromptTemplate(prompts["refine_chapter"])
            refine_chain = prompt | self.llm | StrOutputParser()
            temp_chapter[chapter] = refine_chain.ainvoke(
                {
                    "context": state["chapters"][chapter],
                    "chapter": chapter,
                    "current_words": current_words,
                    "required_words": state["word_counts"][chapter],
                    "expansion_ratio": state["word_counts"][chapter] / current_words,
                    "instruction": state["instruction"],
                },
                config,
            )
        results = await asyncio.gather(*temp_chapter.values())
        for chapter, result in zip(temp_chapter.keys(), results):
            state["chapters"][chapter] = result

    def assemble_final_document(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Assemble the final document from the filled chapters.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with the assembled final document.
        """
        final_document = "\n\n".join(
            f"{content}" for _, content in state["chapters"].items()
        )
        return {"final_document": final_document}

    def refine_summary(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Refine the summary of the final document.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.

        Returns:
            Dict[str, Any]: The updated state with the refined final document.
        """
        prompt = ChatPromptTemplate(prompts["refine_summary"])
        refine_chain = prompt | self.llm | StrOutputParser()
        final_document = refine_chain.invoke(
            {
                "context": state["final_document"],
                "final_document": state["final_document"],
            },
            config,
        )
        return {"final_document": final_document}

    def save_as_pdf(self, state: Dict[str, Any], config: RunnableConfig):
        """Save the final document as a PDF file.

        Args:
            state (Dict[str, Any]): The current state of the pipeline.
            config (RunnableConfig): Configuration for the runnable.
        """
        convert_markdown_to_pdf(state["final_document"], "output_file.pdf")

    @property
    def app(self):
        """Get the Streamlit app for the pipeline.

        Returns:
            Any: The Streamlit app for the pipeline.
        """
        app = self.graph.compile()
        return app

    def save_graph(self, path: str):
        """Save the state graph to a file.

        Args:
            path (str): The path to save the state graph.
        """
        app = self.graph.compile()

        image_data = self.graph.get_graph().draw_mermaid_png()

        # Save the image to a file
        with open("graph.png", "wb") as f:
            f.write(image_data)