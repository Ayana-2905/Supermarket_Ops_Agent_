import asyncio

from agents import Runner

from app.agent.agent import kirana_pilot

from app.agent.tools import (
    _confirm_pending_bill,
    is_confirmation
)


async def process_input(user_input: str):

    # Explicit confirmation is handled by the application,
    # not by the LLM.
    if is_confirmation(user_input):

        result = _confirm_pending_bill(
            payment_mode="CASH"
        )

        if "error" in result:
            return f"Cannot confirm sale: {result['error']}"

        return (
            f"Sale completed successfully.\n\n"
            f"Bill Number: {result['bill_number']}\n"
            f"Status: {result['status']}\n"
            f"Payment: {result['payment_mode']}\n"
            f"Total: ₹{result['total']:.2f}"
        )

    # Everything else goes through the AI agent
    result = await Runner.run(
        kirana_pilot,
        user_input
    )

    return result.final_output


async def main():

    print("=" * 60)
    print("KiranaPilot - Inventory Assistant")
    print("Type 'exit' to stop.")
    print("=" * 60)

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            break

        if not user_input:
            continue

        try:

            response = await process_input(
                user_input
            )

            print(f"\nKiranaPilot: {response}")

        except Exception as e:

            print(
                f"\nKiranaPilot: Something went wrong: {e}"
            )


if __name__ == "__main__":
    asyncio.run(main())