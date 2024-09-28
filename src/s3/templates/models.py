from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List


@dataclass
class Parameter:
    """
    Parameter

    Newsletter templates contain numerous parameters that each comprise a key and a prompt.
    The key is used to specify where in the template to input the response to the prompt.
    The parameters used by the templates allow Walter to write custom sections tailored
    for each user.

    Example:

    Walter's Newsletter
    { key: Greeting, prompt: Write a newsletter greeting for Walter}
    { key: Goodbye, prompt: Write a goodbye message for Walter and wish him a great day! }
    """

    key: str
    prompt: str


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
