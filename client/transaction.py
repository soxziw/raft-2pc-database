from typing import Tuple, List
from pydantic import BaseModel, Field, validator
import json
import utils



class TransactionRequest(BaseModel):
    """The transaction data structure"""
    sender_id: int = Field(example=1)
    recipient_id: int = Field(example=2)
    amount: float = Field(example=1.0)
    timestamp: str = None
    type: str = Field(default='INTRA-SHARD')  # INTRA-SHARD, CROSS-SHARD
    status: str = Field(default='PENDING')  # PENDING, SUCCESS, FAILED
    
    def __eq__(self, other):
        return self.sender_id == other.sender_id and self.recipient_id == other.recipient_id and self.amount == other.amount and self.type == other.type and self.timestamp == other.timestamp

    @validator('timestamp', pre=True, always=True)
    def set_create_time_now(cls, v):
        return v or utils.get_current_time()
    
    def to_json_str(self):
        return json.dumps(self.__dict__, sort_keys=True)

    def to_tuple(self):
        return self.sender_id, self.recipient_id, self.amount
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)