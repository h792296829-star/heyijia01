from sqlalchemy.orm import Session
from .models import Scene, Node

def seed_if_empty(db: Session):
    if db.query(Scene).count() > 0:
        return

    # 你给的 Prompt（简化版：只放 3-5 个节点示例；可自行替换成完整 Prompt）
    grammar_prompt = """请你作为内容合规审核专家,完成以下任务:
任务:用下面提供的法规及对应审核点要求,审核文档全文每一句内容,判断其是否符合各项审核点要求,不符合则is_pass记为“否”,输出全部所有的不符合项,将每个不符合项作为单独的dict对象,按JSON list格式输出:
[{"is_pass": "否", "unpass_type": "文法类错误","unpass_content": "不符合要求内容原文,不少于20个字符","unpass_reason": "原因","suggest": "修改建议"}]。
<审核点要求开始位置>
1.不符合要求的类型:文法类错误
(1)错字、少字、多字错误
(2)人名一致性验证
(3)文字不合理重复
(4) 不要校验日期格式问题
<审核点要求结束位置>
<要审核文档内容开始位置>
{text}
<要审核文档内容结束位置>
请按JSON list格式输出审核结果:
"""

    adlaw_prompt = """请你作为内容合规审核专家,完成以下任务:
任务:用下面提供的法规及对应审核点要求,审核文档全文每一句内容,判断其是否符合各项审核点要求,不符合则is_pass记为“否”,输出全部所有的不符合项,将每个不符合项作为单独的dict对象,按JSON list格式输出:
[{"is_pass": "否", "unpass_type": "广告法合规违规","unpass_content": "原文不少于20个字符","unpass_reason": "原因","suggest": "修改建议"}]。
<审核点要求开始位置>
《广告法》核心条款：第四条（禁止虚假误导）、第九条（禁止绝对化用语）、十一条（数据需标注来源）、二十五条（禁止保本保收益承诺）
<审核点要求结束位置>
<要审核文档内容开始位置>
{text}
<要审核文档内容结束位置>
请按JSON list格式输出审核结果:
"""

    source_prompt = """请你作为内容合规审核专家,完成以下任务:
任务:用下面提供的法规及对应条款要求,审核文档全文每一句内容,判断其是否符合各个条款要求,不符合则is_pass记为“否”,将每个不符合项作为单独的dict对象,按JSON list格式输出:
[{"is_pass": "否","unpass_content": "不符合要求内容原文或缺少内容","unpass_reason": "原因","suggest": "修改意见"}]。
<审核点要求开始位置>
凡是文章中涉及到数据的地方(比如金额、数字、百分比等)没有标注数据出处；“最近/近日/近期”需精确到日；指数名词无需标注。
<审核点要求结束位置>
<要审核文档内容开始位置>
{text}
<要审核文档内容结束位置>
请按JSON格式输出审核结果:
"""

    award_prompt = """{
从以下基金营销物料的正文以及备注中审核数据逻辑是否正确,请将以下【文本】拆分为【正文】和【备注】2部分,然后按顺序执行以下任务:
抽取【正文】中关于获奖次数的描述并抽取次数记为a；
抽取【备注】中的获奖时间并统计个数记为b；
抽取【备注】中关于获奖次数的描述并抽取次数记为c；
判断: a==b, a==c, 输出json:
如果全部成立输出:{"获奖次数":"yes","正文获奖次数":a,"备注获奖日期-次数":b,"备注获奖次数":c}
否则输出:{"获奖次数":"no","正文获奖次数":a,"备注获奖日期-次数":b,"备注获奖次数":c}
【文本】:
{text}
} 
"""

    fund_rule_prompt = """请你作为内容合规审核专家,完成以下任务:
任务:用下面提供的法规及对应审核点要求,审核文档全文每一句内容,判断其是否符合各项审核点要求,不符合则is_pass记为“否”,输出全部所有的不符合项,将每个不符合项作为单独的dict对象,按JSON list格式输出:
[{"is_pass":"否","unpass_type":"基金宣传规定违规","unpass_content":"原文不少于20个字符","unpass_reason":"原因","suggest":"修改建议"}]。
<审核点要求开始位置>
《公开募集证券投资基金宣传推介材料管理暂行规定》核心条款：第四条（业绩展示需超6个月）、第六条（禁止承诺未来收益）、第十五条（禁止使用“安全/高收益/无风险”等表述）
<审核点要求结束位置>
<要审核文档内容开始位置>
{text}
<要审核文档内容结束位置>
请按JSON list格式输出审核结果:
"""

    s2 = Scene(name="基金产品宣传类", description="演示：基金产品宣传类全链路")
    s2.nodes = [
        Node(key="start", title="开始", order=0, x=40, y=40, prompt_template=""),
        Node(key="grammar", title="文法类审核", order=1, x=60, y=160, prompt_template=grammar_prompt),
        Node(key="ad_law", title="《广告法》合规", order=2, x=330, y=160, prompt_template=adlaw_prompt),
        Node(key="data_source", title="数据来源存在性", order=3, x=600, y=160, prompt_template=source_prompt),
        Node(key="award", title="获奖次数准确性", order=4, x=60, y=310, prompt_template=award_prompt),
        Node(key="fund_reg", title="基金宣传规定合规", order=5, x=330, y=310, prompt_template=fund_rule_prompt),
    ]
    db.add(s2)

    s1 = Scene(name="市场点评类", description="演示：市场点评类")
    s1.nodes = [
        Node(key="start", title="开始", order=0, x=40, y=40, prompt_template=""),
        Node(key="grammar", title="文法类审核", order=1, x=60, y=160, prompt_template=grammar_prompt),
        Node(key="ad_law", title="《广告法》合规", order=2, x=330, y=160, prompt_template=adlaw_prompt),
        Node(key="data_source", title="数据来源存在性", order=3, x=600, y=160, prompt_template=source_prompt),
    ]
    db.add(s1)

    s3 = Scene(name="投资者教育类", description="演示：投教类")
    s3.nodes = [
        Node(key="start", title="开始", order=0, x=40, y=40, prompt_template=""),
        Node(key="grammar", title="文法类审核", order=1, x=60, y=160, prompt_template=grammar_prompt),
        Node(key="ad_law", title="《广告法》合规", order=2, x=330, y=160, prompt_template=adlaw_prompt),
        Node(key="data_source", title="数据来源存在性", order=3, x=600, y=160, prompt_template=source_prompt),
    ]
    db.add(s3)

    db.commit()
