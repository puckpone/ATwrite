from openai import OpenAI
import os
import re
import time

#  API Key
API_KEY = ""

# DeepSeek API 配置
client = OpenAI(api_key=API_KEY, base_url="")

# 小说设定
NOVEL_FILE = "novel.txt"
OVERVIEW_FILE = "overview.txt"  # 新增概要文件
NOVEL_TITLE = "仙途奇缘录"
WORD_LIMIT = 330000  # 66章 x 5000字
WORDS_PER_CHAPTER = 5000  # 每章5000汉字
CONTEXT_LENGTH = 1500  # 初始上下文长度，防止 input 过长
MAX_RETRIES = 10      # 每章最大重试次数

# 动态 sleep 变量
sleep_time = 20
sleep_levels = [20, 30, 40, 60, 120, 180, 300]  # 失败时逐步增加 sleep 时间
error_counts = {"20034": 0, "20035": 0, "20059": 0}  # 记录各错误次数

# 小说背景设定（玄幻/修真题材，详细设定）
NOVEL_BACKGROUND = """
《仙途奇缘录》讲述了一个凡人意外获得上古传承，踏入修真世界，历经无数艰险与磨难，最终羽化登仙的传奇历程。以下是本书的详细设定：

🔹 **世界背景**：
故事发生在一个名为“玄苍界”的浩渺天地，灵气弥漫，山川异彩，分为五大陆域（东玄、南荒、西漠、北寒、中州），各具特色。修真文明高度发达，凡人、修士、妖兽共存，天外魔域隐现，危机四伏。

🔹 **主要人物**：
1. **柳尘**：主角，凡人出身，因机缘获《混沌仙诀》，从平凡少年成长为修真顶峰之人。坚韧果敢，心怀仁义。
2. **冷锋**：剑修，机智冷峻，擅用“寒影剑法”，与柳尘结为生死兄弟。
3. **云瑶**：丹师，温柔坚毅，天赋异禀，精通炼丹与疗伤，是团队的灵魂支柱。
4. **玄阵子**：阵法师，身怀绝技，掌握“九天玄阵”，足智多谋，性情孤僻。
5. **魔皇苍冥**：反派领袖，邪修之王，冷酷残忍，欲以“天魔血祭”颠覆正道。
6. **其他人物**：仙门掌教凌霄子（正道领袖）、妖王赤焰（中立势力）、魔女紫鸢（阴险狡诈）等。

🔹 **重要书籍/文献**：
1. **《混沌仙诀》**：上古传承，柳尘核心功法，蕴含混沌之力，贯穿全书。
2. **《天丹录》**：云瑶随身之物，记录炼丹秘术，助团队渡劫疗伤。
3. **《玄阵残谱》**：玄阵子所得，记载失传阵法，是破敌关键。

🔹 **势力与组织**：
1. **正道仙盟**：以凌霄宗为首，维护修真界和平。
2. **天魔教**：邪修势力，野心勃勃，欲染指天下。
3. **妖族联盟**：妖兽族群，中立偏乱，伺机扩张。
4. **散修会**：无门派修士联合，势力分散但潜力巨大。

🔹 **战斗方式**：
1. **灵力战**：以灵气驱动功法、法宝，剑气、掌风、符箓为主。
2. **阵法战**：布阵困敌或增益己方，玄阵子擅用。
3. **丹药战**：云瑶以丹药提升战力或削弱敌人。
4. **法宝**：飞剑（寒影剑）、丹炉（天火炉）、阵盘（玄天盘），种类有限。

🔹 **升级体系**：
1. **境界划分**：炼气、筑基、金丹、元婴、化神、合道、渡劫、大乘、飞升九阶，每阶分初、中、后期。
2. **灵力升级**：通过修炼《混沌仙诀》、吞噬灵石、吸收天地灵气提升。
3. **心境升级**：历经生死、心魔试炼，领悟大道真谛。
4. **团队升级**：四人协作，功法互补，战力叠加。

🔹 **核心剧情**：
柳尘在山村偶得《混沌仙诀》，因体内混沌之力觉醒，引来正邪两道关注。他与冷锋、云瑶、玄阵子结伴，从妖兽肆虐的南荒出发，历经仙盟试炼、天魔教围剿，逐步揭开混沌之力的秘密。魔皇苍冥欲以“天魔血祭”重塑玄苍界，柳尘在复仇与拯救间抉择，最终对决苍冥，飞升仙界。

🔹 **主题与风格**：
小说融合惊险战斗、温情羁绊与哲理思索，展现修真者在逆境中磨砺心志、超脱凡尘的精神追求，兼具唯美与残酷。
"""

# 章节大纲（共66章，修真玄幻题材）
CHAPTERS = [
    "灵根初启", "凡尘起步", "仙缘初现", "命运转机", "洞天秘境", "灵脉觉醒", "剑气纵横", "妖兽来袭",
    "逆天试炼", "天罡降临", "灵丹妙药", "灵山之巅", "道心初成", "绝境求生", "仙法传承", "妖魔乱世",
    "秘术探秘", "神兽降世", "天界召唤", "天机流转", "破虚斩魔", "剑影迷踪", "灵魂净化", "元婴境界",
    "妖气缠身", "苍穹裂变", "仙路坎坷", "剑门争锋", "玄冰诀法", "血脉奇缘", "烈火真传", "星河倒影",
    "魔域重生", "灵脉风暴", "天道试炼", "魂魄归位", "古籍遗秘", "风云际会", "真元爆发", "丹药奇效",
    "秘境探险", "幻影重重", "宿命之争", "神光乍现", "逆境飞升", "仙魔大战", "九天诀破", "心魔迷境",
    "修罗战场", "神秘圣域", "剑仙归来", "重铸天命", "混沌初开", "天劫降临", "仙缘无双", "星辰大海",
    "幻境真章", "尘埃落定", "万法归宗", "灵魂觉醒", "逆转乾坤", "天道轮回", "傲视苍穹", "仙界之门",
    "极道巅峰", "永恒仙途"
]

def get_last_context():
    """获取文件末尾 CONTEXT_LENGTH 个汉字作为上下文"""
    if not os.path.exists(NOVEL_FILE):
        return ""
    with open(NOVEL_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    return text[-CONTEXT_LENGTH:] if len(text) > CONTEXT_LENGTH else text

def count_chinese_characters(text):
    """统计文本中的汉字数量"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def get_chapter_content(chapter_number):
    """获取指定章节的全部内容"""
    if not os.path.exists(NOVEL_FILE):
        return ""
    with open(NOVEL_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    chapter_pattern = fr"### 第{chapter_number}章.*?\n\n(.*?)(?=(### 第\d+章|\Z))"
    match = re.search(chapter_pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""

def get_latest_chapter_number():
    """根据文件内容判断当前已生成的章节数量"""
    if not os.path.exists(NOVEL_FILE):
        return 1
    with open(NOVEL_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    matches = re.findall(r"### 第(\d+)章", content)
    return max(map(int, matches)) + 1 if matches else 1

def get_all_overviews():
    """读取 overview.txt 中的所有概要内容"""
    if not os.path.exists(OVERVIEW_FILE):
        return ""
    with open(OVERVIEW_FILE, "r", encoding="utf-8") as f:
        return f.read()

def generate_chapter(chapter_number):
    """生成章节，持续生成直到达到5000汉字，同时生成概要"""
    chapter_title_line = f"### 第{chapter_number}章 {CHAPTERS[chapter_number - 1]}"
    print(f"\n📝 正在生成 {chapter_title_line} ...")
    retries = 0
    first_chunk = True  # 标记是否为第一次调用

    while True:
        # 获取当前章节已有内容并检查字数
        current_content = get_chapter_content(chapter_number)
        current_word_count = count_chinese_characters(current_content)
        if current_word_count >= WORDS_PER_CHAPTER:
            print(f"✅ {chapter_title_line} 已完成，字数：{current_word_count}")
            return  # 字数达标，退出生成

        print(f"当前字数：{current_word_count}/{WORDS_PER_CHAPTER}，继续续写...")
        retries = 0  # 重置重试计数

        while retries < MAX_RETRIES:
            try:
                context = get_last_context()
                all_overviews = get_all_overviews()  # 获取已有概要
                if first_chunk:
                    # 第一次调用时包含章节标题信息和详细设定
                    prompt = f"""你是一位顶级的修真小说家，现在正在创作一本玄幻修真题材的小说《{NOVEL_TITLE}》。
请根据以下设定和已有内容续写本章内容，并生成一个约100字的概要：

🔹 **小说背景设定**：
{NOVEL_BACKGROUND}

🔹 **已有剧情概要**（请确保剧情连贯）：
{all_overviews}

🔹 **本章节标题**：
{chapter_title_line}

🔹 **上一章节内容**（请参考，但避免剧情重复）：
{context}

🔹 **章节写作要求**：
1. 严格按照章节标题和已有概要推进剧情，不要跳跃式发展；
2. 保持修真玄幻与真实人性交织的风格；
3. 生成内容中不要重复章节标题；
4. 请生成续写内容，直接接续上文，不需要再添加章节标题；
5. 本次生成的内容直接写入文件；
6. 生成内容不小于5000个汉字，注意字数要求！

🔹 **概要要求**：
1. 生成一个约100字的概要，总结本章核心剧情；
2. 概要不包含标题，直接写入 overview.txt 文件。

✍️ 请以以下格式返回：
正文：
[续写内容]
概要：
[约100字的概要]
"""
                else:
                    # 后续调用时，不再包含章节标题
                    prompt = f"""你是一位顶级的修真小说家，现在正在续写玄幻修真题材的小说《{NOVEL_TITLE}》的第{chapter_number}章。
请根据以下设定和已有内容继续写作续篇，并生成一个约100字的概要：

🔹 **小说背景设定**：
{NOVEL_BACKGROUND}

🔹 **已有剧情概要**（请确保剧情连贯）：
{all_overviews}

🔹 **上一章节内容**（请参考，但避免剧情重复）：
{context}

🔹 **续写要求**：
1. 请续写上文情节，直接衔接，不要再次生成章节标题；
2. 保持修真玄幻与真实人性交织的风格；
3. 生成的续写内容不应包含多余的标题或重复内容；
4. 请生成续写部分内容，直接写入文件；
5. 生成内容不小于5000个汉字，注意字数要求！

🔹 **概要要求**：
1. 生成一个约100字的概要，总结本章核心剧情；
2. 概要不包含标题，直接写入 overview.txt 文件。

✍️ 请以以下格式返回：
正文：
[续写内容]
概要：
[约100字的概要]
"""
                # 记录 DeepSeek API 的思考开始时间
                think_start_time = time.time()
                print("🤔 DeepSeek 开始思考...")
                completion = client.chat.completions.create(
                    model="deepseek-r1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=WORDS_PER_CHAPTER * 4 // 3,  # 尽量多生成内容
                    stream=False
                )
                # 记录 DeepSeek API 的思考结束时间
                think_end_time = time.time()
                think_duration = think_end_time - think_start_time
                # 如果 API 返回了思考过程则打印，否则提示无显式思考过程
                if hasattr(completion.choices[0].message, "reasoning_content") and completion.choices[0].message.reasoning_content:
                    print(f"🤔 DeepSeek 思考过程：{completion.choices[0].message.reasoning_content}")
                else:
                    print("🤔 DeepSeek 无显式思考过程")
                print(f"🤔 DeepSeek 思考耗时：{think_duration:.2f}秒")
                
                final_answer = completion.choices[0].message.content
                if not final_answer:
                    final_answer = ""

                # 分割正文和概要
                parts = final_answer.split("概要：")
                if len(parts) != 2:
                    raise ValueError("返回格式错误，未正确分割正文和概要")
                
                main_content = parts[0].replace("正文：", "").strip()
                overview_content = parts[1].strip()

                # 写入正文到 novel.txt
                with open(NOVEL_FILE, "a", encoding="utf-8") as f:
                    if first_chunk:
                        # 第一次写入时包含章节标题
                        f.write(chapter_title_line + "\n\n" + main_content + "\n\n")
                    else:
                        # 后续写入时仅追加内容
                        f.write(main_content + "\n\n")

                # 写入概要到 overview.txt
                with open(OVERVIEW_FILE, "a", encoding="utf-8") as f:
                    f.write(overview_content + "\n\n")

                first_chunk = False  # 后续调用不再包含标题
                break  # 单次生成成功，跳出重试循环，继续检查字数

            except Exception as e:
                error_message = str(e)
                print(f"⚠️ 章节生成失败：{error_message}")

                if "20034" in error_message:  # 并发超限
                    error_counts["20034"] += 1
                    sleep_time_adjust = min(sleep_time * 2, sleep_levels[-1])
                    print(f"⚠️ 触发并发限制，增加 sleep_time 为 {sleep_time_adjust}s")
                    time.sleep(sleep_time_adjust)
                elif "20035" in error_message:  # 内容过滤
                    error_counts["20035"] += 1
                    prompt += " 请严格避免敏感内容，使用更委婉的语言。"
                    print("⚠️ 触发内容过滤，调整 prompt 后重试")
                    time.sleep(10)
                elif "20059" in error_message:  # 输入内容超长
                    error_counts["20059"] += 1
                    global CONTEXT_LENGTH
                    CONTEXT_LENGTH = max(CONTEXT_LENGTH - 200, 800)
                    print(f"⚠️ 触发输入过长，减少 CONTEXT_LENGTH 为 {CONTEXT_LENGTH}")
                    time.sleep(10)
                else:
                    print("⚠️ 未知错误，稍后重试")
                    time.sleep(sleep_time)

                retries += 1

            if retries >= MAX_RETRIES:
                print(f"⚠️ 重试 {MAX_RETRIES} 次仍未成功，等待后继续重试本章节...")
                time.sleep(sleep_time)
                break

def main():
    while True:
        chapter_number = get_latest_chapter_number()
        if chapter_number > len(CHAPTERS):
            print("✅ 所有章节已生成完毕！")
            break
        generate_chapter(chapter_number)

if __name__ == "__main__":
    main()