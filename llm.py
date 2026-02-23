from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

class NodeIn(BaseModel):
    key: str
    title: str
    order: int = 0
    x: int = 60
    y: int = 160
    prompt_template: str = ""

class SceneCreate(BaseModel):
    name: str
    description: str = ""
    nodes: List[NodeIn] = Field(default_factory=list)

class SceneOut(BaseModel):
    id: int
    name: str
    description: str

class SceneDetail(SceneOut):
    nodes: List[NodeIn]

class RunCreate(BaseModel):
    scene_id: int
    text: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    model: Optional[str] = None  # e.g. qwen-plus

class RunOut(BaseModel):
    id: int
    scene_id: int
    status: str
    conclusion: str
    risk: str
    input_text: str
    results: Dict[str, Any]
    merged: Dict[str, Any]
