"""Simple evaluation harness for local Ollama models.

Sends a code snippet to one or more Ollama models running at localhost:11434 and
collects their analysis. Saves per-model JSON outputs under tests/unit/outputs/.

Usage:
  python tests/unit/test_ollama_model_eval.py --models gemma3:latest granite4:latest

If no models are provided, defaults are read from .env: OLLAMA_MODEL and
OLLAMA_SUBAGENT_MODEL.

This script uses a lightweight heuristic scorer to rank model responses by
presence of code-analysis keywords and JSON structure.
"""

import os
import json
import re
import argparse
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434").rstrip("/")
# Note: When reading from .env, strip the ollama_chat/ prefix for native Ollama API
DEFAULT_MODEL_RAW = os.environ.get("OLLAMA_MODEL", "granite4:latest")
DEFAULT_MODEL = DEFAULT_MODEL_RAW.replace("ollama_chat/", "")

"""
Available models (use plain names for native Ollama API):
phi4:latest                
granite4:latest                
gemma3:latest                  
tinyllama:latest               
nomic-embed-text:latest        
llama3.1:8b 
gpt-oss                  
"""

OUT_DIR = Path(__file__).parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CODE_SNIPPET = '''
async def run_agent_sequential(agent, code_submission: str, session_service, agent_name: str, max_retries: int = 3):
    """Helper function to run a single agent with retry logic and return its response"""
    for attempt in range(max_retries):
        try:
            print(f"--- Sequential Pipeline: Executing {agent_name} (attempt {attempt + 1}/{max_retries}) ---")
            
            # Create runner for this specific agent
            runner = Runner(
                agent=agent,
                app_name="code_review_sequential",
                session_service=session_service
            )
            
            # Create session for this analysis
            session = await session_service.create_session(
                app_name="code_review_sequential",
                user_id="orchestrator",
                session_id=f"analysis_{agent_name}_{attempt}"
            )
            
            # Prepare user message with code
            content = types.Content(
                role='user', 
                parts=[types.Part(text=f"Analyze this code:\n\n{code_submission}")]
            )
            
            # Run agent and capture result
            final_response = ""
            async for event in runner.run_async(
                user_id="orchestrator",
                session_id=f"analysis_{agent_name}_{attempt}",
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    break
            
            if final_response:
                print(f"--- Sequential Pipeline: {agent_name} completed successfully ---")
                return final_response
            else:
                print(f"--- Sequential Pipeline: {agent_name} returned empty response ---")
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    backoff_delay = 2 ** attempt
                    print(f"--- Sequential Pipeline: Retrying {agent_name} in {backoff_delay}s ---")
                    await asyncio.sleep(backoff_delay)
                    continue
                else:
                    return f"Analysis incomplete: {agent_name} returned empty response after {max_retries} attempts"
        
        except Exception as e:
            print(f"--- Sequential Pipeline: Error in {agent_name} (attempt {attempt + 1}): {str(e)} ---")
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                backoff_delay = 2 ** attempt
                print(f"--- Sequential Pipeline: Retrying {agent_name} in {backoff_delay}s due to error ---")
                await asyncio.sleep(backoff_delay)
                continue
            else:
                return f"Analysis failed: {agent_name} failed after {max_retries} attempts. Last error: {str(e)}"
    
    return f"Analysis failed: {agent_name} exceeded maximum retry attempts"
'''

PROMPT_TEMPLATE = (
    "You are an expert software engineer. Analyze the following Python code snippet "
    "and produce a JSON object with these fields: summary (short), issues (array of {{severity, location, description}}), "
    "recommendations (array of short actionable items). Return ONLY a single JSON object, no extra text.\n\n"
    "Code:\n" + """{code}"""
)

KEYWORDS = [
    "security",
    "vulnerab",
    "complexit",
    "recurs",
    "performance",
    "bug",
    "overflow",
    "stack",
    "error",
    "refactor",
    "readab",
]


def call_ollama_generate(
    model: str, 
    prompt: str, 
    timeout: int = 60,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 40,
    repeat_penalty: float = 1.1
):
    """Call Ollama's /api/generate endpoint with tunable parameters.
    
    Args:
        model: Model name (e.g., 'gemma3:latest')
        prompt: The prompt text
        timeout: Request timeout in seconds
        temperature: Controls randomness (0.0-2.0). Lower = more focused/deterministic
        top_p: Nucleus sampling threshold (0.0-1.0). Lower = more focused
        top_k: Limits vocabulary to top K tokens. Lower = more focused
        repeat_penalty: Penalizes repetition (1.0 = no penalty, >1.0 = penalize)
    
    Returns response text or raises.
    """
    url = f"{OLLAMA_API}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,  # Disable streaming for cleaner JSON response
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "num_predict": 2048,  # Max tokens to generate
        }
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    # Ollama may return plain text or JSON; prefer text
    return resp.text


def extract_json(text: str):
    """Try to extract a JSON object from the model output."""
    # First try to parse entire text
    try:
        return json.loads(text)
    except Exception:
        pass
    # Fallback: find first { ... } block
    m = re.search(r"\{(?:.|\n)*\}", text)
    if m:
        sub = m.group(0)
        try:
            return json.loads(sub)
        except Exception:
            return {"raw": text}
    return {"raw": text}


def score_response(j: dict):
    """Simple heuristic scoring: presence of keywords and structured fields."""
    s = 0
    text = json.dumps(j).lower()
    # reward structured fields
    if "summary" in j:
        s += 5
    if "issues" in j and isinstance(j.get("issues"), list):
        s += 10
        s += min(20, len(j.get("issues")) * 2)
    if "recommend" in j or "recommendations" in j:
        s += 5
    # keyword matches
    for k in KEYWORDS:
        if k in text:
            s += 1
    # penalize raw output
    if j.keys() == {"raw"}:
        s -= 5
    return s


def evaluate_models(models, temperature=0.7, top_p=0.9, top_k=40, repeat_penalty=1.1):
    """Evaluate models with specified generation parameters."""
    results = []
    print(f"\n🔧 Generation Parameters: temp={temperature}, top_p={top_p}, top_k={top_k}, repeat_penalty={repeat_penalty}")
    
    for model in models:
        print(f"\n== Testing model: {model} ==")
        prompt = PROMPT_TEMPLATE.format(code=CODE_SNIPPET)
        start = time.time()
        try:
            out = call_ollama_generate(
                model, 
                prompt, 
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty
            )
            elapsed = time.time() - start
            parsed = extract_json(out)
            score = score_response(parsed)
            
            # Save with parameter info in filename
            param_suffix = f"_t{temperature}_p{top_p}_k{top_k}"
            out_path = OUT_DIR / f"{model.replace(':','_').replace('/','_')}{param_suffix}.json"
            
            with open(out_path, "w") as f:
                json.dump({
                    "model": model, 
                    "elapsed": elapsed, 
                    "score": score, 
                    "params": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "repeat_penalty": repeat_penalty
                    },
                    "parsed": parsed
                }, f, indent=2)
            print(f"Model {model} responded in {elapsed:.2f}s, score={score}")
        except Exception as e:
            elapsed = time.time() - start
            print(f"Model {model} failed: {e}")
            parsed = {"error": str(e)}
            score = -100
            param_suffix = f"_t{temperature}_p{top_p}_k{top_k}"
            out_path = OUT_DIR / f"{model.replace(':','_').replace('/','_')}{param_suffix}.json"
            with open(out_path, "w") as f:
                json.dump({
                    "model": model, 
                    "elapsed": elapsed, 
                    "score": score, 
                    "params": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "repeat_penalty": repeat_penalty
                    },
                    "parsed": parsed
                }, f, indent=2)
        results.append({"model": model, "elapsed": elapsed, "score": score, "parsed": parsed})
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Evaluate Ollama models with tunable generation parameters")
    p.add_argument("--models", nargs="*", help="List of Ollama models to test (e.g. gemma3:latest)")
    p.add_argument("--temperature", type=float, default=0.3, 
                   help="Temperature (0.0-2.0). Lower=more focused. Default: 0.3 (good for code analysis)")
    p.add_argument("--top-p", type=float, default=0.9, 
                   help="Top-p nucleus sampling (0.0-1.0). Default: 0.9")
    p.add_argument("--top-k", type=int, default=40, 
                   help="Top-k sampling limit. Default: 40")
    p.add_argument("--repeat-penalty", type=float, default=1.1,
                   help="Repetition penalty (1.0=none, >1.0=penalize). Default: 1.1")
    args = p.parse_args()

    if args.models and len(args.models) > 0:
        models = args.models
    else:
        models = []
        if DEFAULT_MODEL:
            models.append(DEFAULT_MODEL)
        
    print("Testing models:", models)
    results = evaluate_models(
        models,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        repeat_penalty=args.repeat_penalty
    )
    # sort by score desc
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    print("\n📊 Summary ranking:")
    for r in results_sorted:
        print(f"- {r['model']}: score={r['score']} elapsed={r['elapsed']:.2f}s")

    best = results_sorted[0]
    print(f"\n🏆 Best model: {best['model']} (score={best['score']})")
    print("Outputs saved under:", OUT_DIR)
