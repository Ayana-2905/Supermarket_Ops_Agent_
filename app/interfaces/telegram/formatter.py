def format_response(response) -> str:

    if response is None:
        return ""

    response = str(response).strip()

    if not response:
        return ""

    return response