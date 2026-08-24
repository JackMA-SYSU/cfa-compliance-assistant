/* 离线规则引擎：后端 RuleBasedClassifier 的 JS 精简版，断网时提供基础分析 */
window.CATEGORIES = {
  gift_entertainment: {
    name: '收礼/招待/差旅', standards: ['I(B)', 'IV(B)', 'VI(A)'],
    keywords: ['礼品','礼物','赠礼','送礼','收礼','馈赠','好处','招待','宴请','请客','吃饭','聚餐','餐饮','娱乐','差旅','旅行','旅游','机票','酒店','住宿','报销','高尔夫','球票','门票','演唱会','赛事','度假','免费','会议费'],
  },
  side_job: {
    name: '兼职/副业/外部授课', standards: ['IV(A)', 'IV(B)', 'VI(A)'],
    keywords: ['兼职','副业','私活','第二职业','授课','讲课','讲座','培训','演讲','顾问','咨询','外部董事会','业余','外聘'],
  },
  leaving_job: {
    name: '离职/跳槽/创业', standards: ['IV(A)', 'III(E)'],
    keywords: ['离职','跳槽','辞职','创业','换工作','离开公司','新雇主','新公司','带走客户','客户名单','挖角','竞争对手','竞业'],
  },
  personal_trade: {
    name: '个人账户交易/抢先交易', standards: ['VI(B)', 'II(A)'],
    keywords: ['个人交易','个人账户','自己的账户','本人账户','亲属账户','抢先交易','先于客户','抢在客户前','自营','个人投资','提前下单'],
  },
  extra_compensation: {
    name: '额外报酬/介绍费', standards: ['IV(B)', 'VI(C)'],
    keywords: ['额外报酬','额外补偿','额外收入','介绍费','推荐费','业绩奖励','业绩提成','奖金','回扣','好处费','佣金','报酬安排','薪酬之外'],
  },
  research_integrity: {
    name: '研报/评级/虚假陈述', standards: ['V(A)', 'V(B)', 'I(C)'],
    keywords: ['研报','研究报告','评级','推荐','预测','目标价','虚假陈述','误导','夸大','遗漏','不实','编造','合理依据','尽职调查','模型','假设'],
  },
  mnpi: {
    name: '内幕信息/泄密', standards: ['II(A)'],
    keywords: ['内幕','非公开','重大非公开','未公开信息','机密','泄密','泄露','内部消息','小道消息','传闻','未披露','并购消息','透露'],
  },
  conflict_interest: {
    name: '利益冲突/持股/董事职务', standards: ['VI(A)', 'I(B)'],
    keywords: ['利益冲突','冲突','持股','持有股票','股权','股份','董事','董事会','关联方','关联交易','亲属','家人','配偶','朋友','供应商'],
  },
  misconduct: {
    name: '不当行为/专业失德', standards: ['I(D)'],
    keywords: ['骂','辱骂','侮辱','威胁','恐吓','打架','斗殴','贿赂','行贿','受贿','欺诈','欺骗','舞弊','挪用','侵吞','侵占','盗用','骚扰','性骚扰','歧视','造假','做假','伪造','泄露隐私','泄漏隐私','粗口','飙脏话','不尊重'],
  },
};

window.STANDARD_INFO = {
  'I(A)': ['法律认知', '遵守适用法律法规，对违法行为向监管者报告', '法律 法规 监管 违法 报告'],
  'I(B)': ['独立性与客观性', '拒绝可能损害独立客观性的礼品、招待或好处', '送礼 收礼 礼品 招待 差旅 高尔夫 独立 客观 好处'],
  'I(C)': ['虚假陈述', '不得虚假陈述或遗漏重大事实', '虚假 误导 遗漏 夸大 不实'],
  'I(D)': ['不当行为', '不得欺诈、欺骗等有损职业声誉的行为', '欺诈 欺骗 舞弊 不当'],
  'II(A)': ['重大非公开信息', '不得利用或促使他人利用重大非公开信息', '内幕 非公开 机密 泄密 未公开 重大信息'],
  'II(B)': ['市场操纵', '不得操纵市场价格或成交量', '操纵 价格 虚假交易'],
  'III(A)': ['忠诚、审慎与谨慎', '以客户利益为先，审慎管理客户资产', '忠诚 客户利益 代理投票 审慎 谨慎'],
  'III(B)': ['公平交易', '公平客观对待所有客户', '公平 平等 客户'],
  'III(C)': ['适当性', '行动前了解客户需求、目标与风险承受能力', '适当 风险承受 了解客户 需求 目标'],
  'III(D)': ['业绩陈述', '业绩陈述公平、准确、完整', '业绩 收益 展示 陈述'],
  'III(E)': ['保密', '对客户及前雇主信息保密', '保密 机密 客户信息 前雇主'],
  'IV(A)': ['对雇主的忠诚', '不得剥夺雇主技能优势，避免利益冲突', '雇主 兼职 离职 跳槽 副业 竞争 忠诚'],
  'IV(B)': ['额外报酬安排', '向雇主书面披露并取得所有相关方书面同意', '额外报酬 奖金 佣金 报酬 书面披露 同意'],
  'IV(C)': ['监督者责任', '建立合规程序，监督下属行为', '监督 下属 管理 合规程序'],
  'V(A)': ['勤勉与合理依据', '基于充分研究与合理依据提出建议', '研报 研究 依据 尽职调查 勤勉'],
  'V(B)': ['与客户沟通', '区分事实与观点，披露分析方法与风险', '沟通 观点 事实 风险 披露'],
  'V(C)': ['记录保存', '保存支持投资决策与建议的记录', '记录 保存 存档'],
  'VI(A)': ['利益冲突披露', '充分披露影响独立性的利益冲突', '利益冲突 持股 董事 股份 冲突'],
  'VI(B)': ['交易优先顺序', '客户交易优先于个人交易，禁止抢先', '个人交易 抢先 客户优先 自营 优先'],
  'VI(C)': ['介绍费', '披露并取得同意后收取介绍费', '介绍费 推荐费 转介'],
  'VII(A)': ['CFA项目参与者行为', '遵守考试规则，不泄露考题', '考试 作弊 泄题'],
  'VII(B)': ['CFA头衔引用', '按规范引用CFA会员资格与头衔', '头衔 引用 会员资格'],
};

function offlineClassify(text) {
  let best = null, bestScore = 0, rules = [];
  for (const [cat, cfg] of Object.entries(CATEGORIES)) {
    let score = 0, hits = [];
    cfg.keywords.forEach(kw => { if (text.includes(kw)) { score++; hits.push(kw); } });
    if (score > bestScore) { bestScore = score; best = cat; rules = hits; }
  }
  if (!best) return { category: 'uncertain', confidence: 0, matched_rules: [] };
  return {
    category: best,
    confidence: Math.min(0.95, 0.55 + bestScore * 0.08),
    matched_rules: rules.slice(0, 6),
  };
}

function charBigrams(s) {
  const clean = String(s || '').replace(/\s+/g, '');
  const set = new Set();
  for (let i = 0; i < clean.length - 1; i++) set.add(clean.slice(i, i + 2));
  return set;
}

function bigramOverlap(a, b) {
  const A = charBigrams(a), B = charBigrams(b);
  if (!A.size || !B.size) return 0;
  let n = 0;
  for (const x of A) if (B.has(x)) n++;
  return n / Math.min(A.size, B.size);
}

function findSimilarCases(text, category) {
  const cases = window.CASES || [];
  if (!cases.length) return [];
  const scored = cases.map(c => {
    let score = 0;
    if ((c.behavior_tags || []).includes(category)) score += 3;
    score += bigramOverlap(text, c.summary) * 5;
    return { c, score };
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, 3).map(s => ({
    question_id: s.c.id,
    similarity: Math.min(0.95, 0.3 + s.score * 0.08),
    risk_level: s.c.risk_level,
    standard_code: s.c.standard_code,
    summary: s.c.summary,
  }));
}

function localPolish(text) {
  let t = String(text || '').trim().replace(/[。！!；;]+$/, '');
  const rules = [
    ['客户请我吃饭', '接受客户宴请'],
    ['客户请我', '接受客户邀请'],
    ['客户送我', '接受客户提供的'],
    ['客户给我一笔钱', '接受客户支付的一笔报酬'],
    ['客户给我奖金', '接受客户支付的奖金'],
    ['客户给我', '接受客户提供的'],
    ['给我一笔钱', '向我支付一笔报酬'],
    ['给我奖金', '向我支付奖金'],
    ['请客', '宴请招待'],
    ['吃饭', '宴请'],
    ['打高尔夫', '高尔夫活动'],
    ['报销', '费用报销'],
    ['送我', '向我提供'],
    ['带我', '安排我'],
    ['送我去', '安排我前往'],
    ['承担', '由对方承担'],
  ];
  for (const [from, to] of rules) t = t.split(from).join(to);
  if (t.startsWith('本人')) return t + '，特此申报。';
  return '本人' + t + '，特此申报。';
}

function offlineAnalyze(text) {
  const cls = offlineClassify(text);  const cat = cls.category;
  const codes = (CATEGORIES[cat] ? CATEGORIES[cat].standards : []);
  const standards = codes.map(c => {
    const [name, desc] = STANDARD_INFO[c] || [c, ''];
    return { code: c, name, description: desc };
  });
  const checklist = codes.map((c, i) => ({
    id: i + 1,
    text: (STANDARD_INFO[c] || [c, c])[1],
    required: true,
  }));
  const isHigh = ['gift_entertainment', 'personal_trade', 'extra_compensation', 'mnpi', 'misconduct'].includes(cat);
  const risk = isHigh ? 'high' : (cat === 'uncertain' ? 'low' : 'mid');
  return {
    risk_level: risk,
    risk_score: risk === 'high' ? 0.9 : risk === 'mid' ? 0.6 : 0.3,
    category: cat,
    confidence: cls.confidence,
    standards,
    checklist,
    action_advice: (risk === 'high' ? '该行为风险较高，请在接受任何利益前完成披露与审批。' : '请按清单履行披露与审慎义务。') + '；' + checklist.map(c => c.text).join('；') + '。',
    disclosure_draft: risk === 'low' ? '' : `致合规部门：\n本人就以下事项主动披露：${text}\n\n可能涉及准则：${codes.join('、')}\n\n特此披露，请审查。`,
    risk_reasoning: risk === 'high' ? '高风险：涉及需书面披露或事先同意的事项' : risk === 'mid' ? '中风险：需履行披露或审慎义务' : '低风险：常规执业行为',
    referenced_cases: findSimilarCases(text, cat),
    offline: true,
    processing_time_ms: 0,
  };
}
