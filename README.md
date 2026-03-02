# Appraisal-Theory-ERC-Dataset

This repository provides a processed benchmark dataset for appraisal-based emotion prediction.

## Dataset Composition

This merged dataset contains processed data derived from:

- MELD (GPL-3.0 License)
  https://github.com/declare-lab/MELD

- EmoryNLP Emotion Detection (Apache License 2.0)
  https://github.com/emorynlp/emotion-detection

- DailyDialog (CC BY-NC-SA 4.0)
  http://yanran.li/dailydialog

All original licenses apply to their respective portions of the dataset.

This repository redistributes processed forms of these publicly available datasets in compliance with their licenses.

## IEMOCAP

IEMOCAP is not redistributed due to its restricted license.
To reproduce the IEMOCAP portion, please obtain it from:

https://sail.usc.edu/iemocap/

and run:

```bash
python scripts/iemocap_processing.py
