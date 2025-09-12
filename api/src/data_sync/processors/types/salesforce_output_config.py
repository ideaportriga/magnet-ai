from dataclasses import dataclass


@dataclass
class SalesforceOutputConfig:
    columns: list[str]
    output_template: str
