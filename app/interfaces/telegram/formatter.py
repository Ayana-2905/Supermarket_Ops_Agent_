def format_response(text: str) -> str:
    """
    Keeps Telegram responses clean and readable.
    """

    if not text:
        return "I couldn't generate a response."

    return text.strip()