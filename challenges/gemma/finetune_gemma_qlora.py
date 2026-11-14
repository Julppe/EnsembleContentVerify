#!/usr/bin/env python3
"""
QLoRA Fine-Tuning Script for Open-Weight Gemma on CheckEm ("Name the Technique")
================================================================================
Fine-tunes a Gemma instruction/VLM checkpoint using 4-bit NF4 QLoRA so the model:
1. Emits CheckEm's exact JSON evaluation schema reliably.
2. Accurately extracts short verbatim `trigger_quote` spans.
3. Achieves low False-Positive Rate on Hard Negatives (articles *about* propaganda).

Example training JSONL line (`propaganda_train.jsonl`):
{
  "title": "Sample Headline",
  "url": "https://example.org/article",
  "sections": [{"section_id": "sec-1", "heading": "Intro", "text": "..."}],
  "label_json": {
    "page_vote": "questionable",
    "page_confidence": 94,
    "page_techniques": ["Loaded Language", "Fear Appeal"],
    "page_reason": "Uses emotionally charged labels and worst-case dread without evidence.",
    "section_evaluations": [...],
    "image_evaluations": []
  }
}
"""

import argparse
import json
import os
from typing import List, Dict


def load_jsonl_dataset(path: str) -> List[Dict]:
    if not os.path.exists(path):
        # Provide minimal synthetic bootstrap examples for dry-run inspection
        return [
            {
                "title": "Winter Grid Warning",
                "url": "https://synthetic.example/grid",
                "sections": [{
                    "section_id": "sec-1",
                    "heading": "Warning",
                    "text": "Reckless bureaucrats are engineering a winter catastrophe that will leave families freezing in darkness.",
                }],
                "label_json": {
                    "page_vote": "questionable",
                    "page_confidence": 96,
                    "page_techniques": ["Loaded Language", "Fear Appeal"],
                    "page_reason": "Uses 'reckless bureaucrats' (Loaded Language) and imminent freezing doom (Fear Appeal).",
                    "section_evaluations": [{
                        "section_id": "sec-1",
                        "vote": "questionable",
                        "techniques": ["Loaded Language", "Fear Appeal"],
                        "trigger_quote": "engineering a winter catastrophe",
                        "reason": "Escalates dread without technical evidence.",
                    }],
                    "image_evaluations": [],
                },
            },
            {
                "title": "Propaganda techniques (Encyclopedia)",
                "url": "https://en.wikipedia.org/wiki/Propaganda_techniques",
                "sections": [{
                    "section_id": "sec-1",
                    "heading": "Overview",
                    "text": "Fear appeal is a psychological persuasion technique analyzed in media literacy textbooks.",
                }],
                "label_json": {
                    "page_vote": "clean",
                    "page_confidence": 98,
                    "page_techniques": [],
                    "page_reason": "Encyclopedic article defining propaganda objectively without attempting persuasion.",
                    "section_evaluations": [{
                        "section_id": "sec-1",
                        "vote": "clean",
                        "techniques": [],
                        "trigger_quote": "",
                        "reason": "Hard negative: defines Fear Appeal neutrally.",
                    }],
                    "image_evaluations": [],
                },
            },
        ]

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def format_sft_example(row: Dict) -> Dict[str, str]:
    prompt = (
        "Analyze the sections below for Name the Technique propaganda detection and output ONLY valid JSON.\n"
        f"Page Title: {row['title']}\nPage URL: {row['url']}\n"
        f"Sections: {json.dumps(row['sections'], ensure_ascii=False)}\n"
    )
    completion = json.dumps(row["label_json"], ensure_ascii=False)
    return {
        "text": f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n{completion}<end_of_turn>"
    }


def main():
    parser = argparse.ArgumentParser(description="QLoRA fine-tune Gemma for CheckEm")
    parser.add_argument("--model-id", default="google/gemma-3-27b-it")
    parser.add_argument("--train-file", default="data/propaganda_train.jsonl")
    parser.add_argument("--output-dir", default="checkpoints/gemma-checkem-lora")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--dry-run", action="store_true", help="Format dataset without loading GPU weights")
    args = parser.parse_args()

    raw_rows = load_jsonl_dataset(args.train_file)
    formatted = [format_sft_example(r) for r in raw_rows]
    print(f"Prepared {len(formatted)} CheckEm training examples.")

    if args.dry_run:
        print("Sample formatted SFT turn:\n", formatted[0]["text"][:400], "...")
        return

    import torch
    from datasets import Dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from trl import SFTTrainer

    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        quantization_config=bnb_cfg,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    train_ds = Dataset.from_list(formatted)
    train_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=8,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_8bit",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_ds,
        peft_config=lora_cfg,
        dataset_text_field="text",
        max_seq_length=4096,
        tokenizer=tokenizer,
        args=train_args,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    print(f"Saved Gemma CheckEm QLoRA adapter to {args.output_dir}")


if __name__ == "__main__":
    main()
