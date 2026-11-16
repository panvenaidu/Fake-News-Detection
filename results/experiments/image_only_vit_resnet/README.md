# Frozen ViT-B/16 and ResNet-50 comparison

Private saved notebook outputs, cache shards, checkpoints, and post-level results belong here when downloaded for verification. Keep this directory's experimental outputs out of Git. The earlier end-to-end ResNet-50 run remains separate.

For a saved version, download its private output, retaining the directory tree. Verify the result from the repository root with:

```sh
PYTHONPATH='Training/Text + Image/Scripts:Testing/Text + Image' \
  .venv-urop/bin/python 'Testing/Image Only/verify_frozen_image_pair_v1.py' \
  'Metrics/Results/experiments/image_only_vit_resnet/<downloaded-version>/urop_frozen_pair'
```

The check requires the per-arm prediction CSVs, metric files, selected and epoch head weights, split manifests, resolved configuration, and pre-test freeze record. Feature cache shards and smoke-test weights are not needed to check a completed result. Add the exact saved Kaggle version link to the report after reopening its output.
