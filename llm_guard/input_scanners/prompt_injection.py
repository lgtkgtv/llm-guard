import logging

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
)

from .base import Scanner

_model_path = "JasperLS/gelectra-base-injection"

log = logging.getLogger(__name__)


class PromptInjection(Scanner):
    """
    A prompt injection scanner based on HuggingFace model. It is used to
    detect if a prompt is attempting to perform an injection attack.

    Note: The current model has been known to yield high false positive rates and might not be suited for production use.
    """

    def __init__(self, threshold: float = 0.75):
        """
        Initializes PromptInjection with a threshold.

        Parameters:
            threshold (float): Threshold for the injection score. Default is 0.75.

        Raises:
            None.
        """

        model = AutoModelForSequenceClassification.from_pretrained(_model_path)
        self._tokenizer = AutoTokenizer.from_pretrained(_model_path)
        self._threshold = threshold
        self._text_classification_pipeline = TextClassificationPipeline(
            model=model, tokenizer=self._tokenizer
        )

    def scan(self, prompt: str) -> (str, bool):
        if prompt.strip() == "":
            return prompt, True

        result = self._text_classification_pipeline(
            prompt, truncation=True, max_length=self._tokenizer.model_max_length
        )
        injection_score = (
            1 - result[0]["score"] if result[0]["label"] == "INJECTION" else result[0]["score"]
        )

        if injection_score > self._threshold:
            log.debug(
                f"No prompt injection detected (max score: {injection_score}, threshold: {self._threshold})"
            )

            return prompt, True

        log.warning(
            f"Detected prompt injection with score: {injection_score}, threshold: {self._threshold}"
        )

        return prompt, False