from typing import Any, Dict, List

from pydantic import BaseModel, PositiveInt

class CryptoWatchDTO(BaseModel):
    result: Dict[str, List[List[float]]]
    allowance: Dict[str, Any]
