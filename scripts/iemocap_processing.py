import os
import re
import csv
import sys
import pandas as pd
from collections import defaultdict


class Logger(object):
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


def build_iemocap_f_all_sessions(
    base_root="IEMOCAP_full_release",
    output_csv="iemocap_F_all_sessions_full_emotion.csv"
):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    header = [
        "Sr No.", "Method", "Session", "Turn", "Speaker", "Emotion", "Vad",
        "N_Annotators", "Agreement", "Utterance", "Dialogue_ID", "Utterance_ID"
    ]

    transcription_re = re.compile(r"^(\S+)\s*\[\s*(\d+\.\d+)\s*-\s*(\d+\.\d+)\s*\]:\s*(.*)$")
    evaluation_re = re.compile(r"\[(.*?)\]\s+(\S+)\s+(\w+)\s+\[(.*?)\]")

    reverse_emotion_map = {
        "ang": "anger",
        "fru": "frustration",
        "neu": "neutral",
        "hap": "happiness",
        "sad": "sadness",
        "exc": "excited",
        "fea": "fear",
        "sur": "surprise",
        "dis": "disgust",
        "xxx": "unknown",
        "oth": "other",
    }

    emotion_map = {
        "anger": "ang",
        "frustration": "fru",
        "neutral": "neu",
        "happiness": "hap",
        "sadness": "sad",
        "excited": "exc",
        "fear": "fea",
        "surprise": "sur",
        "disgust": "dis",
        "other": "oth",
        "unknown": "xxx",
    }

    def parse_emo_file(emo_path):
        segments = {}
        with open(emo_path, encoding="utf-8") as f:
            txt = f.read()
        blocks = txt.split("\n\n")

        for block in blocks:
            m = evaluation_re.search(block)
            if not m:
                continue
            _, turn_name, emo, vad = m.groups()
            if "XX" in turn_name:
                continue

            vad = "[" + vad.strip() + "]"
            n_ann, agree = 0, 0

            for line in block.splitlines():
                if line.startswith("C-"):
                    n_ann += 1
                    parts = line.split(";")
                    if len(parts) >= 2:
                        annot_emotion = parts[0].split(":")[1].strip().lower()
                        annot_short = emotion_map.get(annot_emotion, annot_emotion)
                        if annot_short == emo.lower():
                            agree += 1

            segments[turn_name] = (emo, vad, n_ann, agree)
        return segments

    rows, sr_no = [], 0
    global_dialogue_id = 0
    abs_base_root = os.path.join(os.getcwd(), base_root)

    for session in ["Session1", "Session2", "Session3", "Session4", "Session5"]:
        s_num = session[-1]
        base = os.path.join(abs_base_root, session, "dialog")
        trans_dir = os.path.join(base, "transcriptions")
        emo_dir = os.path.join(base, "EmoEvaluation")

        if not os.path.isdir(trans_dir) or not os.path.isdir(emo_dir):
            print(f"[WARN] Missing dir: {trans_dir} or {emo_dir}")
            continue

        files = [
            f for f in os.listdir(trans_dir)
            if f.endswith(".txt") and re.match(r"^Ses\d{2}F_", f)
        ]

        for fname in sorted(files):
            turn = fname[:-4]
            method = "script" if "script" in fname else "impro"

            trans_path = os.path.join(trans_dir, fname)
            emo_path = os.path.join(emo_dir, fname)
            if not os.path.exists(trans_path) or not os.path.exists(emo_path):
                continue

            emo_segments = parse_emo_file(emo_path)

            with open(trans_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            utt_id = 0
            for line in lines:
                line = line.strip()
                m = transcription_re.match(line)

                if m:
                    utt_name, _start, _end, utt = m.groups()
                    if "XX" in utt_name:
                        continue

                    speaker = "F" if "_F" in utt_name else "M"
                    if utt_name in emo_segments:
                        emotion, vad, n_ann, agree = emo_segments[utt_name]
                    else:
                        emotion, vad, n_ann, agree = "None", "None", 0, 0
                else:
                    if line.startswith("F:") or line.startswith("F :"):
                        speaker, utt = "F", line.split(":", 1)[1].strip()
                    elif line.startswith("M:") or line.startswith("M :"):
                        speaker, utt = "M", line.split(":", 1)[1].strip()
                    else:
                        continue
                    emotion, vad, n_ann, agree = "None", "None", 0, 0

                emotion_full = reverse_emotion_map.get(str(emotion).strip().lower(), emotion)

                rows.append([
                    sr_no, method, s_num, turn, speaker, emotion_full, vad,
                    n_ann, agree, utt, global_dialogue_id, utt_id
                ])
                sr_no += 1
                utt_id += 1

            global_dialogue_id += 1

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"[OK] IEMOCAP merged rows: {len(rows)}")
    print(f"[OK] Saved: {output_csv}")
    return output_csv


def filter_dialogues_by_emotion_shift(
    input_path,
    output_dir="./Processed_dataset_all_filter_rules_output",
    require_min_emotions=4,
    require_min_total_shifts=2
):
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_path):
        print(f"[ERR] File not found: {input_path}")
        return None

    input_filename = os.path.basename(input_path)
    log_filename = input_filename.replace(".csv", "_filter_log.txt")
    log_path = os.path.join(output_dir, log_filename)

    sys.stdout = Logger(log_path)

    print(f"[RUN] Input: {input_path}")
    df = pd.read_csv(input_path)

    total_dialogues = df["Dialogue_ID"].nunique()
    total_utterances = len(df)

    filtered_rows = []
    kept_dialogues, kept_utterances = 0, 0

    for dialogue_id, group in df.groupby("Dialogue_ID"):
        group = group.sort_values(by="Utterance_ID")
        emotions = group["Emotion"].astype(str).str.strip().str.lower().tolist()

        if len(set(emotions)) < require_min_emotions:
            continue

        last_emotion = {}
        shift_count = defaultdict(int)

        for _, row in group.iterrows():
            speaker = row["Speaker"]
            emotion = str(row["Emotion"]).strip().lower()
            if speaker in last_emotion and emotion != last_emotion[speaker]:
                shift_count[speaker] += 1
            last_emotion[speaker] = emotion

        total_shifts = sum(shift_count.values())
        if total_shifts < require_min_total_shifts:
            continue

        print(f"\n[KEEP] Dialogue_ID={dialogue_id} | unique_emotions={len(set(emotions))} | total_shifts={total_shifts}")
        for spk, sc in shift_count.items():
            print(f"       speaker={spk} shifts={sc}")

        filtered_rows.append(group)
        kept_dialogues += 1
        kept_utterances += len(group)

    output_filename = input_filename.replace(".csv", "_filtered.csv")
    output_path = os.path.join(output_dir, output_filename)

    if filtered_rows:
        filtered_df = pd.concat(filtered_rows).reset_index(drop=True)

        if "Sr No." in filtered_df.columns:
            filtered_df["Sr No."] = range(len(filtered_df))

        filtered_df.to_csv(output_path, index=False)

        print("\n[DONE]")
        print(f"  dialogues: {total_dialogues} -> {kept_dialogues}")
        print(f"  utterances: {total_utterances} -> {kept_utterances}")
        print(f"  output_csv: {output_path}")
        print(f"  log_file:   {log_path}")
    else:
        print("[DONE] No dialogues matched the rules.")
        output_path = None

    sys.stdout.log.close()
    sys.stdout = sys.stdout.terminal
    return output_path


def main():
    merged_csv = build_iemocap_f_all_sessions(
        base_root="IEMOCAP_full_release",
        output_csv="iemocap_F_all_sessions_full_emotion.csv"
    )

    filter_dialogues_by_emotion_shift(
        input_path=merged_csv,
        output_dir="./Processed_dataset_all_filter_rules_output",
        require_min_emotions=4,
        require_min_total_shifts=2
    )


if __name__ == "__main__":
    main()
