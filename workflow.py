from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import (
        login_activity,
        get_phys_if_activity,
        get_ingr_total_activity,
        LoginInput,
        PhysIfInput,
        IngrTotalInput,
        WorkflowInput,
    )


@workflow.defn
class CrcErrorWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        ip = await workflow.execute_activity(
            login_activity,
            LoginInput(ip=input.ip),
            start_to_close_timeout=timedelta(seconds=30),
        )

        phys_if_result = await workflow.execute_activity(
            get_phys_if_activity,
            PhysIfInput(ip=ip),
            start_to_close_timeout=timedelta(seconds=60),
        )

        result = await workflow.execute_activity(
            get_ingr_total_activity,
            IngrTotalInput(
                ip=phys_if_result.ip,
                interfaces=phys_if_result.interfaces,
            ),
            start_to_close_timeout=timedelta(seconds=60),
        )

        return result
