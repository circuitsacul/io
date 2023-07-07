import dataclasses
import typing as t

import dotenv


@dataclasses.dataclass
class Config:
    TOKEN: str
    PISTON_URL: str = "https://emkc.org/api/v2/piston/"
    GODBOLT_URL: str = "https://godbolt.org/api/"


env_vars: dict[str, str] = t.cast(dict[str, str], dotenv.dotenv_values())
try:
    CONFIG = Config(**env_vars)
except TypeError as e:
    raise Exception(
        "You have an error in your .env file. Check the README for more info."
    ) from e
