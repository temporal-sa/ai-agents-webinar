from temporalio import workflow
from datetime import timedelta

import json

# Marks these imports as side-effect-free so the workflow sandbox allows them without re-validating determinism.
with workflow.unsafe.imports_passed_through():
    from tools import get_tools
    from helpers import tool_helpers
    from activities import openai_responses

# Workflow: durable, replayable orchestration logic.
@workflow.defn
class AgentWorkflow:
    # Entry point Temporal calls to start the workflow.
    @workflow.run
    async def run(self, input: str) -> str:

        input_list = [{"type": "message", "role": "user", "content": input}]

        # TODO: Uncomment the agentic loop below.
        # Each pass calls the LLM as a durable activity, then either dispatches
        # every tool the model asked for (feeding the results back into input_list)
        # or returns the model's final text answer, ending the loop.
        # while True:
        #     workflow.logger.info("=" * 80)
        #
        #     # consult the LLM
        #     # Activity: a durable, retryable unit of non-deterministic work (I/O, API calls).
        #     llm_result = await workflow.execute_activity(
        #         openai_responses.invoke_model,
        #         openai_responses.OpenAIResponsesRequest(
        #             model="gpt-6.1-terra",
        #             instructions=tool_helpers.HELPFUL_AGENT_SYSTEM_INSTRUCTIONS,
        #             input=input_list,
        #             tools=get_tools(),
        #         ),
        #         # Start-to-close timeout: max time Temporal allows one activity attempt to run.
        #         start_to_close_timeout=timedelta(seconds=60),
        #     )
        #
        #     # One response can hold several output items: reasoning, one or more
        #     # function calls, and/or a message. Add them all to the conversation
        #     # so the next LLM call sees everything the model just produced.
        #     input_list += [item.model_dump(exclude_none=True) for item in llm_result.output]
        #
        #     function_calls = [item for item in llm_result.output if item.type == "function_call"]
        #
        #     # if the LLM didn't ask for any tools, respond with its message
        #     if not function_calls:
        #         workflow.logger.info(
        #             "No tools chosen, responding with a message: %s",
        #             llm_result.output_text,
        #         )
        #         return llm_result.output_text
        #
        #     # otherwise call every tool it asked for
        #     for item in function_calls:
        #         tool_output = await self._handle_function_call(item)
        #
        #         # add the tool call result to the input list for context
        #         input_list.append({
        #             "type": "function_call_output",
        #             "call_id": item.call_id,
        #             "output": tool_output,
        #         })


    async def _handle_function_call(self, item):
        # execute dynamic activity with the tool name chosen by the LLM
        # and the arguments crafted by the LLM
        args = json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments

        # Activity: a durable, retryable unit of non-deterministic work (I/O, API calls).
        tool_output = await workflow.execute_activity(
            item.name,
            args,
            # Start-to-close timeout: max time Temporal allows one activity attempt to run.
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info("Made a tool call to %s", item.name)

        return tool_output
