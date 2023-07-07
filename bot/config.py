import dataclasses
import typing

import dotenv


@dataclasses.dataclass
class Config:
    TOKEN: str
    PISTON_URL: str
    GODBOLT_URL: str


env_vars: typing.Any = dotenv.dotenv_values()
CONFIG = Config(**env_vars)
