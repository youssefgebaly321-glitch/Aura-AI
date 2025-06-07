# --- core/prompts.py ---
# This module centralizes all AI prompt engineering.

def get_interview_suggestion_prompt(question: str, context: dict) -> str:
    """
    Generates a prompt to get a suggestion for an interview question.
    
    Args:
        question: The question asked by the interviewer.
        context: A dictionary containing 'resume', 'job_description', etc.
    
    Returns:
        A formatted prompt string.
    """
    
    # Basic prompt for now. We will enhance this in Phase 2d.
    prompt = f"""
    You are an expert interview coach. Your user is in a live interview.
    The interviewer just asked the following question:
    "{question}"

    Based on this question, provide a proper, helpful answer or a key talking point for the user to mention.
    Keep the suggestion to one or two short sentences.
    
    Example:
    Question: "Tell me about a time you handled a conflict with a coworker."
    Suggestion: "Remember to use the STAR method: Situation, Task, Action, Result. Focus on a positive resolution and what you learned."
    """
    return prompt.strip()