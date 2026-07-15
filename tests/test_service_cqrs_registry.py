"""Service CQRS contributor registry."""

from __future__ import annotations

from palm.common.cqrs.service_contributors import (
    ServiceCqrsContributor,
    iter_service_cqrs_contributors,
    register_service_cqrs_contributor,
)


def test_register_and_iterate_service_contributors() -> None:
    before = len(iter_service_cqrs_contributors())

    def wire(_cmd, _qry, _ctx) -> None:
        pass

    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="demo-registry-test",
            command_types=(str,),
            query_types=(int,),
            wire=wire,
        )
    )
    contributors = iter_service_cqrs_contributors()
    assert len(contributors) == before + 1
    assert any(item.service_name == "demo-registry-test" for item in contributors)