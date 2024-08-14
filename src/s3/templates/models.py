from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List


@dataclass
class Parameter:
    key: str
    prompt: str


@dataclass
class TemplateSpec:
    parameters: List[Parameter]


@dataclass
class Template:
    name: str
    contents: str


@dataclass
class TemplateAssets:
    name: str
    assets: Dict[str, BytesIO]
