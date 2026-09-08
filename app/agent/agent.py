from agents import Agent, OpenAIChatCompletionsModel

from app.agent.instructions import AGENT_INSTRUCTIONS
from app.agent.tools import (
    search_products,
    get_product,
    get_stock,
    get_low_stock,
    add_product,
    receive_stock,
    count_products,
    list_inventory,
    get_total_inventory_quantity,
    create_draft_bill,
    edit_draft_bill,
    get_pending_bill,
    add_khata_credit,
    settle_khata,
    get_khata_balance,
    get_khata_transactions,
    generate_invoice,
    get_daily_sales_summary,
    set_owner_preference,
    get_owner_preferences,
    generate_sales_analysis
)

from app.domain.preferences.service import PreferenceService
from app.infrastructure.database.database import SessionLocal
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
            "\n\nOWNER PREFERENCES:\n"
            + "\n".join(
                f"- {key}: {value}"
                for key, value in preferences.items()
            )
        )

    finally:
        db.close()


owner_preferences = load_owner_preferences()


kirana_pilot = Agent(
    name="KiranaPilot",

    instructions=(
        AGENT_INSTRUCTIONS
        + owner_preferences
    ),

    model=groq_model,

    tools=[
        search_products,
        get_product,
        get_stock,
        get_low_stock,
        add_product,
        receive_stock,
        count_products,
        list_inventory,
        get_total_inventory_quantity,
        create_draft_bill,
        edit_draft_bill,
        get_pending_bill,
        add_khata_credit,
        settle_khata,
        get_khata_balance,
        get_khata_transactions,
        generate_invoice,
        get_daily_sales_summary,
        set_owner_preference,
        get_owner_preferences,
        generate_sales_analysis
    ]
)