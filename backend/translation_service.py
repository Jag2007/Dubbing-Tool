from functools import lru_cache

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

SUPPORTED_LANGUAGES = {
    "hi": {"name": "Hindi", "nllb_code": "hin_Deva"},
    "te": {"name": "Telugu", "nllb_code": "tel_Telu"},
    "kn": {"name": "Kannada", "nllb_code": "kan_Knda"},
    "fr": {"name": "French", "nllb_code": "fra_Latn"},
    "es": {"name": "Spanish", "nllb_code": "spa_Latn"},
}

MODEL_NAME = "facebook/nllb-200-distilled-600M"
SOURCE_LANGUAGE = "eng_Latn"


def get_supported_languages() -> list[dict[str, str]]:
    return [
        {"code": code, "name": language["name"]}
        for code, language in SUPPORTED_LANGUAGES.items()
    ]


@lru_cache(maxsize=1)
def get_translation_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, use_safetensors=False)
    model.eval()
    return tokenizer, model


def translate_text(text: str, target_lang: str) -> str:
    if target_lang not in SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported target language selected.")

    tokenizer, model = get_translation_model()
    tokenizer.src_lang = SOURCE_LANGUAGE
    target_code = SUPPORTED_LANGUAGES[target_lang]["nllb_code"]

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_code)

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_new_tokens=256,
        )

    translated_text = tokenizer.batch_decode(
        output_tokens,
        skip_special_tokens=True,
    )[0].strip()

    if not translated_text:
        raise RuntimeError("NLLB returned an empty translation.")

    return translated_text
