from dataclasses import dataclass
from datetime import datetime as dt
from typing import List


@dataclass(frozen=True)
class TemplateContext:
    """
    Template Context

    The contextual information to provide to the template to ensure Walter
    writes informed newsletters.
    """

    user: str
    datestamp: dt
    portfolio_value: float
    stocks: list

    def get_context(self) -> str:
        return f"""
The current user is {self.user} and the date is {self.datestamp}. The total value of the user's portfolio as of this
date is ${self.portfolio_value:.2f} and the stocks owned by the user are {self.stocks}. When analyzing stocks, focus on 
the stocks owned by the user to deliver relevant insights about stocks the user owns. 
"""


@dataclass(frozen=True)
class TemplateKey:
    """
    Template Key

    The model object for a key given in the template. A template key is
    simply string substitution, the value given is not feed through Bedrock
    like a TemplatePrompt.
    """

    name: str
    value: str


@dataclass(frozen=True)
class TemplatePrompt:
    """
    Template Prompt

    The model object for a template prompt that is to be fed into Bedrock
    and the response injected into the template. The max generation length
    can be specified to ensure the newsletter is not too lengthy.
    """

    name: str
    prompt: str
    max_gen_length: int


@dataclass(frozen=True)
class TemplateSpec:
    """
    Template Spec

    The specifications of a given template and how to render it with
    responses from Bedrock.
    """

    context: TemplateContext
    keys: List[TemplateKey]
    prompts: List[TemplatePrompt]

    def get_context(self) -> str:
        return self.context.get_context()

    def get_prompts(self) -> List[TemplatePrompt]:
        return self.prompts

    def get_template_args(self) -> dict:
        template_args = {}
        for key in self.keys:
            template_args[key.name] = key.value
        for prompt in self.prompts:
            template_args[prompt.name] = prompt.prompt
        return template_args


def template_spec_from_dict(template_spec: dict) -> TemplateSpec:
    """
    Create a TemplateSpec object from a dictionary of key-value pairs.

    Args:
        template_spec: The arguments for the TemplateSpec

    Returns:
        The TemplateSpec object containing the key-value pairs as arguments.
    """
    # create context
    context = TemplateContext(
        user=template_spec["TemplateSpec"]["Context"]["User"],
        datestamp=template_spec["TemplateSpec"]["Context"]["Datestamp"],
        portfolio_value=template_spec["TemplateSpec"]["Context"]["PortfolioValue"],
        stocks=template_spec["TemplateSpec"]["Context"]["Stocks"],
    )
    # create template keys
    keys = []
    for key in template_spec["TemplateSpec"]["Keys"]:
        keys.append(TemplateKey(name=key["Key"], value=key["Value"]))
    # create template prompts
    prompts = []
    for prompt in template_spec["TemplateSpec"]["Prompts"]:
        prompts.append(
            TemplatePrompt(
                name=prompt["Key"],
                prompt=prompt["Prompt"],
                max_gen_length=prompt["MaxGenLength"],
            )
        )
    # create template spec
    spec = TemplateSpec(context=context, keys=keys, prompts=prompts)
    return spec
