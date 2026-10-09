**9 October planning update:** percentages are unchanged. The saved checkpoint is intact, but the original resume path needs a sample-order repair and focused checks before GPU execution. BERT completion will be a separate job with complete validation/test exports. Plan: `context/TEXT_COMPLETION_PLAN_20261009.md`. No GPU job launched. At 20% assistant usage remaining, reserve work for checkpoint/context/GitHub handoff while any healthy submitted cloud job continues.

# Six-way project progress bars

User preference: Whenever asked for progress, show these bars plus data/model/train/validate/test checkpoints. Read PROGRESS_TRACKER.json and refresh from verified evidence; never increment merely because time passed. Keep pilots separate from full benchmark work. This preference does not create an automation.

Five workflow checkpoints, each worth20%: official dataset audit; model implementation; training; validation; final test + saved results. Percentages measure workflow completion, not accuracy, percent of data processed, elapsed time or remaining GPU time. Dataset audit is complete for all three modalities; full image availability remains incomplete. Five training/validation epochs were observed; the verified recoverable tensor is epoch5 batch15000/17625. Training-stage progress uses this older durable state, approximately81% of the six-epoch maximum; observed validation checks are83%. Some epoch5 work needs replay.

```text
Text-only BERT      ███████░░░  73%
Text + image, full  ████░░░░░░  40%
Image-only         ██░░░░░░░░  20%
Overall            ████░░░░░░  44%
```

| Checkpoint | Text-only BERT | Text+image full benchmark | Image-only |
|---|---|---|---|
| Official dataset/label/split audit | Done | Done | Done |
| Model code | Done | Done; pilot demonstrated | Pending standalone model |
| Training | Recoverable state:81% of six-epoch budget | Full run pending | Pending |
| Validation | 5/6 epoch checks,83% | Full run pending | Pending |
| Final test + saved final results | Pending | Full run pending | Pending |

Text+image engineering pilot:100% completed,3epochs,2000/300/300 rows; separate from the full benchmark. ModernBERT additional comparison:40% prepared, training/validation/test pending; excluded from the BERT headline and three-modality average.

We did train BERT; validation followed each training epoch. Final testing is evaluation on unseen test data, not another training stage on that data. Best checkpoint is selected using validation.

Recovery files are preserved under data/cloud_recovery/. BERT checkpoint integrity passed: epoch5 batch15000, four validations inside tensor, best epoch4. Original fifth-epoch observed history remains preserved. Resume must replay the epoch5 tail. Original multimodal archive and all300 validation/300 test predictions are now synced and verified. No GPU training job is currently running.
