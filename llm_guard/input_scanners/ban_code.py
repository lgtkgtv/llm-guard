from typing import Optional

from llm_guard.model import Model
from llm_guard.transformers_helpers import get_tokenizer_and_model_for_classification, pipeline
from llm_guard.util import calculate_risk_score, get_logger

from .base import Scanner

LOGGER = get_logger()

MODEL_SM = Model(
    path="vishnun/codenlbert-sm",
    revision="caa3d167fd262c76c7da23cd72c1d24cfdcafd0f",
    onnx_path="protectai/vishnun-codenlbert-sm-onnx",
    onnx_revision="2b1d298410bd98832e41e3da82e20f6d8dff1bc7",
    pipeline_kwargs={"truncation": True, "max_length": 512},
)

MODEL_TINY = Model(
    path="vishnun/codenlbert-tiny",
    revision="2caf5a621b29c50038ee081479a82f192e9a5e69",
    onnx_path="protectai/vishnun-codenlbert-tiny-onnx",
    onnx_revision="84148cb4b3f08fe44705e2d8ed81505450ae8abd",
    pipeline_kwargs={"truncation": True, "max_length": 512},
)


class BanCode(Scanner):
    """
    A scanner that detects if input is code and blocks it.
    """

    def __init__(
        self,
        *,
        model: Optional[Model] = None,
        threshold: float = 0.9,
        use_onnx: bool = False,
    ):
        """
        Initializes the BanCode scanner.

        Parameters:
           model (Model, optional): The model object.
           threshold (float): The probability threshold. Default is 0.9.
           use_onnx (bool): Whether to use ONNX instead of PyTorch for inference.
        """

        self._threshold = threshold
        if model is None:
            model = MODEL_SM

        tf_tokenizer, tf_model = get_tokenizer_and_model_for_classification(
            model=model,
            use_onnx=use_onnx,
        )

        self._classifier = pipeline(
            task="text-classification",
            model=tf_model,
            tokenizer=tf_tokenizer,
            **model.pipeline_kwargs,
        )

    def scan(self, prompt: str) -> (str, bool, float):
        if prompt.strip() == "":
            return prompt, True, 0.0

        result = self._classifier(prompt)[0]
        score = round(
            result["score"] if result["label"] == "CODE" else 1 - result["score"],
            2,
        )

        if score > self._threshold:
            LOGGER.warning("Detected code in the text", score=score, threshold=self._threshold)

            return prompt, False, calculate_risk_score(score, self._threshold)

        LOGGER.debug("No code detected in the text", score=score, threshold=self._threshold)

        return prompt, True, 0.0
