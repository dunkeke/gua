import streamlit as st
import yfinance as yf
import pandas as pd
import random
import time
from datetime import datetime, timedelta

# --- 1. 页面配置与样式注入 ---
st.set_page_config(
    page_title="能源·周易量化",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 注入自定义 CSS 以实现“双风格”和字体
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* 全局样式调整 */
    .main {
        background-color: #f8fafc;
    }
    
    /* 风格类定义 */
    .tech-font {
        font-family: 'JetBrains Mono', monospace;
    }
    .trad-font {
        font-family: 'Noto Serif SC', serif;
    }
    .calligraphy {
        font-family: 'Ma Shan Zheng', cursive;
    }
    
    /* 卦象符号大字 */
    .hex-symbol {
        font-size: 80px;
        line-height: 1;
        color: #333;
    }
    
    /* 爻的样式 (红阳黑阴) */
    .yao-yang {
        background-color: #dc2626;
        height: 12px;
        border-radius: 4px;
        margin: 4px 0;
    }
    .yao-yin {
        display: flex;
        justify-content: space-between;
        height: 12px;
        margin: 4px 0;
    }
    .yao-yin-part {
        background-color: #1e293b;
        width: 42%;
        height: 100%;
        border-radius: 4px;
    }
    
    /* 动爻标记 */
    .moving-dot {
        color: #d97706;
        font-weight: bold;
        margin-left: 8px;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心数据字典 (Python版) ---
# 键：从初爻(下)到上爻(上)的序列 (0=阴, 1=阳)
# 修正了所有键值对应关系，并保留了丰富解读
HEXAGRAMS = {
    "1,1,1,1,1,1": {"name": "乾", "pinyin": "qián", "symbol": "䷀", "judgment": "元亨利贞。", "interp": "【大象】天行健，君子以自强不息。\n【量化】多头强势，动能充沛，如飞龙在天。\n【策略】顺势做多，但需警惕高位滞涨。\n【生活】运势极佳，适合大展宏图，忌骄傲。", "outlook": "bullish"},
    "0,0,0,0,0,0": {"name": "坤", "pinyin": "kūn", "symbol": "䷁", "judgment": "元亨，利牝马之贞。", "interp": "【大象】地势坤，君子以厚德载物。\n【量化】空头主导或底部盘整，波动率低。\n【策略】不宜追高，适合定投或空仓观望。\n【生活】包容忍耐，以静制动。", "outlook": "bearish"},
    "1,0,0,0,1,0": {"name": "屯", "pinyin": "zhūn", "symbol": "䷂", "judgment": "元亨利贞。", "interp": "【大象】云雷屯。\n【量化】筑底阶段，震荡剧烈，方向未明。\n【策略】建仓需谨慎，控制仓位。\n【生活】万事开头难，积蓄力量。", "outlook": "neutral"},
    "0,1,0,0,0,1": {"name": "蒙", "pinyin": "méng", "symbol": "䷃", "judgment": "亨。", "interp": "【大象】山下出泉，蒙。\n【量化】信息混沌，趋势不明，迷雾重重。\n【策略】多看少动，等待信号。\n【生活】局势不明朗，建议多咨询专家。", "outlook": "neutral"},
    "1,1,1,0,1,0": {"name": "需", "pinyin": "xū", "symbol": "䷄", "judgment": "有孚，光亨。", "interp": "【大象】云上于天，需。\n【量化】上涨趋势中的回调，需求在积蓄。\n【策略】逢低吸纳，持仓待涨。\n【生活】时机未到，耐心等待。", "outlook": "bullish"},
    "0,1,0,1,1,1": {"name": "讼", "pinyin": "sòng", "symbol": "䷅", "judgment": "有孚，窒惕。", "interp": "【大象】天与水违，讼。\n【量化】多空分歧巨大，成交量放大但滞涨。\n【策略】风险较高，建议减仓。\n【生活】易生口角，以和为贵。", "outlook": "neutral"},
    "0,1,0,0,0,0": {"name": "师", "pinyin": "shī", "symbol": "䷆", "judgment": "贞，丈人吉。", "interp": "【大象】地中有水，师。\n【量化】空头排列，趋势性下跌，力量集中。\n【策略】顺势做空，严守纪律。\n【生活】需要严明的纪律和领导。", "outlook": "bearish"},
    "0,0,0,0,1,0": {"name": "比", "pinyin": "bǐ", "symbol": "䷇", "judgment": "吉。", "interp": "【大象】地上有水，比。\n【量化】板块轮动良好，市场情绪和谐。\n【策略】跟随龙头，寻找补涨机会。\n【生活】人际关系和谐，有贵人相助。", "outlook": "neutral"},
    "1,1,1,0,1,1": {"name": "小畜", "pinyin": "xiǎo chù", "symbol": "䷈", "judgment": "亨。密云不雨。", "interp": "【大象】风行天上，小畜。\n【量化】上涨遇阻，窄幅震荡，蓄势待发。\n【策略】高抛低吸，短期盘整。\n【生活】积蓄力量，不可急于求成。", "outlook": "bullish"},
    "1,1,0,1,1,1": {"name": "履", "pinyin": "lǚ", "symbol": "䷉", "judgment": "履虎尾。", "interp": "【大象】上天下泽，履。\n【量化】高位震荡，风险积聚，如履薄冰。\n【策略】设置止损，步步为营。\n【生活】有惊无险，但须小心。", "outlook": "neutral"},
    "1,1,1,0,0,0": {"name": "泰", "pinyin": "tài", "symbol": "䷊", "judgment": "小往大来。", "interp": "【大象】天地交，泰。\n【量化】多头市场，量价齐升，极为顺畅。\n【策略】积极做多，享受泡沫。\n【生活】三阳开泰，非常吉利。", "outlook": "bullish"},
    "0,0,0,1,1,1": {"name": "否", "pinyin": "pǐ", "symbol": "䷋", "judgment": "否之匪人。", "interp": "【大象】天地不交，否。\n【量化】流动性枯竭，阴跌不止。\n【策略】清仓离场，现金为王。\n【生活】闭塞不通，宜退守。", "outlook": "bearish"},
    "1,0,1,1,1,1": {"name": "同人", "pinyin": "tóng rén", "symbol": "䷌", "judgment": "同人于野。", "interp": "【大象】天与火，同人。\n【量化】市场共识形成，普涨行情。\n【策略】重仓出击，跟随主流。\n【生活】志同道合，利于团队。", "outlook": "bullish"},
    "1,1,1,1,0,1": {"name": "大有", "pinyin": "dà yǒu", "symbol": "䷍", "judgment": "元亨。", "interp": "【大象】火在天上，大有。\n【量化】牛市主升浪，收获颇丰。\n【策略】持有核心资产，防止获利回吐。\n【生活】运势昌隆，忌满招损。", "outlook": "bullish"},
    "0,0,1,0,0,0": {"name": "谦", "pinyin": "qiān", "symbol": "䷎", "judgment": "君子有终。", "interp": "【大象】地中有山，谦。\n【量化】价值低估，底部夯实。\n【策略】逢低布局，长线持有。\n【生活】谦虚受益，低调行事。", "outlook": "neutral"},
    "0,0,0,1,0,0": {"name": "豫", "pinyin": "yù", "symbol": "䷏", "judgment": "利建侯行师。", "interp": "【大象】雷出地奋，豫。\n【量化】突破盘整，放量上行。\n【策略】积极参与，顺势加仓。\n【生活】安乐愉悦，利于行动。", "outlook": "neutral"},
    "1,0,0,1,1,0": {"name": "随", "pinyin": "suí", "symbol": "䷐", "judgment": "元亨利贞。", "interp": "【大象】泽中有雷，随。\n【量化】趋势跟随，无明显主见。\n【策略】右侧交易，不摸顶底。\n【生活】随遇而安，随时变通。", "outlook": "neutral"},
    "0,1,1,0,0,1": {"name": "蛊", "pinyin": "gǔ", "symbol": "䷑", "judgment": "元亨。", "interp": "【大象】山下有风，蛊。\n【量化】利空出尽，估值修复。\n【策略】关注困境反转股。\n【生活】整顿积弊，改革良机。", "outlook": "neutral"},
    "1,1,0,0,0,0": {"name": "临", "pinyin": "lín", "symbol": "䷒", "judgment": "元亨利贞。", "interp": "【大象】泽上有地，临。\n【量化】多头逼空，阳线连发。\n【策略】果断进场，持有待涨。\n【生活】居高临下，运势增长。", "outlook": "bullish"},
    "0,0,0,0,1,1": {"name": "观", "pinyin": "guān", "symbol": "䷓", "judgment": "盥而不荐。", "interp": "【大象】风行地上，观。\n【量化】高位滞涨，缩量整理。\n【策略】多看少动，观察盘面。\n【生活】冷静观察，静观其变。", "outlook": "neutral"},
    "1,0,0,1,0,1": {"name": "噬嗑", "pinyin": "shì hé", "symbol": "䷔", "judgment": "利用狱。", "interp": "【大象】雷电，噬嗑。\n【量化】关键阻力位，多空激烈博弈。\n【策略】需要放量突破，否则回落。\n【生活】遇到阻碍，需果断解决。", "outlook": "neutral"},
    "1,0,1,0,0,1": {"name": "贲", "pinyin": "bì", "symbol": "䷕", "judgment": "小利有攸往。", "interp": "【大象】山下有火，贲。\n【量化】题材炒作，概念火热但无支撑。\n【策略】短线快进快出。\n【生活】表面繁荣，需看清本质。", "outlook": "neutral"},
    "0,0,0,0,0,1": {"name": "剥", "pinyin": "bō", "symbol": "䷖", "judgment": "不利有攸往。", "interp": "【大象】山附于地，剥。\n【量化】高位崩塌，获利盘出逃。\n【策略】止损离场，不可抄底。\n【生活】基础不稳，防范损失。", "outlook": "bearish"},
    "1,0,0,0,0,0": {"name": "复", "pinyin": "fù", "symbol": "䷗", "judgment": "亨。", "interp": "【大象】雷在地中，复。\n【量化】超跌反弹，V型反转。\n【策略】左侧建仓，长线布局。\n【生活】一阳来复，否极泰来。", "outlook": "bullish"},
    "1,0,0,1,1,1": {"name": "无妄", "pinyin": "wú wàng", "symbol": "䷘", "judgment": "元亨利贞。", "interp": "【大象】天下雷行，物与无妄。\n【量化】回归价值，去除泡沫。\n【策略】不追题材，关注基本面。\n【生活】真实无妄，不可投机。", "outlook": "neutral"},
    "1,1,1,0,0,1": {"name": "大畜", "pinyin": "dà chù", "symbol": "䷙", "judgment": "利贞。", "interp": "【大象】天在山中，大畜。\n【量化】横盘吸筹，主力建仓。\n【策略】耐心持股，等待主升浪。\n【生活】积蓄巨大，厚积薄发。", "outlook": "neutral"},
    "1,0,0,0,0,1": {"name": "颐", "pinyin": "yí", "symbol": "䷚", "judgment": "贞吉。", "interp": "【大象】山下有雷，颐。\n【量化】缩量整固，上下两难。\n【策略】高抛低吸，或休息观望。\n【生活】颐养身心，此时宜静。", "outlook": "neutral"},
    "0,1,1,1,1,0": {"name": "大过", "pinyin": "dà guò", "symbol": "䷛", "judgment": "栋桡。", "interp": "【大象】泽灭木，大过。\n【量化】严重超买，乖离率过大。\n【策略】风险极大，建议清仓。\n【生活】压力过大，需释放压力。", "outlook": "neutral"},
    "0,1,0,0,1,0": {"name": "坎", "pinyin": "kǎn", "symbol": "䷜", "judgment": "习坎。", "interp": "【大象】水流而不盈，习坎。\n【量化】破位下行，深不见底。\n【策略】现金为王，切勿接飞刀。\n【生活】重重险陷，务必保守。", "outlook": "bearish"},
    "1,0,1,1,0,1": {"name": "离", "pinyin": "lí", "symbol": "䷝", "judgment": "利贞。", "interp": "【大象】明两作，离。\n【量化】加速赶顶，情绪狂热。\n【策略】短线博弈，快进快出。\n【生活】如日中天，但来去匆匆。", "outlook": "bullish"},
    "0,0,1,1,1,0": {"name": "咸", "pinyin": "xián", "symbol": "䷞", "judgment": "亨。", "interp": "【大象】山上有泽，咸。\n【量化】消息刺激，脉冲式行情。\n【策略】关注消息面，灵活操作。\n【生活】感应沟通，利于社交。", "outlook": "neutral"},
    "0,1,1,1,0,0": {"name": "恒", "pinyin": "héng", "symbol": "䷟", "judgment": "亨。", "interp": "【大象】雷风，恒。\n【量化】趋势稳定，慢牛或阴跌。\n【策略】顺着当前趋势操作。\n【生活】恒久持续，保持现状。", "outlook": "neutral"},
    "0,0,1,1,1,1": {"name": "遁", "pinyin": "dùn", "symbol": "䷠", "judgment": "亨，小利贞。", "interp": "【大象】天下有山，遁。\n【量化】诱多出货，重心下移。\n【策略】逢反弹减仓，避险为主。\n【生活】退避隐遁，不宜争锋。", "outlook": "bearish"},
    "1,1,1,1,0,0": {"name": "大壮", "pinyin": "dà zhuàng", "symbol": "䷡", "judgment": "利贞。", "interp": "【大象】雷在天上，大壮。\n【量化】放量突破，强势上攻。\n【策略】重仓持有，防冲高回落。\n【生活】声势壮大，适合进攻。", "outlook": "bullish"},
    "0,0,0,1,0,1": {"name": "晋", "pinyin": "jìn", "symbol": "䷢", "judgment": "康侯用锡马。", "interp": "【大象】明出地上，晋。\n【量化】稳步推升，进二退一。\n【策略】积极进取，持股待涨。\n【生活】旭日东升，步步高升。", "outlook": "bullish"},
    "1,0,1,0,0,0": {"name": "明夷", "pinyin": "míng yí", "symbol": "䷣", "judgment": "利艰贞。", "interp": "【大象】明入地中，明夷。\n【量化】黑天鹅事件，大幅跳水。\n【策略】空仓避险，不要抱有幻想。\n【生活】前景黯淡，需忍耐。", "outlook": "bearish"},
    "1,0,1,0,1,1": {"name": "家人", "pinyin": "jiā rén", "symbol": "䷤", "judgment": "利女贞。", "interp": "【大象】风自火出，家人。\n【量化】防御性板块走强，结构性行情。\n【策略】关注消费、公用事业。\n【生活】相亲相爱，基础稳固。", "outlook": "neutral"},
    "1,1,0,1,0,1": {"name": "睽", "pinyin": "kuí", "symbol": "䷥", "judgment": "小事吉。", "interp": "【大象】上火下泽，睽。\n【量化】板块分化，赚钱效应差。\n【策略】多空分歧大，不宜重仓。\n【生活】意见不合，小事可为。", "outlook": "neutral"},
    "0,0,1,0,1,0": {"name": "蹇", "pinyin": "jiǎn", "symbol": "䷦", "judgment": "利西南。", "interp": "【大象】山上有水，蹇。\n【量化】上有压力下有支撑，僵持不下。\n【策略】不宜硬闯，等待变盘。\n【生活】前有险阻，最好求援。", "outlook": "bearish"},
    "0,1,0,1,0,0": {"name": "解", "pinyin": "jiě", "symbol": "䷧", "judgment": "利西南。", "interp": "【大象】雷雨作，解。\n【量化】利空消化，止跌回升。\n【策略】布局超跌反弹。\n【生活】冰消瓦解，困难消除。", "outlook": "bullish"},
    "1,1,0,0,0,1": {"name": "损", "pinyin": "sǔn", "symbol": "䷨", "judgment": "有孚，元吉。", "interp": "【大象】山下有泽，损。\n【量化】缩量阴跌，市值缩水。\n【策略】止损换股，先失后得。\n【生活】减损获益，需投入成本。", "outlook": "bearish"},
    "1,0,0,0,1,1": {"name": "益", "pinyin": "yì", "symbol": "䷩", "judgment": "利有攸往。", "interp": "【大象】风雷，益。\n【量化】政策利好，资金流入。\n【策略】积极参与，大展拳脚。\n【生活】损上益下，环境宽松。", "outlook": "bullish"},
    "1,1,1,1,1,0": {"name": "夬", "pinyin": "guài", "symbol": "䷪", "judgment": "扬于王庭。", "interp": "【大象】泽上于天，夬。\n【量化】冲关时刻，多头总攻。\n【策略】必须果断跟进，切勿犹豫。\n【生活】决断突破，必须果断。", "outlook": "bullish"},
    "0,1,1,1,1,1": {"name": "姤", "pinyin": "gòu", "symbol": "䷫", "judgment": "女壮。", "interp": "【大象】天下有风，姤。\n【量化】冲高回落，头部迹象。\n【策略】虽然上涨但需减仓。\n【生活】不期而遇，防微杜渐。", "outlook": "bearish"},
    "0,0,0,0,1,1": {"name": "萃", "pinyin": "cuì", "symbol": "䷬", "judgment": "亨。", "interp": "【大象】泽上于地，萃。\n【量化】资金抱团，龙头效应。\n【策略】加入核心资产，享受泡沫。\n【生活】聚集荟萃，人气高涨。", "outlook": "bullish"},
    "0,1,1,0,0,0": {"name": "升", "pinyin": "shēng", "symbol": "䷭", "judgment": "元亨。", "interp": "【大象】地中生木，升。\n【量化】稳步上涨，均线多头。\n【策略】坚定持仓，不轻易下车。\n【生活】积小成大，步步高升。", "outlook": "bullish"},
    "0,1,0,1,1,0": {"name": "困", "pinyin": "kùn", "symbol": "䷮", "judgment": "亨，贞。", "interp": "【大象】泽无水，困。\n【量化】成交低迷，无人问津。\n【策略】不要轻易抄底，效率极低。\n【生活】困顿穷乏，需坚守。", "outlook": "neutral"},
    "0,1,1,0,1,0": {"name": "井", "pinyin": "jǐng", "symbol": "䷯", "judgment": "改邑不改井。", "interp": "【大象】木上有水，井。\n【量化】织布机行情，原地踏步。\n【策略】适合高股息策略，做定投。\n【生活】价值仍在，适合定投。", "outlook": "neutral"},
    "1,0,1,1,1,0": {"name": "革", "pinyin": "gé", "symbol": "䷰", "judgment": "元亨利贞。", "interp": "【大象】泽中有火，革。\n【量化】风格切换，新老交替。\n【策略】调仓换股，跟随新热点。\n【生活】除旧布新，面临变革。", "outlook": "neutral"},
    "0,1,1,1,0,1": {"name": "鼎", "pinyin": "dǐng", "symbol": "䷱", "judgment": "元吉。", "interp": "【大象】木上有火，鼎。\n【量化】新周期确立，格局稳定。\n【策略】布局蓝筹，长线看好。\n【生活】稳重图新，新的繁荣。", "outlook": "bullish"},
    "1,0,0,1,0,0": {"name": "震", "pinyin": "zhèn", "symbol": "䷲", "judgment": "亨。", "interp": "【大象】洊雷，震。\n【量化】消息面利空，盘中急跌。\n【策略】或是黄金坑，注意情绪修复。\n【生活】突发事件，有惊无险。", "outlook": "neutral"},
    "0,0,1,0,0,1": {"name": "艮", "pinyin": "gèn", "symbol": "䷳", "judgment": "艮其背。", "interp": "【大象】兼山，艮。\n【量化】上涨乏力，多重顶。\n【策略】止盈离场，休息观望。\n【生活】动静适时，止步不前。", "outlook": "neutral"},
    "0,0,1,0,1,1": {"name": "渐", "pinyin": "jiàn", "symbol": "䷴", "judgment": "女归吉。", "interp": "【大象】山上有木，渐。\n【量化】碎步上行，慢牛行情。\n【策略】保持耐心，不要被震荡洗出局。\n【生活】循序渐进，终成大器。", "outlook": "neutral"},
    "1,1,0,1,0,0": {"name": "归妹", "pinyin": "guī mèi", "symbol": "䷵", "judgment": "征凶。", "interp": "【大象】泽上有雷，归妹。\n【量化】走势怪异，诱多陷阱。\n【策略】如果不看好，坚决不参与。\n【生活】错位之象，易失误。", "outlook": "neutral"},
    "1,0,1,1,0,0": {"name": "丰", "pinyin": "fēng", "symbol": "䷶", "judgment": "亨。", "interp": "【大象】雷电皆至，丰。\n【量化】成交天量，情绪亢奋。\n【策略】逐步止盈，落袋为安。\n【生活】达到顶峰，盛极必衰。", "outlook": "bullish"},
    "0,0,1,1,0,1": {"name": "旅", "pinyin": "lǚ", "symbol": "䷷", "judgment": "小亨。", "interp": "【大象】山上有火，旅。\n【量化】游资主导，一日游行情。\n【策略】打板或超短线，快进快出。\n【生活】漂泊不定，不宜久留。", "outlook": "neutral"},
    "0,1,1,0,1,1": {"name": "巽", "pinyin": "xùn", "symbol": "䷸", "judgment": "小亨。", "interp": "【大象】随风，巽。\n【量化】市场形成一致预期，无脑跟随。\n【策略】不要逆势操作，风往哪吹往哪倒。\n【生活】顺风而行，顺从时势。", "outlook": "neutral"},
    "1,1,0,1,1,0": {"name": "兑", "pinyin": "duì", "symbol": "䷹", "judgment": "亨。", "interp": "【大象】丽泽，兑。\n【量化】交易活跃，换手率高。\n【策略】积极参与热点，但防高位被套。\n【生活】喜悦沟通，防口舌是非。", "outlook": "bullish"},
    "0,1,0,0,1,1": {"name": "涣", "pinyin": "huàn", "symbol": "䷺", "judgment": "亨。", "interp": "【大象】风行水上，涣。\n【量化】筹码松动，主力撤退。\n【策略】该跑就跑，不要留恋。\n【生活】离散之象，人心涣散。", "outlook": "neutral"},
    "1,1,0,0,1,0": {"name": "节", "pinyin": "jié", "symbol": "䷻", "judgment": "亨。", "interp": "【大象】泽上有水，节。\n【量化】箱体震荡，上有顶下有底。\n【策略】高抛低吸，懂得止盈。\n【生活】节制适度，量力而行。", "outlook": "neutral"},
    "1,1,0,0,1,1": {"name": "中孚", "pinyin": "zhōng fú", "symbol": "䷼", "judgment": "豚鱼吉。", "interp": "【大象】泽上有风，中孚。\n【量化】技术指标有效，走势规范。\n【策略】按技术图形操作，相信信号。\n【生活】诚信感通，脚下有路。", "outlook": "neutral"},
    "0,0,1,1,0,0": {"name": "小过", "pinyin": "xiǎo guò", "symbol": "䷽", "judgment": "亨，利贞。", "interp": "【大象】山上有雷，小过。\n【量化】小幅波动，大趋势不明。\n【策略】小仓位试错，不要重仓博弈。\n【生活】小有过度，宜守。", "outlook": "neutral"},
    "1,0,1,0,1,0": {"name": "既济", "pinyin": "jì jì", "symbol": "䷾", "judgment": "亨，小利贞。", "interp": "【大象】水在火上，既济。\n【量化】完美收官，利好兑现。\n【策略】获利了结，见好就收。\n【生活】大功告成，防盛极而衰。", "outlook": "neutral"},
    "0,1,0,1,0,1": {"name": "未济", "pinyin": "wèi jì", "symbol": "䷿", "judgment": "亨。", "interp": "【大象】火在水上，未济。\n【量化】行情未完，充满变数。\n【策略】寻找新的增长点，在此博弈。\n【生活】未完成，充满希望。", "outlook": "neutral"}
};

// --- 3. 工具函数 ---
def calculate_hexagram(df):
    """
    生成本卦和之卦
    逻辑:
    1. 数据按时间降序 (df[0]是最新, df[5]是6天前)
    2. 最新数据 = 初爻 (Bottom), 最旧数据 = 上爻 (Top)
    3. 波动率 > 1.5倍平均值 = 动爻 (老阴/老阳)
    """
    closes = df['Close'].values
    opens = df['Open'].values
    dates = df.index.strftime('%Y-%m-%d').tolist()
    
    # 计算涨跌幅绝对值
    changes = abs((closes - opens) / opens)
    avg_change = changes.mean()
    volatility_threshold = avg_change * 1.5
    
    ben_lines = [] # 0 or 1
    zhi_lines = [] # 0 or 1
    details = []

    # 遍历顺序：从 0 (最新/初爻) 到 5 (最旧/上爻)
    # 修正：K线数据切片通常是 [Oldest ... Newest]
    # 所以 df.iloc[-1] 是最新 (初爻), df.iloc[-6] 是最旧 (上爻)
    # 我们需要取最后6行
    
    subset = df.tail(6).iloc[::-1] # 反转，变成 [最新 ... 最旧]
    
    # 此时 subset.iloc[0] 是最新 (初爻)
    
    for i in range(6):
        row = subset.iloc[i]
        is_up = row['Close'] >= row['Open']
        change_pct = abs((row['Close'] - row['Open']) / row['Open'])
        
        # 判断阴阳和动静
        # 阳: 7(静), 9(动)
        # 阴: 8(静), 6(动)
        
        is_moving = change_pct > volatility_threshold
        
        if is_up:
            line_val = 9 if is_moving else 7
        else:
            line_val = 6 if is_moving else 8
            
        # 构建本卦和之卦
        # 7 -> 本1, 之1
        # 9 -> 本1, 之0 (变)
        # 8 -> 本0, 之0
        # 6 -> 本0, 之1 (变)
        
        ben_val = 1 if line_val in [7, 9] else 0
        zhi_val = 0 if line_val == 9 else (1 if line_val == 6 else ben_val)
        
        ben_lines.append(str(ben_val))
        zhi_lines.append(str(zhi_val))
        
        details.append({
            "date": row.name.strftime('%Y-%m-%d'),
            "close": row['Close'],
            "change": (row['Close'] - row['Open']) / row['Open'],
            "type": line_val,
            "position": i # 0=初爻
        })
        
    return ",".join(ben_lines), ",".join(zhi_lines), details

# --- 4. 界面布局 ---

# 侧边栏/顶部设置 (Tech Mode)
with st.container():
    # 使用自定义 CSS 切换类
    st.markdown('<div class="main-header"></div>', unsafe_allow_html=True)

# TABS
tab_market, tab_daily = st.tabs(["📈 市场量化 (Tech)", "🎲 趣味问卜 (国潮)"])

# --- MARKET TAB ---
with tab_market:
    st.markdown('<div class="tech-font">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        symbol = st.selectbox("选择品种 (Asset)", 
                     ["BZ=F", "NG=F", "TTF=F", "RB=F"], 
                     format_func=lambda x: {
                         "BZ=F": "🛢️ Brent Crude", 
                         "NG=F": "🔥 Natural Gas",
                         "TTF=F": "🇪🇺 Dutch TTF", 
                         "RB=F": "⛽ RBOB Gasoline"
                     }[x])
    with col2:
        date_val = st.date_input("基准日期 (Date)", datetime.now())
        
    if st.button("🚀 启动量化模型 (RUN MODEL)", type="primary"):
        with st.spinner("Fetching Exchange Data..."):
            try:
                # Fetch Data
                end_date = pd.to_datetime(date_val)
                start_date = end_date - timedelta(days=40) # 多取一些以防假期
                
                df = yf.download(symbol, start=start_date, end=end_date + timedelta(days=1), progress=False)
                
                if len(df) < 6:
                    st.error("数据不足，无法生成卦象 (Need at least 6 trading days)")
                else:
                    # Calc Hexagram
                    ben_key, zhi_key, line_details = calculate_hexagram(df)
                    
                    ben_info = HEXAGRAMS.get(ben_key)
                    zhi_info = HEXAGRAMS.get(zhi_key)
                    
                    if not ben_info:
                        st.error(f"System Error: Invalid Hexagram Key {ben_key}")
                    else:
                        # Display Results
                        st.markdown("---")
                        
                        # 1. Hexagram Cards
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            st.markdown(f"""
                            <div style="background:#e2e8f0; padding:20px; border-radius:10px; text-align:center;">
                                <div style="color:#64748b; font-weight:bold; font-size:12px;">CURRENT PHASE (本卦)</div>
                                <div class="hex-symbol">{ben_info['symbol']}</div>
                                <div style="font-size:24px; font-weight:bold;">{ben_info['name']}</div>
                                <div style="font-size:14px; font-style:italic; color:#475569;">{ben_info['judgment']}</div>
                                <hr style="margin:10px 0;">
                                <div style="text-align:left; font-size:13px; line-height:1.6;">{ben_info['interp']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with c2:
                            opacity = "1" if ben_key != zhi_key else "0.5"
                            title_suffix = "(变卦)" if ben_key != zhi_key else "(无变动)"
                            st.markdown(f"""
                            <div style="background:#f1f5f9; padding:20px; border-radius:10px; text-align:center; opacity:{opacity};">
                                <div style="color:#64748b; font-weight:bold; font-size:12px;">PROJECTION (之卦)</div>
                                <div class="hex-symbol">{zhi_info['symbol']}</div>
                                <div style="font-size:24px; font-weight:bold;">{zhi_info['name']} {title_suffix}</div>
                                <div style="font-size:14px; font-style:italic; color:#475569;">{zhi_info['judgment']}</div>
                                <hr style="margin:10px 0;">
                                <div style="text-align:left; font-size:13px; line-height:1.6;">{zhi_info['interp']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # 2. K-Line Table
                        st.subheader("📊 K-Line Sequence")
                        
                        # Process details for dataframe
                        table_data = []
                        pos_map = ["初爻 (Bottom)", "二爻", "三爻", "四爻", "五爻", "上爻 (Top)"]
                        
                        for d in line_details:
                            type_str = "阳 (7)"
                            if d['type'] == 8: type_str = "阴 (8)"
                            if d['type'] == 9: type_str = "老阳 (9) 🔴"
                            if d['type'] == 6: type_str = "老阴 (6) 🔵"
                            
                            table_data.append({
                                "Date": d['date'],
                                "Position": pos_map[d['position']],
                                "Close": f"{d['close']:.2f}",
                                "Chg%": f"{d['change']*100:.2f}%",
                                "Type": type_str
                            })
                            
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

            except Exception as e:
                st.error(f"Error fetching data: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)

# --- DAILY TAB ---
with tab_daily:
    st.markdown('<div class="trad-font">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; padding: 40px 0;">
        <h1 class="calligraphy" style="font-size: 48px; color: #b91c1c;">诚心问卜</h1>
        <p style="color: #888;">默念心中之事，点击下方按钮起卦</p>
    </div>
    """, unsafe_allow_html=True)
    
    question = st.text_input("", placeholder="在此输入您的问题...", key="q_input")
    
    if st.button("🎲 掷出六爻 (SHAKE)", type="secondary", use_container_width=True):
        if not question:
            st.warning("请先输入问题")
        else:
            with st.spinner("正在以此诚心，沟通天地..."):
                time.sleep(2) # Simulate shaking
                
                # Generate 6 lines
                # Logic: 3 coins. Head=3, Tail=2.
                # Sums: 6(Old Yin), 7(Young Yang), 8(Young Yin), 9(Old Yang)
                # Probabilities: 6(1/8), 7(3/8), 8(3/8), 9(1/8)
                
                lines = []
                for _ in range(6):
                    c1 = 3 if random.random() > 0.5 else 2
                    c2 = 3 if random.random() > 0.5 else 2
                    c3 = 3 if random.random() > 0.5 else 2
                    lines.append(c1 + c2 + c3)
                
                # Build Keys (Bottom -> Top)
                ben_res = []
                zhi_res = []
                
                for val in lines:
                    if val in [7, 9]: # Yang
                        ben_res.append("1")
                        zhi_res.append("0" if val == 9 else "1")
                    else: # Yin
                        ben_res.append("0")
                        zhi_res.append("1" if val == 6 else "0")
                
                d_ben_key = ",".join(ben_res)
                d_zhi_key = ",".join(zhi_res)
                
                d_ben = HEXAGRAMS[d_ben_key]
                d_zhi = HEXAGRAMS[d_zhi_key]
                
                # Display Daily Result
                st.markdown(f"""
                <div style="background-color:#fffbf0; border:2px solid #b91c1c; border-radius:15px; padding:30px; margin-top:20px;">
                    <div style="text-align:center; margin-bottom:20px; color:#b91c1c; font-weight:bold;">问：{question}</div>
                    
                    <div style="display:flex; justify-content:space-around;">
                        <div style="text-align:center;">
                            <div style="font-size:14px; color:#888;">本卦 (现状)</div>
                            <div class="hex-symbol" style="color:#b91c1c;">{d_ben['symbol']}</div>
                            <div class="calligraphy" style="font-size:36px;">{d_ben['name']}</div>
                            <div style="font-size:14px; margin-top:10px;">{d_ben['judgment']}</div>
                        </div>
                        
                        <div style="text-align:center; opacity: {1.0 if d_ben_key != d_zhi_key else 0.3};">
                            <div style="font-size:14px; color:#888;">之卦 (变数)</div>
                            <div class="hex-symbol" style="color:#888;">{d_zhi['symbol']}</div>
                            <div class="calligraphy" style="font-size:36px;">{d_zhi['name']}</div>
                            <div style="font-size:14px; margin-top:10px;">{d_zhi['judgment']}</div>
                        </div>
                    </div>
                    
                    <hr style="border-color:#e5e7eb; margin:20px 0;">
                    
                    <div style="background:rgba(255,255,255,0.5); padding:15px; border-radius:8px;">
                        <p style="font-weight:bold; color:#b91c1c;">💡 锦囊妙计：</p>
                        <p style="line-height:1.8;">{d_ben['interp']}</p>
                        {f'<p style="margin-top:10px; color:#d97706;">⚡ <strong>变爻启示：</strong>局势正在向 {d_zhi["name"]} 转变，请参考之卦建议。</p>' if d_ben_key != d_zhi_key else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)