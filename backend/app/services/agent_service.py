from google import genai
from google.genai import types
from app.config import get_settings
from app.database.vector_db import retrieve_context
from app.schemas import ChatMessage, UserRole
from typing import AsyncGenerator

settings = get_settings()

GLOBAL_SYSTEM_PROMPT = """Bạn là Agent Trợ lý Kỹ thuật của Team Tech, hoạt động theo kiến trúc Global Core + Local Project Knowledge.
Nhiệm vụ: hỗ trợ Dev (Lập trình viên) và QC (Kiểm thử viên) dựa trên tài liệu đặc tả dự án được cung cấp.

# QUY TẮC BẮT BUỘC
- Chỉ trả lời dựa trên DỮ LIỆU ĐẶC TẢ DỰ ÁN được cung cấp bên dưới.
- Nếu tài liệu không đề cập, hãy nói rõ: "Tài liệu hiện tại chưa mô tả phần này."
- Tuyệt đối không tự suy diễn logic nghiệp vụ ngoài tài liệu.
- Ngôn ngữ: Tiếng Việt chuyên ngành IT. Văn phong ngắn gọn, trực tiếp.

# CHUẨN ĐẦU RA CHO QC
Khi nhận diện yêu cầu từ QC hoặc liên quan đến kiểm thử:
- Định dạng Test Case: Bảng Markdown: | ID | Feature | Scenario | Pre-conditions | Steps | Expected Result | Test Type |
- Test Type: Happy Path / Negative / Edge Case
- Luôn bao gồm đủ 3 nhóm: Happy Path, Negative Path, Edge Cases (timeout, mất kết nối, race condition)
- Định dạng Bug Jira: **Title** | **Environment** | **Steps to Reproduce** | **Expected vs Actual** | **Logs**

# CHUẨN ĐẦU RA CHO DEV
Khi nhận diện yêu cầu từ Dev hoặc liên quan đến code:
- Code phải có Exception Handling, logging đầy đủ nhưng không log thông tin nhạy cảm (OTP, password, token)
- Luôn xuất kèm GitLab MR Template:
  ```
  ## Purpose: [Jira Ticket] - Mục đích
  ## Changes: Các file/logic thay đổi
  ## Testing: Hướng dẫn QC test tính năng này
  ## Checklist: [ ] Unit test [ ] Backward compatible
  ```

# CÔNG CỤ & MÔI TRƯỜNG
- Quản lý công việc: Jira | Quản lý code: GitLab | Tài liệu: Confluence, Figma

# DỮ LIỆU ĐẶC TẢ DỰ ÁN
{project_context}"""


def build_system_prompt(project_context: str) -> str:
    if not project_context:
        context_text = "⚠️ Chưa có tài liệu đặc tả nào được nạp cho dự án này. Hãy thông báo cho người dùng upload tài liệu trước."
    else:
        context_text = project_context
    return GLOBAL_SYSTEM_PROMPT.format(project_context=context_text)


def build_role_hint(user_role: UserRole) -> str:
    if user_role == UserRole.qc:
        return "[Người dùng là QC - Ưu tiên định dạng Test Case và Bug Report]\n"
    return "[Người dùng là Dev - Ưu tiên định dạng code và MR Template]\n"


async def stream_chat(
    project_id: str,
    user_role: UserRole,
    message: str,
    history: list[ChatMessage]
) -> AsyncGenerator[str, None]:
    client = genai.Client(api_key=settings.gemini_api_key)

    # RAG: only retrieve docs for this specific project
    project_context = retrieve_context(query=message, project_id=project_id, k=5)
    system_prompt = build_system_prompt(project_context)
    role_hint = build_role_hint(user_role)

    # Build conversation history (keep last 10 turns)
    contents = []
    for msg in history[-10:]:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))

    # Add current message with role hint
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=role_hint + message)]
    ))

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.2,
        max_output_tokens=4096,
    )

    async for chunk in await client.aio.models.generate_content_stream(
        model=settings.gemini_flash_model,
        contents=contents,
        config=config,
    ):
        if chunk.text:
            yield chunk.text
