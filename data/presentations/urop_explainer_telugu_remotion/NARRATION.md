# Beyond the caption

Multimodal misinformation classification · Telugu-English narration

Voice: ElevenLabs Bella; model: Eleven v4, with explicit Telugu support.

## Context — Text ఒక్కటే సరిపోతుందా?

ఒక post‌ని చూసినప్పుడు caption మాత్రమే చదవం. Image‌ని కూడా చూసి, రెండూ కలిపి ఏం చెబుతున్నాయో అర్థం చేసుకుంటాం. పాత photo‌కి కొత్త caption పెట్టినా, image‌కి సంబంధం లేని text జోడించినా, ఒక్క input‌తో ముఖ్యమైన context మిస్ కావచ్చు. మన research‌లో text, image patterns‌ని కలిపి, misinformation‌కి సంబంధించిన research categories‌ని predict చేస్తాం.

## Inputs — ఒక pair, రెండు inputs

మన research‌కి faculty-provided dataset‌ని వాడుతున్నాం. ప్రతి example‌లో text, image జతగా ఉంటాయి. Training, validation, test కోసం separate splits ఉంటాయి. Pairing‌ని ఒకే post identifier‌తో check చేస్తాం. Labels research categories మాత్రమే; అవి independent fact-check కాదు. ఈ visuals అన్నీ illustrations.

## Model — Text → contextual features

Text pathway‌లో tokenizer title‌ని tokens‌గా మార్చి, IDs, attention mask ఇస్తుంది. BERT-base వాటిని context‌తో కలిపి process చేస్తుంది. దాని CLS representation‌ని title feature vector‌గా తీసుకుంటాం. Learned projection, LayerNorm దాన్ని fusion‌కి సరిపోయే size‌లోకి మారుస్తాయి. Context‌ని capture చేసే pretrained representation కోసం BERT‌ని వాడుతున్నాం; అన్ని tasks‌కి ఇదే best model అని కాదు.

## Model — Image → visual features

Image‌ని RGB format‌లోకి మార్చి, resize, crop, normalization చేస్తాం. Evaluation‌లో fixed preprocessing ఉంటుంది. ResNet-50 visual patterns‌ని feature vector‌గా మారుస్తుంది. Original classifier బదులు pooled features వాడతాం. వీటికీ separate projection, LayerNorm ఉంటాయి. BERT, ResNet backbones రెండూ fine-tune అవుతాయి; అంటే వాటి weights కూడా training‌లో update అవుతాయి.

## Fusion — రెండు streams, ఒక representation

Text, image features dimensions మొదట వేర్వేరుగా ఉంటాయి. Projections వాటిని ఒకే size‌కి తెస్తాయి. Max fusion ప్రతి position‌లో text value, image value రెండింటిలో పెద్దదాన్ని ఉంచుతుంది. మొత్తం ఒక stream‌ని ఎంచుకోకుండా, position by position combine చేస్తుంది. ఉపయోగపడే features‌ని encoders, projections training‌లో నేర్చుకుంటాయి. Fusion అనేది direct fact-check లేదా reasoning proof కాదు.

## Output — Features నుంచి category prediction

Fused features classification head‌లోకి వెళ్తాయి. ఇందులో linear layer, GELU, dropout, చివరగా category scores ఇచ్చే layer ఉంటాయి. Cross-entropy loss ఆ scores‌ని correct label‌తో పోల్చి training‌ని guide చేస్తుంది. Softmax‌తో scores‌ని probabilities‌గా మార్చి, ఎక్కువ probability ఉన్న research category‌ని output‌గా తీసుకోవచ్చు. ఆ probability నిజానికి certificate కాదు; learned patterns ఆధారంగా model ఇచ్చే confidence.

## Evaluation — Prediction‌ని ఎలా పరీక్షిస్తాం?

Train split‌తో weights నేర్చుకుంటాం. Validation‌తో checkpoint‌ని select చేసి, selection freeze అయిన తర్వాత held-out test‌ని evaluate చేస్తాం. Test చూసి model‌ని tune చేస్తే అది independent check‌గా ఉండదు. Accuracy‌తో పాటు Macro-F1, class-wise precision, recall చూస్తాం. Confusion matrix ఏ categories మధ్య mistakes వస్తున్నాయో చూపిస్తుంది. ఒకే score అన్ని situations‌లో performance‌ని చెప్పదు.

## Takeaway — Context‌ని కలిసి చూడటం

Text ఏం చెబుతోంది, image‌లో ఏ patterns ఉన్నాయి, రెండింటినీ ఒక shared representation‌లోకి తీసుకురావడమే ఈ design. Text encoder, image encoder, projections, max fusion, classification head కలిసి పనిచేస్తాయి. Clear pairing, separate evaluation, careful interpretation ఉంటేనే prediction‌కి research meaning ఉంటుంది. ఇది independent factual verification‌కి ప్రత్యామ్నాయం మాత్రం కాదు.
