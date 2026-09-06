from agents import Agent, OpenAIChatCompletionsModel

from app.agent.instructions import AGENT_INSTRUCTIONS
from app.domain.preferences.service import PreferenceService
from app.infrastructure.database.database import SessionLocal
from app.agent.tools import (
    search_products,
    get_product,
    get_stock,
    count_products,
    get_low_stock,
    get_total_inventory_quantity,
    list_inventory,
    add_product,
    receive_stock,

    create_draft_bill,
    edit_draft_bill,
    get_pending_bill,

    add_khata_credit,
    settle_khata,
    get_khata_balance,
    get_khata_transactions,

    generate_invoice,

    confirm_pending_bill,

    get_daily_sales_summary,
    generate_sales_analysis,
    set_owner_preference,
    get_owner_preferences, 
    generate_sales_deck, 
)

from app.infrastructure.llm.provider import groq_client


groq_model = OpenAIChatCompletionsModel(
    model="openai/gpt-oss-20b",
    openai_client=groq_client
)



def load_owner_preferences():
    db = SessionLocal()

    try:
        service = PreferenceService(db)
        preferences = service.get_all_preferences()

        if not preferences:
            return ""

        return (
            "\n\nOWNER PREFERENCES\n"
            "-----------------\n"
            + "\n".join(
                f"- {key}: {value}"
                for key, value in preferences.items()
            )
        )

    finally:
        db.close()


OWNER_PREFERENCES = load_owner_preferences()
kirana_pilot = Agent(
    name="KiranaPilot",

    instructions=AGENT_INSTRUCTIONS+OWNER_PREFERENCES,

    model=groq_model,

    tools=[
        # Inventory
        search_products,
        get_product,
        get_stock,
        count_products,
        get_low_stock,
        get_total_inventory_quantity,
        list_inventory,
        add_product,
        receive_stock,

        # Billing
        create_draft_bill,
        edit_draft_bill,
        get_pending_bill,

        # Khata
        add_khata_credit,
        settle_khata,
        get_khata_balance,
        get_khata_transactions,

        # Invoice
        generate_invoice,

        # Confirmation
        confirm_pending_bill,

        get_daily_sales_summary,
        generate_sales_analysis,
        set_owner_preference,
        get_owner_preferences,
        generate_sales_deck,
    ]
)