import re

def sanitize_filename(value: str) -> str:
    """
    Sanitize input to make it safe for use in filenames.
    Removes or replaces problematic characters like / \\ : * ? " < > | !
    """
    return re.sub(r'[\/\\:\*\?"<>\|!]', ' ', str(value))