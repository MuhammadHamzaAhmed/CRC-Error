from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

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
    from activities.logger import workflow_logger as logger


# No retry policy - fail immediately on error
NO_RETRY_POLICY = RetryPolicy(maximum_attempts=1)


@workflow.defn
class CrcErrorWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        logger.info(f"Starting CrcErrorWorkflow for {input.ip} using {input.protocol}")

        logger.info("Executing login activity...")
        login_result = await workflow.execute_activity(
            login_activity,
            LoginInput(ip=input.ip, protocol=input.protocol),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=NO_RETRY_POLICY,
        )
        logger.info("Login activity completed")

        logger.info("Executing physical interface activity...")
        phys_if_result = await workflow.execute_activity(
            get_phys_if_activity,
            PhysIfInput(ip=login_result.ip, protocol=login_result.protocol),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY_POLICY,
        )
        logger.info(f"Physical interface activity completed. Found {len(phys_if_result.interfaces)} interfaces")

        logger.info("Executing ingress total activity...")
        result = await workflow.execute_activity(
            get_ingr_total_activity,
            IngrTotalInput(
                ip=phys_if_result.ip,
                interfaces=phys_if_result.interfaces,
                protocol=phys_if_result.protocol,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY_POLICY,
        )
        logger.info("Ingress total activity completed")

        logger.info(f"Workflow completed successfully. Result contains {len(result)} interfaces")
        return result
