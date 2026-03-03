from __future__ import annotations

from cogentiq.knowledge import Knowledge
from runtime.orchestrator import ChatbotRuntime
from runtime.utils import setup_logging


def choose(label: str, options: list[str]) -> str:
    print(f"\nSelect {label}:")
    for i, x in enumerate(options, 1):
        print(f"  {i}. {x}")
    idx = int(input("> ")) - 1
    return options[idx]


def main() -> None:
    setup_logging()
    k = Knowledge("data")
    domain = choose("domain", k.domains())
    org = choose("org", k.orgs())
    usecase = choose("usecase", k.usecases())

    runtime = ChatbotRuntime("data")
    print("\nChat started. Type 'exit' to quit.")
    while True:
        q = input("You: ").strip()
        if q.lower() == "exit":
            break
        out = runtime.answer(domain, org, usecase, q)
        print("\nAssistant:")
        print(out["answer"])
        print("\nSources:")
        for s in out["sources"]:
            print("-", s)
        print("\nTools used:")
        for t in out["tool_traces"]:
            print("-", t["tool_name"], "=>", t["output_preview"])


if __name__ == "__main__":
    main()
