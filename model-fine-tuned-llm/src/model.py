import torch
import torch.nn as nn
from transformers import DistilBertModel, DistilBertConfig
from typing import Optional, Dict, Any


class DistilBertForPhishingDetection(nn.Module):
    def __init__(
        self, 
        model_name: str = 'distilbert-base-uncased',
        num_labels: int = 2,
        dropout_rate: float = 0.3,
        freeze_bert: bool = False
    ):
        super().__init__()
        
        self.config = DistilBertConfig.from_pretrained(model_name)
        self.distilbert = DistilBertModel.from_pretrained(model_name)
        
        if freeze_bert:
            for param in self.distilbert.parameters():
                param.requires_grad = False
        
        self.pre_classifier = nn.Linear(self.config.hidden_size, self.config.hidden_size)
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(self.config.hidden_size, num_labels)
        
        self.relu = nn.ReLU()
        
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        
        outputs = self.distilbert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        hidden_state = outputs.last_hidden_state
        pooled_output = hidden_state[:, 0]
        
        pooled_output = self.pre_classifier(pooled_output)
        pooled_output = self.relu(pooled_output)
        pooled_output = self.dropout(pooled_output)
        
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))
        
        return {
            'loss': loss,
            'logits': logits,
            'hidden_states': outputs.hidden_states if hasattr(outputs, 'hidden_states') else None
        }
    
    def get_embeddings(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        with torch.no_grad():
            outputs = self.distilbert(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            hidden_state = outputs.last_hidden_state
            pooled_output = hidden_state[:, 0]
        return pooled_output


class ModelConfig:
    def __init__(self, **kwargs):
        self.model_name = kwargs.get('model_name', 'distilbert-base-uncased')
        self.num_labels = kwargs.get('num_labels', 2)
        self.max_length = kwargs.get('max_length', 512)
        self.batch_size = kwargs.get('batch_size', 16)
        self.learning_rate = kwargs.get('learning_rate', 2e-5)
        self.num_epochs = kwargs.get('num_epochs', 3)
        self.warmup_steps = kwargs.get('warmup_steps', 500)
        self.weight_decay = kwargs.get('weight_decay', 0.01)
        self.dropout_rate = kwargs.get('dropout_rate', 0.3)
        self.freeze_bert = kwargs.get('freeze_bert', False)
        self.gradient_accumulation_steps = kwargs.get('gradient_accumulation_steps', 1)
        self.max_grad_norm = kwargs.get('max_grad_norm', 1.0)
        self.fp16 = kwargs.get('fp16', False)
        self.save_steps = kwargs.get('save_steps', 500)
        self.logging_steps = kwargs.get('logging_steps', 50)
        self.evaluation_strategy = kwargs.get('evaluation_strategy', 'steps')
        self.eval_steps = kwargs.get('eval_steps', 500)
        self.save_total_limit = kwargs.get('save_total_limit', 3)
        self.load_best_model_at_end = kwargs.get('load_best_model_at_end', True)
        self.metric_for_best_model = kwargs.get('metric_for_best_model', 'f1')
        self.greater_is_better = kwargs.get('greater_is_better', True)
        
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__