# 1 represent no filtration based on p-value
investigated_alphas = [1, 0.05, 0.01, 0.001]

scenarios = ["all", "MSFT_MSFT", "PUBL_MSFT", "intoXX", "fromEN", "ENU",
             "nonWMT", "nonLatin", "nonEnglish", "discussion",
             "logogram_alphabet", "bootstrap"]

investigated_metrics = ['BERT_SCORE', 'BLEURT_default', 'COMET', 'COMET_src',
                        'Prism_ref', 'Prism_src', 'SacreBLEU_bleu',
                        'SacreBLEU_chrf', 'SacreBLEU_ter_neg',
                        'ExtendedEditDist_neg', 'CharacTER_neg', 'ESIM_']

wmt_langs = ["ENU", "ZHO", "CHS", "CSY", "DEU", "IUS", "JPN", "PLK", "RUS",
             "TAM", "KHM", "PAS", "ENU", "ZHO", "CHS", "CSY", "DEU", "FIN",
             "GUJ", "KKZ", "RUS", "LTH", "ENU", "ZHO", "CHS", "CSY", "DEU",
             "FIN", "ETI", "RUS", "TRK", "ENU", "ZHO", "CHS", "CSY", "DEU",
             "FIN", "LVI", "RUS", "TRK", ]
logograms = ['CHS', 'CHT', 'JPN', 'YUE', 'KOR']
non_latin_langs = ['CHS', 'CHT', 'ELL', 'FAR', 'HEB', 'HYE', 'KAT', 'NEP',
                   'ORI', 'RUS', 'BGR', 'KKZ', 'TGK', 'JPN', 'UKR', 'KOR',
                   'URD', 'YUE', 'AMH', 'HIN', 'PAN', 'PRS', 'TIR', 'KUR',
                   'SRO', 'BNB', 'TAM', 'MKI', 'MON', 'MYA', 'THA', 'ARA']

metrics_names = {'BERT_SCORE': 'BERTScore', 'BLEURT_default': 'BLEURT',
                 'COMET': 'COMET', 'COMET_src': 'COMET-src',
                 'Prism_ref': 'Prism', 'Prism_src': 'Prism-src',
                 'SacreBLEU_bleu': 'BLEU', 'SacreBLEU_chrf': 'ChrF',
                 'SacreBLEU_ter_neg': 'TER', 'ExtendedEditDist_neg': 'EED',
                 'CharacTER_neg': 'CharacTER', 'ESIM_': 'ESIM',
                 'BLEURT_large': 'BLEURT-large', "COMET_base": "COMET-base",
                 "neg_COMET_hter": "COMET-hter",
                 "neg_COMET_hter_base": "COMET-hter-base",
                 "COMET_relativeDA": "COMET-ranker", }

lang_names = {'ENU': 'English', 'FRA': 'French', 'DEU': 'German',
              'CHS': 'Chinese', 'JPN': 'Japanese', 'KOR': 'Korean',
              'ITA': 'Italian', 'SVE': 'Swedish', 'DAN': 'Danish',
              'RUS': 'Russian', 'PLK': 'Polish', 'PTB': 'Portuguese',
              'NLD': 'Dutch', 'HIN': 'Hindi', 'CSY': 'Czech', 'THA': 'Thai',
              'IND': 'Indonesian', 'ESN': 'Spanish', 'ARA': 'Arabic',
              'TRK': 'Turkish', 'HUN': 'Hungarian', 'ROM': 'Romanian',
              'FAR': 'Persian', 'HEB': 'Hebrew', 'UKR': 'Ukrainian',
              'NOR': 'Norwegian', 'ELL': 'Greek', 'CAT': 'Catalan',
              'HRV': 'Croatian', 'CYM': 'Welsh', 'SKY': 'Slovak', 'URD': 'Urdu',
              'FIN': 'Finnish', 'VIT': 'Vietnamese', 'LTH': 'Lithuanian',
              'MLT': 'Maltese', 'TAH': 'Tahitian', 'IRE': 'Irish',
              'SWK': 'Kiswahili', 'TAM': 'Tamil'}
