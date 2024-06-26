from typing import Optional, TextIO, Dict
import functools
import random

from rich.prompt import Prompt
from rich.console import Console

from fastrepl.eval.base import BaseSimpleEvalNode


class HumanClassifierRich(BaseSimpleEvalNode):
    def __init__(
        self,
        labels: Dict[str, str],
        rg=random.Random(42),
        instruction: str = "Classify the following sample",
        prompt_template="[bright_magenta]{instruction}:[/bright_magenta]\n\n{sample}\n\n",
        console: Optional[Console] = None,
        stream: Optional[TextIO] = None,
    ) -> None:
        self.labels = labels
        self.rg = rg
        self.render_prompt = functools.partial(
            prompt_template.format, instruction=instruction
        )
        self.console = console
        self.stream = stream

    def _shuffle(self):
        keys = list(self.labels.keys())
        choices = self.rg.sample(keys, len(keys))
        return choices

    def run(self, *, sample: str) -> str:
        prompt = self.render_prompt(sample=sample)  # TODO: Render descriptions
        choices = self._shuffle()

        return Prompt.ask(
            prompt,
            choices=choices,
            console=self.console,
            stream=self.stream,
        )
