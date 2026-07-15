"""Base context shared by Explorer page modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.ssr.explorer.fetch import ExplorerFetcher

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


@dataclass
class PageContext:
    """Read-model facade and version for a page handler group."""

    fetch: ExplorerFetcher

    @property
    def version(self) -> str:
        return self.fetch.version

    @classmethod
    def from_server(cls, ctx: ServerContext) -> PageContext:
        return cls(fetch=ExplorerFetcher(ctx))
