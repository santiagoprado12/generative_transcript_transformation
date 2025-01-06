prompts = {
    "generate_content_table": (
        (
            "system",
            "You are an expert in creating structured content tables in json format. "
            "And you are going to create a content table for this instruction: {instruction}",
        ),
        (
            "user",
            "Based on the following text, with the objective of creating a teacher-friendly transcript, "
            "select between 5 and 7 chapters that should have the text, and the topics it should include, "
            "try to avoid duplication of information between chapters:\n\n{context}\n\n"
            "Example of outcome, only write the output dict, a dict with: 'Chapter 1: ...': [topics that should have], "
            "'Chapter 2: ...':[...], 'Chapter 3: ...':[...], 'Chapter 4: ...':[...], 'Chapter 5: ...':[...], ...",
        ),
    ),
    "assign_word_counts": [
        ("system", "{instruction}"),
        (
            "user",
            "Fill the json with the percentage of words that should have each chapter based on its importance, "
            "use a number between 0 and 1, the sum should be 1:\n\n{template}",
        ),
    ],
    "fill_each_chapter": [
        (
            "system",
            "You are writing detailed content for the chapter '{chapter}'. "
            "And you were instructed to {instruction}",
        ),
        (
            "user",
            "Based on the following text, write content for the chapter '{chapter}' with approximately {words} words "
            "and using the topics {topics}, you can add important information that might not be in the text:\n\n{context}",
        ),
    ],
    "refine_chapter": [
        (
            "system",
            "You are refining the chapter '{chapter}'. "
            "And you were instructed to {instruction}",
        ),
        (
            "user",
            "The current words count is {current_words} and should be {required_words}, "
            "create a text {expansion_ratio} times larger, extend the information "
            "you consider relevant, be detailed, the information you add might or might not be in the text "
            "in order to achieve the required length:\n\n{chapter_content}",
        ),
    ],
    "refine_summary": [
        (
            "system",
            "You are refining the final document for an educational transcript.",
        ),
        (
            "user",
            "Based on the following text, refine the content to make it more coherent and teacher-friendly, "
            "fix titles and remove duplication of information, but try to maintain as much as possible the original:\n\n{final_document}",
        ),
    ],
}
