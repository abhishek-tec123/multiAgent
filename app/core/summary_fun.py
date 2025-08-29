import logging
import re
from dotenv import load_dotenv
from app.core.llm_provider import get_llm_provider

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()


def truncate_to_token_limit(text: str, max_tokens: int = 30000, buffer: int = 500) -> str:
    """
    Truncate the input text to fit within token limit.
    Approximate 1 token ≈ 4 characters.
    The buffer reserves tokens for prompt/query content.
    """
    max_chars = (max_tokens - buffer) * 4
    return text[:max_chars]


async def summarize_extracted_text(
    input_text: str,
    custom_prompt: str = None,
    llm_provider: str = "groq",
) -> str:
    """
    Generate a structured, detailed summary of extracted text using an LLM.
    """

    summarization_prompt = custom_prompt or (
        "You are a highly skilled AI tasked with generating structured summary of the following input text.\n\n"
        "Your goal is to extract and present all facts and data points.\n\n"
    )

    # Get the appropriate LLM provider
    provider = get_llm_provider(llm_provider)
    log.info(f"Using {llm_provider} provider for text summarization")

    # Truncate input to fit within token limits
    truncated_input = truncate_to_token_limit(input_text)

    full_input = f"{summarization_prompt}\n\nInput Text:\n{truncated_input}\n\nSummary:"

    # Generate summary using the provider
    response = await provider.generate_response(full_input)

    # Clean whitespace
    return re.sub(r"\s+", " ", response).strip()
