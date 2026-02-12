import httpx
import time
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime

from database import engine, create_db_and_tables
from models import AuditLog, SecurityPolicy
from config import settings
from schemas import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionResponseChoice
from safety_engine import safety_engine

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def log_request(user_input: str, response: str, risk_score: float, risk_details: dict, action: str, latency: float):
    print(f"DEBUG: Saving Log with details: {risk_details}")
    try:
        with Session(engine) as session:
            log = AuditLog(
                user_input=user_input,
                model_response=response,
                risk_score=risk_score,
                risk_details=json.dumps(risk_details),
                action=action,
                latency_ms=latency
            )
            session.add(log)
            session.commit()
    except Exception as e:
        print(f"ERROR: Failed to save log: {e}")

# Helper to check risk against policies
def check_risk(risk_map: dict, session: Session) -> (bool, str, str):
    # Returns (is_safe, blocked_category, reason)
    policies = session.exec(select(SecurityPolicy)).all()
    policy_map = {p.risk_category: p for p in policies if p.enabled}
    
    max_score = 0.0
    
    for category, score in risk_map.items():
        if score > max_score:
            max_score = score
            
        # Check against policy
        if category in policy_map:
            policy = policy_map[category]
            threshold = policy.threshold
            if score >= threshold:
                # Return generic blocked message with code
                # Frontend will handle localization
                return False, category, f"BLOCKED:{category}:{score:.4f}"

    return True, None, None


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    start_time = time.time()
    
    # 1. Extract User Prompt
    # We only check the LAST user message usually, or all? 
    # Let's check the last message for now for Prompt Safety
    last_user_msg = next((m for m in reversed(request.messages) if m.role == "user"), None)
    user_content = last_user_msg.content if last_user_msg else ""
    
    if not user_content:
        # Pass through if no user content?
        pass

    # 2. Prompt Safety Check
    # We construct a list of dicts for infer
    msgs_for_check = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Infer
    risk_map = safety_engine.infer(msgs_for_check, check_response=False)
    
    # Check Policy
    is_safe, blocked_cat, reason = check_risk(risk_map, session)
    
    if not is_safe:
        latency = (time.time() - start_time) * 1000
        # Log raw risk map
        background_tasks.add_task(log_request, user_content, None, risk_map.get(blocked_cat, 0), risk_map, "block_prompt", latency)
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=reason),
                    finish_reason="stop"
                )
            ]
        )

    # 3. Forward to Upstream LLM
    # Handle Streaming
    if request.stream:
        return await handle_streaming_response(request, user_content, session, background_tasks)

    # Standard Blocking Request
    try:
        async with httpx.AsyncClient() as client:
            upstream_response = await client.post(
                f"{settings.UPSTREAM_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {settings.UPSTREAM_API_KEY}"},
                json=request.dict(),
                timeout=60.0
            )
            upstream_response.raise_for_status()
            upstream_data = upstream_response.json()
            
            # Extract assistant response
            assistant_content = upstream_data['choices'][0]['message']['content']
            
    except Exception as e:
        # Fallback handling
        print(f"Upstream error: {e}")
        # Return mock response if upstream fails?
        assistant_content = "Error: Unable to contact upstream LLM."
        upstream_data = {
            "id": "error", "created": int(time.time()), "model": request.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": assistant_content}, "finish_reason": "stop"}]
        }

    # 4. Response Safety Check
    # Append assistant response to messages
    msgs_for_check_resp = msgs_for_check + [{"role": "assistant", "content": assistant_content}]
    
    resp_risk_map = safety_engine.infer(msgs_for_check_resp, check_response=True)
    is_safe_resp, blocked_cat_resp, reason_resp = check_risk(resp_risk_map, session)
    
    latency = (time.time() - start_time) * 1000
    
    if not is_safe_resp:
        # Block Response
        background_tasks.add_task(log_request, user_content, assistant_content, resp_risk_map.get(blocked_cat_resp, 0), resp_risk_map, "block_response", latency)
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=reason_resp),
                    finish_reason="stop"
                )
            ]
        )
    
    # 5. Allow
    background_tasks.add_task(log_request, user_content, assistant_content, 0.0, resp_risk_map, "allow", latency)
    
    # Construct response from upstream data
    # We basically pass through upstream_data but need to cast to our model
    return ChatCompletionResponse(**upstream_data)

from fastapi.responses import StreamingResponse

async def handle_streaming_response(request: ChatCompletionRequest, user_content: str, session: Session, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    async def stream_generator():
        full_content = ""
        client = httpx.AsyncClient()
        try:
            async with client.stream(
                "POST",
                f"{settings.UPSTREAM_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {settings.UPSTREAM_API_KEY}"},
                json=request.dict(),
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        body = line[6:] # Strip "data: "
                        if body != "[DONE]":
                            try:
                                json_body = json.loads(body)
                                # Accumulate content for audit
                                if "choices" in json_body and len(json_body["choices"]) > 0:
                                    delta = json_body["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_content += delta["content"]
                            except:
                                pass
                    yield line + "\n"
        except Exception as e:
            print(f"Stream Error: {e}")
            yield f'data: {{"error": "{str(e)}"}}\n\n'
        finally:
            await client.aclose()
            
            # Post-Stream Audit (Async)
            latency = (time.time() - start_time) * 1000
            
            # 1. Infer risk on full content
            # Reconstruct messages context
            msgs_context = [{"role": m.role, "content": m.content} for m in request.messages]
            msgs_context.append({"role": "assistant", "content": full_content})
            
            risk_map = safety_engine.infer(msgs_context, check_response=True)
            is_safe, blocked_cat, reason = check_risk(risk_map, session)
            
            if not is_safe:
               # Log as blocked (even though user saw it - Stream tradeoff)
               # Use a special action 'audit_fail_stream' ? Or just block_response
               print(f"Stream Audit Failed: {blocked_cat}")
               # We use a new session since the passed one might be closed/unsafe in generator? 
               # Actually log_request creates its own session.
               await log_request_async(user_content, full_content, risk_map.get(blocked_cat, 0), risk_map, "block_response_stream", latency)
            else:
               await log_request_async(user_content, full_content, 0.0, risk_map, "allow", latency)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

async def log_request_async(user_input, response, risk_score, risk_details, action, latency):
    # Wrapper to run sync log_request in threadpool if needed, but log_request is sync.
    # We can just call it directly since we are in async generator (blocking loop slightly but ok for log)
    # Better: Use same logic as background tasks but we are inside the generator which is async.
    # We can just call the synchronous log_request here, it's fast enough DB write.
    log_request(user_input, response, risk_score, risk_details, action, latency)
