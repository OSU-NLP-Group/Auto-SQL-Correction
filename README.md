# Auto-SQL-Correction
Code, data, and model for our ACL 2023 paper [Text-to-SQL Error Correction with Language Models of Code](https://arxiv.org/abs/2305.13073).


**Note:**
Although the raw codes for all experiments are released, we are actively cleaning and reorganizing the repository, so some temporary issues may occur till we finalize it. Please check the following TODO list for our progress: 

#### TODO
- [x] Data and model
- [x] Code for `CodeT5-PyDict+Program`
- [ ] Code for simulated interaction
- [ ] Code for other experiments

## Table of Contents

1. Installation
2. Data
3. Preprocessing
4. Training
5. Evaluation
6. Citation

## Installation
Please run the following commands to create a conda environment in Python 3.9 with the required packages.
```sh
conda create -n sqledit python=3.9 pip
conda activate sqledit
pip install -r requirements.txt
```

## Data
Please first download the original Spider dataset from this [link](https://drive.google.com/uc?export=download&id=1TqleXec_OykOYFREKKtschzY29dUcVAQ) and unzip it in the `data/` folder.
```sh
unzip spider.zip -d data/
```
Then, please download our synthesized SQL error correction data from this [link](https://buckeyemailosu-my.sharepoint.com/:f:/g/personal/chen_8336_buckeyemail_osu_edu/EjAxbCHp5q9BgT9Ljyq60xUBN_gEFGeOLQFSl5NusgV9VQ?e=EpB555) and also put them in the `data/` folder.

The `data/` folder should be organized as follows:
```
.
├───  data
│    ├───  spider
│        ├───  ...
│    ├───  spider-dev-bridge.json
│    ├───  spider-dev-codet5.json
│    ├───  spider-dev-smbop.json
│    ├───  spider-train-bridge.json
│    ├───  spider-train-codet5.json
│    ├───  spider-train-smbop.json
│    ├───  sqledit_dev_gold.sql
│   ...
```

## Preprocessing
TODO
```sh
python run.py --preproc --use_content --query_type pydict --edit_type program --base_parser smbop
```

## Training
TODO
```sh
mkdir model
python run.py --train --load_checkpoint Salesforce/codet5-base --save_checkpoint model/codet5-sqledit --seed 42 --gpu 0
```

## Evaluation
TODO
```sh
python run.py --eval --load_checkpoint model/codet5-sqledit --gpu 0
```


### Model Checkpoints
You may download our pre-trained model checkpoints from this [link](https://buckeyemailosu-my.sharepoint.com/:f:/g/personal/chen_8336_buckeyemail_osu_edu/Er_mV3sNNotPoaCivzCLwDQBBuI5rRR1fymCJpshIrJEZA?e=U4Xz2t). It includes our `CodeT5-PyDict+Program` model trained for the three text-to-SQL base parser in our paper.

## Citation
```
@inproceedings{chen-etal-2023-sqledit,
    title = "Text-to-SQL Error Correction with Language Models of Code",
    author = "Chen, Ziru  and
      Chen, Shijie  and
      White, Michael  and
      Mooney, Raymond  and
      Payani, Ali  and
      Srinivasa, Jayanth  and
      Su, Yu  and
      Sun, Huan",
    booktitle = "Proceedings of the 61th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)",
    year = "2023",
    address = "Toronto, Canada",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/2305.13073"
}
```