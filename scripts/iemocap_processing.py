import os, csv, re
from datetime import datetime

# 新文件名（加了 full_emotion）
output_csv = "./reprocessed_dataset/pingjie_rawdataset/iemocap_F_all_sessions_full_emotion.csv"


header = [
    'Sr No.', 'Method', 'Session', 'Turn', 'Speaker', 'Emotion', 'Vad',
    'N_Annotators', 'Agreement', 'Utterance', 'Dialogue_ID', 'Utterance_ID'
]

rows, sr_no = [], 0

transcription_re = re.compile(
    r'^(\S+)\s*\[\s*(\d+\.\d+)\s*-\s*(\d+\.\d+)\s*\]:\s*(.*)$'
)
evaluation_re = re.compile(
    r'\[(.*?)\]\s+(\S+)\s+(\w+)\s+\[(.*?)\]'
)

# 情绪缩写 → 全称映射（直接用于最终输出）
reverse_emotion_map = {
    'ang': 'anger',
    'fru': 'frustration',
    'neu': 'neutral',
    'hap': 'happiness',
    'sad': 'sadness',
    'exc': 'excited',
    'fea': 'fear',
    'sur': 'surprise',
    'dis': 'disgust',
    'xxx': 'unknown',    # 或者 'ambiguous'，代表无法标注的情绪
    'oth': 'other'       # 如果你的数据中存在此缩写
}


# 原始标签 → 缩写（只用于解析 annotator 的标签）
emotion_map = {
    'anger': 'ang',
    'frustration': 'fru',
    'neutral': 'neu',
    'happiness': 'hap',
    'sadness': 'sad',
    'excited': 'exc',
    'fear': 'fea',
    'surprise': 'sur',
    'disgust': 'dis',
    'other': 'oth',         # 区分于 xxx
    'unknown': 'xxx'        # 表示无法标注或模糊的情绪
}


base_root = os.path.join(os.getcwd(), 'IEMOCAP_full_release')

def parse_emo_file(emo_path):
    segments = {}
    with open(emo_path, encoding='utf-8') as f:
        txt = f.read()
    blocks = txt.split('\n\n')
    for block in blocks:
        m = evaluation_re.search(block)
        if not m:
            continue
        _, turn_name, emo, vad = m.groups()
        if 'XX' in turn_name:
            continue
        vad = '[' + vad.strip() + ']'

        n_ann, agree = 0, 0
        for line in block.splitlines():
            if line.startswith('C-'):
                n_ann += 1
                parts = line.split(';')
                if len(parts) >= 2:
                    annot_emotion = parts[0].split(':')[1].strip().lower()
                    annot_short = emotion_map.get(annot_emotion, annot_emotion)
                    if annot_short == emo.lower():
                        agree += 1

        segments[turn_name] = (emo, vad, n_ann, agree)
    return segments


global_dialogue_id = 0

for session in ['Session1', 'Session2', 'Session3', 'Session4', 'Session5']:
    s_num = session[-1]
    base = os.path.join(base_root, session, 'dialog')
    trans_dir = os.path.join(base, 'transcriptions')
    emo_dir = os.path.join(base, 'EmoEvaluation')

    # ✅ 只处理 Female 音轨
    files = [
        f for f in os.listdir(trans_dir)
        if f.endswith('.txt') and re.match(r'^Ses\d{2}F_', f)
    ]

    for fname in sorted(files):
        turn = fname[:-4]
        method = 'script' if 'script' in fname else 'impro'

        trans_path = os.path.join(trans_dir, fname)
        emo_path = os.path.join(emo_dir, fname)

        if not os.path.exists(trans_path) or not os.path.exists(emo_path):
            continue

        emo_segments = parse_emo_file(emo_path)

        with open(trans_path, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        utt_id = 0

        for line in lines:
            line = line.strip()
            m = transcription_re.match(line)

            if m:  # 标准句子
                utt_name, start, end, utt = m.groups()
                if 'XX' in utt_name:
                    continue
                speaker = 'F' if '_F' in utt_name else 'M'
                if utt_name in emo_segments:
                    emotion, vad, n_ann, agree = emo_segments[utt_name]
                else:
                    emotion, vad, n_ann, agree = 'None', 'None', 0, 0

            else:  # 非标准句子
                if line.startswith('F:') or line.startswith('F :'):
                    speaker, utt = 'F', line.split(':', 1)[1].strip()
                elif line.startswith('M:') or line.startswith('M :'):
                    speaker, utt = 'M', line.split(':', 1)[1].strip()
                else:
                    continue
                utt_name, emotion, vad, n_ann, agree = 'None', 'None', 'None', 0, 0

            # ✅ 替换 emotion 为全称（例如 neu → neutral）
            emotion_full = reverse_emotion_map.get(emotion.strip().lower(), emotion)

            rows.append([
                sr_no, method, s_num, turn, speaker, emotion_full, vad,
                n_ann, agree, utt, global_dialogue_id, utt_id
            ])
            sr_no += 1
            utt_id += 1

        global_dialogue_id += 1

print(f"✅ 提取完成，共写入 {len(rows)} 条记录（仅 Female + 全称情绪标签）")

with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"🎉 输出文件：{output_csv}")

