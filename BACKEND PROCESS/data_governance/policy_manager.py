from database.connection import SessionLocal
from data_governance.governance_model import GovernancePolicy


def get_all_policies():

    db = SessionLocal()

    try:

        policies = db.query(
            GovernancePolicy
        ).all()

        result = []

        for policy in policies:

            result.append({

                "id": policy.id,

                "policy_name": policy.policy_name,

                "description": policy.description,

                "status": policy.status,

                "created_at": str(
                    policy.created_at
                )

            })

        return result

    finally:

        db.close()