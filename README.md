# Appraisal-Theory-ERC-Dataset

This repository provides a processed benchmark dataset for appraisal-based emotion prediction (LREC 2026).

## Dataset Description

The merged dataset contains the following columns, Dialogue_ID and Utterance_ID are re-indexed after merging:

| Column Name | Description |
|-------------|-------------|
| Sr No. | Global row index after dataset merging |
| Is_Transition | Binary indicator (1 = emotion differs from previous utterance of same speaker) |
| Is_Appraisal_Driven | Binary indicator (1 = transition selected as appraisal-driven event) |
| Utterance | Text content of the dialogue utterance |
| Speaker | Speaker identifier (A/B or character ID depending on source dataset) |
| Emotion | Ground-truth emotion label from original dataset |
| Dialogue_ID | Dialogue identifier (re-indexed after merging) |
| Utterance_ID | Position of utterance within the dialogue |
| Set | Data split (train / dev / test) |
| expectation | Model-generated or annotated psychological expectation (if applicable) |
| dataset | Source dataset name (MELD / EmoryNLP / DailyDialog) |
| Moment_Utterence_ID | Reference utterance index used for expectation alignment |

## Data Sources

This dataset includes processed data derived from:

### 1. MELD
- License: GPL-3.0
- Source: https://github.com/declare-lab/MELD

### 2. EmoryNLP Emotion Detection
- License: Apache License 2.0
- Source: https://github.com/emorynlp/emotion-detection

### 3. DailyDialog
- License: CC BY-NC-SA 4.0
- Source: http://yanran.li/dailydialog

All original licenses remain applicable to their respective data portions.

This repository redistributes processed forms of publicly available datasets in compliance with their licenses.

## IEMOCAP

IEMOCAP is not redistributed due to its restricted license.

To reproduce IEMOCAP results:
1. Obtain the dataset from https://sail.usc.edu/iemocap/
2. Place the data in a local folder
3. Run the processing script

## License

- Code and newly added annotations (e.g., expectation, transition flags) are licensed under MIT License.
- Original dataset licenses remain valid for their respective data portions.

