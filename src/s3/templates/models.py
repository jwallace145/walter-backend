from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List


@dataclass
class Parameter:
    """
    Parameter

    Newsletter templates contain numerous parameters that each comprise a key, a prompt, and
    a max generation length. The key is used to specify where in the template to input the
    response to the prompt and the max generation length limits the response from the foundation
    model to the number of tokens specified. The parameters used by the templates allow Walter
    to write custom newsletters tailored for each user.

    Example:

    Walter's Newsletter
    { key: Greeting, prompt: Write a newsletter greeting for Walter, max_gen_len: 50}
    { key: Goodbye, prompt: Write a goodbye message for Walter and wish him a great day!, max_gen_len: 20}
    """

    key: str
    prompt: str
    max_gen_len: float


@dataclass
class TemplateSpec:
    """
    TemplateSpec

    The TemplateSpec is the specifications to render the template with the responses to the
    included prompts. To successfully render a template, answers to all of its parameters
    prompts must have responses. The list of parameters defines the template spec completely.
    """

    parameters: List[Parameter]


@dataclass
class Template:
    name: str
    contents: str


@dataclass
class TemplateAssets:
    name: str
    assets: Dict[str, BytesIO]
