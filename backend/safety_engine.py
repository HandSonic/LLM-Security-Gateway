import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import settings

class SafetyEngine:
    def __init__(self):
        print(f"Loading model from {settings.MODEL_PATH}...")
        self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_PATH)
        self.model = AutoModelForCausalLM.from_pretrained(
            settings.MODEL_PATH, 
            torch_dtype="auto", 
            device_map=settings.DEVICE
        ).eval()
        self.id2risk = self.tokenizer.init_kwargs.get('id2risk', {})
        print("Model loaded successfully.")

    def infer(self, messages, check_response=False, max_new_tokens=1):
        """
        Executes model inference to detect risks.
        If check_response is True, the messages list should include the assistant's response.
        """
        rendered_query = self.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=not check_response
        )
        
        model_inputs = self.tokenizer([rendered_query], return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **model_inputs, 
                max_new_tokens=max_new_tokens, 
                do_sample=False, 
                output_scores=True, 
                return_dict_in_generate=True
            )

        input_length = model_inputs['input_ids'].shape[1]
        
        # Parse output for risk scores
        # The first generated token usually contains the risk classification
        # We look at the scores for the first generated token
        
        scores = torch.stack(outputs.scores, 1)
        scores = scores.softmax(-1)
        
        # We only care about the first token for risk classification (safe/unsafe)
        # In this model's specific architecture for 0.6B:
        # It generates structured output. We need to look at the probability of risk tokens.
        
        first_token_scores = scores[0, 0, :] # Batch 0, Step 0
        
        risk_score_map = {}
        
        # Iterate over all tokens in vocab is too slow, we should look at top k or specific tokens
        # The README example logic is a bit complex, iterating topk. Let's adapt it.
        
        values, indices = first_token_scores.topk(k=20)
        print(f"Top 5 tokens: {[self.tokenizer.decode([i]).strip() + f'({v.item():.4f})' for v, i in zip(values[:5], indices[:5])]}")
        
        for v, i in zip(values, indices):
            token_id = i.item()
            score = v.item()
            token_str = self.tokenizer.decode([token_id]).strip()
            
            # Map token to risk category if possible
            # The model outputs raw tokens like "dw", "safe", etc.
            # We need to match these with id2risk if available, or just usage
            
            # README says:
            # token_score = {k:v['prob'] for k,v in generated_tokens_with_probs...}
            # risk_score = {id2risk[k]:v['prob'] ...}
            
            # Simplified for now: return all top tokens that look like risk keys
            # The keys in id2risk are likely the tokens we see (e.g., 'dw', 'sec')
            
            # Prevent overwriting if we already have a higher score for this stripped token
            if token_str in risk_score_map:
                continue

            if token_str in self.id2risk:
                risk_score_map[token_str] = score
            elif token_str in ['dw', 'pc', 'dc', 'pi', 'ec', 'ac', 'def', 'ti', 'cy', 'ph', 'mh', 'se', 'sci', 'pp', 'cs', 'acc', 'mc', 'ha', 'ps', 'ter', 'sd', 'ext', 'fin', 'med', 'law', 'cm', 'ma', 'md', 'sec']:
                 # Fallback if id2risk is empty or doesn't have it
                 risk_score_map[token_str] = score

        return risk_score_map

safety_engine = SafetyEngine()
