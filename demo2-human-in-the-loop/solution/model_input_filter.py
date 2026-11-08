# ABOUTME: RunConfig that drops null-valued fields from the model input before every LLM call.
# Works around gateways that return explicit nulls (e.g. "namespace": null) on output items.

# Why this exists: some OpenAI-compatible gateways, such as the LiteLLM proxy
# the hosted workshop uses, return output items with explicit nulls, e.g. a
# function_call with "namespace": null. The Agents SDK copies each output item
# into the next model call's input. The Temporal plugin's model activity then
# validates that input against the OpenAI SDK's input types, which reject null
# for those fields. The activity fails with "Failed decoding arguments" on the
# first model call after a tool call. A field that is null carries no
# information, so leaving it out is equivalent.

from typing import Any

from agents import RunConfig
from agents.run_config import CallModelData, ModelInputData


def _drop_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_nulls(v) for v in value]
    return value


def drop_null_fields(data: CallModelData[Any]) -> ModelInputData:
    """Return the model input with every null-valued field removed."""
    return ModelInputData(
        input=[_drop_nulls(item) for item in data.model_data.input],
        instructions=data.model_data.instructions,
    )


# Pass this to Runner.run(..., run_config=RUN_CONFIG).
RUN_CONFIG = RunConfig(call_model_input_filter=drop_null_fields)
