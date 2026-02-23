import json
import os
from typing import Dict, Any, List, Optional, Type

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models  # ✅ 不再 from models import Scene...，避免名字不一致直接崩
from llm import LLMClient

# --------- DB 依赖（尽量兼容你现有 db.py）---------
try:
    from db import SessionLocal  # 你仓库里一般会有
except Exception as e:
    SessionLocal = None  # type: ignore


def get_db():
    if SessionLocal is None:
        raise RuntimeError("找不到 db.SessionLocal：请检查 db.py 是否定义了 SessionLocal")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------- 自动匹配 ORM 类名（兼容 Scene/SceneModel/AuditScene 等）---------
def _pick_model(candidates: List[str]) -> Type:
    for name in candidates:
        obj = getattr(models, name, None)
        if obj is not None:
            return obj
    raise RuntimeError(
        f"models.py 里找不到这些类名：{candidates}。"
        f"请打开 models.py 看看真实类名，然后我帮你把候选列表补全。"
    )


SceneModel = _pick_model(["Scene", "SceneModel", "AuditScene", "Scenes"])
NodeModel  = _pick_model(["Node", "NodeModel", "AuditNode", "Nodes"])
RunModel   = _pick_model(["Run", "RunModel", "AuditRun", "Runs"])


DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen-plus")  # 可通过环境变量覆盖


# --------- 工具：尽量把 LLM 输出转 JSON ---------
def _try_parse_json(text: str) -> Any:
    if not text:
        return text
    s = text.strip()
    try:
        return json.loads(s)
    except Exception:
        pass

    # 尝试截取第一段 JSON
    start = None
    for i, ch in enumerate(s):
        if ch in "[{":
            start = i
            break
    if start is None:
        return s

    end = None
    for j in range(len(s) - 1, -1, -1):
        if s[j] in "]}":
            end = j + 1
            break
    if end is None:
        return s

    snippet = s[start:end]
    try:
        return json.loads(snippet)
    except Exception:
        return s


def _merge_results(scene_name: str, per_node: Dict[str, Any]) -> Dict[str, Any]:
    conclusion = "通过"
    risk = "低"
    details: List[Dict[str, Any]] = []

    def add_detail(node_key: str, item: Any):
        if isinstance(item, dict):
            d = dict(item)
        else:
            d = {"raw": item}
        d.setdefault("node_key", node_key)
        details.append(d)

    for k, v in per_node.items():
        if k == "start":
            continue
        if isinstance(v, list):
            for it in v:
                if isinstance(it, dict) and (it.get("is_pass") in ["否", "no"]):
                    conclusion = "驳回"
                    add_detail(k, it)
                elif isinstance(it, dict) and ("unpass_type" in it or "unpass_reason" in it):
                    conclusion = "驳回"
                    add_detail(k, it)
        elif isinstance(v, dict):
            if v.get("获奖次数") == "no" or v.get("is_pass") == "否":
                conclusion = "驳回"
                add_detail(k, v)
        else:
            if "不符合" in str(v) or "否" in str(v):
                conclusion = "驳回"
                add_detail(k, {"raw": v})

    blob = json.dumps(details, ensure_ascii=False)
    if any(x in blob for x in ["保本", "保收益", "最高", "最佳", "无风险", "承诺", "高风险"]):
        risk = "高"
    elif conclusion == "驳回":
        risk = "中"

    return {
        "scene": scene_name,
        "总审核结果": conclusion,
        "风险等级": risk,
        "违规详情": details,
    }


# --------- 核心：运行审核（不假设 scene.nodes 一定存在）---------
def run_audit(
    db: Session,
    scene_id: int,
    text: str,
    model: Optional[str] = None,
) -> Any:
    scene = db.query(SceneModel).filter(SceneModel.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")

    # 兼容：scene.nodes 可能叫 nodes / node_list / etc
    nodes = getattr(scene, "nodes", None)
    if nodes is None:
        # 尝试通过 NodeModel 查
        nodes = db.query(NodeModel).filter(NodeModel.scene_id == scene_id).all()

    # 兼容：order 字段可能不存在
    try:
        nodes = sorted(nodes, key=lambda n: getattr(n, "order", 0))
    except Exception:
        pass

    per_node: Dict[str, Any] = {}
    chosen_model = model or DEFAULT_MODEL

    llm = LLMClient()

    for node in nodes:
        node_key = getattr(node, "key", None) or str(getattr(node, "id", "node"))
        tpl = getattr(node, "prompt_template", "") or ""

        if node_key == "start" or not str(tpl).strip():
            per_node[node_key] = {"ok": True}
            continue

        prompt = str(tpl).replace("{text}", text).replace("{替换为待审核文本}", text)

        messages = [
            {"role": "system", "content": "你是金融合规与内容审核专家。请严格按要求输出 JSON。"},
            {"role": "user", "content": prompt},
        ]
        out = llm.chat(model=chosen_model, messages=messages, temperature=0.0)
        per_node[node_key] = _try_parse_json(out)

    scene_name = getattr(scene, "name", f"scene_{scene_id}")
    merged = _merge_results(scene_name, per_node)

    # 写入 Run 记录（字段名做兼容）
    run = RunModel()
    setattr(run, "scene_id", scene_id)
    setattr(run, "status", "done")
    setattr(run, "conclusion", merged.get("总审核结果", "—"))
    setattr(run, "risk", merged.get("风险等级", "—"))
    setattr(run, "input_text", text)
    setattr(run, "results", per_node)
    setattr(run, "merged", merged)

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


# --------- FastAPI ---------
app = FastAPI(title="Audit SaaS Backend", version="0.1.0")


class AuditRunReq(BaseModel):
    scene_id: int
    text: str
    model: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/scenes")
def list_scenes(db: Session = Depends(get_db)):
    scenes = db.query(SceneModel).all()
    out = []
    for s in scenes:
        out.append(
            {
                "id": getattr(s, "id", None),
                "name": getattr(s, "name", None),
                "desc": getattr(s, "desc", None),
            }
        )
    return out


@app.post("/audit/run")
def audit_run(req: AuditRunReq, db: Session = Depends(get_db)):
    # ✅ 千问 key 没配会直接报错（提示你去 Railway Variables 配）
    if not os.getenv("DASHSCOPE_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="缺少环境变量 DASHSCOPE_API_KEY（Railway -> Variables 里添加）",
        )
    run = run_audit(db, req.scene_id, req.text, req.model)
    return {
        "run_id": getattr(run, "id", None),
        "scene_id": getattr(run, "scene_id", None),
        "status": getattr(run, "status", None),
        "conclusion": getattr(run, "conclusion", None),
        "risk": getattr(run, "risk", None),
        "merged": getattr(run, "merged", None),
        "results": getattr(run, "results", None),
    }


@app.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(RunModel).filter(RunModel.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": getattr(run, "id", None),
        "scene_id": getattr(run, "scene_id", None),
        "status": getattr(run, "status", None),
        "conclusion": getattr(run, "conclusion", None),
        "risk": getattr(run, "risk", None),
        "merged": getattr(run, "merged", None),
        "results": getattr(run, "results", None),
        "input_text": getattr(run, "input_text", None),
    }
