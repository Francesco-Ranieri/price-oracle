from typing import Any, Dict, List, Union

from pydantic import BaseModel, PositiveInt

class KrakenDTO(BaseModel, extra="allow"):
    result: Dict[str, Union[List[List[float]], float]]
    error: List[Any]
