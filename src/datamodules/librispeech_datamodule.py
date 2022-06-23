import os
from typing import Optional
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from pytorch_lightning import LightningDataModule


class LibriSpeechDataModule(LightningDataModule):
    """
    A DataModule implements 5 key methods:
        - prepare_data (things to do on 1 GPU/TPU, not on every GPU/TPU in distributed mode)
        - setup (things to do on every accelerator in distributed mode)
        - train_dataloader (the training dataloader)
        - val_dataloader (the validation dataloader(s))
        - test_dataloader (the test dataloader(s))
    This allows you to share a full dataset without explaining how to download,
    split, transform and process the data.
    Read the docs:
        https://pytorch-lightning.readthedocs.io/en/latest/extensions/datamodules.html
    """
    def __init__(
        self,
        collator,
        data_dir,
        train_batch_size,
        val_batch_size,
        test_batch_size,
        split='train.360',
        pin_memory=True):
        super().__init__()
        
        # this line allows to access init params with 'self.hparams' attribute
        self.save_hyperparameters()
        
        self.collator = collator
        
        self.num_workers = os.cpu_count()
        if self.hparams.load_preprocessed_data:
            self.num_proc = 1
        else:
            self.num_proc = os.cpu_count()
            
        self.libri_train: Optional[Dataset] = None
        self.libri_val: Optional[Dataset] = None
        self.libri_test: Optional[Dataset] = None
        
        
    def prepare_data(self):
        """Download data if needed. This method is called only from a single GPU.
        Do not use it to assign state (self.x = y)."""
        
        load_dataset('librispeech_asr', 'clean', split=self.hparams.split, cache_dir=self.hparams.data_dir)
            
        
    def setup(self, stage=None):
        """Load data. Set variables: `self.data_train`, `self.data_val`, `self.data_test`.
        This method is called by lightning twice for `trainer.fit()` and `trainer.test()`, so be careful if you do a random split!
        The `stage` can be used to differentiate whether it's called before trainer.fit()` or `trainer.test()`."""
        
        # Assign train/val datasets for use in dataloaders
        
        if stage == "fit" or stage is None:
            self.libri_train = load_dataset('librispeech_asr', 'clean', split=self.hparams.split)
            self.libri_val = load_dataset('librispeech_asr', 'clean', split='validation')
                

        # Assign test dataset for use in dataloader(s)
        if stage == "test" or stage is None:
            self.libri_test = load_dataset('librispeech_asr', 'clean', split='Test')
        
        if stage == "predict" or stage is None:
            raise Exception("""This DataModule is not designed to be used for prediction.
                            Please use the Spotify DataModule for prediction.""")
    
    
    def train_dataloader(self):
        return DataLoader(
            self.libri_train, 
            batch_size=self.hparams.train_batch_size, 
            shuffle=True, 
            collate_fn=self.collator, 
            num_workers=self.num_workers,
            pin_memory=self.hparams.pin_memory
            )
        
        
    def val_dataloader(self):
        return DataLoader(
            self.libri_val, 
            batch_size=self.hparams.val_batch_size, 
            shuffle=False, 
            collate_fn=self.collator, 
            num_workers=self.num_workers,
            pin_memory=self.hparams.pin_memory
            )
        
        
    def test_dataloader(self):
        return DataLoader(
            self.libri_test, 
            batch_size=self.hparams.test_batch_size, 
            shuffle=False, 
            collate_fn=self.collator, 
            num_workers=self.num_workers,
            pin_memory=self.hparams.pin_memory
            )
        
