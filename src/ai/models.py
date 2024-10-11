from dataclasses import dataclass
from enum import Enum


class Model(Enum):
    META_LLAMA3_70B = "meta.llama3-70b-instruct-v1:0"


def get_model(model_id: str) -> Model:
    for model in Model:
        if model.value == model_id:
            return model
    raise ValueError(f"Unexpected model '{model_id}' given!")


@dataclass
class Prompt:
    name: str
    prompt: str
    max_gen_len: float


@dataclass
class Response:
    name: str
    response: str
