from dataclasses import dataclass
from io import BytesIO
from typing import Dict


@dataclass
class Template:
    name: str
    contents: str


@dataclass
class TemplateAssets:
    name: str
    assets: Dict[str, BytesIO]
