import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from .models import Scene, Node, Run
from .llm import LLMClient

DEFAULT_MODEL = "qwen-plus"  # 可在请求里覆盖

def _try_parse_json(text: str) -> Any:
    # 兼容 LLM 输出前后带说明的情况：尽量截取首个 JSON 数组或对象
    if not text:
        return text
    s = text.strip()
    try:
        return json.loads(s)
    except Exception:
        pass

    # heuristic: find first '{' or '[' and last matching end
    start = None
    for i,ch in enumerate(s):
        if ch in "[{":
            start = i
            break
    if start is None:
        return s
    end = None
    for j in range(len(s)-1, -1, -1):
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

def _merge_results(scene: Scene, per_node: Dict[str, Any]) -> Dict[str, Any]:
    # 这里做一个“最小可用”的合并器：
    # - 任何节点有不通过项 => 驳回
    # - 粗略风险：存在“高风险/保本/绝对化/承诺收益”等关键字 => 高，否则中/低
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

    for k,v in per_node.items():
        if k == "start":
            continue
        if isinstance(v, list):
            # list 里如果有 is_pass=否 或 unpass_type 等，就当作不通过
            for it in v:
                if isinstance(it, dict) and (it.get("is_pass") == "否" or it.get("is_pass") == "no"):
                    conclusion = "驳回"
                    add_detail(k, it)
                elif isinstance(it, dict) and ("unpass_type" in it or "unpass_reason" in it):
                    conclusion = "驳回"
                    add_detail(k, it)
        elif isinstance(v, dict):
            # award prompt 的 yes/no
            if v.get("获奖次数") == "no" or v.get("is_pass") == "否":
                conclusion = "驳回"
                add_detail(k, v)
        else:
            # plain text
            if "不符合" in str(v) or "否" in str(v):
                conclusion = "驳回"
                add_detail(k, {"raw": v})

    blob = json.dumps(details, ensure_ascii=False)
    if any(x in blob for x in ["保本", "保收益", "最高", "最佳", "无风险", "承诺", "高风险"]):
        risk = "高"
    elif conclusion == "驳回":
        risk = "中"

    return {
        "scene": scene.name,
        "总审核结果": conclusion,
        "风险等级": risk,
        "违规详情": details,
    }

def run_audit(db: Session, scene_id: int, text: str, meta: Dict[str, Any] | None = None, model: str | None = None) -> Run:
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise ValueError("scene not found")

    nodes = sorted(scene.nodes, key=lambda n: n.order)

    llm = None
    per_node: Dict[str, Any] = {}
    chosen_model = model or DEFAULT_MODEL

    for node in nodes:
        if node.key == "start" or not node.prompt_template.strip():
            per_node[node.key] = {"ok": True}
            continue

        if llm is None:
            llm = LLMClient()

        prompt = node.prompt_template.replace("{text}", text)
        messages = [
            {"role":"system","content":"你是金融合规与内容审核专家。请严格按要求输出 JSON。"},
            {"role":"user","content":prompt},
        ]
        out = llm.chat(model=chosen_model, messages=messages, temperature=0.0)
        per_node[node.key] = _try_parse_json(out)

    merged = _merge_results(scene, per_node)

    run = Run(
        scene_id=scene_id,
        status="done",
        conclusion=merged.get("总审核结果","—"),
        risk=merged.get("风险等级","—"),
        input_text=text,
        results=per_node,
        merged=merged,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
