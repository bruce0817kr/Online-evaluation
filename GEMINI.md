구조적 변경 우선)

- **구조적 변경(Structural Change)**과 **행위 변경(Behavioral Change)**을 반드시 분리  
  - 구조적 변경: 리네이밍, 함수 추출, 코드 이동 등 (동작 변화 없음)
  - 행위 변경: 실제 기능 추가/변경
- 구조적 변경이 필요하면 **먼저** 진행, 테스트 통과 확인
- 두 변경을 **같은 커밋에 포함 금지**
- 변경 전후 반드시 테스트 실행

### 2.3 커밋 및 작업 단위

- 모든 테스트/컴파일/린트 통과 시에만 커밋
- 한 번에 하나의 논리적 변경만 커밋
- 커밋 메시지에 **[구조적 변경]** 또는 **[행위 변경]** 명확히 표기

### 2.4 코드 품질 기준

- 중복 제거, 명확한 의도 표현, 함수/메서드 단일 책임
- 상태/부수효과 최소화
- React/TypeScript: 함수형 스타일, Option/Result/map/andThen 등 함수형 패턴 우선
- Python: 타입 힌트, 불변 데이터, 함수형 스타일(map/filter/reduce) 우선

## 3. MCP & Gemini 활용 규the weather in London today?"
            await session.initialize()
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[session],
                ),
            )
            print(response.text)
```

#### TypeScript

```typescript
import { GoogleGenAI } from "@google/genai";
const ai = new GoogleGenAI({});
const mcpServer = {
  command: "npx",
  args: ["-y", "gemini-mcp-tool"]
};
const tools = [mcpServer];
const contents = [
  {
    role: "user",
    parts: [{ text: "Analyze the architecture of this GitHub repository." }]
  }
];
const result = await ai.models.generate_content({
  model: "gemini-2.5-flash",
  contents,
  config: { tools }
});
console.log(result.text);
```

### 3.4 실제 활용

- **코드 분석/아키텍처 설명**: Gemini가 MCP 서버를 통해 대규모 코드베이스 구조, 의로 본 규칙 저장  
  - 반복되는 워크플로우는 프롬프트 파일로 관리  
- **MCP/Gemini**:  
  - 여러 도구/서버 등록해 필요에 따라 자동 호출  
  - 자연어 명령, 코드 프롬프트, 자동화된 분석/테스트에 모두 활용

**이 규칙을 프로젝트의 instruction 파일로 저장하면,  
TDD & Tidy First 기반의 고품질 개발과 MCP/Gemini 기반의 AI 자동화/분석을  
하나의 일관된 워크플로우로 실현할 수 있습니다.**