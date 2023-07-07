import dataclasses
import typing as t

import dotenv


@dataclasses.dataclass
class Config:
    TOKEN: str
    PISTON_URL: str
    GODBOLT_URL: str


env_vars: dict[str, str] = t.cast(dict[str, str], dotenv.dotenv_values())
CONFIG = Config(**env_vars)
