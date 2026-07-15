def format_helpers_wanted(count) -> str:
    """Avoid displaying literal 'None' when there are no events."""
    if count is None:
        return "0"
    return str(count)
