from datetime import datetime

from pydantic import BaseModel

class Metrics(BaseModel):
    metric_name: str
    date: datetime
    target: str
    metric_all: float
    metric_90_d: float
    metric_30_d: float
    metric_7_d: float
    model_name: str

    def __repr__(self):
        return f"Metrices(metric_name={self.metric_name}, date={self.date}, target={self.target}, metric_all={self.metric_all}, metric_90_d={self.metric_90_d}, metric_30_d={self.metric_30_d}, metric_7_d={self.metric_7_d}, model_name={self.model_name})"