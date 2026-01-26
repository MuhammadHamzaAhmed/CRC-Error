from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# No retry policy - fail immediately on error
NO_RETRY = RetryPolicy(maximum_attempts=1)

with workflow.unsafe.imports_passed_through():
    from activities import (
        login_activity,
        get_phys_if_activity,
        get_ingr_total_activity,
        store_history_activity,
        calculate_delta_activity,
        evaluate_incident_activity,
        LoginInput,
        PhysIfInput,
        IngrTotalInput,
        StoreHistoryInput,
        DeltaInput,
        IncidentInput,
        WorkflowInput,
    )


@workflow.defn
class CrcErrorWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        """
        Execute CRC Error detection workflow.

        Flow:
        1. Login to ACI
        2. Get physical interfaces (with CRC errors, adminSt)
        3. Get ingress totals (with pktsCum)
        4. Store history to MongoDB
        5. Calculate deltas between polls
        6. Evaluate incidents based on rules

        Each activity returns analytics for debugging but:
        - Analytics are NOT passed to next activity
        - Analytics are NOT stored in DB
        - Analytics are NOT included in final output
        """

        # Step 1: Login to ACI
        login_result = await workflow.execute_activity(
            login_activity,
            LoginInput(ip=input.ip, protocol=input.protocol),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=NO_RETRY,
        )

        # Step 2: Get physical interfaces (CRC errors, adminSt, node)
        # Analytics returned but not passed forward
        phys_if_result = await workflow.execute_activity(
            get_phys_if_activity,
            PhysIfInput(ip=login_result.ip, protocol=login_result.protocol),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY,
        )

        # Step 3: Get ingress totals (pktsCum)
        # Analytics returned but not passed forward
        ingr_total_result = await workflow.execute_activity(
            get_ingr_total_activity,
            IngrTotalInput(
                ip=phys_if_result.ip,
                interfaces=phys_if_result.interfaces,  # Pass interfaces only, not analytics
                protocol=phys_if_result.protocol,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY,
        )

        # Step 4: Store history to MongoDB
        # Analytics returned but not passed forward
        store_result = await workflow.execute_activity(
            store_history_activity,
            StoreHistoryInput(
                ip=ingr_total_result.ip,
                interfaces=ingr_total_result.interfaces,  # Pass interfaces only, not analytics
                protocol=ingr_total_result.protocol,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY,
        )

        # Step 5: Calculate deltas between polls
        # Analytics returned but not passed forward
        delta_result = await workflow.execute_activity(
            calculate_delta_activity,
            DeltaInput(
                ip=store_result.ip,
                poll_id=store_result.poll_id,
                protocol=store_result.protocol,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY,
        )

        # Step 6: Evaluate incidents
        # Analytics returned but not included in final output
        incident_result = await workflow.execute_activity(
            evaluate_incident_activity,
            IncidentInput(
                ip=delta_result.ip,
                deltas=delta_result.deltas,  # Pass deltas only, not analytics
                protocol=delta_result.protocol,
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=NO_RETRY,
        )

        # Final output - all details except analytics
        # Count total interfaces across all nodes in nested structure
        total_interfaces = sum(len(ifaces) for ifaces in delta_result.deltas.values())
        return {
            "ip": incident_result.ip,
            "protocol": incident_result.protocol,
            "poll_id": store_result.poll_id,
            "total_interfaces": total_interfaces,
            "deltas": delta_result.deltas,
            "incidents": incident_result.incidents,
            "total_incidents": len(incident_result.incidents)
        }
