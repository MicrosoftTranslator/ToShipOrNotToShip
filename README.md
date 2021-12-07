# To Ship or Not to Ship: An Extensive Evaluation of Automatic Metrics for Machine Translation

This repo contains human judgment data and code for the [paper](http://statmt.org/wmt21/pdf/2021.wmt-1.57.pdf]):

    To Ship or Not to Ship: An Extensive Evaluation of Automatic Metrics for Machine Translation

## Data format description

The data structure may be confusing because we have anonymized campaigns, system names, sources, references, and translations. Everything is anonymized with the MD5 algorithm.

In the folder, `public_release` is a list of individual campaigns. Each folder is a single campaign as described in the paper. The campaign is an evaluation of several systems over the same conditions (same sentences, same annotators, at the same time).

In each campaign folder, you can find several XLSX files, each containing the results of a single system.

There are always following two sheets (sometimes there are four for special cases). `hum_annotations` where each line represents the results of a single evaluated sentence. And `automatic_metrics` contains system-level scores over all sentences. 

The sheet `hum_annotations` contains except scores of automatic metrics following columns: Source (source language), Target (target language), User (identification of user within a campaign), SegmentID (unique sentence ID, comparable across systems within campaign), Segment (hash of source sentence), Reference (hash of reference), Translation (hash of system output), Score (human DA score between 0-100), valid_line (filtration of sentences missing in some systems)

In order to replicate the bootstrap resampling experiments, download resources [here](https://1drv.ms/u/s!Aq0goPMF_LnlhPUOytbrxUSdZnjQAA?e=5Q01GU).

## Evaluating new metrics

For legal reasons, we do not release textual data on which metric scores have been calculated. However, it would greatly help the MT community if new metrics would be evaluated over this blind set.
If you are an author of a new metric and would like to have it evaluated, create an issue, where you point us to:
 - GitHub with implementation. Please, have an installation script ready and command-line approach that takes inputs for references, hypotheses (and sources).
 - paper or blog post showing superior performance on the [WMT Metrics shared tasks data](http://www.statmt.org/wmt21/metrics-task.html).

 We set these conditions to decrease the time needed for evaluating individual metrics, we may reconsider them in the future. Also, having simple installation and usage scripts can help metrics to be adopted. If you have any suggestions or questions, describe them in the issue. We plan to evaluate metrics in batches at most twice a year (most likely once a year). Therefore, we encourage you to submit your metrics to the WMT Metrics shared task.

 Lastly and most importantly, we do not promise to evaluate all metrics. Moreover, we may decide to not evaluate any future metrics for time-constrains reasons.


## How to Cite

Please cite our WMT paper:

```
@InProceedings{kocmi2021to_ship,
  author    = {Kocmi, Tom and Federmann, Christian and Grundkiewicz, Roman and Junczys-Dowmunt, Marcin and Matsushita, Hitokazu and Menezes, Arul}
  title     = {To Ship or Not to Ship: An Extensive Evaluation of Automatic Metrics for Machine Translation},
  booktitle      = {Proceedings of the Sixth Conference on Machine Translation},
  month          = {November},
  year           = {2021},
  publisher      = {Association for Computational Linguistics},
  pages     = {483--499},
  url       = {http://statmt.org/wmt21/pdf/2021.wmt-1.57.pdf}
}
```

## Announcement

Greetings from Microsoft Translator!

We have released an initial version of this data set on November 10, 2021. Please create an issue or contact [@kocmitom](https://github.com/kocmitom) with your questions and concerns. We hope that this data may inspire future research on better quality metrics for machine translation.

Cheers and best, have a good day,<br/>
   [@cfedermann](https://github.com/cfedermann)
